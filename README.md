# VSCode Puppeteer Power-Up v2 (Web Openers Included, Free-Only, Add-Only)

This pack adds Puppeteer flows + VS Code tasks, including safe openers for **ChatGPT**, **Gemini**, and **Abacus AI** web apps using your own browser profile (you log in once, sessions persist).

## Install
1. Unzip into your repo root.
2. Patch `package.json` add-only and install free dev deps:
   ```bash
   node scripts/patch_package_json.mjs
   npm i -D dotenv pixelmatch pngjs
   ```
3. Optionally set in `.env.local`:
   ```
   PUP_BROWSER_PATH=/path/to/your/chrome/or/edge
   PUP_USER_DATA_DIR=./.chrome-profile
   ```

## Run (VS Code -> Terminal -> Run Task)
- PUP: headful check
- PUP: login flow
- PUP: screenshot diff
- PUP: device matrix
- PUP: performance trace
- PUP: open ChatGPT web
- PUP: open Gemini web
- PUP: open Abacus web

## Notes
- No credentials are stored in code; your browser profile keeps sessions.
- All scripts are add-only and avoid removals.
