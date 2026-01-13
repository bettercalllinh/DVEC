"""
NFC Reader Service for MFRC522
Reads NFC cards in a background thread and validates against valid_uid.txt
"""

import threading
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('nfc_reader')

# Flag to check if we're running on Raspberry Pi with SPI
HARDWARE_AVAILABLE = False

try:
    from app.mfrc522 import SimpleMFRC522
    import spidev
    # Try to open SPI to verify hardware is available
    test_spi = spidev.SpiDev()
    test_spi.open(1, 1)
    test_spi.close()
    HARDWARE_AVAILABLE = True
    logger.info("MFRC522 hardware detected - NFC reader enabled")
except Exception as e:
    logger.warning(f"MFRC522 hardware not available: {e}")
    logger.info("Running in simulation mode - use /api/nfc/simulate to test")


class NFCReader:
    """Background NFC card reader service"""

    def __init__(self, event_callback=None):
        """
        Initialize NFC reader

        Args:
            event_callback: Function to call when card is detected
                           Signature: callback(uid: str, valid: bool)
        """
        self.event_callback = event_callback
        self.running = False
        self.thread = None
        self.reader = None
        self.last_uid = None
        self.last_read_time = 0
        self.debounce_seconds = 2  # Prevent duplicate reads

        # Load valid UIDs
        self.valid_uids = self._load_valid_uids()
        logger.info(f"Loaded {len(self.valid_uids)} valid UIDs")

    def _get_valid_uids_file(self):
        """Get path to valid_uid.txt"""
        return os.path.join(os.path.dirname(__file__), '..', '..', 'valid_uid.txt')

    def _load_valid_uids(self):
        """Load valid UIDs from valid_uid.txt"""
        uid_file = self._get_valid_uids_file()
        uids = set()
        try:
            with open(uid_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        uids.add(line.upper())
        except FileNotFoundError:
            logger.warning(f"valid_uid.txt not found at {uid_file}")
        return uids

    def reload_valid_uids(self):
        """Reload valid UIDs from file (can be called to refresh)"""
        self.valid_uids = self._load_valid_uids()
        logger.info(f"Reloaded {len(self.valid_uids)} valid UIDs")

    def validate_uid(self, uid):
        """Check if UID is valid"""
        if not uid:
            return False
        return uid.upper() in self.valid_uids

    def start(self):
        """Start the NFC reader background thread"""
        if not HARDWARE_AVAILABLE:
            logger.info("NFC hardware not available - reader not started")
            return False

        if self.running:
            logger.warning("NFC reader already running")
            return True

        try:
            self.reader = SimpleMFRC522()
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            logger.info("NFC reader started")
            return True
        except Exception as e:
            logger.error(f"Failed to start NFC reader: {e}")
            return False

    def stop(self):
        """Stop the NFC reader"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=3)
        logger.info("NFC reader stopped")

    def _read_loop(self):
        """Main reading loop - runs in background thread"""
        logger.info("NFC read loop started - waiting for cards...")

        while self.running:
            try:
                # Non-blocking read attempt
                uid = self.reader.read_id_no_block()

                if uid:
                    current_time = time.time()

                    # Debounce: ignore same card within debounce period
                    if uid == self.last_uid and (current_time - self.last_read_time) < self.debounce_seconds:
                        time.sleep(0.1)
                        continue

                    self.last_uid = uid
                    self.last_read_time = current_time

                    # Convert UID to string (it's already hex from SimpleMFRC522)
                    uid_str = str(uid).upper()
                    is_valid = self.validate_uid(uid_str)

                    logger.info(f"Card detected - UID: {uid_str}, Valid: {is_valid}")

                    # Call the event callback if set
                    if self.event_callback:
                        self.event_callback(uid_str, is_valid)

                # Small delay to prevent CPU spinning
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error reading NFC: {e}")
                time.sleep(1)  # Longer delay on error

        logger.info("NFC read loop ended")


# Global reader instance
_reader_instance = None


def get_reader():
    """Get the global NFC reader instance"""
    global _reader_instance
    return _reader_instance


def init_reader(event_callback=None):
    """Initialize and start the global NFC reader"""
    global _reader_instance
    if _reader_instance is None:
        _reader_instance = NFCReader(event_callback=event_callback)
        _reader_instance.start()
    return _reader_instance


def is_hardware_available():
    """Check if NFC hardware is available"""
    return HARDWARE_AVAILABLE
