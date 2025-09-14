/**
 * TRAE.AI Dashboard JavaScript
 * Main dashboard functionality and interactions
 */

// Enhanced Dashboard JavaScript functionality
const Dashboard = {
  refreshInterval: 5000, // 5 seconds
  activeModule: 'command-center',
  socket: null,
  charts: {},
  websocket: null,
  
  // Configuration
  config: {
    refreshInterval: 30000, // 30 seconds
    wsReconnectDelay: 5000,
    apiBaseUrl: '/api',
    cacheTimeout: 60000, // 1 minute cache
    batchSize: 50, // For pagination
    debounceDelay: 300 // For search
  },
  
  // Authentication state
  auth: {
    token: null,
    user: null,
    isAuthenticated: false
  },
  
  // Performance optimization
  cache: new Map(),
  loadingStates: new Set(),
  debounceTimers: new Map(),

  // Initialize dashboard
  init() {
    console.log('🚀 Initializing Dashboard...');
    
    // Performance monitoring
    const startTime = performance.now();
    
    // Check authentication first
    this.checkAuthentication();
    
    this.setupEventListeners();
    this.initializeModulesLazy();
    this.initializeCharts();
    this.startSmartRefresh();
    this.connectWebSocket();
    this.loadInitialData();
    
    // Setup performance monitoring
    this.setupPerformanceMonitoring();
    
    const endTime = performance.now();
    console.log(`✅ Dashboard initialized successfully in ${(endTime - startTime).toFixed(2)}ms`);
  },

  // Setup event listeners
  setupEventListeners() {
    // Authentication event listeners
    this.setupAuthEventListeners();
    
    // User management event listeners
    this.setupUserManagementListeners();
    
    // Module tab switching
    document.querySelectorAll('.tab-button, .nav-tab').forEach(button => {
      button.addEventListener('click', e => {
        const moduleId = e.target.dataset.module || e.target.dataset.tab;
        if (moduleId) {
          this.switchModule(moduleId);
          this.updateURL(moduleId);
          this.trackAnalytics('tab_switch', { tab: moduleId });
        }
      });
    });

    // Refresh buttons
    document.querySelectorAll('.refresh-btn, [onclick*="refresh"]').forEach(button => {
      button.addEventListener('click', e => {
        e.preventDefault();
        const endpoint = e.target.dataset.endpoint || 'all';
        this.refreshData(endpoint);
        this.showRefreshAnimation(e.target);
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

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', this.handleSearch.bind(this));
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    
    // User management event listeners
    this.setupUserManagementListeners();
  },

  // Authentication event listeners
  setupAuthEventListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleLogin();
      });
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', () => {
        this.handleLogout();
      });
    }
  },
  
  // User management event listeners
  setupUserManagementListeners() {
    // Add user button
    const addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
      addUserBtn.addEventListener('click', () => {
        this.showUserModal();
      });
    }
    
    // User form
    const userForm = document.getElementById('user-form');
    if (userForm) {
      userForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleUserSave();
      });
    }
    
    // Close user modal
    const closeUserModal = document.getElementById('close-user-modal');
    const cancelUserForm = document.getElementById('cancel-user-form');
    if (closeUserModal) {
      closeUserModal.addEventListener('click', () => {
        this.hideUserModal();
      });
    }
    if (cancelUserForm) {
      cancelUserForm.addEventListener('click', () => {
        this.hideUserModal();
      });
    }
  },

  // Initialize modules
  initializeModules() {
    // Initialize modules without loading data (data loading handled by loadAllData)
    console.log('📊 Modules initialized');
  },
  
  // Initialize modules with lazy loading
  initializeModulesLazy() {
    // Initialize only visible charts
    this.initializeVisibleCharts();
    
    // Setup intersection observer for lazy loading
    this.setupLazyLoading();
    
    console.log('📊 Modules initialized with lazy loading');
  },
  
  // Setup lazy loading for charts and heavy components
  setupLazyLoading() {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const element = entry.target;
            const chartType = element.dataset.chartType;
            
            if (chartType && !this.charts[chartType]) {
              this.initializeChart(chartType, element);
            }
            
            observer.unobserve(element);
          }
        });
      }, {
        rootMargin: '50px'
      });
      
      // Observe all chart containers
      document.querySelectorAll('[data-chart-type]').forEach(el => {
        observer.observe(el);
      });
    }
  },
  
  // Initialize only visible charts
  initializeVisibleCharts() {
    const visibleCharts = document.querySelectorAll('[data-chart-type]:not([hidden])');
    visibleCharts.forEach(element => {
      const chartType = element.dataset.chartType;
      if (chartType) {
        this.initializeChart(chartType, element);
      }
    });
  },
  
  // Setup performance monitoring
  setupPerformanceMonitoring() {
    // Monitor memory usage
    if ('memory' in performance) {
      setInterval(() => {
        const memory = performance.memory;
        if (memory.usedJSHeapSize > memory.jsHeapSizeLimit * 0.9) {
          console.warn('High memory usage detected, clearing cache');
          this.clearCache();
        }
      }, 60000); // Check every minute
    }
    
    // Monitor page visibility
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        // Refresh data when page becomes visible
        this.loadCriticalData();
      }
    });
  },
  
  // Clear cache to free memory
  clearCache() {
    const oldSize = this.cache.size;
    this.cache.clear();
    console.log(`🧹 Cleared ${oldSize} cached items`);
  },
  
  // Initialize a specific chart
  initializeChart(chartType, element) {
    // Placeholder for chart initialization logic
    console.log(`Initializing chart: ${chartType}`);
    this.charts[chartType] = { element, initialized: true };
  },

  // Switch between modules
  switchModule(moduleId) {
    // Check if user has permission for this module
    if (moduleId === 'users' && (!this.auth.user || this.auth.user.role !== 'ADMIN')) {
      this.showError('Access denied. Admin privileges required.');
      return;
    }
    
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
      case 'users':
        this.loadUsers();
        break;
    }
  },

  // Load reports
  async loadReports() {
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth('/api/reports');
      const data = await response.json();
      this.updateReports(data);
    } catch (error) {
      console.error('Failed to load reports:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load reports');
      }
    }
  },

  // Update reports display
  updateReports(reports) {
    const container = document.getElementById('reports-container');
    if (!container) return;

    container.innerHTML = '';

    if (reports.length === 0) {
      container.innerHTML = '<p class="text-center text-muted">No reports available</p>';
      return;
    }

    reports.forEach(report => {
      const reportCard = document.createElement('div');
      reportCard.className = 'report-card';
      reportCard.innerHTML = `
        <div class="report-header">
          <h5>${report.title}</h5>
          <span class="badge badge-${report.status}">${report.status}</span>
        </div>
        <div class="report-details">
          <p>${report.description}</p>
          <small class="text-muted">Generated: ${report.created_at}</small>
        </div>
      `;
      container.appendChild(reportCard);
    });
  },

  // Load database stats
  async loadDatabaseStats() {
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth('/api/database/stats');
      const data = await response.json();
      this.updateDatabaseStats(data);
    } catch (error) {
      console.error('Failed to load database stats:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load database stats');
      }
    }
  },

  // Update database stats display
  updateDatabaseStats(stats) {
    Object.entries(stats).forEach(([key, value]) => {
      const element = document.getElementById(`db-${key}`);
      if (element) {
        element.textContent = value;
      }
    });
  },

  // Load projects
  async loadProjects() {
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth('/api/projects');
      const data = await response.json();
      this.updateProjects(data);
    } catch (error) {
      console.error('Failed to load projects:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load projects');
      }
    }
  },

  // Update projects display
  updateProjects(projects) {
    const container = document.getElementById('projects-container');
    if (!container) return;

    container.innerHTML = '';

    if (projects.length === 0) {
      container.innerHTML = '<p class="text-center text-muted">No projects available</p>';
      return;
    }

    projects.forEach(project => {
      const projectCard = document.createElement('div');
      projectCard.className = 'project-card';
      projectCard.innerHTML = `
        <div class="project-header">
          <h5>${project.name}</h5>
          <span class="badge badge-${project.status}">${project.status}</span>
        </div>
        <div class="project-details">
          <p>${project.description}</p>
          <div class="progress">
            <div class="progress-bar" style="width: ${project.progress}%"></div>
          </div>
          <small class="text-muted">Updated: ${project.updated_at}</small>
        </div>
      `;
      container.appendChild(projectCard);
    });
  },

  // Check authentication status
  checkAuthentication() {
    // Skip authentication - show dashboard directly
    this.auth.token = 'demo-token';
    this.auth.user = { username: 'demo', full_name: 'Demo User', role: 'ADMIN' };
    this.auth.isAuthenticated = true;
    this.showDashboard();
  },
  
  // Show login modal
  showLoginModal() {
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
      loginModal.classList.remove('hidden');
    }
  },
  
  // Load remembered credentials
  loadRememberedCredentials() {
    const rememberMeEnabled = localStorage.getItem('remember_me_enabled');
    const rememberedUsername = localStorage.getItem('remembered_username');
    const rememberedPassword = localStorage.getItem('remembered_password');
    
    if (rememberMeEnabled === 'true' && rememberedUsername && rememberedPassword) {
      const usernameField = document.getElementById('username');
      const passwordField = document.getElementById('password');
      const rememberMeCheckbox = document.getElementById('remember-me');
      
      if (usernameField) usernameField.value = rememberedUsername;
      if (passwordField) passwordField.value = rememberedPassword;
      if (rememberMeCheckbox) rememberMeCheckbox.checked = true;
    }
  },
  
  // Hide login modal
  hideLoginModal() {
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
      loginModal.classList.add('hidden');
    }
  },
  
  // Show dashboard
  showDashboard() {
    this.hideLoginModal();
    this.updateUserInfo();
  },
  
  // Update user info in UI
  updateUserInfo() {
    const userInfo = document.getElementById('user-info');
    const userName = document.getElementById('user-name');
    
    if (this.auth.user && userInfo && userName) {
      userName.textContent = `Welcome, ${this.auth.user.full_name || this.auth.user.username}`;
      userInfo.classList.remove('hidden');
    }
  },
  
  // Handle login
  async handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('remember-me').checked;
    const loginError = document.getElementById('login-error');
    const loginErrorMessage = document.getElementById('login-error-message');
    const loginSubmit = document.getElementById('login-submit');
    
    try {
      loginSubmit.disabled = true;
      loginSubmit.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Signing In...';
      
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Store authentication data
        localStorage.setItem('dashboard_token', data.access_token);
        localStorage.setItem('dashboard_user', JSON.stringify(data.user));
        
        // Handle remember me functionality
        if (rememberMe) {
          localStorage.setItem('remembered_username', username);
          localStorage.setItem('remembered_password', password);
          localStorage.setItem('remember_me_enabled', 'true');
        } else {
          localStorage.removeItem('remembered_username');
          localStorage.removeItem('remembered_password');
          localStorage.removeItem('remember_me_enabled');
        }
        
        this.auth.token = data.access_token;
        this.auth.user = data.user;
        this.auth.isAuthenticated = true;
        
        this.showDashboard();
        this.showSuccess('Login successful!');
      } else {
        loginError.classList.remove('hidden');
        loginErrorMessage.textContent = data.detail || 'Login failed';
      }
    } catch (error) {
      console.error('Login error:', error);
      loginError.classList.remove('hidden');
      loginErrorMessage.textContent = 'Network error. Please try again.';
    } finally {
      loginSubmit.disabled = false;
      loginSubmit.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Sign In';
    }
  },
  
  // Handle logout
  handleLogout() {
    localStorage.removeItem('dashboard_token');
    localStorage.removeItem('dashboard_user');
    
    // Keep remembered credentials if remember me is enabled
    const rememberMeEnabled = localStorage.getItem('remember_me_enabled');
    if (rememberMeEnabled !== 'true') {
      localStorage.removeItem('remembered_username');
      localStorage.removeItem('remembered_password');
      localStorage.removeItem('remember_me_enabled');
    }
    
    this.auth.token = null;
    this.auth.user = null;
    this.auth.isAuthenticated = false;
    
    this.showLoginModal();
    this.loadRememberedCredentials();
    this.showSuccess('Logged out successfully');
  },

  // Load agent status
  async loadAgentStatus() {
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth('/api/agents/status');
      const data = await response.json();
      this.updateAgentStatus(data);
    } catch (error) {
      console.error('Failed to load agent status:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load agent status');
      }
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

  // Optimized fetch with caching and error handling
  async fetchWithAuth(url, options = {}) {
    const cacheKey = `${url}_${JSON.stringify(options)}`;
    const useCache = options.cache !== false;
    
    // Check cache first
    if (useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.config.cacheTimeout) {
        return cached.data;
      }
    }
    
    // Prevent duplicate requests
    if (this.loadingStates.has(cacheKey)) {
      return new Promise((resolve, reject) => {
        const checkLoading = () => {
          if (!this.loadingStates.has(cacheKey)) {
            if (this.cache.has(cacheKey)) {
              resolve(this.cache.get(cacheKey).data);
            } else {
              reject(new Error('Request failed'));
            }
          } else {
            setTimeout(checkLoading, 100);
          }
        };
        checkLoading();
      });
    }
    
    this.loadingStates.add(cacheKey);
    
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers
      };
      
      if (this.auth.token) {
        headers['Authorization'] = `Bearer ${this.auth.token}`;
      }
      
      const response = await fetch(url, {
        ...options,
        headers
      });
      
      if (response.status === 401) {
        this.handleLogout();
        throw new Error('Authentication required');
      }
      
      // Cache the response for GET requests
      if (useCache && options.method !== 'POST' && options.method !== 'PUT' && options.method !== 'DELETE') {
        this.cache.set(cacheKey, {
          data: response.clone(),
          timestamp: Date.now()
        });
      }
      
      return response;
    } finally {
      this.loadingStates.delete(cacheKey);
    }
  },

  // Load task queue
  async loadTaskQueue() {
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth('/api/tasks');
      const data = await response.json();
      this.updateTaskQueue(data);
    } catch (error) {
      console.error('Failed to load task queue:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load task queue');
      }
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
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth('/api/system/metrics');
      const data = await response.json();
      this.updateSystemMetrics(data);
    } catch (error) {
      console.error('Failed to load system metrics:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      }
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

  // Load users (admin only)
  async loadUsers() {
    if (!this.auth.isAuthenticated || this.auth.user.role !== 'ADMIN') return;
    
    try {
      const response = await this.fetchWithAuth('/api/users');
      const data = await response.json();
      this.updateUsersTable(data);
    } catch (error) {
      console.error('Failed to load users:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load users');
      }
    }
  },
  
  // Update users table
  updateUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    users.forEach(user => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${user.username}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.full_name || '-'}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${user.email || '-'}</td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
            user.role === 'ADMIN' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
          }">
            ${user.role}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
          <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
            user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }">
            ${user.is_active ? 'Active' : 'Inactive'}
          </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          ${user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
          <button onclick="Dashboard.editUser(${user.id})" class="text-indigo-600 hover:text-indigo-900 mr-3">Edit</button>
          <button onclick="Dashboard.deleteUser(${user.id})" class="text-red-600 hover:text-red-900">Delete</button>
        </td>
      `;
      tbody.appendChild(row);
    });
  },
  
  // Show user modal
  showUserModal(user = null) {
    const modal = document.getElementById('user-modal');
    const form = document.getElementById('user-form');
    const title = document.getElementById('user-modal-title');
    
    if (user) {
      title.textContent = 'Edit User';
      document.getElementById('user-id').value = user.id;
      document.getElementById('user-username').value = user.username;
      document.getElementById('user-full-name').value = user.full_name || '';
      document.getElementById('user-email').value = user.email || '';
      document.getElementById('user-role').value = user.role;
      document.getElementById('user-is-active').checked = user.is_active;
    } else {
      title.textContent = 'Add User';
      form.reset();
      document.getElementById('user-id').value = '';
    }
    
    modal.classList.remove('hidden');
  },
  
  // Hide user modal
  hideUserModal() {
    const modal = document.getElementById('user-modal');
    modal.classList.add('hidden');
  },
  
  // Handle user save
  async handleUserSave() {
    const form = document.getElementById('user-form');
    const formData = new FormData(form);
    const userId = formData.get('id');
    
    const userData = {
      username: formData.get('username'),
      full_name: formData.get('full_name'),
      email: formData.get('email'),
      role: formData.get('role'),
      is_active: formData.has('is_active')
    };
    
    if (formData.get('password')) {
      userData.password = formData.get('password');
    }
    
    try {
      const url = userId ? `/api/users/${userId}` : '/api/users';
      const method = userId ? 'PUT' : 'POST';
      
      const response = await this.fetchWithAuth(url, {
        method,
        body: JSON.stringify(userData)
      });
      
      if (response.ok) {
        this.showSuccess(userId ? 'User updated successfully' : 'User created successfully');
        this.hideUserModal();
        this.loadUsers();
      } else {
        const error = await response.json();
        this.showError(error.detail || 'Failed to save user');
      }
    } catch (error) {
      console.error('Error saving user:', error);
      this.showError('Failed to save user');
    }
  },
  
  // Edit user
  async editUser(userId) {
    try {
      const response = await this.fetchWithAuth(`/api/users/${userId}`);
      const user = await response.json();
      this.showUserModal(user);
    } catch (error) {
      console.error('Error loading user:', error);
      this.showError('Failed to load user data');
    }
  },
  
  // Delete user
  async deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
      return;
    }
    
    try {
      const response = await this.fetchWithAuth(`/api/users/${userId}`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        this.showSuccess('User deleted successfully');
        this.loadUsers();
      } else {
        this.showError('Failed to delete user');
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      this.showError('Failed to delete user');
    }
  },

  // Control agent
  async controlAgent(agentId, action) {
    if (!this.auth.isAuthenticated) return;
    
    try {
      const response = await this.fetchWithAuth(`/api/agents/${agentId}/${action}`, {
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
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError(`Failed to ${action} agent`);
      }
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
      const response = await this.fetchWithAuth(endpoint, {
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
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Operation failed');
      }
    }
  },

  // Handle toggle switches
  async handleToggle(toggle) {
    const setting = toggle.dataset.setting;
    const value = toggle.checked;

    try {
      const response = await this.fetchWithAuth('/api/settings', {
        method: 'POST',
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
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to update setting');
      }
      toggle.checked = !value; // Revert
    }
  },

  // Refresh data
  async refreshData(endpoint = 'all') {
    try {
      this.showLoadingState(true);
      
      if (endpoint === 'all') {
        await this.loadAllData();
      } else {
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
      }

      this.showSuccess('Data refreshed');
    } catch (error) {
      console.error('Refresh error:', error);
      this.showError('Failed to refresh data');
    } finally {
      this.showLoadingState(false);
    }
  },

  // Smart refresh with adaptive intervals
  startSmartRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }
    
    let currentInterval = this.config.refreshInterval;
    let consecutiveErrors = 0;
    
    const refresh = async () => {
      // Only refresh if page is visible and user is authenticated
      if (document.visibilityState === 'visible' && this.auth.isAuthenticated) {
        try {
          await this.loadCriticalData();
          consecutiveErrors = 0;
          currentInterval = this.config.refreshInterval; // Reset to normal interval
        } catch (error) {
          consecutiveErrors++;
          // Exponential backoff on errors
          currentInterval = Math.min(
            this.config.refreshInterval * Math.pow(2, consecutiveErrors),
            300000 // Max 5 minutes
          );
          console.warn(`Refresh failed, backing off to ${currentInterval}ms`);
        }
      }
      
      // Schedule next refresh
      this.refreshTimer = setTimeout(refresh, currentInterval);
    };
    
    // Start first refresh
    this.refreshTimer = setTimeout(refresh, 1000); // Initial delay
    
    console.log('🔄 Smart refresh started');
  },
  
  // Start auto-refresh (legacy method for compatibility)
  startAutoRefresh() {
    this.startSmartRefresh();
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
        this.updateConnectionStatus(true);
      });

      socket.on('disconnect', reason => {
        console.log('❌ Socket.IO disconnected:', reason);
        this.updateConnectionStatus(false);
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

      socket.on('log_entry', data => {
        this.addLogEntry(data.log);
      });

      socket.on('performance_update', data => {
        this.updatePerformanceCharts(data.performance);
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

  // Show warning message
  showWarning(message) {
    this.showAlert(message, 'warning');
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
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes)/Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  formatNumber(num) {
    return new Intl.NumberFormat().format(num);
  },

  // Load critical data only (for frequent updates)
  async loadCriticalData() {
    if (!this.auth.isAuthenticated) {
      return;
    }
    
    try {
      // Only load essential data for auto-refresh
      const promises = [
        this.loadAgentStatus(),
        this.loadSystemMetrics()
      ];
      
      await Promise.all(promises);
      this.updateLastRefreshTime();
      
    } catch (error) {
      console.error('❌ Error loading critical data:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      }
      throw error; // Re-throw for smart refresh error handling
    }
  },
  
  // New enhanced methods
  async loadInitialData() {
    if (!this.auth.isAuthenticated) {
      return;
    }
    
    await this.loadAllData();
    this.initializeRealTimeUpdates();
  },

  async loadAllData() {
    if (!this.auth.isAuthenticated) {
      return;
    }
    
    try {
      this.showLoadingState(true);
      
      // Load all data concurrently with priority batching
      const highPriorityPromises = [
        this.loadAgentStatus(),
        this.loadSystemMetrics()
      ];
      
      const lowPriorityPromises = [
        this.loadTaskQueue(),
        this.loadReports(),
        this.loadRecentActivity()
      ];
      
      // Load high priority data first
      await Promise.all(highPriorityPromises);
      
      // Then load low priority data
      await Promise.all(lowPriorityPromises);
      
      // Load users if admin (lowest priority)
      if (this.auth.user && this.auth.user.role === 'ADMIN') {
        await this.loadUsers();
      }
      
      this.showLoadingState(false);
      this.updateLastRefreshTime();
      
      console.log('All data loaded successfully');
    } catch (error) {
      console.error('❌ Error loading data:', error);
      if (error.message.includes('401')) {
        this.handleLogout();
      } else {
        this.showError('Failed to load dashboard data');
      }
      this.showLoadingState(false);
    }
  },

  // Load recent activity data
  async loadRecentActivity() {
    if (!this.auth.isAuthenticated) {
      console.log('Not authenticated, skipping recent activity load');
      return;
    }
    
    const activityList = document.getElementById('activity-list');
    if (!activityList) return;
    
    // Show skeleton loading
    const skeleton = document.getElementById('activity-list-skeleton');
    if (skeleton) {
      skeleton.classList.remove('d-none');
    }
    
    try {
      const response = await this.fetchWithAuth('/dashboard/api/recent-activity');
      const data = await response.json();
      
      if (skeleton) {
        skeleton.classList.add('d-none');
      }
      
      if (data.activities && data.activities.length > 0) {
        activityList.innerHTML = data.activities.map(activity => `
          <div class="activity-item p-3 border-b border-gray-200">
            <div class="flex justify-between items-start">
              <div>
                <h4 class="font-medium text-gray-900">${activity.title}</h4>
                <p class="text-sm text-gray-600">${activity.description}</p>
              </div>
              <span class="text-xs text-gray-500">${activity.timestamp}</span>
            </div>
          </div>
        `).join('');
      } else {
        activityList.innerHTML = '<p class="text-center text-gray-500">No recent activity</p>';
      }
    } catch (error) {
      console.error('Error loading recent activity:', error);
      if (skeleton) {
        skeleton.classList.add('d-none');
      }
      if (activityList) {
        activityList.innerHTML = '<p class="text-center text-red-500">Error loading activity</p>';
      }
    }
   },
 
    // Update last refresh time
  updateLastRefreshTime() {
    const element = document.getElementById('last-refresh-time');
    if (element) {
      element.textContent = new Date().toLocaleTimeString();
    }
  },

  initializeCharts() {
    // Initialize chart containers for future use
    this.charts = {};
  },

  initializeRealTimeUpdates() {
    // Update current time every second
    setInterval(() => {
      const timeElement = document.getElementById('currentTime');
      if (timeElement) {
        timeElement.textContent = new Date().toLocaleTimeString();
      }
    }, 1000);
  },

  showLoadingState(isLoading) {
    const loadingElements = document.querySelectorAll('.loading-indicator');
    loadingElements.forEach(el => {
      el.style.display = isLoading ? 'block' : 'none';
    });
  },

  showRefreshAnimation(button) {
    const icon = button.querySelector('i');
    if (icon) {
      icon.classList.add('fa-spin');
      setTimeout(() => {
        icon.classList.remove('fa-spin');
      }, 1000);
    }
  },

  updateConnectionStatus(isConnected) {
    const statusDot = document.querySelector('.pulse-dot');
    if (statusDot) {
      statusDot.className = isConnected ? 
        'pulse-dot w-3 h-3 bg-green-400 rounded-full' : 
        'w-3 h-3 bg-red-400 rounded-full';
    }
  },

  addLogEntry(log) {
    const container = document.getElementById('logContainer');
    if (!container) return;
    
    const logElement = document.createElement('div');
    logElement.className = `log-entry mb-1 ${this.getLogLevelClass(log.level)}`;
    logElement.innerHTML = `
      <span class="text-gray-400">[${new Date(log.timestamp).toLocaleTimeString()}]</span>
      <span class="font-medium">[${log.level.toUpperCase()}]</span>
      <span>${log.message}</span>
    `;
    
    container.appendChild(logElement);
    container.scrollTop = container.scrollHeight;
    
    // Keep only last 100 log entries
    const entries = container.querySelectorAll('.log-entry');
    if (entries.length > 100) {
      entries[0].remove();
    }
  },

  getLogLevelClass(level) {
    const classes = {
      error: 'text-red-400',
      warning: 'text-yellow-400',
      info: 'text-blue-400',
      debug: 'text-gray-400'
    };
    return classes[level] || 'text-green-400';
  },

  handleKeyboardShortcuts(event) {
    if (event.ctrlKey || event.metaKey) {
      switch(event.key) {
        case 'r':
          event.preventDefault();
          this.refreshData();
          break;
        case '1':
        case '2':
        case '3':
        case '4':
          event.preventDefault();
          const modules = ['command-center', 'database-explorer', 'product-studio', 'reporting-engine'];
          const moduleIndex = parseInt(event.key) - 1;
          if (modules[moduleIndex]) {
            this.switchModule(modules[moduleIndex]);
          }
          break;
      }
    }
  },

  handleSearch(event) {
    const query = event.target.value.toLowerCase();
    const searchId = 'global_search';
    
    // Clear existing timer
    if (this.debounceTimers.has(searchId)) {
      clearTimeout(this.debounceTimers.get(searchId));
    }
    
    // Debounce search
    const timer = setTimeout(() => {
      this.performSearch(query);
      this.debounceTimers.delete(searchId);
    }, this.config.debounceDelay);
    
    this.debounceTimers.set(searchId, timer);
  },
  
  // Perform actual search
  performSearch(query) {
    console.log('🔍 Searching for:', query);
    
    const startTime = performance.now();
    
    // Use document fragment for better performance
    const searchableElements = document.querySelectorAll('[data-searchable]');
    let visibleCount = 0;
    
    // Batch DOM updates
    requestAnimationFrame(() => {
      searchableElements.forEach(element => {
        const text = element.textContent.toLowerCase();
        const matches = text.includes(query.toLowerCase());
        
        if (matches || query === '') {
          element.style.display = '';
          visibleCount++;
        } else {
          element.style.display = 'none';
        }
      });
      
      const endTime = performance.now();
      console.log(`🔍 Search completed in ${(endTime - startTime).toFixed(2)}ms - Found ${visibleCount} results`);
    });
  },

  updateURL(moduleId) {
    const url = new URL(window.location);
    url.searchParams.set('module', moduleId);
    window.history.replaceState({}, '', url);
  },

  trackAnalytics(event, data) {
    // Analytics tracking - implement based on your analytics service
    console.log('Analytics:', event, data);
  },

  updatePerformanceCharts(data) {
    // Update performance charts with new data
    console.log('Performance update:', data);
  },
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  Dashboard.init();
});

// Export for global access
window.Dashboard = Dashboard;
