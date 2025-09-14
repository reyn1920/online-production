/**
 * Home CTA Script - Creative Sandbox Floating Action Button
 * Adds a floating action button to the dashboard home page that navigates to the Creative Sandbox
 */(function () {
  'use strict';//Only run on the home/dashboard page
  if (window.location.pathname !== '/' && window.location.pathname !== '/dashboard') {
    return;
  }//Create floating action button
  function createFloatingButton() {
    const button = document.createElement('div');
    button.id = 'creative-sandbox-fab';
    button.innerHTML = `
            <div class="fab-icon">🎨</div>
            <div class="fab-text">Creative Sandbox</div>
        `;//Add styles
    const styles = `
            #creative-sandbox-fab {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #00d4ff, #0099cc);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
                transition: all 0.3s ease;
                z-index: 1000;
                overflow: hidden;
            }
            
            #creative-sandbox-fab:hover {
                width: 180px;
                border-radius: 30px;
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(0, 212, 255, 0.4);
            }
            
            #creative-sandbox-fab .fab-icon {
                font-size: 24px;
                transition: all 0.3s ease;
                flex-shrink: 0;
            }
            
            #creative-sandbox-fab .fab-text {
                font-size: 14px;
                font-weight: 600;
                color: #0f1419;
                margin-left: 10px;
                opacity: 0;
                transform: translateX(-10px);
                transition: all 0.3s ease;
                white-space: nowrap;
            }
            
            #creative-sandbox-fab:hover .fab-text {
                opacity: 1;
                transform: translateX(0);
            }
            
            #creative-sandbox-fab:hover .fab-icon {
                transform: scale(0.9);
            }
            
            #creative-sandbox-fab:active {
                transform: translateY(-2px) scale(0.95);
            }/* Pulse animation for attention */@keyframes fab-pulse {
                0% {
                    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
                }
                50% {
                    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.6), 0 0 0 10px rgba(0, 212, 255, 0.1);
                }
                100% {
                    box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
                }
            }
            
            #creative-sandbox-fab.pulse {
                animation: fab-pulse 2s infinite;
            }/* Mobile responsive */@media (max-width: 768px) {
                #creative-sandbox-fab {
                    bottom: 20px;
                    right: 20px;
                    width: 50px;
                    height: 50px;
                }
                
                #creative-sandbox-fab .fab-icon {
                    font-size: 20px;
                }
                
                #creative-sandbox-fab:hover {
                    width: 50px;
                    border-radius: 50%;
                }
                
                #creative-sandbox-fab .fab-text {
                    display: none;
                }
            }
        `;//Add styles to document
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);//Add click handler
    button.addEventListener('click', function () {//Add click animation
      button.style.transform = 'translateY(-2px) scale(0.95)';

      setTimeout(() => {
        window.location.href = '/sandbox';
      }, 150);
    });//Add to page
    document.body.appendChild(button);//Add pulse animation after a delay to draw attention
    setTimeout(() => {
      button.classList.add('pulse');//Remove pulse after user hovers
      button.addEventListener(
        'mouseenter',
        () => {
          button.classList.remove('pulse');
        },
        { once: true }
      );
    }, 3000);

    return button;
  }//Initialize when DOM is ready
  function init() {//Check if we're on a page that should show the FAB
    const shouldShowFab =
      window.location.pathname === '/' ||
      window.location.pathname === '/dashboard' ||
      window.location.pathname.includes('index.html');

    if (!shouldShowFab) {
      return;
    }//Don't show if we're already on the sandbox page
    if (window.location.pathname.includes('sandbox')) {
      return;
    }//Create the button
    createFloatingButton();//Log for debugging
    console.log('Creative Sandbox FAB initialized');
  }//Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }//Also initialize on page navigation (for SPAs)
  window.addEventListener('popstate', init);
})();//Export for manual initialization if needed
window.initCreativeSandboxFAB = function () {
  const existingFab = document.getElementById('creative-sandbox-fab');
  if (existingFab) {
    existingFab.remove();
  }//Re-run initialization
  setTimeout(() => {
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
  }, 100);
};
