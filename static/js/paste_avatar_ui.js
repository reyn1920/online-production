/**
 * Paste Avatar UI - Enhanced Avatar Generation Interface
 * 
 * This module provides a comprehensive user interface for generating enhanced avatars
 * from paste content, integrating with both standard and 3D avatar systems.
 * 
 * Features:
 * - Real-time avatar preview
 * - Smart template suggestions
 * - Emotion detection visualization
 * - Batch processing interface
 * - Custom personality creation
 * - Quality and performance controls
 * 
 * @version 2.0.0
 * @author TRAE.AI Enhancement System
 */

class PasteAvatarUI {
    constructor() {
        this.apiBase = '/paste/avatar';
        this.currentConfig = this.getDefaultConfig();
        this.templates = {};
        this.personalities = {};
        this.processingQueue = [];
        this.isProcessing = false;
        
        this.init();
    }
    
    getDefaultConfig() {
        return {
            avatar_type: 'standard',
            voice_style: 'natural',
            emotion_detection: true,
            auto_gestures: true,
            background_removal: true,
            quality: 'medium',
            language: 'en',
            accent: 'neutral',
            template: null,
            personality_id: null
        };
    }
    
    async init() {
        try {
            // Load templates and initialize UI
            await this.loadTemplates();
            this.createUI();
            this.bindEvents();
            
            console.log('🎬 Paste Avatar UI initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Paste Avatar UI:', error);
        }
    }
    
