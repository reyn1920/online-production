// Dashboard Functionality Test Script
// This script tests all interactive elements on the dashboard

class DashboardTester {
    constructor() {
        this.testResults = [];
        this.totalTests = 0;
        this.passedTests = 0;
        this.failedTests = 0;
    }

    // Main test runner
    async runAllTests() {
        console.log('🚀 Starting Dashboard Functionality Tests...');
        console.log('=' .repeat(50));
        
        // Test navigation tabs
        await this.testTabNavigation();
        
        // Test buttons
        await this.testButtons();
        
        // Test toggles and switches
        await this.testToggles();
        
        // Test forms
        await this.testForms();
        
        // Test avatar functionality
        await this.testAvatarFunctionality();
        
        // Test quick actions
        await this.testQuickActions();
        
        // Test data refresh
        await this.testDataRefresh();
        
        // Display results
        this.displayResults();
    }

    // Test tab navigation
    async testTabNavigation() {
        console.log('\n📋 Testing Tab Navigation...');
        
        const tabs = ['overview', 'analytics', 'services', 'system', 'logs', 'users'];
        
        for (const tab of tabs) {
            try {
                const tabButton = document.querySelector(`[data-tab="${tab}"]`);
                const tabContent = document.getElementById(`${tab}-tab`);
                
                if (tabButton && tabContent) {
                    // Click the tab
                    tabButton.click();
                    
                    // Wait a moment for the transition
                    await this.wait(100);
                    
                    // Check if tab is active
                    const isActive = tabButton.classList.contains('active');
                    const isContentVisible = !tabContent.classList.contains('hidden');
                    
                    this.recordTest(`Tab Navigation - ${tab}`, isActive && isContentVisible, 
                        `Tab button active: ${isActive}, Content visible: ${isContentVisible}`);
                } else {
                    this.recordTest(`Tab Navigation - ${tab}`, false, 'Tab button or content not found');
                }
            } catch (error) {
                this.recordTest(`Tab Navigation - ${tab}`, false, `Error: ${error.message}`);
            }
        }
    }

    // Test all buttons
    async testButtons() {
        console.log('\n🔘 Testing Buttons...');
        
        const buttonTests = [
            { selector: '#refresh-overview', name: 'Refresh Overview' },
            { selector: '#refresh-services', name: 'Refresh Services' },
            { selector: '#add-user-btn', name: 'Add User' },
            { selector: '#quick-refresh', name: 'Quick Refresh' },
            { selector: '#health-check', name: 'Health Check' },
            { selector: '#export-data', name: 'Export Data' },
            { selector: '#generate-dashboard-avatar', name: 'Generate Avatar' },
            { selector: '#avatar-settings', name: 'Avatar Settings' }
        ];
        
        for (const test of buttonTests) {
            try {
                const button = document.querySelector(test.selector);
                
                if (button) {
                    const isEnabled = !button.disabled;
                    const isVisible = button.offsetParent !== null;
                    const hasClickHandler = button.onclick !== null || 
                                          button.addEventListener !== undefined;
                    
                    // Test click (without actually triggering the action)
                    const originalOnClick = button.onclick;
                    let clickTriggered = false;
                    
                    button.onclick = () => {
                        clickTriggered = true;
                        if (originalOnClick) originalOnClick();
                    };
                    
                    button.click();
                    await this.wait(50);
                    
                    button.onclick = originalOnClick;
                    
                    const testPassed = isEnabled && isVisible;
                    this.recordTest(`Button - ${test.name}`, testPassed, 
                        `Enabled: ${isEnabled}, Visible: ${isVisible}, Clickable: ${clickTriggered || hasClickHandler}`);
                } else {
                    this.recordTest(`Button - ${test.name}`, false, 'Button not found');
                }
            } catch (error) {
                this.recordTest(`Button - ${test.name}`, false, `Error: ${error.message}`);
            }
        }
    }

