// Mobile-First Payment Portal JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // HMI Server URL - Update this if HMI is exposed publicly
    // For local demo: 'http://localhost:8080'
    // For VPS with exposed HMI: 'http://YOUR_HMI_IP:8080'
    const HMI_SERVER_URL = 'http://localhost:8080';

    // Connect to HMI server via WebSocket (optional - lab works without it)
    let hmiSocket = null;
    let hmiConnected = false;

    try {
        hmiSocket = io(HMI_SERVER_URL, {
            timeout: 5000,
            reconnectionAttempts: 3
        });

        hmiSocket.on('connect', () => {
            hmiConnected = true;
            console.log('[Lab] Connected to HMI server');
        });

        hmiSocket.on('connect_error', (error) => {
            hmiConnected = false;
            console.log('[Lab] HMI server not available (lab still works without it)');
        });

        hmiSocket.on('disconnect', () => {
            hmiConnected = false;
        });
    } catch (e) {
        console.log('[Lab] WebSocket not available');
    }

    // Helper to safely emit to HMI
    function notifyHMI(event, data) {
        if (hmiSocket && hmiConnected) {
            hmiSocket.emit(event, data);
            console.log('[Lab] Notified HMI:', event);
        } else {
            console.log('[Lab] HMI not connected (skipping notification)');
        }
    }

    // Screen navigation
    function showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        document.getElementById(screenId).classList.add('active');
    }

    // Payment screen - Pay button (normal flow)
    document.getElementById('btn-pay')?.addEventListener('click', async () => {
        const rawValue = document.getElementById('payment-amount').value;
        const amount = rawValue === '' ? 20 : parseFloat(rawValue);
        await processPayment(amount, 'payment');
    });

    // Start Lab button
    document.getElementById('btn-start-lab')?.addEventListener('click', () => {
        showScreen('screen-lab-intro');
    });

    // Lab navigation buttons
    document.getElementById('btn-start-challenge')?.addEventListener('click', () => {
        showScreen('screen-lab-discovery');
    });

    document.getElementById('btn-back-intro')?.addEventListener('click', () => {
        showScreen('screen-lab-intro');
    });

    document.getElementById('btn-found-it')?.addEventListener('click', () => {
        resetExploitForm();
        showScreen('screen-lab-exploit');
    });

    document.getElementById('btn-back-discovery')?.addEventListener('click', () => {
        showScreen('screen-lab-discovery');
    });

    document.getElementById('btn-restart')?.addEventListener('click', () => {
        resetExploitForm();
        showScreen('screen-payment');
    });

    // Modal close
    document.getElementById('btn-modal-close')?.addEventListener('click', () => {
        document.getElementById('modal-failure').classList.add('hidden');
    });

    // Simulate button - Run the exploit code
    document.getElementById('btn-simulate')?.addEventListener('click', () => {
        // Execute the exploit: set the hidden field to 0
        document.getElementById('payment-amount').value = 0;

        // Visual feedback - flash the button
        const btn = document.getElementById('btn-simulate');
        btn.innerHTML = '<span class="simulate-icon">&#10003;</span> Code Executed!';
        btn.style.background = 'linear-gradient(135deg, #4CAF50, #43a047)';

        // Reset button after 2 seconds
        setTimeout(() => {
            btn.innerHTML = '<span class="simulate-icon">&#9654;</span> Run Code';
            btn.style.background = '';
        }, 2000);

        console.log('[Lab] Exploit executed: document.getElementById("payment-amount").value = 0');
    });

    // Exploit pay button
    document.getElementById('btn-exploit-pay')?.addEventListener('click', async () => {
        const rawValue = document.getElementById('payment-amount').value;
        const amount = rawValue === '' ? 20 : parseFloat(rawValue);
        await processPayment(amount, 'exploit');
    });

    // Monitor payment amount field for exploit
    function monitorExploitField() {
        setInterval(() => {
            const field = document.getElementById('payment-amount');
            const display = document.getElementById('demo-amount-display');
            const btnText = document.getElementById('btn-amount-text');
            const badge = document.getElementById('modified-badge');

            if (!field || !display) return;

            const value = parseFloat(field.value) || 0;

            if (value !== 20) {
                display.textContent = `$${value.toFixed(2)}`;
                btnText.textContent = value;
                badge.classList.remove('hidden');
            } else {
                display.textContent = '$20.00';
                btnText.textContent = '20';
                badge.classList.add('hidden');
            }
        }, 300);
    }

    function resetExploitForm() {
        const field = document.getElementById('payment-amount');
        const display = document.getElementById('demo-amount-display');
        const btnText = document.getElementById('btn-amount-text');
        const badge = document.getElementById('modified-badge');

        if (field) field.value = '20';
        if (display) display.textContent = '$20.00';
        if (btnText) btnText.textContent = '20';
        if (badge) badge.classList.add('hidden');
    }

    // Process payment
    async function processPayment(amount, source) {
        try {
            const response = await fetch('/api/pay', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    amount: amount,
                    card: '4242424242424242',
                    expiry: '12/28',
                    cvv: '123'
                })
            });

            const result = await response.json();
            console.log('[Lab] Payment:', result);

            if (result.status === 'success') {
                if (amount < 20) {
                    // Exploit successful!
                    notifyHMI('payment_success', {
                        status: 'success',
                        message: 'Exploit payment',
                        amount: amount
                    });

                    document.getElementById('final-paid').textContent = `$${amount.toFixed(2)}`;
                    document.getElementById('final-saved').textContent = `$${(20 - amount).toFixed(2)}`;
                    showScreen('screen-lab-success');
                } else {
                    // Paid full amount - show failure modal
                    document.getElementById('modal-failure').classList.remove('hidden');
                }
            }
        } catch (error) {
            console.error('[Lab] Error:', error);
            alert('Payment failed. Please try again.');
        }
    }

    // Initialize
    monitorExploitField();

    console.log('[Lab] Payment Portal initialized');
    console.log('[Lab] Tip: document.getElementById("payment-amount").value = 0;');
});
