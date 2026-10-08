#!/usr/bin/env node
// Renders film.html frame by frame in headless Chromium and pipes the PNGs into ffmpeg.
//
//   node render.cjs --audio soundtrack.wav --out claude-self-promo.mp4   # full film
//   node render.cjs --stills 1.0,5.5,12.2 --dir previews                 # spot-check frames
//
// Requires: Playwright (Chromium is preinstalled in this environment) and ffmpeg on PATH.
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { once } = require('events');

let chromium;
try {
  ({ chromium } = require('playwright'));
} catch (e) {
  ({ chromium } = require('/opt/node22/lib/node_modules/playwright'));
}

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : def;
};
const FPS = 30;
const DUR = 25.0;
const here = __dirname;
const pageUrl = 'file://' + path.join(here, 'film.html');
const audio = opt('--audio', null);
const out = opt('--out', path.join(here, 'claude-self-promo.mp4'));
const stills = opt('--stills', null);
const dir = opt('--dir', path.join(here, 'previews'));

(async () => {
  const browser = await chromium.launch({ args: ['--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const problems = [];
  page.on('pageerror', e => problems.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') problems.push(m.text()); });
  await page.goto(pageUrl);
  await page.evaluate(() => document.fonts.ready);

  if (stills) {
    fs.mkdirSync(dir, { recursive: true });
    for (const t of stills.split(',').map(Number)) {
      await page.evaluate(tt => window.renderAt(tt), t);
      await page.screenshot({ path: path.join(dir, `t${t.toFixed(2)}.png`) });
      console.log('still', t.toFixed(2));
    }
  } else {
    const n = Math.round(DUR * FPS);
    const ff = spawn('ffmpeg', [
      '-y', '-loglevel', 'error',
      '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
      ...(audio ? ['-i', audio] : []),
      '-map', '0:v', ...(audio ? ['-map', '1:a'] : []),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(FPS),
      '-movflags', '+faststart',
      ...(audio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []),
      out,
    ], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      await page.evaluate(tt => window.renderAt(tt), i / FPS);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await once(ff.stdin, 'drain');
      if (i % 100 === 0) console.log(`frame ${i}/${n}`);
    }
    ff.stdin.end();
    const code = await new Promise(res => ff.on('close', res));
    if (code !== 0) throw new Error(`ffmpeg exited with ${code}`);
    console.log('wrote', out);
  }
  if (problems.length) console.error('page problems:', problems);
  await browser.close();
})().catch(e => {
  console.error(e);
  process.exit(1);
});
