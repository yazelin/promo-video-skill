# promo-video — 零成本 web 專案宣傳片 / 廣告管線(Claude Code skill)

把一個 web 專案(會動的 app / 出圖 feed)變成多比例宣傳片或社群廣告。
螢幕錄 或 Ken Burns + edge-tts + Gemini 海選 + ffmpeg,全程零付費 API。

實戰:battlefield-editor 宣傳片(螢幕錄)、catime 廣告「會讀世界的貓」(Ken Burns + 新聞→圖)。

## 安裝(每台機)

```bash
git clone https://github.com/yazelin/promo-video-skill.git ~/promo-video-skill
ln -s ~/promo-video-skill ~/.claude/skills/promo-video
```

之後在 Claude Code 叫 `/promo-video` 或自然語言「幫某專案做宣傳片」即可。

## 檔案

- `SKILL.md` — playbook:決策樹、四階段、14 條 GOTCHAS checklist、CTA/交付指南
- `brand.py` — 守比例合成器 + 比例稽核 + 常駐角標 + CTA 卡 + QR(走 API)
- `kenburns.sh` — 無抖動 Ken Burns + 文字貼圖緣 + 串接/配樂
- `capture-app.mjs` — Playwright + xvfb 螢幕錄(內建 http server、藏 HUD)

## 依賴

ffmpeg、python3+pillow、Noto Sans TC 字型;MODE A 另需 playwright + xvfb;
旁白 edge-tts、驗音/海選 Gemini(key 在各機 `~/gemini/.env`)。
