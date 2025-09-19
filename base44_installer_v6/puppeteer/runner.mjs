// Headful research runner (ethical; no bypassing security)
import puppeteer from 'puppeteer';
const targets = [
  'https://github.com',
  'https://developer.mozilla.org/',
  'https://www.python.org/',
];
const browser = await puppeteer.launch({headless:false, defaultViewport:null});
const page = await browser.newPage();
for (const url of targets){
  try {
    console.log('[visit]', url);
    await page.goto(url, {waitUntil:'domcontentloaded', timeout:60000});
    await page.waitForTimeout(1500);
  } catch(e){ console.log('[skip]', url, e.message) }
}
console.log('Done. Close the browser when finished.');
