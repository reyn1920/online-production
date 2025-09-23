// path: tools/puppeteer/trace_run.js
const fs = require("fs");
const puppeteer = require("puppeteer");
const URL = process.env.PUP_URL || "http://127.0.0.1:8000";
const OUT = "_puppeteer_artifacts";
(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.tracing.start({ path: `${OUT}/trace.json`, screenshots: true });
  await page.goto(URL, { waitUntil: "networkidle2" });
  await page.tracing.stop();
  fs.mkdirSync(OUT, { recursive: true });
  console.log("[PUP] trace saved to", `${OUT}/trace.json`);
  await browser.close();
})();
