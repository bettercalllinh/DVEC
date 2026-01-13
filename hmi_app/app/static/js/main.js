// Screen State Manager for Damn Vulnerable EV Charger
class ScreenManager {
    constructor() {
        this.currentScreen = 'welcome';
        this.authTimeout = null;
        this.authTimeoutDuration = 90000; // 90 seconds
        this.nfcPollInterval = null;
        this.paymentPollInterval = null;
        this.socket = null;

        // Payment Portal URL (VPS)
        this.paymentPortalUrl = 'http://14.225.253.243:8081';

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.showScreen('welcome');
    }

    setupWebSocket() {
        // Connect to Socket.IO server
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to HMI server');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from HMI server');
        });

        // Listen for payment confirmation
        this.socket.on('payment_confirmed', (data) => {
            console.log('Payment confirmed:', data);
            this.showScreen('ready');
        });

        // Listen for NFC result (from WebSocket)
        this.socket.on('nfc_result', (data) => {
            console.log('NFC result via WebSocket:', data);
            if (data.type === 'valid') {
                this.showScreen('ready');
            } else {
                this.showScreen('auth-failed');
            }
        });
    }

    setupEventListeners() {
        // Welcome screen - click anywhere to go to auth
        const welcomeScreen = document.getElementById('screen-welcome');
        welcomeScreen.addEventListener('click', () => {
            this.showScreen('auth');
        });

        // Auth failed screen - click to go back to welcome
        const authFailedScreen = document.getElementById('screen-auth-failed');
        authFailedScreen.addEventListener('click', () => {
            this.showScreen('welcome');
        });

        // Ready screen - click to go back to welcome (for demo)
        const readyScreen = document.getElementById('screen-ready');
        readyScreen.addEventListener('click', () => {
            this.showScreen('welcome');
        });
    }

    showScreen(screenName) {
        // Clear any existing timeouts and intervals
        this.clearAuthTimeout();
        this.stopNFCPolling();
        // Don't stop payment polling - it runs on both welcome and auth screens

        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });

        // Show target screen
        const targetScreen = document.getElementById(`screen-${screenName}`);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentScreen = screenName;
        }

        // Screen-specific actions
        if (screenName === 'welcome') {
            // Start payment polling on welcome screen
            this.startPaymentPolling();
        } else if (screenName === 'auth') {
            this.generateQRCode();
            this.startAuthTimeout();
            this.startNFCPolling();
            this.startPaymentPolling();
        } else if (screenName === 'auth-failed') {
            // Auto-return to welcome after 3 seconds
            setTimeout(() => {
                if (this.currentScreen === 'auth-failed') {
                    this.showScreen('welcome');
                }
            }, 3000);
        } else if (screenName === 'ready') {
            // Stop polling when on ready screen
            this.stopPaymentPolling();
        }

        console.log(`Screen changed to: ${screenName}`);
    }

    generateQRCode() {
        const qrContainer = document.getElementById('qr-code');
        qrContainer.innerHTML = ''; // Clear previous QR code

        // Generate QR code pointing to payment portal (VPS)
        const paymentUrl = 'http://14.225.253.243:8081';

        try {
            new QRCode(qrContainer, {
                text: paymentUrl,
                width: 150,
                height: 150,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.H
            });
        } catch (error) {
            console.error('QR Code generation error:', error);
        }
    }

    startAuthTimeout() {
        // Set timeout to return to welcome after 90 seconds
        this.authTimeout = setTimeout(() => {
            if (this.currentScreen === 'auth') {
                console.log('Auth timeout - returning to welcome');
                this.showScreen('welcome');
            }
        }, this.authTimeoutDuration);
    }

    clearAuthTimeout() {
        if (this.authTimeout) {
            clearTimeout(this.authTimeout);
            this.authTimeout = null;
        }
    }

    startNFCPolling() {
        // Poll for NFC events every 500ms
        this.nfcPollInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/nfc/poll');
                const data = await response.json();

                if (data.event) {
                    console.log('NFC event received:', data.event);
                    if (data.event.type === 'valid') {
                        this.showScreen('ready');
                    } else if (data.event.type === 'invalid') {
                        this.showScreen('auth-failed');
                    }
                }
            } catch (error) {
                console.error('NFC polling error:', error);
            }
        }, 500);
    }

    stopNFCPolling() {
        if (this.nfcPollInterval) {
            clearInterval(this.nfcPollInterval);
            this.nfcPollInterval = null;
        }
    }

    startPaymentPolling() {
        // Poll payment portal for exploit success every 1 second
        this.paymentPollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.paymentPortalUrl}/api/payment-status`);
                const data = await response.json();

                if (data.exploit_success) {
                    console.log('Payment exploit detected! Amount:', data.amount);
                    this.showScreen('ready');
                }
            } catch (error) {
                // Silently ignore errors (VPS might not be reachable)
                console.log('Payment portal polling...', error.message);
            }
        }, 1000);

        console.log('Started payment polling to:', this.paymentPortalUrl);
    }

    stopPaymentPolling() {
        if (this.paymentPollInterval) {
            clearInterval(this.paymentPollInterval);
            this.paymentPollInterval = null;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.screenManager = new ScreenManager();
});
