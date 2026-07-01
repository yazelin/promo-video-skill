#!/bin/bash
# promo-video MODE B 主力:把一張圖做成無抖動 Ken Burns clip,文字貼圖緣。
# 依賴 ffmpeg。搭配 brand.py 的 composite()(先做好模糊底+主體置中的 PNG + .h 圖高)。
#
# 用法(單 clip):
#   kb_clip <comp.png> <W> <H> <dur_s> <out.mp4> [zoom_in|zoom_out]
# 用法(貼緣文字的 reveal):
#   kb_reveal <comp.png> <hfile> <W> <H> <dur> <out> <news> <title> <news_fs> <title_fs>
set -e
FB="$HOME/.local/share/fonts/1NotoSansTC-Black.ttf"
FR="$HOME/.local/share/fonts/NotoSansTC-Bold.ttf"

# ── 無抖動 Ken Burns(GOTCHA 2+3)──────────────────
# 關鍵:來源 2x 預縮放 + 線性幀號縮放;單張圖 -frames:v D(不 -loop)。
kb_clip(){ png=$1; W=$2; H=$3; dur=$4; out=$5; dir=${6:-zoom_in}
  local D=$(python3 -c "print(int($dur*30))")
  local fo=$(python3 -c "print($dur-0.15)")
  local z
  if [ "$dir" = zoom_out ]; then z="z='1.12-0.12*on/($D-1)'"; else z="z='1+0.12*on/($D-1)'"; fi
  ffmpeg -y -loglevel error -i "$png" -vf "scale=$((W*2)):$((H*2)):flags=lanczos,\
zoompan=$z:d=$D:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=30,\
fade=t=in:st=0:d=0.15,fade=t=out:st=$fo:d=0.15,format=yuv420p" \
    -frames:v $D -c:v libx264 -pix_fmt yuv420p -r 30 "$out"
}

# ── reveal:圖 + 貼緣文字(GOTCHA 4)────────────────
# 文字 y = 中心 ± (圖高 × 1.07)/2 ± gap,逐圖算 → 橫圖不遠、不壓到。
kb_reveal(){ png=$1; hfile=$2; W=$3; H=$4; dur=$5; out=$6; news=$7; title=$8; nf=${9:-38}; tf=${10:-64}
  local h=$(cat "$hfile"); local D=$(python3 -c "print(int($dur*30))"); local fo=$(python3 -c "print($dur-0.3)")
  local ny=$(python3 -c "print(max(130, int($H/2 - $h*1.07/2 - ($nf+40))))")
  local ty=$(python3 -c "print(min($H-$tf-30, int($H/2 + $h*1.07/2 + 22)))")
  ffmpeg -y -loglevel error -i "$png" -vf "scale=$((W*2)):$((H*2)):flags=lanczos,\
zoompan=z='1+0.07*on/($D-1)':d=$D:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=${W}x${H}:fps=30,\
drawtext=fontfile=$FR:text='$news':fontcolor=0xfff5f9:fontsize=$nf:x=(w-tw)/2:y=$ny:box=1:boxcolor=black@0.55:boxborderw=14:alpha='min(1\,max(0\,(t-0.25)/0.5))',\
drawtext=fontfile=$FB:text='→　$title':fontcolor=white:fontsize=$tf:x=(w-tw)/2:y=$ty:box=1:boxcolor=0xa0386b@0.55:boxborderw=18:alpha='min(1\,max(0\,(t-0.9)/0.6))',\
fade=t=in:st=0:d=0.3,fade=t=out:st=$fo:d=0.3,format=yuv420p" \
    -frames:v $D -c:v libx264 -pix_fmt yuv420p -r 30 "$out"
}

# ── 串接一堆 mp4 + 鋪配樂 + faststart(GOTCHA 14)──
kb_finish(){ music=$1; out=$2; shift 2; local seglist="$@"
  local tmp=$(dirname "$out")/_kb_list.txt; : > "$tmp"
  for s in $seglist; do echo "file '$s'" >> "$tmp"; done
  ffmpeg -y -loglevel error -f concat -safe 0 -i "$tmp" -c copy "${out%.mp4}_v.mp4"
  local VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${out%.mp4}_v.mp4")
  local afo=$(python3 -c "print($VD-2)")
  ffmpeg -y -loglevel error -i "${out%.mp4}_v.mp4" -i "$music" \
    -filter_complex "[1:a]atrim=0:$VD,afade=t=in:st=0:d=0.8,afade=t=out:st=$afo:d=2,volume=0.82[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -t $VD "$out"
  echo "→ $out (${VD}s)"
}

# 疊常駐角標(整支);corner 為 brand.py 產的透明 PNG(GOTCHA 12)
kb_overlay_tag(){ vin=$1; corner=$2; vout=$3
  ffmpeg -y -loglevel error -i "$vin" -i "$corner" \
    -filter_complex "[0:v][1:v]overlay=0:0,format=yuv420p[v]" -map "[v]" -map 0:a? \
    -c:v libx264 -crf 20 -preset medium -c:a copy -movflags +faststart "$vout"
}

# 被 source 時只載入函式;直接執行則印用法
[ "${BASH_SOURCE[0]}" = "$0" ] && { echo "source this file, then call kb_clip / kb_reveal / kb_finish / kb_overlay_tag"; }
