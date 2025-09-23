// path: tools/puppeteer/check.js
const puppeteer = require("puppeteer");

(async () => {
  const url = process.env.PUP_URL || "http://127.0.0.1:8000";
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  page.setDefaultTimeout(15000);
  console.log("[PUP] opening", url);
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => document.body && document.body.focus());
  const title = await page.title().catch(() => "");
  console.log("[PUP] title:", title || "(none)");
  await browser.close();
  console.log("[PUP] ok");
})().catch(err => {
  console.error("[PUP] error:", err && err.message ? err.message : err);
  process.exit(1);
});
