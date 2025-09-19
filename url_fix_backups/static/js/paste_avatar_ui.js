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

        // AI Assistant features
        this.aiAssistant = {
            enabled: true,
            suggestions: [],
            userPreferences: {},
            learningData: [],
            contextualHelp: true,
            smartRecommendations: true
        };

        this.userBehavior = {
            interactions: [],
            preferences: {},
            successfulConfigs: [],
            timeSpent: {},
            errorPatterns: []
        };

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
            await this.loadUserPreferences();
            this.createUI();
            this.bindEvents();
            this.initializeAIAssistant();

            console.log('🎬 Paste Avatar UI with AI Assistant initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Paste Avatar UI:', error);
        }
    }

    async loadUserPreferences() {
        try {
            const stored = localStorage.getItem('pasteAvatarPreferences');
            if (stored) {
                this.aiAssistant.userPreferences = JSON.parse(stored);
                this.userBehavior.preferences = this.aiAssistant.userPreferences;
            }
        } catch (error) {
            console.error('Failed to load user preferences:', error);
        }
    }

    initializeAIAssistant() {
        if (!this.aiAssistant.enabled) return;

        // Create AI assistant panel
        this.createAIAssistantPanel();

        // Start contextual help system
        this.startContextualHelp();

        // Initialize smart recommendations
        this.initializeSmartRecommendations();

        // Track user behavior for learning
        this.startBehaviorTracking();

        console.log('🤖 AI Assistant features activated');
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
        // Configuration change handlers with AI tracking
        document.querySelectorAll('input[name="avatar_type"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentConfig.avatar_type = e.target.value;
                this.updateUI();
                this.trackUserInteraction('avatar_type_change', e.target.value);
                this.provideSuggestions('avatar_type', e.target.value);
            });
        });

        document.getElementById('voice-style').addEventListener('change', (e) => {
            this.currentConfig.voice_style = e.target.value;
            this.trackUserInteraction('voice_style_change', e.target.value);
            this.provideSuggestions('voice_style', e.target.value);
        });

        document.getElementById('accent').addEventListener('change', (e) => {
            this.currentConfig.accent = e.target.value;
            this.trackUserInteraction('accent_change', e.target.value);
        });

        document.getElementById('language').addEventListener('change', (e) => {
            this.currentConfig.language = e.target.value;
            this.trackUserInteraction('language_change', e.target.value);
        });

        document.getElementById('template-selector').addEventListener('change', (e) => {
            this.currentConfig.template = e.target.value || null;
            this.trackUserInteraction('template_change', e.target.value);
            this.provideSuggestions('template', e.target.value);
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

        // Action button handlers with AI tracking
        document.getElementById('analyze-content').addEventListener('click', () => {
            this.analyzeContent();
            this.trackUserInteraction('analyze_content', this.currentConfig);
        });

        document.getElementById('generate-avatar').addEventListener('click', () => {
            this.generateAvatar();
            this.trackUserInteraction('generate_avatar', this.currentConfig);
        });

        document.getElementById('batch-process').addEventListener('click', () => {
            this.showBatchProcessDialog();
            this.trackUserInteraction('batch_process', null);
        });

        // AI Assistant event handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('.ai-suggestion-btn')) {
                this.applySuggestion(e.target.dataset.suggestion);
                this.trackUserInteraction('apply_suggestion', e.target.dataset.suggestion);
            }

            if (e.target.matches('.ai-help-btn')) {
                this.showContextualHelp(e.target.dataset.context);
                this.trackUserInteraction('request_help', e.target.dataset.context);
            }

            if (e.target.matches('.ai-dismiss-btn')) {
                this.dismissSuggestion(e.target.dataset.suggestionId);
            }
        });

        // Progress modal handlers
        document.getElementById('cancel-generation').addEventListener('click', () => {
            this.cancelGeneration();
            this.trackUserInteraction('cancel_generation', null);
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

    // AI Assistant Methods
    createAIAssistantPanel() {
        const aiPanel = document.createElement('div');
        aiPanel.className = 'ai-assistant-panel';
        aiPanel.innerHTML = `
            <div class="ai-assistant-header">
                <h4>🤖 AI Assistant</h4>
                <button class="ai-toggle-btn" data-expanded="true">−</button>
            </div>
            <div class="ai-assistant-content">
                <div class="ai-suggestions" id="ai-suggestions"></div>
                <div class="ai-contextual-help" id="ai-contextual-help"></div>
                <div class="ai-quick-actions">
                    <button class="btn btn-sm ai-help-btn" data-context="general">💡 Get Help</button>
                    <button class="btn btn-sm ai-optimize-btn">⚡ Optimize Settings</button>
                </div>
            </div>
        `;

        const targetContainer = document.querySelector('.paste-avatar-container');
        if (targetContainer) {
            targetContainer.insertBefore(aiPanel, targetContainer.firstChild);
        }
    }

    startContextualHelp() {
        // Monitor user interactions and provide contextual help
        setInterval(() => {
            this.analyzeUserBehavior();
            this.updateContextualHelp();
        }, 10000); // Check every 10 seconds
    }

    initializeSmartRecommendations() {
        // Load historical successful configurations
        this.loadSuccessfulConfigs();

        // Analyze current context and provide recommendations
        this.generateSmartRecommendations();
    }

    startBehaviorTracking() {
        this.userBehavior.sessionStart = Date.now();

        // Track time spent on different sections
        document.addEventListener('focus', (e) => {
            if (e.target.matches('.config-input, select, input[type="radio"], input[type="checkbox"]')) {
                this.trackTimeSpent(e.target.name || e.target.id);
            }
        }, true);
    }

    trackUserInteraction(action, data) {
        if (!this.aiAssistant.enabled) return;

        const interaction = {
            timestamp: Date.now(),
            action,
            data,
            config: { ...this.currentConfig }
        };

        this.userBehavior.interactions.push(interaction);

        // Keep only last 100 interactions
        if (this.userBehavior.interactions.length > 100) {
            this.userBehavior.interactions.shift();
        }

        // Update AI learning data
        this.updateAILearning(interaction);
    }

    provideSuggestions(field, value) {
        if (!this.aiAssistant.smartRecommendations) return;

        const suggestions = this.generateFieldSuggestions(field, value);
        if (suggestions.length > 0) {
            this.displaySuggestions(suggestions);
        }
    }

    generateFieldSuggestions(field, value) {
        const suggestions = [];

        // Smart suggestions based on field and value
        switch (field) {
            case 'avatar_type':
                if (value === 'professional') {
                    suggestions.push({
                        id: 'prof_voice',
                        text: 'Consider using "authoritative" voice style for professional avatars',
                        action: () => this.updateConfig('voice_style', 'authoritative')
                    });
                }
                break;

            case 'voice_style':
                if (value === 'casual') {
                    suggestions.push({
                        id: 'casual_gestures',
                        text: 'Enable auto-gestures for more natural casual presentation',
                        action: () => this.updateConfig('auto_gestures', true)
                    });
                }
                break;

            case 'template':
                const template = this.templates[value];
                if (template && template.recommended_settings) {
                    suggestions.push({
                        id: 'template_optimize',
                        text: `Apply recommended settings for ${template.description}`,
                        action: () => this.applyTemplateSettings(template.recommended_settings)
                    });
                }
                break;
        }

        return suggestions;
    }

    displaySuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('ai-suggestions');
        if (!suggestionsContainer) return;

        suggestions.forEach(suggestion => {
            const suggestionEl = document.createElement('div');
            suggestionEl.className = 'ai-suggestion';
            suggestionEl.innerHTML = `
                <div class="suggestion-content">
                    <span class="suggestion-text">${suggestion.text}</span>
                    <div class="suggestion-actions">
                        <button class="btn btn-sm ai-suggestion-btn" data-suggestion="${suggestion.id}">Apply</button>
                        <button class="btn btn-sm ai-dismiss-btn" data-suggestion-id="${suggestion.id}">×</button>
                    </div>
                </div>
            `;

            suggestionsContainer.appendChild(suggestionEl);

            // Auto-remove after 30 seconds
            setTimeout(() => {
                if (suggestionEl.parentNode) {
                    suggestionEl.remove();
                }
            }, 30000);
        });
    }

    showContextualHelp(context) {
        const helpContent = this.getContextualHelpContent(context);
        const helpContainer = document.getElementById('ai-contextual-help');

        if (helpContainer && helpContent) {
            helpContainer.innerHTML = `
                <div class="contextual-help">
                    <h5>💡 ${helpContent.title}</h5>
                    <p>${helpContent.content}</p>
                    ${helpContent.tips ? `<ul>${helpContent.tips.map(tip => `<li>${tip}</li>`).join('')}</ul>` : ''}
                    <button class="btn btn-sm" onclick="this.parentElement.remove()">Got it</button>
                </div>
            `;
        }
    }

    getContextualHelpContent(context) {
        const helpContent = {
            general: {
                title: 'Getting Started',
                content: 'Create engaging avatars from your content with AI assistance.',
                tips: [
                    'Start by analyzing your content for personalized suggestions',
                    'Choose avatar type based on your content tone',
                    'Use templates for quick professional results'
                ]
            },
            avatar_type: {
                title: 'Choosing Avatar Type',
                content: 'Select the avatar style that best matches your content and audience.',
                tips: [
                    'Professional: Best for business presentations',
                    'Casual: Great for social media content',
                    'Educational: Perfect for tutorials and explanations'
                ]
            },
            voice_style: {
                title: 'Voice Style Guide',
                content: 'Voice style affects how your avatar communicates your message.',
                tips: [
                    'Authoritative: For expert content and presentations',
                    'Friendly: For approachable, conversational content',
                    'Energetic: For motivational and exciting content'
                ]
            }
        };

        return helpContent[context] || helpContent.general;
    }

    applySuggestion(suggestionId) {
        // Find and apply the suggestion
        const suggestion = this.aiAssistant.suggestions.find(s => s.id === suggestionId);
        if (suggestion && suggestion.action) {
            suggestion.action();
            this.trackUserInteraction('suggestion_applied', suggestionId);
        }
    }

    dismissSuggestion(suggestionId) {
        const suggestionEl = document.querySelector(`[data-suggestion-id="${suggestionId}"]`);
        if (suggestionEl) {
            suggestionEl.closest('.ai-suggestion').remove();
        }
    }

    updateConfig(field, value) {
        this.currentConfig[field] = value;

        // Update UI element if it exists
        const element = document.getElementById(field) || document.querySelector(`[name="${field}"]`);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = value;
            } else {
                element.value = value;
            }
        }

        this.updateUI();
    }

    analyzeUserBehavior() {
        const recentInteractions = this.userBehavior.interactions.slice(-10);

        // Detect patterns and potential issues
        const patterns = this.detectBehaviorPatterns(recentInteractions);

        if (patterns.struggling) {
            this.offerHelp(patterns.context);
        }

        if (patterns.repetitive) {
            this.suggestOptimization(patterns.suggestion);
        }
    }

    detectBehaviorPatterns(interactions) {
        const patterns = { struggling: false, repetitive: false };

        // Check for repeated similar actions (might indicate confusion)
        const actionCounts = {};
        interactions.forEach(interaction => {
            actionCounts[interaction.action] = (actionCounts[interaction.action] || 0) + 1;
        });

        Object.entries(actionCounts).forEach(([action, count]) => {
            if (count > 3 && action.includes('change')) {
                patterns.repetitive = true;
                patterns.suggestion = `Consider using a template for ${action.replace('_change', '')} settings`;
            }
        });

        return patterns;
    }

    updateAILearning(interaction) {
        this.aiAssistant.learningData.push({
            timestamp: interaction.timestamp,
            action: interaction.action,
            success: this.determineInteractionSuccess(interaction),
            context: this.getCurrentContext()
        });

        // Update user preferences based on successful interactions
        if (interaction.action === 'generate_avatar') {
            this.userBehavior.successfulConfigs.push({ ...this.currentConfig });
        }

        // Save preferences
        this.saveUserPreferences();
    }

    determineInteractionSuccess(interaction) {
        // Simple heuristic: if user proceeds to next step quickly, it was likely successful
        const nextInteraction = this.userBehavior.interactions[this.userBehavior.interactions.length - 1];
        return nextInteraction && (nextInteraction.timestamp - interaction.timestamp) < 5000;
    }

    getCurrentContext() {
        return {
            config: { ...this.currentConfig },
            timestamp: Date.now(),
            hasContent: !!this.getPasteContent()
        };
    }

    saveUserPreferences() {
        try {
            const preferences = {
                successfulConfigs: this.userBehavior.successfulConfigs.slice(-10), // Keep last 10
                preferences: this.userBehavior.preferences,
                lastUpdated: Date.now()
            };

            localStorage.setItem('pasteAvatarPreferences', JSON.stringify(preferences));
        } catch (error) {
            console.error('Failed to save user preferences:', error);
        }
    }

    loadSuccessfulConfigs() {
        try {
            const stored = localStorage.getItem('pasteAvatarPreferences');
            if (stored) {
                const data = JSON.parse(stored);
                this.userBehavior.successfulConfigs = data.successfulConfigs || [];
            }
        } catch (error) {
            console.error('Failed to load successful configs:', error);
        }
    }

    generateSmartRecommendations() {
        if (this.userBehavior.successfulConfigs.length === 0) return;

        // Analyze successful configurations to recommend similar settings
        const commonSettings = this.findCommonSettings(this.userBehavior.successfulConfigs);

        if (Object.keys(commonSettings).length > 0) {
            const recommendation = {
                id: 'smart_config',
                text: 'Apply your most successful settings',
                action: () => this.applyRecommendedSettings(commonSettings)
            };

            this.displaySuggestions([recommendation]);
        }
    }

    findCommonSettings(configs) {
        const settingCounts = {};
        const totalConfigs = configs.length;

        configs.forEach(config => {
            Object.entries(config).forEach(([key, value]) => {
                const settingKey = `${key}:${value}`;
                settingCounts[settingKey] = (settingCounts[settingKey] || 0) + 1;
            });
        });

        // Return settings that appear in >50% of successful configs
        const commonSettings = {};
        Object.entries(settingCounts).forEach(([setting, count]) => {
            if (count / totalConfigs > 0.5) {
                const [key, value] = setting.split(':');
                commonSettings[key] = value === 'true' ? true : value === 'false' ? false : value;
            }
        });

        return commonSettings;
    }

    applyRecommendedSettings(settings) {
        Object.entries(settings).forEach(([key, value]) => {
            this.updateConfig(key, value);
        });

        this.setStatus('Applied your most successful settings', 'success');
    }

    trackTimeSpent(elementId) {
        const now = Date.now();
        if (this.userBehavior.timeSpent[elementId]) {
            this.userBehavior.timeSpent[elementId] += now - (this.userBehavior.lastFocusTime || now);
        } else {
            this.userBehavior.timeSpent[elementId] = 0;
        }
        this.userBehavior.lastFocusTime = now;
    }

    updateContextualHelp() {
        // Provide contextual help based on current state
        const helpContainer = document.getElementById('ai-contextual-help');
        if (!helpContainer) return;

        const context = this.getCurrentHelpContext();
        if (context) {
            this.showContextualHelp(context);
        }
    }

    getCurrentHelpContext() {
        // Determine what help to show based on current state
        if (!this.getPasteContent()) {
            return 'no_content';
        }

        if (this.userBehavior.interactions.length === 0) {
            return 'getting_started';
        }

        return null; // No specific help needed
    }

    offerHelp(context) {
        const helpSuggestion = {
            id: 'contextual_help',
            text: 'Need help? Click for guidance on current settings',
            action: () => this.showContextualHelp(context)
        };

        this.displaySuggestions([helpSuggestion]);
    }

    suggestOptimization(suggestion) {
        const optimizationSuggestion = {
            id: 'optimization',
            text: suggestion,
            action: () => this.showTemplateSelector()
        };

        this.displaySuggestions([optimizationSuggestion]);
    }

    showTemplateSelector() {
        const templateSelector = document.getElementById('template-selector');
        if (templateSelector) {
            templateSelector.focus();
            templateSelector.scrollIntoView({ behavior: 'smooth' });
        }
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

            /* AI Assistant Styles */
            .ai-assistant-panel {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 12px;
                margin-bottom: 20px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }

            .ai-assistant-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }

            .ai-assistant-header h4 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }

            .ai-toggle-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }

            .ai-toggle-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }

            .ai-assistant-content {
                padding: 20px;
            }

            .ai-suggestions {
                margin-bottom: 15px;
            }

            .ai-suggestion {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                backdrop-filter: blur(5px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                animation: slideInFromTop 0.3s ease-out;
            }

            @keyframes slideInFromTop {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .suggestion-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 15px;
            }

            .suggestion-text {
                flex: 1;
                font-size: 14px;
                line-height: 1.4;
            }

            .suggestion-actions {
                display: flex;
                gap: 8px;
            }

            .ai-suggestion-btn, .ai-dismiss-btn {
                padding: 6px 12px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
            }

            .ai-suggestion-btn {
                background: rgba(255, 255, 255, 0.9);
                color: #667eea;
                font-weight: 600;
            }

            .ai-suggestion-btn:hover {
                background: white;
                transform: translateY(-1px);
            }

            .ai-dismiss-btn {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                width: 24px;
                height: 24px;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .ai-dismiss-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }

            .ai-contextual-help {
                margin-bottom: 15px;
            }

            .contextual-help {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 15px;
                backdrop-filter: blur(5px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }

            .contextual-help h5 {
                margin: 0 0 10px 0;
                font-size: 14px;
                font-weight: 600;
            }

            .contextual-help p {
                margin: 0 0 10px 0;
                font-size: 13px;
                line-height: 1.4;
                opacity: 0.9;
            }

            .contextual-help ul {
                margin: 10px 0;
                padding-left: 20px;
                font-size: 12px;
                opacity: 0.8;
            }

            .contextual-help li {
                margin-bottom: 5px;
            }

            .ai-quick-actions {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }

            .ai-help-btn, .ai-optimize-btn {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
                backdrop-filter: blur(5px);
            }

            .ai-help-btn:hover, .ai-optimize-btn:hover {
                 background: rgba(255, 255, 255, 0.3);
                 transform: translateY(-1px);
             }

             /* Responsive AI Assistant */
             @media (max-width: 768px) {
                 .ai-assistant-panel {
                     margin: 10px;
                 }

                 .suggestion-content {
                     flex-direction: column;
                     align-items: flex-start;
                     gap: 10px;
                 }

                 .suggestion-actions {
                     align-self: flex-end;
                 }

                 .ai-quick-actions {
                     justify-content: center;
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
