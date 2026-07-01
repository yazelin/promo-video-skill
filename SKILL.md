---
name: promo-video
description: Zero-cost promo video / trailer / social ad for a web project (cinematic web app, game, or an image feed/gallery), driving traffic to a site or Telegram/social. Use when the user wants a trailer, promo, teaser, or ad made from an existing web app or a generated-image feed — outputs multi-aspect (16:9/9:16/1:1/4:5) with narration, captions, brand tag and CTA. All free: screen-capture or Ken Burns + edge-tts + Gemini audition + ffmpeg. No paid APIs.
---

# promo-video — 零成本宣傳片 / 廣告管線

把一個 web 專案變成宣傳片或社群廣告。**核心 insight:如果 app 自己會電影運鏡演出,就螢幕錄它,不用「生成」影片;如果是出圖專案,就下載精選圖做 Ken Burns。** 其餘(旁白 / 驗音 / 合成 / 品牌 / CTA)兩者共用。實戰驗證:`battlefield-editor/tools/trailer`(螢幕錄)+ catime 廣告「會讀世界的貓」(Ken Burns + 新聞→圖揭示)。

## 決策樹:先選 capture 模式

- **會動的 app**(3D/canvas/自動運鏡、有 auto-play)→ **MODE A 螢幕錄**(`capture-app.mjs`)。
- **出圖 / 圖庫 / 相片 feed**(AI 生成圖、gallery)→ **MODE B Ken Burns montage**(下載精選圖 + `kenburns.sh`)。
- 混合:screen-record 當主體、Ken Burns 當補充,都行。

## 四階段

1. **Capture** — MODE A：`xvfb-run` 跑 headed Chromium,Playwright `recordVideo` 錄自動播映的高潮段。MODE B：撈來源清單、精選、下載。
2. **Narration**(選)— edge-tts `zh-TW-YunJheNeural --rate=-5%` 生旁白。
3. **Verify**(選)— Gemini pro 代聽逐字驗聲調;Gemini flash 海選配樂。
4. **Compose** — `brand.py` 產品牌素材(字卡/角標/CTA/QR),ffmpeg 疊字幕/串接/混音,出多比例 + 濃縮版。

## 這裡的三個模板(改頂部 config 就能用)

- `brand.py` — PIL:**cover/contain 守比例合成器**、字卡、常駐角標、CTA 卡、mini 圖庫、QR(走 API)。
- `kenburns.sh` — **無抖動 Ken Burns** clip + **文字貼圖緣** + concat + 混音(MODE B 主力)。
- `capture-app.mjs` — Playwright+xvfb 螢幕錄(MODE A);內建 http server、藏 HUD、點時間軸節點跳段。

## GOTCHAS —— 這份是最值錢的資產,每次照它檢查

1. **比例守恆**:**絕不**對混合比例的圖用 `scale=W:H`(會拉伸變形)。背景用 cover(等比放大後裁切),主體用 contain(等比縮放放入)。ffmpeg 的 scale 只能是整數倍(2x)或加 `force_original_aspect_ratio`。收工前跑「原始比例 vs 顯示比例」稽核(誤差 <0.1% 才過)。
2. **Ken Burns 抖動**:來源先放大 **2x** 再縮(整數像素跳動變次像素)+ 縮放用**線性幀號** `z='1+K*on/(D-1)'`,**絕不**用會累積捨入的 `z='min(zoom+inc,...)'`。
3. **zoompan 幀爆炸**:**別** `-loop 1 -t`(每輸入幀被 ×d);單張圖 `-frames:v D` + `zoompan d=D`。
4. **文字貼圖緣**:圖先垂直置中;文字位置 = 中心 ± (圖高 × zmax)/2 ± gap,**逐圖算**(PIL 輸出各圖高當 sidecar)。這樣橫圖不會離很遠、也不會壓到。
5. **file:// fetch 被擋**:app 用 `fetch(?pkg=)`/載 JSON → 起 `python3 -m http.server` 走 http(或 capture-app.mjs 內建 server)。
6. **headless WebGL 掉 swiftshader/全黑** → 用 `xvfb-run -a --server-args="-screen 0 WxHx24"` 跑 **headed** Chromium。
7. **ES-module app**:`gotoPhase` 不在 window 上 → 用 DOM 點時間軸節點 `#tlNodes .node[i].click()`,別 `evaluate(gotoPhase)`。
8. **QR**:PEP668 裝不了 qrcode → `api.qrserver.com/v1/create-qr-code/?data=<公開連結>`(只放公開連結);**上線前手機掃一次確認**。
9. **edge-tts 破音字**:先繞(「沒 mò」→改詞避開);聲調驗證用 **Gemini pro 問音高走向**,whisper STT 驗不了聲調(念錯照樣轉回同字)。
10. **配樂**:Gemini flash 海選 CC0,**對味**(別把戰爭配樂套在貓上);記 CC0 出處。
11. **多比例**:16:9=YouTube、9:16=Reels/Shorts/LINE、1:1 & 4:5=FB/IG 動態。MODE A 每比例**原生重錄**(直式 viewport);MODE B 每比例**重合成**。
12. **常駐角標(台標)**:品牌+URL 全程在畫面角落(不只結尾卡),整支疊一張透明 PNG。
13. **廣告要驅動行動**:前 2 秒鉤子(靜音自動播,首幀就有畫面/大字)、燒錄字幕(FB 靜音)、CTA 給「現在就做」的理由。
14. **平台細節**:FB 影片進貼文、**連結放第一則留言**(避免觸及被壓);`+movflags +faststart`;LINE 內嵌播放要用相簿/影片鈕傳,不能用「檔案」。
15. **截圖要等載入完成 + 逐張驗非空**:MODE A/gallery 逐項截圖**別用固定秒數**(慢的那張會截到「載入中」空畫面)。輪詢到 loading 指示消失才截;截完**逐張量目標區 stdev**(≈0 = 空/沒渲染),自動抓漏的重截。實戰:roll-formosa 苗栗固定 1.8s 截到空白,改 wait-for-load + stdev 掃描補回。
16. **實際放大看,別只信縮圖**:驗證務必抽**全解析度**單張細看(裁切/糊邊/被切在縮圖看不出)。量座標時對原圖畫 y/x 格線。實戰:地標下緣被裁 55px、下半糊影,都是縮圖看不出、放大畫格線才抓到。

## Config 表面(每專案換這些)

- 品牌 tokens:主色、字標、印章字、URL、社群 handle(brand.py 頂部)。
- 文案:旁白台詞、卡司介紹、(廣告)新聞→圖對照(kenburns/compose 頂部)。
- capture:MODE A 的 URL / 跳哪段 / 藏哪些 HUD;MODE B 的來源清單 / 精選規則。

## 交付與 CTA

- 出 9:16(主力社群)、1:1 或 4:5(FB/IG 動態)、16:9(YT);廣告另附 ~15s 濃縮版。
- CTA:主要目標(訂閱/來訪)放大 + QR;次要出口一行。訂閱型產品(每小時 feed)偏 Telegram/訂閱;作品展示偏網站。兩者可雙軌並重 + 角標帶 URL。
- FB 社團:貼文本體放影片,第一則留言放連結。

相關筆記:[[reference-web-trailer-pipeline]]、[[reference-gemini-audio-audition]]、[[reference-edge-tts-zhtw-polyphone]]、[[reference-mobile-verify-playwright]]。