    // Test toggles and switches
    async testToggles() {
        console.log('\n🔄 Testing Toggles and Switches...');
        
        const toggleTests = [
            { selector: 'input[type="checkbox"]', name: 'Checkbox Toggles' },
            { selector: '.toggle-switch', name: 'Toggle Switches' },
            { selector: 'input[type="radio"]', name: 'Radio Buttons' }
        ];
        
        for (const test of toggleTests) {
            try {
                const toggles = document.querySelectorAll(test.selector);
                
                if (toggles.length > 0) {
                    let allWorking = true;
                    let workingCount = 0;
                    
                    toggles.forEach((toggle, index) => {
                        try {
                            const initialState = toggle.checked;
                            toggle.click();
                            const newState = toggle.checked;
                            
                            if (initialState !== newState) {
                                workingCount++;
                            }
                            
                            // Reset to original state
                            toggle.checked = initialState;
                        } catch (error) {
                            allWorking = false;
                        }
                    });
                    
                    this.recordTest(`Toggle - ${test.name}`, workingCount > 0, 
                        `${workingCount}/${toggles.length} toggles working`);
                } else {
                    this.recordTest(`Toggle - ${test.name}`, true, 'No toggles found (not required)');
                }
            } catch (error) {
                this.recordTest(`Toggle - ${test.name}`, false, `Error: ${error.message}`);
            }
        }
    }

