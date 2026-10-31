# 랭킹 이미지 1장(1080×1920 PNG)을 그린다. 밝은 바탕(라이트) 고정. Figma figma_fill.js 와 같은 디자인을 HTML + Playwright(Chromium)로 그린다
# (Figma 무료 플랜은 MCP 호출이 월 20회라 매일 쓸 수 없음). 글꼴은 ranking/fonts/(OFL)
# 쓰는 법: python3 ranking/render.py <자료.json> <결과.png>   자료 형식: 만드는법.md 2절
# "image": 자료 JSON 옆 그림 파일(주제 그림, 선택) — 제목 오른쪽 위에 놓인다
# 두 가지 모양: 순위 목록(기본, items 10~15개, 1위 가림) · 구간표("layout": "tier", rows 5~12개 ["상위 1%", "값"])
import sys
import json, pathlib, html
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
# 색은 라이트 하나로 고정(2026-10-30 결정)
C = dict(bg='#FFF7EB', panel='#FFFFFF', line='#F0E2CC', ink='#211A14', sub='#8A7461', gold='#F5A300', silver='#8E979F', bronze='#C8702E', accent='#FF6A13', badge_ink='#FFFFFF')

def esc(s): return html.escape(s).replace('\n', '<br>')

CROWN = '<svg class="a" style="left:{x}px;top:{y}px" width="{w}" height="{h}" viewBox="0 0 110 70"><path d="M 0 70 L 10 10 L 35 40 L 55 0 L 75 40 L 100 10 L 110 70 Z" fill="{c}"/></svg>'
def card_html(D):
    # 1위 카드. "qstyle": O(원래) · A~E (기본 O). 2026-10-31 Gyan: 물음표가 왼쪽으로 치우쳐 시안 5개
    st = D.get('qstyle', 'O'); g = C['gold']; hint = esc(D['hint'])
    box = lambda extra='': f'<div class="a" style="left:80px;top:640px;width:920px;height:190px;border-radius:28px;background:{C["panel"]};border:3px solid {g};box-shadow:0 6px 18px rgba(0,0,0,.06){extra}"></div>'
    if st == 'O':  # 원래 모양(10/30~). 10/31 Gyan: 물음표만 오른쪽으로 — 왕관 끝(228)과 힌트 칸 시작(500) 사이 가운데
        return (box() + CROWN.format(x=118, y=690, w=110, h=70, c=g)
            + f'<div class="a bhs" style="left:120px;top:768px;width:110px;text-align:center;font-size:34px;color:{g}">1위</div>'
            + f'<div class="a bhs" style="left:250px;top:650px;width:250px;text-align:center;font-size:150px;line-height:1.1;color:{g}">?</div>'
            + f'<div id="hint" class="a" style="left:500px;top:688px;width:470px;font-weight:700;font-size:36px;line-height:1.3;text-align:right;white-space:normal;word-break:keep-all">{hint}</div>')
    if st == 'A':  # 왕관 | 금색 원 속 흰 ? (가운데 쪽) | 힌트 오른쪽
        return (box() + CROWN.format(x=118, y=690, w=110, h=70, c=g)
            + f'<div class="a bhs" style="left:120px;top:768px;width:110px;text-align:center;font-size:34px;color:{g}">1위</div>'
            + f'<div class="a bhs" style="left:300px;top:665px;width:140px;height:140px;border-radius:70px;background:{g};color:#fff;font-size:104px;line-height:140px;text-align:center">?</div>'
            + f'<div id="hint" class="a" style="left:480px;top:688px;width:490px;font-weight:700;font-size:36px;line-height:1.3;text-align:right;white-space:normal;word-break:keep-all">{hint}</div>')
    if st == 'B':  # 힌트 왼쪽 정렬 | 오른쪽에 금색 상자 속 큰 ? (미스터리 박스)
        return (box() + CROWN.format(x=118, y=668, w=62, h=40, c=g)
            + f'<div class="a bhs" style="left:190px;top:668px;font-size:34px;line-height:40px;color:{g}">1위</div>'
            + f'<div id="hint" class="a" style="left:118px;top:722px;width:600px;font-weight:700;font-size:36px;line-height:1.3;text-align:left;white-space:normal;word-break:keep-all">{hint}</div>'
            + f'<div class="a bhs" style="left:790px;top:662px;width:170px;height:146px;border-radius:24px;background:{g};color:#fff;font-size:120px;line-height:146px;text-align:center;transform:rotate(-6deg)">?</div>')
    if st == 'C':  # 왕관 1위 | 가린 이름 막대 "? ? ?" (점선) | 힌트는 막대 위
        return (box() + CROWN.format(x=118, y=690, w=110, h=70, c=g)
            + f'<div class="a bhs" style="left:120px;top:768px;width:110px;text-align:center;font-size:34px;color:{g}">1위</div>'
            + f'<div id="hint" class="a" style="left:270px;top:658px;width:700px;font-weight:700;font-size:30px;line-height:1.3;text-align:center;white-space:normal;word-break:keep-all">{hint}</div>'
            + f'<div class="a bhs" style="left:330px;top:760px;width:580px;height:54px;border-radius:27px;border:3px dashed {g};background:#FFF3D6;color:{g};font-size:40px;line-height:50px;text-align:center;letter-spacing:18px">???</div>')
    if st == 'D':  # 카드 윗변에 걸친 금색 원 ? (가운데) | 왕관 · 힌트는 가운데 정렬
        return (box() + f'<div class="a bhs" style="left:470px;top:596px;width:140px;height:140px;border-radius:70px;background:{g};border:6px solid {C["bg"]};color:#fff;font-size:100px;line-height:128px;text-align:center">?</div>'
            + CROWN.format(x=140, y=676, w=70, h=45, c=g)
            + f'<div class="a bhs" style="left:225px;top:676px;font-size:36px;line-height:45px;color:{g}">1위</div>'
            + f'<div id="hint" class="a" style="left:120px;top:730px;width:840px;font-weight:700;font-size:32px;line-height:1.3;text-align:center;white-space:normal;word-break:keep-all">{hint}</div>')
    if st == 'E':  # 금색 왼쪽 띠(왕관 + 1위, 흰색) | 힌트 가운데 | 오른쪽 끝 큰 외곽선 ?
        return (box('') + f'<div class="a" style="left:80px;top:640px;width:200px;height:190px;border-radius:28px 0 0 28px;background:{g}"></div>'
            + CROWN.format(x=125, y=678, w=110, h=70, c='#fff')
            + f'<div class="a bhs" style="left:80px;top:758px;width:200px;text-align:center;font-size:38px;color:#fff">1위</div>'
            + f'<div id="hint" class="a" style="left:310px;top:688px;width:520px;font-weight:700;font-size:36px;line-height:1.3;text-align:center;white-space:normal;word-break:keep-all">{hint}</div>'
            + f'<div class="a bhs" style="left:840px;top:648px;width:140px;text-align:center;font-size:150px;line-height:1.1;color:transparent;-webkit-text-stroke:5px {g}">?</div>')
    sys.exit(f'qstyle 은 O · A~E: {st}')

