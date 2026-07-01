// promo-video MODE C(終端/解說):非視覺 repo(CLI/lib/backend)沒畫面可錄 →
// 用 term-player.html 把「指令+真實輸出」做成打字動畫的終端錄影,再進 compose(標題+字幕+CTA)。
// 需求:playwright + xvfb(WebGL 非必要,但沿用同 launch)。無需 asciinema/xterm/vhs。
//   xvfb-run -a --server-args="-screen 0 1280x720x24" node capture-term.mjs
// 產出:./raw/term.webm。
//
// TERM_SCRIPT 每步:{ cmd:'指令', out:['輸出行(可含 <span class=c/d/r/g/y>)'], typeMs, gapMs, lineMs, holdMs }
// 色: c=cyan(分支) d=dim r=red(dirty/錯) g=green(成功) y=gold。out 用真實指令輸出改寫,別腦補。
const TERM_SCRIPT = [
  { cmd: 'yourtool status', gapMs: 400, holdMs: 2600, out: [
    '<span class="d"># 貼真實輸出、關鍵處加色</span>',
    '<b>item-a</b>  <span class="c">ok</span>   <span class="r">[2 warn]</span>' ]},
];
// ── ─────────────────────────────────────────────
import { chromium } from "playwright";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { mkdirSync, readdirSync, renameSync } from "node:fs";
import { join, dirname, extname } from "node:path";
import { fileURLToPath } from "node:url";
const HERE = dirname(fileURLToPath(import.meta.url));
const RAW = join(process.cwd(), "raw"); mkdirSync(RAW, { recursive: true });
const server = createServer(async (req, res) => {
  try { const p = join(HERE, req.url.split("?")[0]);
    res.writeHead(200, { "Content-Type": extname(p) === ".html" ? "text/html" : "text/plain" });
    res.end(await readFile(p)); } catch { res.writeHead(404).end("404"); }
});
await new Promise(r => server.listen(8210, "127.0.0.1", r));
const b = await chromium.launch({ headless: false, args: ["--no-sandbox"] });
const dir = join(RAW, "term"); mkdirSync(dir, { recursive: true });
const ctx = await b.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir, size: { width: 1280, height: 720 } } });
const p = await ctx.newPage();
await p.addInitScript(s => { window.TERM_SCRIPT = s; }, TERM_SCRIPT);
await p.goto("http://127.0.0.1:8210/term-player.html", { waitUntil: "load" });
for (let t = 0; t < 40; t++) { if (await p.evaluate(() => window.__TERM_DONE)) break; await p.waitForTimeout(500); }
await p.waitForTimeout(800); await ctx.close();
const f = readdirSync(dir).find(x => x.endsWith(".webm")); renameSync(join(dir, f), join(RAW, "term.webm"));
await b.close(); server.close(); console.log("term.webm recorded");