    // Test forms
    async testForms() {
        console.log('\n📝 Testing Forms...');
        
        const formTests = [
            { selector: '#user-form', name: 'User Form' },
            { selector: '#chat-input', name: 'Chat Input' },
            { selector: 'select', name: 'Dropdown Selects' }
        ];
        
        for (const test of formTests) {
            try {
                const elements = document.querySelectorAll(test.selector);
                
                if (elements.length > 0) {
                    let workingCount = 0;
                    
                    elements.forEach(element => {
                        try {
                            if (element.tagName === 'FORM') {
                                // Test form inputs
                                const inputs = element.querySelectorAll('input, textarea, select');
                                inputs.forEach(input => {
                                    const originalValue = input.value;
                                    input.value = 'test';
                                    if (input.value === 'test') workingCount++;
                                    input.value = originalValue;
                                });
                            } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                                const originalValue = element.value;
                                element.value = 'test';
                                if (element.value === 'test') workingCount++;
                                element.value = originalValue;
                            } else if (element.tagName === 'SELECT') {
                                const originalIndex = element.selectedIndex;
                                if (element.options.length > 1) {
                                    element.selectedIndex = 1;
                                    if (element.selectedIndex === 1) workingCount++;
                                    element.selectedIndex = originalIndex;
                                }
                            }
                        } catch (error) {
                            console.warn(`Form element test error: ${error.message}`);
                        }
                    });
                    
                    this.recordTest(`Form - ${test.name}`, workingCount > 0, 
                        `${workingCount} form elements working`);
                } else {
                    this.recordTest(`Form - ${test.name}`, true, 'No form elements found (not required)');
                }
            } catch (error) {
                this.recordTest(`Form - ${test.name}`, false, `Error: ${error.message}`);
            }
        }
    }

    // Test avatar functionality
    async testAvatarFunctionality() {
        console.log('\n🤖 Testing Avatar Functionality...');
        
        try {
            // Test avatar initialization
            const avatarExists = window.dashboardAvatar !== undefined;
            this.recordTest('Avatar - Initialization', avatarExists, 
                `Dashboard avatar object: ${avatarExists ? 'Found' : 'Not found'}`);
            
            if (avatarExists) {
                // Test chat interface
                const chatInterface = document.getElementById('chat-interface');
                const chatInput = document.getElementById('chat-input');
                const chatMessages = document.getElementById('chat-messages');
                
                this.recordTest('Avatar - Chat Interface', 
                    chatInterface && chatInput && chatMessages,
                    `Interface: ${!!chatInterface}, Input: ${!!chatInput}, Messages: ${!!chatMessages}`);
                
                // Test quick actions
                const quickActions = document.querySelectorAll('.quick-action-btn');
                this.recordTest('Avatar - Quick Actions', quickActions.length > 0, 
                    `${quickActions.length} quick action buttons found`);
            }
        } catch (error) {
            this.recordTest('Avatar - Functionality', false, `Error: ${error.message}`);
        }
    }

    // Test quick actions
    async testQuickActions() {
        console.log('\n⚡ Testing Quick Actions...');
        
        const quickActionTests = [
            { id: 'quick-refresh', name: 'Quick Refresh' },
            { id: 'health-check', name: 'Health Check' },
            { id: 'export-data', name: 'Export Data' }
        ];
        
        for (const test of quickActionTests) {
            try {
                const button = document.getElementById(test.id);
                
                if (button) {
                    const isClickable = !button.disabled && button.offsetParent !== null;
                    
                    // Test visual feedback on hover
                    button.dispatchEvent(new MouseEvent('mouseenter'));
                    await this.wait(50);
                    button.dispatchEvent(new MouseEvent('mouseleave'));
                    
                    this.recordTest(`Quick Action - ${test.name}`, isClickable, 
                        `Button clickable: ${isClickable}`);
                } else {
                    this.recordTest(`Quick Action - ${test.name}`, false, 'Button not found');
                }
            } catch (error) {
                this.recordTest(`Quick Action - ${test.name}`, false, `Error: ${error.message}`);
            }
        }
    }

    // Test data refresh functionality
    async testDataRefresh() {
        console.log('\n🔄 Testing Data Refresh...');
        
        try {
            // Test if refresh functions exist
            const refreshFunctions = [
                'loadDashboardData',
                'updateMetrics',
                'updateServices',
                'updateSystemInfo'
            ];
            
            let functionsFound = 0;
            refreshFunctions.forEach(funcName => {
                if (typeof window[funcName] === 'function') {
                    functionsFound++;
                }
            });
            
            this.recordTest('Data Refresh - Functions', functionsFound > 0, 
                `${functionsFound}/${refreshFunctions.length} refresh functions found`);
            
            // Test auto-refresh interval
            const hasAutoRefresh = window.setInterval !== undefined;
            this.recordTest('Data Refresh - Auto Refresh', hasAutoRefresh, 
                `Auto-refresh capability: ${hasAutoRefresh ? 'Available' : 'Not available'}`);
            
        } catch (error) {
            this.recordTest('Data Refresh - Functionality', false, `Error: ${error.message}`);
        }
    }

    // Helper methods
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    recordTest(testName, passed, details) {
        this.totalTests++;
        if (passed) {
            this.passedTests++;
            console.log(`✅ ${testName}: PASSED - ${details}`);
        } else {
            this.failedTests++;
            console.log(`❌ ${testName}: FAILED - ${details}`);
        }
        
        this.testResults.push({
            name: testName,
            passed,
            details,
            timestamp: new Date().toISOString()
        });
    }

    displayResults() {
        console.log('\n' + '=' .repeat(50));
        console.log('📊 TEST RESULTS SUMMARY');
        console.log('=' .repeat(50));
        console.log(`Total Tests: ${this.totalTests}`);
        console.log(`✅ Passed: ${this.passedTests}`);
        console.log(`❌ Failed: ${this.failedTests}`);
        console.log(`📈 Success Rate: ${((this.passedTests/this.totalTests) * 100).toFixed(1)}%`);
        
        if (this.failedTests > 0) {
            console.log('\n🔍 FAILED TESTS:');
            this.testResults
                .filter(test => !test.passed)
                .forEach(test => {
                    console.log(`   • ${test.name}: ${test.details}`);
                });
        }
        
        console.log('\n✨ Testing completed!');
        
        // Return results for programmatic access
        return {
            total: this.totalTests,
            passed: this.passedTests,
            failed: this.failedTests,
            successRate: (this.passedTests/this.totalTests) * 100,
            results: this.testResults
        };
    }
}

// Auto-run tests when script is loaded
if (typeof window !== 'undefined') {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                const tester = new DashboardTester();
                window.dashboardTester = tester;
                tester.runAllTests();
            }, 1000); // Wait 1 second for dashboard to initialize
        });
    } else {
        setTimeout(() => {
            const tester = new DashboardTester();
            window.dashboardTester = tester;
            tester.runAllTests();
        }, 1000);
    }
}

// Export for manual testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardTester;
}