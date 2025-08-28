// Telegram WebApp API integration
class TelegramWebApp {
    constructor() {
        this.webapp = window.Telegram?.WebApp;
        this.isInitialized = false;
        this.user = null;
        this.init();
    }

    init() {
        if (!this.webapp) {
            console.warn('Telegram WebApp API not available');
            return;
        }

        try {
            // Initialize the web app
            this.webapp.ready();
            this.webapp.expand();
            
            // Apply theme
            this.applyTheme();
            
            // Enable closing confirmation
            this.webapp.enableClosingConfirmation();
            
            // Set up main button
            this.setupMainButton();
            
            // Set up back button
            this.setupBackButton();
            
            this.isInitialized = true;
            
            console.log('Telegram WebApp initialized', {
                version: this.webapp.version,
                platform: this.webapp.platform,
                colorScheme: this.webapp.colorScheme
            });
            
        } catch (error) {
            console.error('Error initializing Telegram WebApp:', error);
        }
    }

    applyTheme() {
        if (!this.webapp?.themeParams) return;

        const theme = this.webapp.themeParams;
        const root = document.documentElement;

        // Apply Telegram theme colors
        if (theme.bg_color) root.style.setProperty('--tg-theme-bg-color', theme.bg_color);
        if (theme.text_color) root.style.setProperty('--tg-theme-text-color', theme.text_color);
        if (theme.hint_color) root.style.setProperty('--tg-theme-hint-color', theme.hint_color);
        if (theme.link_color) root.style.setProperty('--tg-theme-link-color', theme.link_color);
        if (theme.button_color) root.style.setProperty('--tg-theme-button-color', theme.button_color);
        if (theme.button_text_color) root.style.setProperty('--tg-theme-button-text-color', theme.button_text_color);
        if (theme.secondary_bg_color) root.style.setProperty('--tg-theme-secondary-bg-color', theme.secondary_bg_color);
        if (theme.header_bg_color) root.style.setProperty('--tg-theme-header-bg-color', theme.header_bg_color);
        if (theme.accent_text_color) root.style.setProperty('--tg-theme-accent-text-color', theme.accent_text_color);
        if (theme.section_bg_color) root.style.setProperty('--tg-theme-section-bg-color', theme.section_bg_color);
        if (theme.section_header_text_color) root.style.setProperty('--tg-theme-section-header-text-color', theme.section_header_text_color);
        if (theme.subtitle_text_color) root.style.setProperty('--tg-theme-subtitle-text-color', theme.subtitle_text_color);
        if (theme.destructive_text_color) root.style.setProperty('--tg-theme-destructive-text-color', theme.destructive_text_color);

        // Add theme class to body
        document.body.classList.toggle('theme-dark', this.webapp.colorScheme === 'dark');
    }

    setupMainButton() {
        if (!this.webapp?.MainButton) return;

        const mainButton = this.webapp.MainButton;
        
        // Hide by default
        mainButton.hide();
        
        // Set up click handler
        mainButton.onClick(() => {
            const event = new CustomEvent('telegram-main-button-click');
            document.dispatchEvent(event);
        });
    }

    setupBackButton() {
        if (!this.webapp?.BackButton) return;

        const backButton = this.webapp.BackButton;
        
        // Set up click handler
        backButton.onClick(() => {
            const event = new CustomEvent('telegram-back-button-click');
            document.dispatchEvent(event);
        });
    }

    showMainButton(text, callback) {
        if (!this.webapp?.MainButton) return;

        const mainButton = this.webapp.MainButton;
        mainButton.setText(text);
        mainButton.show();
        
        if (callback) {
            document.removeEventListener('telegram-main-button-click', this.mainButtonCallback);
            this.mainButtonCallback = callback;
            document.addEventListener('telegram-main-button-click', callback);
        }
    }

    hideMainButton() {
        if (!this.webapp?.MainButton) return;
        this.webapp.MainButton.hide();
    }

