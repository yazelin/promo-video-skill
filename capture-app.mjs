// promo-video MODE A:程式驅動瀏覽器,錄「會自動運鏡的 web app」高潮段成 webm。
//
// 依賴:playwright(npm i -D playwright)+ ffmpeg。WebGL 要真 GL → 務必 xvfb 下跑(GOTCHA 6):
//   xvfb-run -a --server-args="-screen 0 1280x720x24" node capture-app.mjs
//   xvfb-run -a --server-args="-screen 0 720x1280x24"  node capture-app.mjs --portrait
// 產出:./raw/<id>.webm(portrait 版加 _v)。之後交給 ffmpeg 合成。
//
// 內建 http server(GOTCHA 5:file:// 下 fetch(?pkg=)/載 JSON 會被擋)。
// 驅動用 DOM(GOTCHA 7:ES-module app 的函式不在 window 上,點 UI 節點,別 evaluate 內部函式)。
//
// ── CONFIG(每專案換)─────────────────────────────
const PORT = 8199;
const SERVE_ROOT = process.cwd();                 // 靜態伺服的根(通常 repo 根)
const HIDE = "#hud,#panel,#controls{display:none!important}";  // 要藏的 UI selector(留畫布/letterbox)
// 要錄的「段」:每段 = 開哪個 URL、怎麼進到高潮、hold 多久(毫秒)。DRIVE 為 app-specific。
const SHOTS = [
  { id: "shot1", url: "/play.html?scene=climax", hold: 9000 },
];
// GOTCHA 15:別用固定秒數等載入,慢的那張會截到「載入中」空畫面。輪詢到 loading 消失才動。
async function waitLoaded(page, { gone = "載入中", sel = null, max = 15000 } = {}) {
  for (let t = 0; t < max / 250; t++) {
    const ready = sel
      ? await page.evaluate(s => document.querySelectorAll(s).length > 0, sel)
      : await page.evaluate(g => !document.body.innerText.includes(g), gone);
    if (ready) return;
    await page.waitForTimeout(250);
  }
}
// app-specific:載入完成後怎麼開始播 + 跳到高潮。改這裡對接你的 app。
async function DRIVE(page, shot) {
  await waitLoaded(page, { sel: "#tlNodes .node" });   // 例:等時間軸節點出現(或改 {gone:'載入中'})
  await page.evaluate(() => document.getElementById("btnAuto")?.click());
  await page.waitForTimeout(700);
  // await page.evaluate(i => document.querySelectorAll("#tlNodes .node")[i]?.click(), shot.phase);
}
// GOTCHA 17:互動遊戲沒 auto-play → 送鍵盤自己玩。範例(Katamari 類):
//   const hold = async (p,k,ms)=>{ await p.keyboard.down(k); await p.waitForTimeout(ms); await p.keyboard.up(k); };
//   await waitLoaded(page, { gone: "PREPARING" });                       // 等預快取完 START 才 ready
//   try { await page.getByText("START",{exact:false}).first().click(); } // 點開始
//   catch { await page.mouse.click(vp.width/2, vp.height*0.25); }
//   await page.waitForTimeout(1500);
//   for (const [k,ms] of [["ArrowUp",2600],["ArrowRight",1400],["ArrowUp",2400]]) await hold(page,k,ms);
//   // 遊戲常 load 後 ~10s 才真開始;trim gameplay 挑「球夠大/物件多」的窗(GOTCHA 17)。
// 截圖/錄完後,MODE B 端務必逐張量目標區 stdev(≈0=空)自動抓漏重截。
// ─────────────────────────────────────────────────

import { chromium } from "playwright";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { mkdirSync, readdirSync, renameSync } from "node:fs";
import { join, extname } from "node:path";

const portrait = process.argv.includes("--portrait");
const VIEW = portrait ? { width: 720, height: 1280 } : { width: 1280, height: 720 };
const RAW = join(process.cwd(), "raw"); mkdirSync(RAW, { recursive: true });
const MIME = { ".html":"text/html", ".json":"application/json", ".js":"text/javascript",
               ".mjs":"text/javascript", ".mp3":"audio/mpeg", ".png":"image/png", ".webp":"image/webp",
               ".glb":"model/gltf-binary", ".css":"text/css" };

const server = createServer(async (req, res) => {
  try {
    const p = join(SERVE_ROOT, decodeURIComponent(req.url.split("?")[0]));
    res.writeHead(200, { "Content-Type": MIME[extname(p)] || "application/octet-stream" });
    res.end(await readFile(p));
  } catch { res.writeHead(404).end("404"); }
});
await new Promise(r => server.listen(PORT, "127.0.0.1", r));

const browser = await chromium.launch({ headless: false,
  args: ["--use-gl=angle","--use-angle=swiftshader","--ignore-gpu-blocklist","--no-sandbox",
         "--autoplay-policy=no-user-gesture-required"] });

for (const shot of SHOTS) {
  const vdir = join(RAW, shot.id); mkdirSync(vdir, { recursive: true });
  const ctx = await browser.newContext({ viewport: VIEW, recordVideo: { dir: vdir, size: VIEW } });
  const page = await ctx.newPage();
  await page.goto(`http://127.0.0.1:${PORT}${shot.url}`, { waitUntil: "load" });
  await page.addStyleTag({ content: HIDE });
  await DRIVE(page, shot);
  await page.addStyleTag({ content: HIDE });   // 再確保 cinema 切換後 HUD 仍藏
  await page.waitForTimeout(shot.hold);
  await ctx.close();
  const f = readdirSync(vdir).find(x => x.endsWith(".webm"));
  const out = join(RAW, `${shot.id}${portrait ? "_v" : ""}.webm`);
  renameSync(join(vdir, f), out);
  console.log("captured", out);
}
await browser.close(); server.close();
console.log("capture done");