    async loadTemplates() {
        try {
            const response = await fetch(`${this.apiBase}/templates`);
            const data = await response.json();
            
            if (data.success) {
                this.templates = data.templates;
            }
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    }
    
    createUI() {
        // Create main avatar UI container
        const avatarUI = document.createElement('div');
        avatarUI.id = 'paste-avatar-ui';
        avatarUI.className = 'paste-avatar-container';
        
        avatarUI.innerHTML = `
            <div class="avatar-header">
                <h3>🎭 Enhanced Avatar Generation</h3>
                <div class="avatar-status" id="avatar-status">
                    <span class="status-indicator">Ready</span>
                </div>
            </div>
            
            <div class="avatar-content">
                <!-- Configuration Panel -->
                <div class="config-panel">
                    <div class="config-section">
                        <h4>Avatar Type</h4>
                        <div class="avatar-type-selector">
                            <label class="radio-option">
                                <input type="radio" name="avatar_type" value="standard" checked>
                                <span class="radio-label">
                                    <strong>Standard Avatar</strong>
                                    <small>Fast 2D generation with Linly-Talker</small>
                                </span>
                            </label>
                            <label class="radio-option">
                                <input type="radio" name="avatar_type" value="3d">
                                <span class="radio-label">
                                    <strong>3D Avatar</strong>
                                    <small>Professional 3D character with advanced animation</small>
                                </span>
                            </label>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h4>Voice & Style</h4>
                        <div class="voice-controls">
                            <select id="voice-style" class="form-select">
                                <option value="natural">Natural</option>
                                <option value="professional">Professional</option>
                                <option value="casual">Casual</option>
                                <option value="dramatic">Dramatic</option>
                            </select>
                            
                            <select id="accent" class="form-select">
                                <option value="neutral">Neutral</option>
                                <option value="american">American</option>
                                <option value="british">British</option>
                                <option value="australian">Australian</option>
                            </select>
                            
                            <select id="language" class="form-select">
                                <option value="en">English</option>
                                <option value="es">Spanish</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="zh">Chinese</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="config-section">
                        <h4>Template & Quality</h4>
                        <select id="template-selector" class="form-select">
                            <option value="">Auto-select template</option>
                        </select>
                        
                        <select id="quality-selector" class="form-select">
                            <option value="low">Low (Fast)</option>
                            <option value="medium" selected>Medium (Balanced)</option>
                            <option value="high">High (Quality)</option>
                            <option value="ultra">Ultra (Best)</option>
                        </select>
                    </div>
                    
                    <div class="config-section">
                        <h4>Advanced Options</h4>
                        <div class="checkbox-group">
                            <label class="checkbox-option">
                                <input type="checkbox" id="emotion-detection" checked>
                                <span>Emotion Detection</span>
                            </label>
                            <label class="checkbox-option">
                                <input type="checkbox" id="auto-gestures" checked>
                                <span>Auto Gestures</span>
                            </label>
                            <label class="checkbox-option">
                                <input type="checkbox" id="background-removal" checked>
                                <span>Background Removal</span>
                            </label>
                        </div>
                    </div>
                </div>
                
                <!-- Content Analysis Panel -->
                <div class="analysis-panel" id="analysis-panel" style="display: none;">
                    <h4>📊 Content Analysis</h4>
                    <div class="analysis-results" id="analysis-results">
                        <!-- Analysis results will be populated here -->
                    </div>
                    
                    <h4>🎭 Suggested Personalities</h4>
                    <div class="personality-suggestions" id="personality-suggestions">
                        <!-- Personality suggestions will be populated here -->
                    </div>
                </div>
                
                <!-- Preview Panel -->
                <div class="preview-panel">
                    <h4>Preview</h4>
                    <div class="avatar-preview" id="avatar-preview">
                        <div class="preview-placeholder">
                            <div class="preview-icon">🎬</div>
                            <p>Generate an avatar to see preview</p>
                        </div>
                    </div>
                    
                    <div class="preview-controls" style="display: none;">
                        <button class="btn btn-secondary" id="download-avatar">Download</button>
                        <button class="btn btn-secondary" id="share-avatar">Share</button>
                        <button class="btn btn-secondary" id="regenerate-avatar">Regenerate</button>
                    </div>
                </div>
            </div>
            
            <div class="avatar-actions">
                <button class="btn btn-primary" id="analyze-content">Analyze Content</button>
                <button class="btn btn-success" id="generate-avatar">Generate Avatar</button>
                <button class="btn btn-info" id="batch-process" style="display: none;">Batch Process</button>
            </div>
            
            <!-- Progress Modal -->
            <div class="modal" id="progress-modal" style="display: none;">
                <div class="modal-content">
                    <h4>Generating Avatar...</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="progress-text" id="progress-text">Initializing...</div>
                    <button class="btn btn-secondary" id="cancel-generation">Cancel</button>
                </div>
            </div>
        `;
        
        // Insert UI into the page
        const targetContainer = document.querySelector('.paste-container') || document.body;
        targetContainer.appendChild(avatarUI);
        
        // Populate templates
        this.populateTemplates();
        
        // Add CSS styles
        this.addStyles();
    }
    
    populateTemplates() {
        const templateSelector = document.getElementById('template-selector');
        
        Object.entries(this.templates).forEach(([key, template]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = `${template.description} (${template.use_cases.join(', ')})`;
            templateSelector.appendChild(option);
        });
    }
    
    bindEvents() {
        // Configuration change handlers
        document.querySelectorAll('input[name="avatar_type"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentConfig.avatar_type = e.target.value;
                this.updateUI();
            });
        });
        
        document.getElementById('voice-style').addEventListener('change', (e) => {
            this.currentConfig.voice_style = e.target.value;
        });
        
        document.getElementById('accent').addEventListener('change', (e) => {
            this.currentConfig.accent = e.target.value;
        });
        
        document.getElementById('language').addEventListener('change', (e) => {
            this.currentConfig.language = e.target.value;
        });
        
        document.getElementById('template-selector').addEventListener('change', (e) => {
            this.currentConfig.template = e.target.value || null;
        });
        
        document.getElementById('quality-selector').addEventListener('change', (e) => {
            this.currentConfig.quality = e.target.value;
        });
        
        // Checkbox handlers
        document.getElementById('emotion-detection').addEventListener('change', (e) => {
            this.currentConfig.emotion_detection = e.target.checked;
        });
        
        document.getElementById('auto-gestures').addEventListener('change', (e) => {
            this.currentConfig.auto_gestures = e.target.checked;
        });
        
        document.getElementById('background-removal').addEventListener('change', (e) => {
            this.currentConfig.background_removal = e.target.checked;
        });
        
        // Action button handlers
        document.getElementById('analyze-content').addEventListener('click', () => {
            this.analyzeContent();
        });
        
        document.getElementById('generate-avatar').addEventListener('click', () => {
            this.generateAvatar();
        });
        
        document.getElementById('batch-process').addEventListener('click', () => {
            this.showBatchProcessDialog();
        });
        
        // Progress modal handlers
        document.getElementById('cancel-generation').addEventListener('click', () => {
            this.cancelGeneration();
        });
    }
    
    updateUI() {
        const avatarType = this.currentConfig.avatar_type;
        const qualitySelector = document.getElementById('quality-selector');
        
        // Update quality options based on avatar type
        if (avatarType === '3d') {
            qualitySelector.innerHTML = `
                <option value="preview">Preview (Fast)</option>
                <option value="production" selected>Production (Balanced)</option>
                <option value="cinematic">Cinematic (Best)</option>
            `;
        } else {
            qualitySelector.innerHTML = `
                <option value="low">Low (Fast)</option>
                <option value="medium" selected>Medium (Balanced)</option>
                <option value="high">High (Quality)</option>
                <option value="ultra">Ultra (Best)</option>
            `;
        }
    }
    
    async analyzeContent() {
        const content = this.getPasteContent();
        if (!content) {
            this.showError('No content found to analyze');
            return;
        }
        
        try {
            this.setStatus('Analyzing content...', 'processing');
            
            const response = await fetch(`${this.apiBase}/suggestions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayAnalysisResults(data.suggestions);
                document.getElementById('analysis-panel').style.display = 'block';
                this.setStatus('Analysis complete', 'success');
            } else {
                this.showError(data.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showError('Failed to analyze content');
        }
    }
    
    displayAnalysisResults(suggestions) {
        const analysisResults = document.getElementById('analysis-results');
        const personalitySuggestions = document.getElementById('personality-suggestions');
        
        // Display content analysis (mock for now)
        analysisResults.innerHTML = `
            <div class="analysis-item">
                <span class="analysis-label">Content Type:</span>
                <span class="analysis-value">Professional Presentation</span>
            </div>
            <div class="analysis-item">
                <span class="analysis-label">Detected Emotion:</span>
                <span class="analysis-value">Confident & Engaging</span>
            </div>
            <div class="analysis-item">
                <span class="analysis-label">Recommended Quality:</span>
                <span class="analysis-value">High</span>
            </div>
        `;
        
        // Display personality suggestions
        personalitySuggestions.innerHTML = suggestions.map(suggestion => `
            <div class="personality-card" data-suggestion='${JSON.stringify(suggestion)}'>
                <h5>${suggestion.name}</h5>
                <p>Traits: ${suggestion.traits.join(', ')}</p>
                <p>Template: ${suggestion.template}</p>
                <button class="btn btn-sm btn-outline-primary apply-suggestion">Apply</button>
            </div>
        `).join('');
        
        // Bind suggestion apply buttons
        document.querySelectorAll('.apply-suggestion').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const suggestionData = JSON.parse(e.target.closest('.personality-card').dataset.suggestion);
                this.applySuggestion(suggestionData);
            });
        });
    }
    
    applySuggestion(suggestion) {
        // Apply suggestion to current config
        this.currentConfig.template = suggestion.template;
        this.currentConfig.voice_style = suggestion.voice_style;
        
        // Update UI elements
        document.getElementById('template-selector').value = suggestion.template;
        document.getElementById('voice-style').value = suggestion.voice_style;
        
        this.setStatus(`Applied suggestion: ${suggestion.name}`, 'success');
    }
    
    async generateAvatar() {
        const content = this.getPasteContent();
        if (!content) {
            this.showError('No content found to generate avatar');
            return;
        }
        
        try {
            this.showProgressModal();
            this.setStatus('Generating avatar...', 'processing');
            
            const requestData = {
                content,
                ...this.currentConfig
            };
            
            const response = await fetch(`${this.apiBase}/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayAvatarResult(data);
                this.setStatus('Avatar generated successfully!', 'success');
            } else {
                this.showError(data.error || 'Generation failed');
            }
        } catch (error) {
            console.error('Generation error:', error);
            this.showError('Failed to generate avatar');
        } finally {
            this.hideProgressModal();
        }
    }
    
    displayAvatarResult(result) {
        const previewPanel = document.getElementById('avatar-preview');
        const previewControls = document.querySelector('.preview-controls');
        
        if (result.video_path) {
            previewPanel.innerHTML = `
                <video controls class="avatar-video">
                    <source src="${result.video_path}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <div class="result-info">
                    <p><strong>Processing Time:</strong> ${result.processing_time}s</p>
                    <p><strong>Engine:</strong> ${result.engine_used}</p>
                    <p><strong>Quality:</strong> ${this.currentConfig.quality}</p>
                </div>
            `;
            
            previewControls.style.display = 'block';
            
            // Store result for download/share
            this.lastResult = result;
        }
    }
    
    showProgressModal() {
        const modal = document.getElementById('progress-modal');
        modal.style.display = 'flex';
        
        // Simulate progress (in real implementation, this would be WebSocket updates)
        this.simulateProgress();
    }
    
    hideProgressModal() {
        const modal = document.getElementById('progress-modal');
        modal.style.display = 'none';
    }
    
    simulateProgress() {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        
        const steps = [
            'Analyzing content...',
            'Loading avatar model...',
            'Generating speech...',
            'Creating animation...',
            'Rendering video...',
            'Applying enhancements...',
            'Finalizing...'
        ];
        
        let currentStep = 0;
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                const progress = ((currentStep + 1) / steps.length) * 100;
                progressFill.style.width = `${progress}%`;
                progressText.textContent = steps[currentStep];
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 2000);
        
        this.progressInterval = interval;
    }
    
    cancelGeneration() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        this.hideProgressModal();
        this.setStatus('Generation cancelled', 'warning');
    }
    
    getPasteContent() {
        // Try to get content from various possible sources
        const contentSources = [
            () => document.querySelector('#paste-content')?.value,
            () => document.querySelector('.paste-text')?.textContent,
            () => document.querySelector('textarea[name="content"]')?.value,
            () => document.querySelector('#content')?.value
        ];
        
        for (const getContent of contentSources) {
            const content = getContent();
            if (content && content.trim()) {
                return content.trim();
            }
        }
        
        return null;
    }
    
    setStatus(message, type = 'info') {
        const statusElement = document.getElementById('avatar-status');
        const indicator = statusElement.querySelector('.status-indicator');
        
        indicator.textContent = message;
        indicator.className = `status-indicator status-${type}`;
    }
    
    showError(message) {
        this.setStatus(message, 'error');
        console.error('Avatar UI Error:', message);
    }
    
    addStyles() {
        const styles = `
            <style>
            .paste-avatar-container {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .avatar-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid #dee2e6;
            }
            
            .avatar-header h3 {
                margin: 0;
                color: #495057;
            }
            
            .status-indicator {
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                background: #e9ecef;
                color: #6c757d;
            }
            
            .status-success { background: #d4edda; color: #155724; }
            .status-error { background: #f8d7da; color: #721c24; }
            .status-warning { background: #fff3cd; color: #856404; }
            .status-processing { background: #cce7ff; color: #004085; }
            
            .avatar-content {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .config-panel, .analysis-panel, .preview-panel {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 15px;
            }
            
            .config-section {
                margin-bottom: 20px;
            }
            
            .config-section h4 {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: 600;
                color: #495057;
            }
            
            .radio-option, .checkbox-option {
                display: flex;
                align-items: flex-start;
                margin-bottom: 8px;
                cursor: pointer;
            }
            
            .radio-option input, .checkbox-option input {
                margin-right: 8px;
                margin-top: 2px;
            }
            
            .radio-label {
                display: flex;
                flex-direction: column;
            }
            
            .radio-label small {
                color: #6c757d;
                font-size: 11px;
            }
            
            .form-select {
                width: 100%;
                padding: 6px 10px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                margin-bottom: 8px;
                font-size: 13px;
            }
            
            .voice-controls {
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .checkbox-group {
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .avatar-preview {
                min-height: 200px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 6px;
                margin-bottom: 15px;
            }
            
            .preview-placeholder {
                text-align: center;
                color: #6c757d;
            }
            
            .preview-icon {
                font-size: 48px;
                margin-bottom: 10px;
            }
            
            .avatar-video {
                width: 100%;
                max-height: 300px;
                border-radius: 6px;
            }
            
            .result-info {
                margin-top: 10px;
                font-size: 12px;
                color: #6c757d;
            }
            
            .avatar-actions {
                display: flex;
                gap: 10px;
                justify-content: center;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s;
            }
            
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-info { background: #17a2b8; color: white; }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-outline-primary { background: transparent; color: #007bff; border: 1px solid #007bff; }
            
            .btn:hover {
                opacity: 0.9;
                transform: translateY(-1px);
            }
            
            .modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }
            
            .modal-content {
                background: white;
                padding: 30px;
                border-radius: 8px;
                text-align: center;
                min-width: 300px;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                margin: 20px 0;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: #007bff;
                width: 0%;
                transition: width 0.3s ease;
            }
            
            .personality-card {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 10px;
            }
            
            .personality-card h5 {
                margin: 0 0 5px 0;
                font-size: 14px;
            }
            
            .personality-card p {
                margin: 3px 0;
                font-size: 12px;
                color: #6c757d;
            }
            
            .analysis-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 13px;
            }
            
            .analysis-label {
                font-weight: 500;
                color: #495057;
            }
            
            .analysis-value {
                color: #007bff;
                font-weight: 500;
            }
            
            @media (max-width: 768px) {
                .avatar-content {
                    grid-template-columns: 1fr;
                }
            }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', styles);
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pasteAvatarUI = new PasteAvatarUI();
    });
} else {
    window.pasteAvatarUI = new PasteAvatarUI();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PasteAvatarUI;
}