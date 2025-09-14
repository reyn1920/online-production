/**
 * TRAE.AI Diagnostics Panel
 * Floating diagnostics panel with system info and action catalog
 */

class DiagnosticsPanel {
  constructor() {
    this.isVisible = false;
    this.panel = null;
    this.apiBase = window.VITE_API_BASE || 'http://127.0.0.1:8083';
    this.init();
  }

  init() {
    this.createPanel();
    this.attachEventListeners();
    this.loadDiagnostics();

    // Auto-refresh every 30 seconds
    setInterval(() => this.loadDiagnostics(), 30000);
  }

  createPanel() {
    // Create floating panel
    this.panel = document.createElement('div');
    this.panel.id = 'trae-diagnostics-panel';
    this.panel.innerHTML = `
            <div class="diagnostics-header">
                <h3>🔧 TRAE Diagnostics</h3>
                <button class="close-btn" onclick="window.traePanel.toggle()">&times;</button>
            </div>
            <div class="diagnostics-tabs">
                <button class="tab-btn active" data-tab="status">Status</button>
                <button class="tab-btn" data-tab="metrics">Metrics</button>
                <button class="tab-btn" data-tab="actions">Actions</button>
            </div>
            <div class="diagnostics-content">
                <div class="tab-content active" id="status-tab">
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-label">Service:</span>
                            <span class="status-value" id="service-status">Loading...</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Version:</span>
                            <span class="status-value" id="version-status">Loading...</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Socket.IO:</span>
                            <span class="status-value" id="socket-status">Checking...</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Readiness:</span>
                            <span class="status-value" id="readiness-status">Checking...</span>
                        </div>
                    </div>
                </div>
                <div class="tab-content" id="metrics-tab">
                    <div class="metrics-grid" id="metrics-content">
                        Loading metrics...
                    </div>
                </div>
                <div class="tab-content" id="actions-tab">
                    <div class="actions-list">
                        <div class="action-item">
                            <h4>📊 Get Metrics</h4>
                            <code class="curl-command">curl ${this.apiBase}/api/metrics</code>
                            <button onclick="window.traePanel.copyToClipboard(this.previousElementSibling.textContent)">Copy</button>
                        </div>
                        <div class="action-item">
                            <h4>📋 Dashboard Snapshot</h4>
                            <code class="curl-command">curl ${this.apiBase}/api/dashboard</code>
                            <button onclick="window.traePanel.copyToClipboard(this.previousElementSibling.textContent)">Copy</button>
                        </div>
                        <div class="action-item">
                            <h4>🔍 Version Info</h4>
                            <code class="curl-command">curl ${this.apiBase}/api/version</code>
                            <button onclick="window.traePanel.copyToClipboard(this.previousElementSibling.textContent)">Copy</button>
                        </div>
                        <div class="action-item">
                            <h4>🔌 Socket.IO Test</h4>
                            <code class="curl-command">curl ${this.apiBase}/socket.io/?EIO=4&transport=polling</code>
                            <button onclick="window.traePanel.copyToClipboard(this.previousElementSibling.textContent)">Copy</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
            #trae-diagnostics-panel {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 400px;
                max-height: 600px;
                background: #1a1a1a;
                border: 1px solid #333;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                z-index: 10000;
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 12px;
                color: #e0e0e0;
                display: none;
                overflow: hidden;
            }
            
            .diagnostics-header {
                background: #2d2d2d;
                padding: 10px 15px;
                border-bottom: 1px solid #333;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .diagnostics-header h3 {
                margin: 0;
                font-size: 14px;
                color: #4CAF50;
            }
            
            .close-btn {
                background: none;
                border: none;
                color: #999;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
            }
            
            .close-btn:hover {
                color: #fff;
            }
            
            .diagnostics-tabs {
                display: flex;
                background: #2d2d2d;
                border-bottom: 1px solid #333;
            }
            
            .tab-btn {
                flex: 1;
                background: none;
                border: none;
                color: #999;
                padding: 8px 12px;
                cursor: pointer;
                font-size: 11px;
                border-right: 1px solid #333;
            }
            
            .tab-btn:last-child {
                border-right: none;
            }
            
            .tab-btn.active {
                background: #1a1a1a;
                color: #4CAF50;
            }
            
            .diagnostics-content {
                max-height: 500px;
                overflow-y: auto;
            }
            
            .tab-content {
                display: none;
                padding: 15px;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .status-grid {
                display: grid;
                gap: 8px;
            }
            
            .status-item {
                display: flex;
                justify-content: space-between;
                padding: 6px 0;
                border-bottom: 1px solid #333;
            }
            
            .status-label {
                color: #999;
            }
            
            .status-value {
                color: #e0e0e0;
                font-weight: bold;
            }
            
            .status-value.ok {
                color: #4CAF50;
            }
            
            .status-value.error {
                color: #f44336;
            }
            
            .status-value.warning {
                color: #ff9800;
            }
            
            .metrics-grid {
                font-size: 11px;
                line-height: 1.4;
            }
            
            .action-item {
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #333;
            }
            
            .action-item:last-child {
                border-bottom: none;
            }
            
            .action-item h4 {
                margin: 0 0 8px 0;
                color: #4CAF50;
                font-size: 12px;
            }
            
            .curl-command {
                display: block;
                background: #0d1117;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                margin: 5px 0;
                font-family: 'Monaco', monospace;
                font-size: 10px;
                color: #58a6ff;
                word-break: break-all;
                white-space: pre-wrap;
            }
            
            .action-item button {
                background: #238636;
                border: none;
                color: white;
                padding: 4px 8px;
                border-radius: 3px;
                cursor: pointer;
                font-size: 10px;
                margin-top: 5px;
            }
            
            .action-item button:hover {
                background: #2ea043;
            }
            
            #trae-diagnostics-toggle {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #4CAF50;
                border: none;
                color: white;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 20px;
                z-index: 9999;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            }
            
            #trae-diagnostics-toggle:hover {
                background: #45a049;
            }
        `;

    document.head.appendChild(style);
    document.body.appendChild(this.panel);

    // Create toggle button
    const toggleBtn = document.createElement('button');
    toggleBtn.id = 'trae-diagnostics-toggle';
    toggleBtn.innerHTML = '🔧';
    toggleBtn.onclick = () => this.toggle();
    document.body.appendChild(toggleBtn);
  }

