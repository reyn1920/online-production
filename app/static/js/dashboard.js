/**
 * TRAE.AI Dashboard JavaScript
 * Main dashboard functionality and interactions
 */

// Global dashboard state
const Dashboard = {
  refreshInterval: 5000, // 5 seconds
  activeModule: 'command-center',
  socket: null,

  // Initialize dashboard
  init() {
    this.setupEventListeners();
    this.initializeModules();
    this.startAutoRefresh();
    this.connectWebSocket();
    console.log('TRAE.AI Dashboard initialized');
  },

  // Setup event listeners
  setupEventListeners() {
    // Module tab switching
    document.querySelectorAll('.tab-button').forEach(button => {
      button.addEventListener('click', e => {
        this.switchModule(e.target.dataset.module);
      });
    });

    // Refresh buttons
    document.querySelectorAll('.refresh-btn').forEach(button => {
      button.addEventListener('click', e => {
        this.refreshData(e.target.dataset.endpoint);
      });
    });

    // Form submissions
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', e => {
        this.handleFormSubmit(e);
      });
    });

    // Toggle switches
    document.querySelectorAll('.toggle-switch').forEach(toggle => {
      toggle.addEventListener('change', e => {
        this.handleToggle(e.target);
      });
    });
  },

  // Initialize modules
  initializeModules() {
    this.loadAgentStatus();
    this.loadTaskQueue();
    this.loadSystemMetrics();
    this.loadRecentActivity();
  },

  // Switch between modules
  switchModule(moduleId) {
    // Hide all modules
    document.querySelectorAll('.module-content').forEach(module => {
      module.classList.remove('active');
    });

    // Remove active class from all tabs
    document.querySelectorAll('.tab-button').forEach(tab => {
      tab.classList.remove('active');
    });

    // Show selected module
    const targetModule = document.getElementById(moduleId);
    if (targetModule) {
      targetModule.classList.add('active');
    }

    // Activate selected tab
    const targetTab = document.querySelector(`[data-module="${moduleId}"]`);
    if (targetTab) {
      targetTab.classList.add('active');
    }

    this.activeModule = moduleId;
    this.loadModuleData(moduleId);
  },

  // Load module-specific data
  loadModuleData(moduleId) {
    switch (moduleId) {
      case 'command-center':
        this.loadAgentStatus();
        this.loadTaskQueue();
        break;
      case 'database-explorer':
        this.loadDatabaseStats();
        break;
      case 'product-studio':
        this.loadProjects();
        break;
      case 'reporting-engine':
        this.loadReports();
        break;
    }
  },

  // Load agent status
  async loadAgentStatus() {
    try {
      const response = await fetch('/api/agents/status');
      const data = await response.json();
      this.updateAgentStatus(data);
    } catch (error) {
      console.error('Failed to load agent status:', error);
      this.showError('Failed to load agent status');
    }
  },

  // Update agent status display
  updateAgentStatus(data) {
    const container = document.getElementById('agent-status');
    if (!container) return;

    container.innerHTML = '';

    Object.entries(data).forEach(([agentId, status]) => {
      const agentCard = document.createElement('div');
      agentCard.className = 'agent-card';
      agentCard.innerHTML = `
                <div class="agent-header">
                    <h4>${status.name}</h4>
                    <span class="status-indicator status-${status.status}"></span>
                </div>
                <div class="agent-details">
                    <p><strong>Status:</strong> ${status.status}</p>
                    <p><strong>Last Active:</strong> ${status.last_active}</p>
                    <p><strong>Tasks Completed:</strong> ${status.tasks_completed}</p>
                </div>
                <div class="agent-actions">
                    <button class="btn btn-custom btn-sm" onclick="Dashboard.controlAgent('${agentId}', 'start')">Start</button>
                    <button class="btn btn-warning btn-sm" onclick="Dashboard.controlAgent('${agentId}', 'pause')">Pause</button>
                    <button class="btn btn-danger btn-sm" onclick="Dashboard.controlAgent('${agentId}', 'stop')">Stop</button>
                </div>
            `;
      container.appendChild(agentCard);
    });
  },

  // Load task queue
  async loadTaskQueue() {
    try {
      const response = await fetch('/api/tasks');
      const data = await response.json();
      this.updateTaskQueue(data);
    } catch (error) {
      console.error('Failed to load task queue:', error);
      this.showError('Failed to load task queue');
    }
  },

  // Update task queue display
  updateTaskQueue(tasks) {
    const container = document.getElementById('task-queue');
    if (!container) return;

    container.innerHTML = '';

    if (tasks.length === 0) {
      container.innerHTML = '<p class="text-center text-muted">No active tasks</p>';
      return;
    }

    tasks.forEach(task => {
      const taskCard = document.createElement('div');
      taskCard.className = 'task-card';
      taskCard.innerHTML = `
                <div class="task-header">
                    <h5>${task.title}</h5>
                    <span class="badge badge-${task.status}">${task.status}</span>
                </div>
                <div class="task-details">
                    <p>${task.description}</p>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${task.progress}%"></div>
                    </div>
                    <small class="text-muted">Created: ${task.created_at}</small>
                </div>
            `;
      container.appendChild(taskCard);
    });
  },

  // Load system metrics
  async loadSystemMetrics() {
    try {
      const response = await fetch('/api/system/metrics');
      const data = await response.json();
      this.updateSystemMetrics(data);
    } catch (error) {
      console.error('Failed to load system metrics:', error);
    }
  },

  // Update system metrics display
  updateSystemMetrics(metrics) {
    Object.entries(metrics).forEach(([key, value]) => {
      const element = document.getElementById(`metric-${key}`);
      if (element) {
        element.textContent = value;
      }
    });
  },

  // Control agent
  async controlAgent(agentId, action) {
    try {
      const response = await fetch(`/api/agents/${agentId}/${action}`, {
        method: 'POST',
      });

      if (response.ok) {
        this.showSuccess(`Agent ${action} successful`);
        this.loadAgentStatus(); // Refresh status
      } else {
        this.showError(`Failed to ${action} agent`);
      }
    } catch (error) {
      console.error(`Failed to ${action} agent:`, error);
      this.showError(`Failed to ${action} agent`);
    }
  },

  // Handle form submissions
  async handleFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const endpoint = form.action || form.dataset.endpoint;

    if (!endpoint) {
      this.showError('No endpoint specified for form');
      return;
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        this.showSuccess(result.message || 'Operation successful');
        form.reset();
      } else {
        this.showError('Operation failed');
      }
    } catch (error) {
      console.error('Form submission error:', error);
      this.showError('Operation failed');
    }
  },

  // Handle toggle switches
  async handleToggle(toggle) {
    const setting = toggle.dataset.setting;
    const value = toggle.checked;

    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          [setting]: value,
        }),
      });

      if (response.ok) {
        this.showSuccess('Setting updated');
      } else {
        this.showError('Failed to update setting');
        toggle.checked = !value; // Revert
      }
    } catch (error) {
      console.error('Toggle error:', error);
      this.showError('Failed to update setting');
      toggle.checked = !value; // Revert
    }
  },

  // Refresh data
  async refreshData(endpoint) {
    if (!endpoint) {
      this.initializeModules();
      return;
    }

    try {
      const response = await fetch(endpoint);
      const data = await response.json();

      // Update relevant display based on endpoint
      if (endpoint.includes('agents')) {
        this.updateAgentStatus(data);
      } else if (endpoint.includes('tasks')) {
        this.updateTaskQueue(data);
      } else if (endpoint.includes('metrics')) {
        this.updateSystemMetrics(data);
      }

      this.showSuccess('Data refreshed');
    } catch (error) {
      console.error('Refresh error:', error);
      this.showError('Failed to refresh data');
    }
  },

  // Start auto-refresh
  startAutoRefresh() {
    setInterval(() => {
      if (document.visibilityState === 'visible') {
        this.loadModuleData(this.activeModule);
      }
    }, this.refreshInterval);
  },

  // Connect WebSocket for real-time updates
  connectWebSocket() {
    if (typeof io !== 'undefined') {
      // Replace existing socket connection with this explicit config:
      const socket = io(window.location.origin, {
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        timeout: 20000,
        forceNew: true, // prevents cached connection issues
      });

      this.socket = socket;

      // Add connection verification
      socket.on('connect', () => {
        console.log('✅ Socket.IO connected:', socket.id, 'via', socket.io.engine.transport.name);
      });

      socket.on('disconnect', reason => {
        console.log('❌ Socket.IO disconnected:', reason);
      });

      // Set up event handlers
      socket.on('agent_status_update', data => {
        this.updateAgentStatus(data);
      });

      socket.on('task_update', data => {
        this.loadTaskQueue();
      });

      socket.on('system_alert', data => {
        this.showAlert(data.message, data.type);
      });

      socket.on('error', err => console.error('[dashboard socket] error', err));
    }
  },

  // Show success message
  showSuccess(message) {
    this.showAlert(message, 'success');
  },

  // Show error message
  showError(message) {
    this.showAlert(message, 'danger');
  },

  // Show alert
  showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container') || document.body;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade-in`;
    alert.innerHTML = `
            <span>${message}</span>
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;

    alertContainer.appendChild(alert);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (alert.parentElement) {
        alert.remove();
      }
    }, 5000);
  },

  // Utility functions
  formatDate(dateString) {
    return new Date(dateString).toLocaleString();
  },

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  formatNumber(num) {
    return new Intl.NumberFormat().format(num);
  },
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  Dashboard.init();
});

// Export for global access
window.Dashboard = Dashboard;
