#!/usr/bin/env python3
"""promo-video 配樂海選 / 旁白驗聲調 —— Gemini 代聽(AI 沒喇叭也能「聽」)。
食譜來源 memory: reference_gemini_audio_audition。key 在 ~/gemini/.env 的 NANOBANANA_GEMINI_API_KEY。

用法:
  python3 audition.py music "<用途一句話>" a.mp3 b.mp3 ...   # gemini-2.5-flash 逐首評 fit 0-10
  python3 audition.py tone  "<預期文字>"   voice.mp3          # gemini-2.5-pro 逐字驗聲調(破音字)

GOTCHA(照做別踩):
- flash-lite 不可用(把正弦波聽成木吉他)。海選用 flash、聲調用 pro。
- 聲調驗證問「音高走向」**非**「念 A 還是 B」(引導式問法會回『正確讀音』而非聽到的)。
- 長檔先截 45s、mono、64k 省 token(本檔自動做)。逾時設 ~25s(90s 會掛)。
- tone 結論與人耳衝突時,人耳優先。whisper STT 驗不了聲調(念錯照樣轉回同字)。
"""
import os, sys, base64, json, subprocess, tempfile, urllib.request, re

ENV = os.path.expanduser("~/gemini/.env")
KEY = next((l.split("=", 1)[1].strip().strip('"\'') for l in open(ENV)
            if l.startswith("NANOBANANA_GEMINI_API_KEY=")), None) if os.path.exists(ENV) else None
URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}"

def _prep(mp3, secs=45):
    """截前 secs 秒 + 轉 mono 64k 省 token,回傳 base64。ffmpeg 失敗就用原檔。"""
    out = tempfile.mktemp(suffix=".mp3")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-t", str(secs), "-i", mp3,
                    "-ac", "1", "-b:a", "64k", out], check=False)
    src = out if os.path.exists(out) and os.path.getsize(out) > 0 else mp3
    return base64.b64encode(open(src, "rb").read()).decode()

def _ask(model, prompt, b64, timeout=25):
    body = json.dumps({"contents": [{"parts": [
        {"text": prompt}, {"inline_data": {"mime_type": "audio/mpeg", "data": b64}}]}]}).encode()
    req = urllib.request.Request(URL.format(m=model, k=KEY), data=body,
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    t = r["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(re.search(r"\{.*\}", t, re.S).group(0))

def music(use_case, files):
    p = (f"這段配樂要配:{use_case}。只回 STRICT JSON:"
         '{"fit":0-10,"tempo":"slow|mid|upbeat","vocals":true/false,"mood":"4-8字","one_line":"一句含是否推薦"}')
    for f in files:
        try:
            j = _ask("gemini-2.5-flash", p, _prep(f))
            print(f"{os.path.basename(f):30} fit={j['fit']} {j['tempo']:6} vocals={str(j['vocals']):5} "
                  f"{j.get('mood','')} — {j['one_line']}")
        except Exception as e:
            print(f"{os.path.basename(f):30} ERR {repr(e)[:90]}")

def tone(expected, f):
    p = ("這是一段中文語音。只根據你【實際聽到的音高走向】逐字寫拼音+聲調"
         "(1=高平 2=上升 3=降升 4=下降),不要用你認為正確或常見的讀音。"
         f"文字內容:「{expected}」。"
         '輸出 STRICT JSON:{"heard":[{"char":"字","pinyin":"gai","tone":1}...],"notes":"任何怪或不確定處"}')
    j = _ask("gemini-2.5-pro", p, _prep(f, secs=30), timeout=60)
    print(" ".join(f"{x['char']}{x['pinyin']}{x['tone']}" for x in j["heard"]))
    if j.get("notes"):
        print("notes:", j["notes"])

if __name__ == "__main__":
    if not KEY:
        sys.exit("缺 NANOBANANA_GEMINI_API_KEY(~/gemini/.env)")
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "music" and len(sys.argv) >= 4:
        music(sys.argv[2], sys.argv[3:])
    elif mode == "tone" and len(sys.argv) == 4:
        tone(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
