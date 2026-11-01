#!/bin/bash
# 랭킹 이미지 1장 → 8초 릴스 + 커버 + 캡션을 게시기 형식 폴더로 만든다
# 쓰는 법: bash ranking/make_reel.sh <이미지.png> <캡션.txt> <발간물폴더(예: /tmp/pub/20261031_치킨브랜드평판)> [배경음 이름(예: 02_웅장)]
# 배경음: ranking/bgm/ 의 곡(자체 제작)을 날짜 순서로 돌려 쓴다(한국 날짜의 연중 일수 ÷ 곡 수의 나머지). 넷째 인자를 주면 그 곡
# 결과: <발간물폴더>/06_캡션.txt, <발간물폴더>/릴스/1판/{릴스.mp4, 커버.jpg, 캡션.txt, 발간준비.json}
set -euo pipefail
IMG="$1"; CAP="$2"; PUB="$3"; HERE="$(cd "$(dirname "$0")" && pwd)"
mapfile -t BGMS < <(ls "$HERE"/bgm/*.m4a | sort)
if [ -n "${4:-}" ]; then BGM="$HERE/bgm/$4.m4a"; else DOY=$(TZ=Asia/Seoul date +%j); HR=$(TZ=Asia/Seoul date +%H); BGM="${BGMS[$(( (10#$DOY + 10#$HR) % ${#BGMS[@]} ))]}"; fi
[ -f "$BGM" ] || { echo "배경음 없음: $BGM"; exit 1; }
REEL="$PUB/릴스/1판"; mkdir -p "$REEL"
python3 - "$IMG" <<'PY'
import sys
from PIL import Image
im = Image.open(sys.argv[1])
if im.size != (1080, 1920): sys.exit(f'이미지 크기 {im.size} — 1080×1920 이어야 함')
PY
ffmpeg -y -loglevel error -loop 1 -framerate 30 -i "$IMG" -i "$BGM" -t 8 -vf format=yuv420p \
  -c:v libx264 -preset veryfast -tune stillimage -crf 18 -r 30 -c:a aac -b:a 160k -shortest -movflags +faststart "$REEL/릴스.mp4"
python3 -c "from PIL import Image; Image.open('$IMG').convert('RGB').save('$REEL/커버.jpg', 'JPEG', quality=92)"
cp "$CAP" "$REEL/캡션.txt"; cp "$CAP" "$PUB/06_캡션.txt"
# 게시 준비 점검 파일(enqueue.py 관문, 2026-11-01 추가): 이미지 크기 · 화면 밖 글자(render.py)를 통과한 뒤 만든 영상 · 커버 · 캡션의 SHA-1.
#   캐릭터 릴스는 INSTA reel_pipeline.py ready 가 쓰고, 랭킹 릴스는 이 스크립트가 쓴다. 이 뒤에 영상 · 커버 · 캡션을 바꾸면 enqueue 가 거부한다
python3 - "$REEL" <<'PY'
import sys, json, hashlib, pathlib, datetime
R = pathlib.Path(sys.argv[1]); h = lambda f: hashlib.sha1(f.read_bytes()).hexdigest()
cap = (R / '캡션.txt').read_text(encoding='utf-8').strip()
if len(cap) > 2200: sys.exit(f'캡션 {len(cap)}자(2,200자 초과)')
if cap.count('#') != 5: sys.exit(f'캡션 해시태그 {cap.count("#")}개(5개여야 함, 만드는법 4절)')
json.dump({'시각': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M'), '점검': 'ranking/make_reel.sh(이미지 1080×1920 · 캡션 2,200자 · 해시태그 5개)',
           'mp4': '릴스.mp4', 'mp4_sha1': h(R / '릴스.mp4'), '커버_sha1': h(R / '커버.jpg'), '캡션_sha1': h(R / '캡션.txt')},
          open(R / '발간준비.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
PY
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$REEL/릴스.mp4")
echo "릴스 $REEL/릴스.mp4 길이 ${D}초 · 배경음 $(basename "$BGM") · 커버 · 캡션"
