// usage: node render.js page.html audio.mp3 out.mp4 duration [fps] [--stills t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [html, audio, out, dur, fpsArg] = process.argv.slice(2);
  const fps = +(fpsArg || 30);
  const stillsIdx = process.argv.indexOf('--stills');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: +(process.env.VW || 1080), height: +(process.env.VH || 1920) }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(html));
  await page.evaluate(() => document.fonts.ready);
  if (stillsIdx > 0) {
    for (const t of process.argv[stillsIdx + 1].split(',')) {
      await page.evaluate(t => render(t), +t);
      await page.screenshot({ path: `still_${t}.jpg`, type: 'jpeg', quality: 80 });
    }
    await browser.close(); return;
  }
  const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-i', audio, '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps),
    '-c:a', 'aac', '-b:a', '192k', '-af', 'apad', '-t', String(dur), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => render(t), i / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('done', out);
})();
