import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import puppeteer from 'puppeteer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function readJSON(p) {
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

async function ensureDir(p) {
  await fs.promises.mkdir(p, { recursive: true });
}

async function launchAll() {
  const cfgPath = path.join(__dirname, '..', 'config', 'sites.json');
  const cfg = readJSON(cfgPath);

  const userDataDir = path.resolve(path.join(__dirname, '..', cfg.persistentProfileDir || '.puppeteer_profile'));
  await ensureDir(userDataDir);

  const browser = await puppeteer.launch({
    headless: false,
    userDataDir,
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-features=IsolateOrigins,site-per-process',
      '--window-size=1440,900'
    ],
    defaultViewport: cfg.viewport || { width: 1440, height: 900, deviceScaleFactor: 1 }
  });

  const ctx = await browser.createIncognitoBrowserContext();
  const sites = cfg.sites || [];

  const results = [];
  for (const site of sites) {
    try {
      const page = await browser.newPage();
      await page.goto(site.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.bringToFront();
      await page.evaluate((title) => { document.title = title + ' — unified'; }, site.name);
      results.push({ name: site.name, url: site.url, status: 'ok' });
    } catch (err) {
      results.push({ name: site.name, url: site.url, status: 'error', message: String(err) });
    }
  }

  // Basic keep-alive loop; can be extended by TRAE.AI orchestrator
  console.log('Web Unifier ready:', results);
  process.on('SIGINT', async () => { await browser.close(); process.exit(0); });
}

launchAll().catch(err => {
  console.error('Failed to launch web unifier:', err);
  process.exit(1);
});