    showBackButton() {
        if (!this.webapp?.BackButton) return;
        this.webapp.BackButton.show();
    }

    hideBackButton() {
        if (!this.webapp?.BackButton) return;
        this.webapp.BackButton.hide();
    }

    showAlert(message) {
        if (!this.webapp?.showAlert) {
            alert(message);
            return;
        }
        this.webapp.showAlert(message);
    }

    showConfirm(message, callback) {
        if (!this.webapp?.showConfirm) {
            const result = confirm(message);
            if (callback) callback(result);
            return;
        }
        this.webapp.showConfirm(message, callback);
    }

    hapticFeedback(type = 'impact') {
        if (!this.webapp?.HapticFeedback) return;

        switch (type) {
            case 'impact':
                this.webapp.HapticFeedback.impactOccurred('medium');
                break;
            case 'notification':
                this.webapp.HapticFeedback.notificationOccurred('success');
                break;
            case 'selection':
                this.webapp.HapticFeedback.selectionChanged();
                break;
        }
    }

    getInitData() {
        return this.webapp?.initData || '';
    }

    getUser() {
        return this.webapp?.initDataUnsafe?.user || null;
    }

    async authenticate() {
        const initData = this.getInitData();
        
        if (!initData) {
            console.warn('No init data available for authentication');
            // For development, allow without Telegram data
            return null;
        }

        try {
            const response = await fetch('/api/auth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ initData })
            });

            if (!response.ok) {
                throw new Error(`Authentication failed: ${response.status}`);
            }

            const result = await response.json();
            this.user = result.user;
            return result;
        } catch (error) {
            console.error('Authentication error:', error);
            throw error;
        }
    }

    setHeaderColor(color) {
        if (!this.webapp?.setHeaderColor) return;
        this.webapp.setHeaderColor(color);
    }

    setBackgroundColor(color) {
        if (!this.webapp?.setBackgroundColor) return;
        this.webapp.setBackgroundColor(color);
    }

    close() {
        if (!this.webapp?.close) return;
        this.webapp.close();
    }

    // Cloud Storage methods
    async getCloudStorageItem(key) {
        if (!this.webapp?.CloudStorage) return null;
        
        return new Promise((resolve) => {
            this.webapp.CloudStorage.getItem(key, (error, value) => {
                if (error) {
                    console.error('CloudStorage getItem error:', error);
                    resolve(null);
                } else {
                    resolve(value);
                }
            });
        });
    }

    async setCloudStorageItem(key, value) {
        if (!this.webapp?.CloudStorage) return false;
        
        return new Promise((resolve) => {
            this.webapp.CloudStorage.setItem(key, value, (error, success) => {
                if (error) {
                    console.error('CloudStorage setItem error:', error);
                    resolve(false);
                } else {
                    resolve(success);
                }
            });
        });
    }

    async removeCloudStorageItem(key) {
        if (!this.webapp?.CloudStorage) return false;
        
        return new Promise((resolve) => {
            this.webapp.CloudStorage.removeItem(key, (error, success) => {
                if (error) {
                    console.error('CloudStorage removeItem error:', error);
                    resolve(false);
                } else {
                    resolve(success);
                }
            });
        });
    }
}

// Initialize Telegram WebApp
window.tgWebApp = new TelegramWebApp();

// Theme toggle functionality
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    themeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.contains('theme-dark');
        document.body.classList.toggle('theme-dark');
        
        // Update icon
        const icon = themeToggle.querySelector('i[data-feather]');
        if (icon) {
            icon.setAttribute('data-feather', isDark ? 'sun' : 'moon');
            feather.replace();
        }
        
        // Haptic feedback
        window.tgWebApp.hapticFeedback('selection');
    });
}

// Auto-authenticate when page loads
document.addEventListener('DOMContentLoaded', async () => {
    try {
        await window.tgWebApp.authenticate();
    } catch (error) {
        console.warn('Auto-authentication failed:', error);
    }
    
    initThemeToggle();
});
