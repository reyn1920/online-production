class AvatarCustomizer {
    constructor() {
        this.currentConfig = {
            style: 'geometric',
            color_scheme: 'monochrome',
            size: 400,
            customizations: {
                complexity: 0.6,
                symmetry: 0.8,
                golden_ratio_emphasis: 0.8,
                transparency: true,
                border_style: 'none',
                texture: 'smooth'
            }
        };

        this.selectedChannel = null;
        this.currentAvatarData = null;

        this.initializeEventListeners();
        this.loadChannels();
    }

    initializeEventListeners() {
        // Style selection
        document.querySelectorAll('.style-card').forEach(card => {
            card.addEventListener('click', (e) => {
                this.selectStyle(card.dataset.style);
            });
        });

        // Color scheme selection
        document.querySelectorAll('.color-picker').forEach(picker => {
            picker.addEventListener('click', (e) => {
                this.selectColorScheme(picker.dataset.scheme);
            });
        });

        // Sliders
        document.getElementById('complexitySlider').addEventListener('input', (e) => {
            this.currentConfig.customizations.complexity = e.target.value/100;
            this.updatePreview();
        });

        document.getElementById('symmetrySlider').addEventListener('input', (e) => {
            this.currentConfig.customizations.symmetry = e.target.value/100;
            this.updatePreview();
        });

        document.getElementById('goldenRatioSlider').addEventListener('input', (e) => {
            this.currentConfig.customizations.golden_ratio_emphasis = e.target.value/100;
            this.updatePreview();
        });

        // Size selection
        document.getElementById('sizeSelect').addEventListener('change', (e) => {
            this.currentConfig.size = parseInt(e.target.value);
            this.updatePreview();
        });

        // Transparent background toggle
        document.getElementById('transparentBg').addEventListener('change', (e) => {
            this.currentConfig.customizations.transparency = e.target.checked;
            this.updatePreview();
        });

        // Action buttons
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateAvatar();
        });

        document.getElementById('downloadBtn').addEventListener('click', () => {
            this.downloadAvatar();
        });

        document.getElementById('randomizeBtn').addEventListener('click', () => {
            this.randomizeSettings();
        });

        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetSettings();
        });

        document.getElementById('saveBtn').addEventListener('click', () => {
            this.showChannelModal();
        });

        // File upload
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('imageUpload');

        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });

        // Channel modal
        document.getElementById('cancelChannelBtn').addEventListener('click', () => {
            this.hideChannelModal();
        });

        document.getElementById('confirmChannelBtn').addEventListener('click', () => {
            this.saveAvatarToChannel();
        });
    }

    selectStyle(style) {
        // Remove previous selection
        document.querySelectorAll('.style-card').forEach(card => {
            card.classList.remove('selected');
        });

        // Add selection to clicked card
        document.querySelector(`[data-style="${style}"]`).classList.add('selected');

        this.currentConfig.style = style;
        this.updatePreview();
    }

    selectColorScheme(scheme) {
        // Remove previous selection
        document.querySelectorAll('.color-picker').forEach(picker => {
            picker.classList.remove('selected');
        });

        // Add selection to clicked picker
        document.querySelector(`[data-scheme="${scheme}"]`).classList.add('selected');

        this.currentConfig.color_scheme = scheme;
        this.updatePreview();
    }

    async updatePreview() {
        // Debounce the preview updates
        clearTimeout(this.previewTimeout);
        this.previewTimeout = setTimeout(() => {
            this.generateAvatar(true);
        }, 500);
    }

    async generateAvatar(isPreview = false) {
        const loadingIndicator = document.getElementById('loadingIndicator');
        const generateBtn = document.getElementById('generateBtn');

        if (!isPreview) {
            loadingIndicator.classList.remove('hidden');
            generateBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/avatar/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.currentConfig)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.currentAvatarData = result;
                this.displayAvatar(result.base64_image);
            } else {
                this.showError(result.error || 'Failed to generate avatar');
            }

        } catch (error) {
            console.error('Error generating avatar:', error);
            this.showError('Failed to generate avatar. Please try again.');
        } finally {
            if (!isPreview) {
                loadingIndicator.classList.add('hidden');
                generateBtn.disabled = false;
            }
        }
    }

    displayAvatar(base64Image) {
        const previewContainer = document.getElementById('avatarPreview');
        previewContainer.innerHTML = `
            <img src="${base64Image}" alt="Generated Avatar" class="max-w-full max-h-full rounded-lg shadow-lg">
        `;
    }

    async handleFileUpload(file) {
        if (!file.type.startsWith('image/')) {
            this.showError('Please select a valid image file.');
            return;
        }

        const loadingIndicator = document.getElementById('loadingIndicator');
        loadingIndicator.classList.remove('hidden');

        try {
            // Convert file to base64
            const base64 = await this.fileToBase64(file);

            // Process the image (remove background)
            const response = await fetch('/api/avatar/process-upload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image_data: base64,
                    enhance: true
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.currentAvatarData = result;
                this.displayAvatar(result.processed_image);
                this.showSuccess('Image uploaded and background removed successfully!');
            } else {
                this.showError(result.error || 'Failed to process uploaded image');
            }

        } catch (error) {
            console.error('Error uploading file:', error);
            this.showError('Failed to upload and process image. Please try again.');
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    }

    randomizeSettings() {
        const styles = ['geometric', 'organic', 'professional', 'artistic', 'minimal', 'golden_ratio'];
        const colorSchemes = ['monochrome', 'complementary', 'triadic', 'warm', 'cool', 'vibrant'];

        // Randomize style
        const randomStyle = styles[Math.floor(Math.random() * styles.length)];
        this.selectStyle(randomStyle);

        // Randomize color scheme
        const randomColorScheme = colorSchemes[Math.floor(Math.random() * colorSchemes.length)];
        this.selectColorScheme(randomColorScheme);

        // Randomize sliders
        const complexitySlider = document.getElementById('complexitySlider');
        const symmetrySlider = document.getElementById('symmetrySlider');
        const goldenRatioSlider = document.getElementById('goldenRatioSlider');

        complexitySlider.value = Math.floor(Math.random() * 100);
        symmetrySlider.value = Math.floor(Math.random() * 100);
        goldenRatioSlider.value = Math.floor(Math.random() * 100);

        // Update config
        this.currentConfig.customizations.complexity = complexitySlider.value/100;
        this.currentConfig.customizations.symmetry = symmetrySlider.value/100;
        this.currentConfig.customizations.golden_ratio_emphasis = goldenRatioSlider.value/100;

        this.updatePreview();
    }

    resetSettings() {
        // Reset to default configuration
        this.currentConfig = {
            style: 'geometric',
            color_scheme: 'monochrome',
            size: 400,
            customizations: {
                complexity: 0.6,
                symmetry: 0.8,
                golden_ratio_emphasis: 0.8,
                transparency: true,
                border_style: 'none',
                texture: 'smooth'
            }
        };

        // Reset UI elements
        this.selectStyle('geometric');
        this.selectColorScheme('monochrome');

        document.getElementById('complexitySlider').value = 60;
        document.getElementById('symmetrySlider').value = 80;
        document.getElementById('goldenRatioSlider').value = 80;
        document.getElementById('sizeSelect').value = '400';
        document.getElementById('transparentBg').checked = true;

        // Reset preview
        const previewContainer = document.getElementById('avatarPreview');
        previewContainer.innerHTML = `
            <div class="w-48 h-48 bg-gray-200 rounded-full flex items-center justify-center">
                <i class="fas fa-user text-gray-400 text-6xl"></i>
            </div>
        `;

        this.currentAvatarData = null;
    }

    async downloadAvatar() {
        if (!this.currentAvatarData) {
            this.showError('Please generate an avatar first.');
            return;
        }

        try {
            // Create download link
            const link = document.createElement('a');
            link.href = this.currentAvatarData.base64_image || this.currentAvatarData.processed_image;
            link.download = `avatar_${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.showSuccess('Avatar downloaded successfully!');

        } catch (error) {
            console.error('Error downloading avatar:', error);
            this.showError('Failed to download avatar.');
        }
    }

    async loadChannels() {
        try {
            const response = await fetch('/api/channels');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const channels = await response.json();
            this.channels = channels;

        } catch (error) {
            console.error('Error loading channels:', error);
            this.channels = [];
        }
    }

    showChannelModal() {
        if (!this.currentAvatarData) {
            this.showError('Please generate an avatar first.');
            return;
        }

        const modal = document.getElementById('channelModal');
        const channelList = document.getElementById('channelList');

        // Populate channel list
        channelList.innerHTML = '';

        if (this.channels && this.channels.length > 0) {
            this.channels.forEach(channel => {
                const channelOption = document.createElement('div');
                channelOption.className = 'flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50';
                channelOption.innerHTML = `
                    <input type="radio" name="channel" value="${channel.id}" class="mr-3">
                    <div>
                        <p class="font-medium">${channel.channel_name}</p>
                        <p class="text-sm text-gray-500">${channel.status}</p>
                    </div>
                `;

                channelOption.addEventListener('click', () => {
                    const radio = channelOption.querySelector('input[type="radio"]');
                    radio.checked = true;
                    this.selectedChannel = channel.id;
                });

                channelList.appendChild(channelOption);
            });
        } else {
            channelList.innerHTML = '<p class="text-gray-500 text-center">No channels available</p>';
        }

        modal.classList.remove('hidden');
    }

    hideChannelModal() {
        const modal = document.getElementById('channelModal');
        modal.classList.add('hidden');
        this.selectedChannel = null;
    }

    async saveAvatarToChannel() {
        if (!this.selectedChannel) {
            this.showError('Please select a channel.');
            return;
        }

        if (!this.currentAvatarData) {
            this.showError('No avatar to save.');
            return;
        }

        try {
            const imageData = this.currentAvatarData.base64_image || this.currentAvatarData.processed_image;

            const response = await fetch('/api/avatar/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    channel_id: this.selectedChannel,
                    image_data: imageData,
                    make_default: true
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                this.showSuccess('Avatar saved successfully!');
                this.hideChannelModal();
            } else {
                this.showError(result.error || 'Failed to save avatar');
            }

        } catch (error) {
            console.error('Error saving avatar:', error);
            this.showError('Failed to save avatar. Please try again.');
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full`;

        if (type === 'error') {
            notification.classList.add('bg-red-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
        } else if (type === 'success') {
            notification.classList.add('bg-green-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
        } else {
            notification.classList.add('bg-blue-500', 'text-white');
            notification.innerHTML = `<i class="fas fa-info-circle mr-2"></i>${message}`;
        }

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
}

// Initialize the avatar customizer when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AvatarCustomizer();
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AvatarCustomizer;
}
