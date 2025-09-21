// Puppeteer Configuration for Chrome Installation and Launch
// Based on official Puppeteer troubleshooting guide and macOS compatibility

module.exports = {
  // Chrome installation configuration
  cacheDirectory: process.env.PUPPETEER_CACHE_DIR || './node_modules/.cache/puppeteer',

  // Launch options for macOS compatibility
  launch: {
    headless: false,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
      '--disable-blink-features=AutomationControlled',
      '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ],
    ignoreDefaultArgs: ['--disable-extensions'],
    timeout: 30000,
    slowMo: 100
  },

  // Environment variables for Chrome setup
  env: {
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD: 'false',
    PUPPETEER_EXECUTABLE_PATH: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
    DISPLAY: process.env.DISPLAY || ':0'
  }
};
