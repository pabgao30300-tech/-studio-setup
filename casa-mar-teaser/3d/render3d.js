// node render3d.js <id> <outdir> <fps> [t1,t2,...]
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [id, out, fps, list] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => m.type() === 'error' && console.log('CONSOLE', m.text()));
  await p.goto(`http://localhost:8790/${process.env.PAGE || 'index.html'}?id=${id}`);
  await p.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  const times = list ? list.split(',').map(Number) : Array.from({ length: Math.round(15 * fps) }, (_, i) => i / fps);
  let i = 0; const t0 = Date.now();
  for (const t of times) {
    const data = await p.evaluate(t => { window.renderAt(t); return document.querySelector('canvas').toDataURL('image/jpeg', 0.94); }, t);
    fs.writeFileSync(`${out}/f${String(i++).padStart(4, '0')}.jpg`, Buffer.from(data.split(',')[1], 'base64'));
    if (i % 30 === 0) console.log(i, ((Date.now() - t0) / i).toFixed(0), 'ms/frame');
  }
  await b.close();
})();
