// SysMon Modal functionality
class SysMonModal {
    constructor() {
        this.modal = null;
        this.iframe = null;
        this.loadingIndicator = null;
        this.sysmonUrl = '';
        this.isEnabled = false;
        this.init();
    }

    init() {
        // Get configuration from data attributes
        const configElement = document.getElementById('sysmon-config');
        if (configElement) {
            this.isEnabled = configElement.getAttribute('data-enabled') === 'true';
            this.sysmonUrl = configElement.getAttribute('data-url') || 'https://localhost:8888/';
        } else {
            // Fallback for backward compatibility
            this.isEnabled = window.sysmonEnabled || false;
            this.sysmonUrl = window.sysmonUrl || 'https://localhost:8888/';
        }
        
        if (!this.isEnabled) {
            console.warn('SysMon is disabled');
            return;
        }

        this.modal = document.getElementById('sysmonModal');
        this.iframe = document.getElementById('sysmonIframe');
        
        if (!this.modal || !this.iframe) {
            console.error('SysMon modal elements not found');
            return;
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close modal when clicking outside
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.close();
            }
        });

        // Handle iframe load events
        this.iframe.addEventListener('load', () => {
            this.hideLoading();
        });

        this.iframe.addEventListener('error', () => {
            this.showError();
        });
    }

    open() {
        if (!this.isEnabled) {
            alert('SysMon n\'est pas configuré ou désactivé');
            return;
        }

        try {
            // Validate URL
            const url = new URL(this.sysmonUrl);
            if (!['https:', 'http:'].includes(url.protocol)) {
                throw new Error('Invalid protocol');
            }

            // Validate hostname - only allow localhost and local network
            const hostname = url.hostname.toLowerCase();
            const allowedHostnames = [
                'localhost',
                '127.0.0.1',
                '0.0.0.0'
            ];
            
            // Allow local network ranges (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
            const isLocalNetwork = 
                hostname.startsWith('192.168.') ||
                hostname.startsWith('10.') ||
                hostname.startsWith('172.') ||
                hostname.startsWith('169.254.') ||
                hostname.endsWith('.local') ||
                hostname.endsWith('.localhost');

            if (!allowedHostnames.includes(hostname) && !isLocalNetwork) {
                throw new Error('Invalid hostname - only localhost and local networks allowed');
            }

            this.showLoading();
            this.iframe.src = url.toString();
            this.modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        } catch (error) {
            console.error('Invalid SysMon URL:', error);
            alert('L\'URL de SysMon n\'est pas valide ou n\'est pas autorisée');
        }
    }

    close() {
        this.modal.style.display = 'none';
        this.iframe.src = '';
        document.body.style.overflow = ''; // Restore scrolling
    }

    showLoading() {
        this.iframe.style.display = 'none';
        
        // Create or update loading indicator
        if (!this.loadingIndicator) {
            this.loadingIndicator = document.createElement('div');
            this.loadingIndicator.className = 'sysmon-loading';
            this.loadingIndicator.innerHTML = '<div>Chargement de SysMon...</div>';
            this.iframe.parentNode.appendChild(this.loadingIndicator);
        }
        this.loadingIndicator.style.display = 'flex';
    }

    hideLoading() {
        this.iframe.style.display = 'block';
        if (this.loadingIndicator) {
            this.loadingIndicator.style.display = 'none';
        }
    }

    showError() {
        this.iframe.style.display = 'none';
        
        // Create or update error indicator
        if (!this.loadingIndicator) {
            this.loadingIndicator = document.createElement('div');
            this.loadingIndicator.className = 'sysmon-error';
            this.loadingIndicator.innerHTML = `
                <div>
                    <h4>Erreur de connexion</h4>
                    <p>Impossible de se connecter à SysMon. Vérifiez que le service est en cours d'exécution.</p>
                    <button type="button" class="btn btn-secondary" onclick="sysMonModal.close()">Fermer</button>
                </div>
            `;
            this.iframe.parentNode.appendChild(this.loadingIndicator);
        }
        this.loadingIndicator.style.display = 'flex';
    }
}

// Initialize modal when DOM is ready
let sysMonModal;
document.addEventListener('DOMContentLoaded', function() {
    sysMonModal = new SysMonModal();
});

// Global functions for backward compatibility
function openSysMonModal() {
    if (sysMonModal) {
        sysMonModal.open();
    }
}

function closeSysMonModal() {
    if (sysMonModal) {
        sysMonModal.close();
    }
}
