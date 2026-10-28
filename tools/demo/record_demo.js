// Drives the running app in a headless browser and records what the pages show.
// It captures the app only, never the desktop, so the video holds nothing but demo data.
//
// Needs: npm install puppeteer-core, a Chrome or chrome-headless-shell binary, and the app
// running on port 8766 with demo data (python src/manage.py seed_demo --password ...).
// Run:   CHROME=/path/to/chrome-headless-shell OUT=frames node tools/demo/record_demo.js
// Then:  python tools/demo/encode_video.py frames sprint1-demo.mp4
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const CHROME = process.env.CHROME;
const BASE = 'http://127.0.0.1:8766';
const OUT = process.env.OUT;
const PASSWORD = 'Demo#Pass2026x';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'shell',
    args: ['--no-sandbox'],
    defaultViewport: { width: 1280, height: 720 },
  });
  const page = await browser.newPage();

  // A caption bar and a visible pointer, restored on every page load.
  await page.evaluateOnNewDocument(() => {
    const draw = () => {
      let bar = document.getElementById('demo-caption');
      if (!bar) {
        bar = document.createElement('div');
        bar.id = 'demo-caption';
        bar.style.cssText =
          'position:fixed;left:0;right:0;bottom:0;z-index:99999;background:rgba(20,20,20,.88);' +
          'color:#fff;font:600 24px system-ui,sans-serif;padding:14px 28px;text-align:center;';
        document.documentElement.appendChild(bar);
      }
      const text = sessionStorage.getItem('demo-caption') || '';
      bar.textContent = text;
      bar.style.display = text ? 'block' : 'none';
      if (!document.getElementById('demo-cursor')) {
        const dot = document.createElement('div');
        dot.id = 'demo-cursor';
        dot.style.cssText =
          'position:fixed;width:22px;height:22px;border-radius:50%;background:rgba(255,193,7,.85);' +
          'border:2px solid #333;z-index:100000;pointer-events:none;left:-50px;top:-50px;';
        document.documentElement.appendChild(dot);
        document.addEventListener('mousemove', (e) => {
          dot.style.left = e.clientX - 11 + 'px';
          dot.style.top = e.clientY - 11 + 'px';
        });
      }
    };
    document.addEventListener('DOMContentLoaded', draw);
    window.__draw = draw;
  });

  const cdp = await page.createCDPSession();
  const frames = [];
  cdp.on('Page.screencastFrame', async ({ data, metadata, sessionId }) => {
    frames.push({ t: metadata.timestamp, data });
    try { await cdp.send('Page.screencastFrameAck', { sessionId }); } catch (e) { /* ending */ }
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1280, maxHeight: 720, everyNthFrame: 1 });

  const caption = async (text) => {
    await page.evaluate((t) => { sessionStorage.setItem('demo-caption', t); window.__draw && window.__draw(); }, text);
  };
  const moveTo = async (selector) => {
    const el = await page.$(selector);
    const box = await el.boundingBox();
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 12 });
    return el;
  };
  const click = async (selector) => { const el = await moveTo(selector); await sleep(250); await el.click(); };
  const typeInto = async (selector, text, delay = 80) => { await click(selector); await page.keyboard.type(text, { delay }); };
  const go = async (url) => { await page.goto(BASE + url, { waitUntil: 'networkidle0' }); await sleep(300); };
  const clickAndWait = async (selector) => {
    await Promise.all([page.waitForNavigation({ waitUntil: 'networkidle0' }), click(selector)]);
    await sleep(300);
  };

  // 1. Staff sign in
  await go('/accounts/login/');
  await caption('Blood Bank Management System: staff sign in');
  await sleep(1500);
  await typeInto('#id_username', 'staff01');
  await typeInto('#id_password', PASSWORD, 50);
  await sleep(300);
  await clickAndWait('form button[type=submit]');

  // 2. Inventory console
  await caption('The menu shows only what this role may use');
  await sleep(2000);
  await caption('Inventory: available units by blood group, counted live');
  await clickAndWait('a[href="/inventory/"]');
  await sleep(3500);

  // 3. Donor search, deferred donors
  await caption('Deferred donors cannot start a collection, and the reason is shown');
  await clickAndWait('a[href="/donors/search/"]');
  await sleep(3500);
  await typeInto('#q', 'Imran');
  await caption('An eligible donor: Start collection is available');
  await page.keyboard.press('Enter');
  await page.waitForNavigation({ waitUntil: 'networkidle0' });
  await sleep(2500);

  // 4. Record the donation
  await caption('Record the donation');
  await clickAndWait('a[data-shortcut="new"]');
  await sleep(1200);
  await typeInto('#id_volume_ml', '450');
  await typeInto('#id_bag_lot_number', 'BG-2026-0601');
  await sleep(500);
  await caption('Alt+S saves');
  await sleep(900);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle0' }),
    (async () => { await page.keyboard.down('Alt'); await page.keyboard.press('KeyS'); await page.keyboard.up('Alt'); })(),
  ]);
  const unitId = (page.url().match(/units\/(BU\d+)\//) || [])[1];
  await caption('Unit ' + unitId + ' created: Quarantined until tested');
  await sleep(3000);

  // 5. Label with barcode
  await caption('Printable label with a Code 128 barcode, no donor details');
  await clickAndWait('a[href^="/inventory/units/"]');
  await sleep(3500);

  // 6. Test results: refused, then released
  await caption('Screening results: all five tests are needed');
  await go('/collection/units/' + unitId + '/results/');
  await sleep(1500);
  for (const t of ['HIV', 'HBV', 'HCV', 'Syphilis']) {
    await moveTo('#id_' + t);
    await page.select('#id_' + t, 'Non-Reactive');
    await sleep(350);
  }
  await caption('Release with Malaria missing');
  await sleep(800);
  await caption('Refused: the missing test is named, the unit stays Quarantined');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle0' }),
    click('button[value=release]'),
  ]);
  await sleep(3500);
  await moveTo('#id_Malaria');
  await page.select('#id_Malaria', 'Non-Reactive');
  await sleep(400);
  await caption('Malaria recorded, release again');
  await caption('All five Non-Reactive: released to inventory');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle0' }),
    click('button[value=release]'),
  ]);
  await sleep(3500);

  // 7. Stock went up
  await caption('Stock count updated straight away');
  await clickAndWait('a[href="/inventory/"]');
  await sleep(3000);

  // 8. Donor view
  await caption('Now a donor signs in');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle0' }),
    click('form[action="/accounts/logout/"] button'),
  ]);
  await sleep(1200);
  await typeInto('#id_username', 'DNR10000001');
  await typeInto('#id_password', PASSWORD, 40);
  await clickAndWait('form button[type=submit]');
  await caption('A donor sees only their own eligibility and next date');
  await clickAndWait('a[href="/donors/me/"]');
  await sleep(3500);
  await caption('Donors cannot open staff screens');
  await go('/inventory/');
  await sleep(3000);
  await caption('');
  await sleep(500);

  await cdp.send('Page.stopScreencast');
  fs.writeFileSync(path.join(OUT, 'frames.json'), JSON.stringify(frames.map((f) => f.t)));
  frames.forEach((f, i) => fs.writeFileSync(path.join(OUT, `f${String(i).padStart(5, '0')}.jpg`), Buffer.from(f.data, 'base64')));
  console.log('frames captured:', frames.length, 'unit:', unitId);
  await browser.close();
})().catch((e) => { console.error('RECORDING FAILED:', e.message); process.exit(1); });
