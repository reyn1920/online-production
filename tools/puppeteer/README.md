# Puppeteer flows in VS Code (Free-Only, Add-Only)

## Flows
- `check.js` — quick headful sanity
- `login_flow.js` — credentialed flow (reads `.env.local`)
- `screenshot_check.js` — before/after capture + pixel diff
- `device_matrix.js` — viewport sweep
- `trace_run.js` — performance trace
- `open_chatgpt.js` — opens https://chatgpt.com/ in your Chrome/Edge profile
- `open_gemini.js` — opens https://gemini.google.com/app in your Chrome/Edge profile
- `open_abacus.js` — opens the Abacus AI chat URL in your Chrome/Edge profile

## Setup
- Set `PUP_BROWSER_PATH` and `PUP_USER_DATA_DIR` in `.env.local` (optional). Defaults shown in each script.
- First run: you may need to sign in once; your session persists in the user data dir.

## Recommended npm additions (free)
```json
{
  "scripts": {
    "pupp:check": "node tools/puppeteer/check.js",
    "pupp:login": "node tools/puppeteer/login_flow.js",
    "pupp:shot": "node tools/puppeteer/screenshot_check.js",
    "pupp:devices": "node tools/puppeteer/device_matrix.js",
    "pupp:trace": "node tools/puppeteer/trace_run.js",
    "pupp:open:chatgpt": "node tools/puppeteer/open_chatgpt.js",
    "pupp:open:gemini": "node tools/puppeteer/open_gemini.js",
    "pupp:open:abacus": "node tools/puppeteer/open_abacus.js"
  },
  "devDependencies": {
    "dotenv": "^16.4.5",
    "pixelmatch": "^5.3.0",
    "pngjs": "^7.0.0"
  }
}
```
