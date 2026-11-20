// node shoot.js <outdir> <w> <h> <q> view:time,view:time...
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [out, w, h, q, list] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: +w, height: +h } });
  p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => m.type() === 'error' && console.log('CONSOLE', m.text()));
  await p.goto(`http://localhost:8793/still.html?w=${w}&h=${h}&q=${q}`);
  await p.waitForFunction(() => window.ready === true, null, { timeout: 300000 });
  for (const it of list.split(',')) {
    const [v, t] = it.split(':'); const t0 = Date.now();
    const data = await p.evaluate(([v, t]) => window.shot(v, +t), [v, t]);
    fs.writeFileSync(`${out}/${v}.png`, Buffer.from(data.split(',')[1], 'base64')); console.log(v, Date.now() - t0, 'ms');
  }
  await b.close();
})();
