#!/bin/bash
# 랭킹 이미지 1장 → 8초 릴스 + 커버 + 캡션을 게시기 형식 폴더로 만든다
# 쓰는 법: bash ranking/make_reel.sh <이미지.png> <캡션.txt> <발간물폴더(예: /tmp/pub/20261031_치킨브랜드평판)>
# 결과: <발간물폴더>/06_캡션.txt, <발간물폴더>/릴스/1판/{릴스.mp4, 커버.jpg, 캡션.txt}
set -euo pipefail
IMG="$1"; CAP="$2"; PUB="$3"; HERE="$(cd "$(dirname "$0")" && pwd)"
REEL="$PUB/릴스/1판"; mkdir -p "$REEL"
python3 - "$IMG" <<'PY'
import sys
from PIL import Image
im = Image.open(sys.argv[1])
if im.size != (1080, 1920): sys.exit(f'이미지 크기 {im.size} — 1080×1920 이어야 함')
PY
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$IMG" -i "$HERE/bgm.m4a" -t 8 -vf format=yuv420p \
  -c:v libx264 -preset veryfast -tune stillimage -crf 18 -r 30 -c:a aac -b:a 160k -shortest -movflags +faststart "$REEL/릴스.mp4"
python3 -c "from PIL import Image; Image.open('$IMG').convert('RGB').save('$REEL/커버.jpg', 'JPEG', quality=92)"
cp "$CAP" "$REEL/캡션.txt"; cp "$CAP" "$PUB/06_캡션.txt"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$REEL/릴스.mp4")
echo "릴스 $REEL/릴스.mp4 길이 ${D}초 · 커버 · 캡션 $(wc -m < "$CAP")자"
