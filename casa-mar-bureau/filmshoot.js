// node filmshoot.js <outdir> <fps> [t1,t2,...]
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [out, fps, list] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto('http://localhost:8793/film.html');
  await p.waitForFunction(() => window.ready === true, null, { timeout: 300000 });
  const times = list ? list.split(',').map(Number) : Array.from({ length: 24 * fps }, (_, i) => i / fps);
  let i = 0; const t0 = Date.now();
  for (const t of times) {
    const d = await p.evaluate(t => window.frame(t), t);
    fs.writeFileSync(`${out}/f${String(i++).padStart(4, '0')}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
    if (i % 60 === 0) console.log(i, ((Date.now() - t0) / i).toFixed(0), 'ms/frame');
  }
  await b.close();
})();
