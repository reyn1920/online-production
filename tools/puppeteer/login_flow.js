// path: tools/puppeteer/login_flow.js
require("dotenv").config({ path: ".env.local" });
const puppeteer = require("puppeteer");

const SLOW_MS = parseInt(process.env.PUP_SLOW_MS || "0", 10);
const URL = process.env.PUP_LOGIN_URL || "http://127.0.0.1:8000/login";
const USER = process.env.PUP_USER || "";
const PASS = process.env.PUP_PASS || "";

(async () => {
  if (!USER || !PASS) {
    console.error("[PUP] missing PUP_USER or PUP_PASS in .env.local");
    process.exit(2);
  }
  const browser = await puppeteer.launch({ headless: false, slowMo: SLOW_MS });
  const page = await browser.newPage();
  page.setDefaultTimeout(20000);
  await page.goto(URL, { waitUntil: "domcontentloaded" });

  // Adjust selectors to your UI
  await page.waitForSelector('input[name="username"]');
  await page.type('input[name="username"]', USER, { delay: 20 });
  await page.type('input[name="password"]', PASS, { delay: 20 });
  await Promise.all([
    page.click('[data-qa="login-submit"], button[type="submit"]'),
    page.waitForNavigation({ waitUntil: "networkidle2" })
  ]);

  console.log("[PUP] login flow completed");
  await browser.close();
})().catch(err => {
  console.error("[PUP] error:", err && err.message ? err.message : err);
  process.exit(1);
});
