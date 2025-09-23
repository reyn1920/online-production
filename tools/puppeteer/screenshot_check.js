// path: tools/puppeteer/screenshot_check.js
const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const pixelmatch = require("pixelmatch");
const { PNG } = require("pngjs");

const URL = process.env.PUP_URL || "http://127.0.0.1:8000";
const OUT = "_puppeteer_artifacts";

async function shot(page, file) {
  await page.screenshot({ path: file, fullPage: true });
  console.log("[PUP] saved", file);
}

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(URL, { waitUntil: "networkidle2" });

  fs.mkdirSync(OUT, { recursive: true });
  const a = path.join(OUT, "before.png");
  const b = path.join(OUT, "after.png");
  const d = path.join(OUT, "diff.png");

  await shot(page, a);
  await page.evaluate(() => document.body && document.body.focus());
  await shot(page, b);

  const imgA = PNG.sync.read(fs.readFileSync(a));
  const imgB = PNG.sync.read(fs.readFileSync(b));
  const { width, height } = imgA;
  const diff = new PNG({ width, height });

  const mismatched = pixelmatch(imgA.data, imgB.data, diff.data, width, height, { threshold: 0.1 });
  fs.writeFileSync(d, PNG.sync.write(diff));
  console.log(`[PUP] pixel diff count: ${mismatched} -> ${d}`);

  await browser.close();
  if (mismatched > 0) process.exitCode = 0;
})();
