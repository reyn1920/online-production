import puppeteer from 'puppeteer';
const START_URL = process.env.START_URL || 'https://example.com/';
const MAX_PAGES = parseInt(process.env.MAX_PAGES || '1', 10);
function sleep(ms){ return new Promise(r=>setTimeout(r, ms)); }
(async () => {
  const browser = await puppeteer.launch({ headless: false, defaultViewport:{width:1400,height:900}, args:['--no-sandbox'] });
  const page = await browser.newPage();
  const ua = await browser.userAgent();
  await page.setUserAgent(ua + ' Base44Automation/1.0');
  page.setDefaultNavigationTimeout(45000); page.setDefaultTimeout(45000);
  await page.goto(START_URL, { waitUntil: 'domcontentloaded' }); await sleep(1200);
  const title = await page.title();
  console.log(JSON.stringify({ok:true,url:START_URL,title}));
  await browser.close();
})().catch(e=>{ console.error(e); process.exit(1); });
