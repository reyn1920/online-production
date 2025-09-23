// path: tools/puppeteer/device_matrix.js
const puppeteer = require("puppeteer");
const DEVICES = [
  { name: "iPhone 12", width: 390, height: 844, isMobile: true, deviceScaleFactor: 3 },
  { name: "iPad Air", width: 820, height: 1180, isMobile: true, deviceScaleFactor: 2 },
  { name: "Laptop 13", width: 1366, height: 768, isMobile: false, deviceScaleFactor: 1 },
  { name: "Desktop HD", width: 1920, height: 1080, isMobile: false, deviceScaleFactor: 1 }
];
const URL = process.env.PUP_URL || "http://127.0.0.1:8000";
(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  for (const d of DEVICES) {
    await page.setViewport({ width: d.width, height: d.height, deviceScaleFactor: d.deviceScaleFactor, isMobile: d.isMobile });
    await page.goto(URL, { waitUntil: "networkidle2" });
    console.log(`[PUP] ${d.name} OK @ ${d.width}x${d.height}`);
  }
  await browser.close();
})();
