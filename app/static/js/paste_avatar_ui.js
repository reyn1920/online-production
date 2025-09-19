/**
 * Paste Avatar UI Integration
 * Connects the paste application with dashboard avatar functionality
 */class PasteAvatarUI {
    constructor() {
        this.pasteEndpoint = 'http://localhost:5000';
        this.avatarEndpoint = '/paste/avatar';
        this.isInitialized = false;
        this.init();
    }

    async init() {
        try {//Check if paste service is available
            const response = await fetch(`${this.pasteEndpoint}/status`);
            if (response.ok) {
                this.isInitialized = true;
// DEBUG_REMOVED: console.log('✅ Paste Avatar UI initialized successfully');
                this.setupEventListeners();
            } else {
// DEBUG_REMOVED: console.warn('⚠️ Paste service not available');
            }
        } catch (error) {
// DEBUG_REMOVED: console.warn('⚠️ Paste service connection failed:', error.message);
        }
    }

    setupEventListeners() {//Listen for avatar generation requests
        document.addEventListener('avatar:generate', (event) => {
            this.handleAvatarGeneration(event.detail);
        });//Listen for paste content updates
        document.addEventListener('paste:update', (event) => {
            this.handlePasteUpdate(event.detail);
        });
    }

    async handleAvatarGeneration(options = {}) {
        if (!this.isInitialized) {
// DEBUG_REMOVED: console.warn('Paste Avatar UI not initialized');
            return null;
        }

        try {
            const response = await fetch(`${this.pasteEndpoint}${this.avatarEndpoint}/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: options.content || 'Dashboard avatar content',
                    avatar_type: options.type || 'professional',
                    voice_style: options.voice || 'natural',
                    quality: options.quality || 'high',
                    template: options.template || 'professional_presenter'
                })
            });

            const result = await response.json();

            if (result.success) {//Dispatch success event
                document.dispatchEvent(new CustomEvent('avatar:generated', {
                    detail: result
                }));
                return result;
            } else {
                throw new Error(result.error || 'Avatar generation failed');
            }
        } catch (error) {
            console.error('Avatar generation error:', error);
            document.dispatchEvent(new CustomEvent('avatar:error', {
                detail: { error: error.message }
            }));
            return null;
        }
    }

    async handlePasteUpdate(data) {//Handle paste content updates for avatar integration
        console.log('Paste content updated:', data);//If avatar is linked to paste content, regenerate
        if (data.autoRegenerate) {
            await this.handleAvatarGeneration({
                content: data.content,
                type: data.avatarType || 'professional'
            });
        }
    }

    async uploadToDownloads(file, filename) {
        if (!this.isInitialized) {
            throw new Error('Paste Avatar UI not initialized');
        }

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('filename', filename);
            formData.append('destination', 'downloads');

            const response = await fetch(`${this.pasteEndpoint}/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                document.dispatchEvent(new CustomEvent('file:uploaded', {
                    detail: result
                }));
                return result;
            } else {
                throw new Error(result.error || 'Upload failed');
            }
        } catch (error) {
            console.error('Upload error:', error);
            throw error;
        }
    }

    async getDownloadsFiles() {
        if (!this.isInitialized) {
            return [];
        }

        try {
            const response = await fetch(`${this.pasteEndpoint}/downloads/list`);
            const result = await response.json();

            return result.files || [];
        } catch (error) {
            console.error('Error fetching downloads files:', error);
            return [];
        }
    }

    async processDownloadsFile(filename, action = 'read') {
        if (!this.isInitialized) {
            throw new Error('Paste Avatar UI not initialized');
        }

        try {
            const response = await fetch(`${this.pasteEndpoint}/downloads/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: filename,
                    action: action
                })
            });

            const result = await response.json();

            if (result.success) {
                document.dispatchEvent(new CustomEvent('file:processed', {
                    detail: result
                }));
                return result;
            } else {
                throw new Error(result.error || 'File processing failed');
            }
        } catch (error) {
            console.error('File processing error:', error);
            throw error;
        }
    }//Utility method to check service status
    async checkStatus() {
        try {
            const response = await fetch(`${this.pasteEndpoint}/status`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }//Method to integrate with dashboard notifications
    showNotification(message, type = 'info') {
        if (window.Dashboard && window.Dashboard.showAlert) {
            window.Dashboard.showAlert(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}//Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pasteAvatarUI = new PasteAvatarUI();
});//Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PasteAvatarUI;
}