  attachEventListeners() {
    // Tab switching
    this.panel.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', e => {
        const tabName = e.target.dataset.tab;
        this.switchTab(tabName);
      });
    });
  }

  switchTab(tabName) {
    // Update tab buttons
    this.panel.querySelectorAll('.tab-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    this.panel.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    this.panel.querySelectorAll('.tab-content').forEach(content => {
      content.classList.remove('active');
    });
    this.panel.querySelector(`#${tabName}-tab`).classList.add('active');

    // Load data for specific tabs
    if (tabName === 'metrics') {
      this.loadMetrics();
    }
  }

  async loadDiagnostics() {
    await Promise.all([this.checkVersion(), this.checkReadiness(), this.checkSocketIO()]);
  }

  async checkVersion() {
    try {
      const response = await fetch(`${this.apiBase}/api/version`);
      if (response.ok) {
        const data = await response.json();
        document.getElementById('service-status').textContent = data.service || 'Unknown';
        document.getElementById('service-status').className = 'status-value ok';
        document.getElementById('version-status').textContent = data.version || 'Unknown';
        document.getElementById('version-status').className = 'status-value ok';
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      document.getElementById('service-status').textContent = 'Error';
      document.getElementById('service-status').className = 'status-value error';
      document.getElementById('version-status').textContent = error.message;
      document.getElementById('version-status').className = 'status-value error';
    }
  }

  async checkReadiness() {
    try {
      const response = await fetch(`${this.apiBase}/api/version`);
      const status = response.ok ? 'Ready' : 'Not Ready';
      const className = response.ok ? 'status-value ok' : 'status-value error';
      document.getElementById('readiness-status').textContent = status;
      document.getElementById('readiness-status').className = className;
    } catch (error) {
      document.getElementById('readiness-status').textContent = 'Error';
      document.getElementById('readiness-status').className = 'status-value error';
    }
  }

  async checkSocketIO() {
    try {
      const response = await fetch(`${this.apiBase}/socket.io/?EIO=4&transport=polling`);
      const status = response.ok ? 'Connected' : 'Disconnected';
      const className = response.ok ? 'status-value ok' : 'status-value warning';
      document.getElementById('socket-status').textContent = status;
      document.getElementById('socket-status').className = className;
    } catch (error) {
      document.getElementById('socket-status').textContent = 'Error';
      document.getElementById('socket-status').className = 'status-value error';
    }
  }

  async loadMetrics() {
    const metricsContent = document.getElementById('metrics-content');
    metricsContent.innerHTML = 'Loading metrics...';

    try {
      const response = await fetch(`${this.apiBase}/api/metrics`);
      if (response.ok) {
        const data = await response.json();
        metricsContent.innerHTML = this.formatMetrics(data);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      metricsContent.innerHTML = `<div class="error">Failed to load metrics: ${error.message}</div>`;
    }
  }

  formatMetrics(data) {
    let html = '';

    if (data.system) {
      html += '<h4>🖥️ System</h4>';
      Object.entries(data.system).forEach(([key, value]) => {
        html += `<div class="status-item"><span>${key}:</span><span>${value}</span></div>`;
      });
    }

    if (data.database) {
      html += '<h4>🗄️ Database</h4>';
      Object.entries(data.database).forEach(([key, value]) => {
        html += `<div class="status-item"><span>${key}:</span><span>${value}</span></div>`;
      });
    }

    if (data.agents && Array.isArray(data.agents)) {
      html += `<h4>🤖 Agents (${data.agents.length})</h4>`;
      data.agents.forEach((agent, i) => {
        html += `<div class="status-item"><span>Agent ${i + 1}:</span><span>${agent.status || 'active'}</span></div>`;
      });
    }

    return html || '<div>No metrics available</div>';
  }

  toggle() {
    this.isVisible = !this.isVisible;
    this.panel.style.display = this.isVisible ? 'block' : 'none';

    if (this.isVisible) {
      this.loadDiagnostics();
    }
  }

  copyToClipboard(text) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        // Show brief success feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.background = '#2ea043';
        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.background = '#238636';
        }, 1000);
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.traePanel = new DiagnosticsPanel();
  });
} else {
  window.traePanel = new DiagnosticsPanel();
}
