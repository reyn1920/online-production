// path: tools/puppeteer/open_gemini.js
const puppeteer = require("puppeteer");
// NOTE: Set the path to your Chrome/Edge executable for your OS:
// macOS (Chrome): /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
// macOS (Edge):   /Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge
// Windows (Chrome): C:\Program Files\Google\Chrome\Application\chrome.exe
// Windows (Edge):   C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
// Linux (Chrome):   /usr/bin/google-chrome
// The "userDataDir" keeps your session/cookies so you log in once and reuse.

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: process.env.PUP_BROWSER_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    userDataDir: process.env.PUP_USER_DATA_DIR || "./.chrome-profile"
  });
  const page = await browser.newPage();
  await page.goto("https://gemini.google.com/app");
  console.log("[PUP] Gemini opened with your browser profile.");
})().catch(err => {
  console.error("[PUP] error:", err && err.message ? err.message : err);
  process.exit(1);
});