def build(D):
    items = D['items']; N = len(items)
    if not 10 <= N <= 15: sys.exit(f'순위는 10~15개여야 함: {N}')
    rest = items[1:]; left = -(-len(rest) // 2)
    rowH = min(104, 740 // left); boxH = rowH - 16; top0 = 870
    rows = []
    for i, it in enumerate(rest):
        name, val = (it, '') if isinstance(it, str) else (it[0], it[1])   # 항목: "이름" 또는 ["이름", "값"]
        rank = i + 2; col = 0 if i < left else 1; row = i if i < left else i - left
        x = [80, 550][col]; y = top0 + row * rowH
        rc = C['silver'] if rank == 2 else C['bronze'] if rank == 3 else C['sub']
        rows.append(f'<div class="box" style="left:{x}px;top:{y}px;height:{boxH}px"></div>'
                    f'<div class="rank" style="left:{x+18}px;top:{y}px;height:{boxH}px;color:{rc}">{rank}</div>'
                    f'<div class="name fit" data-max="{170 if val else 320}" style="left:{x+110}px;top:{y}px;height:{boxH}px">{esc(name)}</div>'
                    + (f'<div class="val fit" data-max="150" style="left:{x+282}px;top:{y}px;height:{boxH}px">{esc(val)}</div>' if val else ''))
    endY = max(top0 + left * rowH + 16, 1590)
    fonts = HERE / 'fonts'
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:BHS;src:url("{(fonts/'BlackHanSans-Regular.ttf').as_uri()}")}}
@font-face{{font-family:NSK;src:url("{(fonts/'NotoSansKR-wght.ttf').as_uri()}");font-weight:100 900}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:{C['bg']};position:relative;overflow:hidden;font-family:NSK;color:{C['ink']}}}
.a{{position:absolute;white-space:nowrap}}
.bhs{{font-family:BHS;font-weight:400}}
.box{{position:absolute;width:450px;background:{C['panel']};border:2px solid {C['line']};border-radius:18px}}
.rank{{position:absolute;width:80px;display:flex;align-items:center;justify-content:center;font-family:BHS;font-size:52px}}
.name{{position:absolute;display:flex;align-items:center;font-weight:700;font-size:38px;white-space:nowrap}}
.val{{position:absolute;width:150px;display:flex;align-items:center;justify-content:flex-end;font-family:BHS;font-size:34px;color:{C['accent']};white-space:nowrap}}
</style></head><body>
<div class="a" style="left:80px;top:250px;width:420px;height:56px;border-radius:28px;background:{C['accent']};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:26px;color:{C['badge_ink']}">{esc(D['badge'])}</div>
{hero(D, 330, 690, 150)}
<div class="a bhs fit" data-max="{600 if D.get('image') else 920}" style="left:80px;top:330px;font-size:116px;line-height:1.2">{esc(D['title'])}</div>
<div id="top" class="a bhs" style="left:80px;top:470px;font-size:116px;line-height:1.2;color:{C['gold']}">TOP {N}</div>
<div id="stat" class="a" style="top:520px;right:80px;font-weight:500;font-size:28px;line-height:1.45;color:{C['sub']};text-align:right">{esc(D['stat'])}</div>
{card_html(D)}
{''.join(rows)}
<div class="a" style="left:80px;top:{endY}px;width:920px;text-align:center;font-weight:700;font-size:34px;color:{C['accent']}">{esc(D.get('cta') or '1위는 어디일까요?  정답은 캡션에')}</div>
<div class="a" style="left:80px;top:{endY+78}px;width:920px;text-align:center;font-weight:400;font-size:19px;line-height:1.45;color:{C['sub']};white-space:normal;word-break:keep-all">{esc(D['source'])}</div>
<script>
document.fonts.ready.then(()=>{{
  for (const el of document.querySelectorAll('.fit')) {{ const m=+el.dataset.max; let fs=parseFloat(getComputedStyle(el).fontSize);
    while (el.scrollWidth>m && fs>12) {{ fs-=2; el.style.fontSize=fs+'px'; }} }}
  const h=document.getElementById('hint'); let fs=36; while (h.offsetHeight>100 && fs>24) {{ fs-=2; h.style.fontSize=fs+'px'; }}
  const t=document.getElementById('top'), s=document.getElementById('stat');
  s.style.maxWidth=(1000-(80+t.offsetWidth+30))+'px';
  document.body.dataset.ready='1';
}});
</script></body></html>'''

def hero(D, size, x, y):
    # 주제 그림(선택): 자료 JSON 옆의 그림 파일. 밝은 바탕과 섞이게 multiply
    if not D.get('image'): return ''
    f = (SRC_DIR / D['image']).resolve()
    if not f.exists(): sys.exit(f'그림 없음: {f}')
    return f'<img class="a" src="{f.as_uri()}" style="left:{x}px;top:{y}px;width:{size}px;height:{size}px;object-fit:contain;mix-blend-mode:multiply;-webkit-mask-image:radial-gradient(closest-side,#000 62%,transparent 100%);mask-image:radial-gradient(closest-side,#000 62%,transparent 100%)">'

def build_tier(D):
    # 구간표: "나는 상위 몇 %?" — rows 위(상위 1%)에서 아래(50% 등)로. 위가 좁고 아래가 넓은 피라미드 막대
    rows = D['rows']; N = len(rows)
    if not 5 <= N <= 12: sys.exit(f'구간은 5~12개여야 함: {N}')
    top0 = 650; rowH = min(124, 900 // N); barH = rowH - 14
    out = []
    for i, (label, val) in enumerate(rows):
        w = int(560 + (920 - 560) * i / max(1, N - 1)); x = (1080 - w) // 2; y = top0 + i * rowH
        t = i / max(1, N - 1)
        bg = C['gold'] if i == 0 else C['panel']
        fg = '#FFFFFF' if i == 0 else C['ink']
        bd = C['gold'] if i < 3 else C['line']
        out.append(f'<div class="a" style="left:{x}px;top:{y}px;width:{w}px;height:{barH}px;border-radius:{barH//2}px;background:{bg};border:3px solid {bd};display:flex;align-items:center;justify-content:space-between;padding:0 34px">'
                   f'<span class="bhs" style="font-size:44px;color:{fg if i == 0 else C["gold"] if i < 3 else C["sub"]}">{esc(label)}</span>'
                   f'<span class="bhs" style="font-size:50px;color:{fg if i == 0 else C["accent"]}">{esc(val)}</span></div>')
    endY = max(top0 + N * rowH + 20, 1590)
    fonts = HERE / 'fonts'
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:BHS;src:url("{(fonts/'BlackHanSans-Regular.ttf').as_uri()}")}}
@font-face{{font-family:NSK;src:url("{(fonts/'NotoSansKR-wght.ttf').as_uri()}");font-weight:100 900}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:{C['bg']};position:relative;overflow:hidden;font-family:NSK;color:{C['ink']}}}
.a{{position:absolute;white-space:nowrap}} .bhs{{font-family:BHS;font-weight:400}}
</style></head><body>
<div class="a" style="left:80px;top:250px;width:420px;height:56px;border-radius:28px;background:{C['accent']};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:26px;color:{C['badge_ink']}">{esc(D['badge'])}</div>
{hero(D, 360, 660, 170)}
<div class="a bhs fit" data-max="{580 if D.get('image') else 920}" style="left:80px;top:330px;font-size:104px;line-height:1.2">{esc(D['title'])}</div>
<div class="a bhs fit" data-max="{580 if D.get('image') else 920}" style="left:80px;top:462px;font-size:104px;line-height:1.2;color:{C['gold']}">{esc(D['title2'])}</div>
<div class="a" style="left:80px;top:590px;width:920px;text-align:right;font-weight:500;font-size:28px;color:{C['sub']}">{esc(D['stat'])}</div>
{''.join(out)}
<div class="a" style="left:80px;top:{endY}px;width:920px;text-align:center;font-weight:700;font-size:34px;color:{C['accent']}">{esc(D.get('cta') or '너는 어디쯤이야? 댓글로 알려줘')}</div>
<div class="a" style="left:80px;top:{endY+78}px;width:920px;text-align:center;font-weight:400;font-size:19px;line-height:1.45;color:{C['sub']};white-space:normal;word-break:keep-all">{esc(D['source'])}</div>
<script>
document.fonts.ready.then(()=>{{
  for (const el of document.querySelectorAll('.fit')) {{ const m=+el.dataset.max; let fs=parseFloat(getComputedStyle(el).fontSize);
    while (el.scrollWidth>m && fs>12) {{ fs-=2; el.style.fontSize=fs+'px'; }} }}
  document.body.dataset.ready='1';
}});
</script></body></html>'''

def main(src, out):
    D = json.loads(pathlib.Path(src).read_text(encoding='utf-8'))
    global SRC_DIR
    SRC_DIR = Path(src).resolve().parent
    page_html = build_tier(D) if D.get('layout') == 'tier' else build(D)
    tmp = pathlib.Path(out).with_suffix('.html'); tmp.write_text(page_html, encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(tmp.resolve().as_uri()); pg.wait_for_selector('body[data-ready="1"]', timeout=20000)
        over = pg.evaluate('''() => [...document.querySelectorAll('.a,.name,.rank')].filter(e => { const r=e.getBoundingClientRect(); return r.right>1080||r.bottom>1920; }).length''')
        pg.screenshot(path=out, full_page=False); b.close()
    tmp.unlink()
    if over: sys.exit(f'화면 밖으로 나간 글자 {over}개 — 자료 글 길이를 줄일 것')
    print('그림', out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
