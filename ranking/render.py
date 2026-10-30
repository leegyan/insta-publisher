# 랭킹 이미지 1장(1080×1920 PNG)을 그린다. Figma figma_fill.js 와 같은 디자인을 HTML + Playwright(Chromium)로 그린다
# (Figma 무료 플랜은 MCP 호출이 월 20회라 매일 쓸 수 없음). 글꼴은 ranking/fonts/(OFL)
# 쓰는 법: python3 ranking/render.py <자료.json> <결과.png>   자료 형식: 만드는법.md 2절
import sys, json, pathlib, html
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
C = dict(bg='#17120E', panel='#241C16', ink='#FFF6EA', sub='#B9A796', gold='#FFB21E', silver='#D9D9D9', bronze='#D98A4E', accent='#FF7A1A')

def esc(s): return html.escape(s).replace('\n', '<br>')

def build(D):
    items = D['items']; N = len(items)
    if not 10 <= N <= 15: sys.exit(f'순위는 10~15개여야 함: {N}')
    rest = items[1:]; left = -(-len(rest) // 2)
    rowH = min(104, 740 // left); boxH = rowH - 16; top0 = 870
    rows = []
    for i, name in enumerate(rest):
        rank = i + 2; col = 0 if i < left else 1; row = i if i < left else i - left
        x = [80, 550][col]; y = top0 + row * rowH
        rc = C['silver'] if rank == 2 else C['bronze'] if rank == 3 else C['sub']
        rows.append(f'<div class="box" style="left:{x}px;top:{y}px;height:{boxH}px"></div>'
                    f'<div class="rank" style="left:{x+18}px;top:{y}px;height:{boxH}px;color:{rc}">{rank}</div>'
                    f'<div class="name fit" data-max="320" style="left:{x+110}px;top:{y}px;height:{boxH}px">{esc(name)}</div>')
    endY = max(top0 + left * rowH + 16, 1590)
    fonts = HERE / 'fonts'
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:BHS;src:url("{(fonts/'BlackHanSans-Regular.ttf').as_uri()}")}}
@font-face{{font-family:NSK;src:url("{(fonts/'NotoSansKR-wght.ttf').as_uri()}");font-weight:100 900}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:{C['bg']};position:relative;overflow:hidden;font-family:NSK;color:{C['ink']}}}
.a{{position:absolute;white-space:nowrap}}
.bhs{{font-family:BHS;font-weight:400}}
.box{{position:absolute;width:450px;background:{C['panel']};border-radius:18px}}
.rank{{position:absolute;width:80px;display:flex;align-items:center;justify-content:center;font-family:BHS;font-size:52px}}
.name{{position:absolute;display:flex;align-items:center;font-weight:700;font-size:38px;white-space:nowrap}}
</style></head><body>
<div class="a" style="left:80px;top:250px;width:420px;height:56px;border-radius:28px;background:{C['accent']};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:26px;color:{C['bg']}">{esc(D['badge'])}</div>
<div class="a bhs fit" data-max="920" style="left:80px;top:330px;font-size:116px;line-height:1.2">{esc(D['title'])}</div>
<div id="top" class="a bhs" style="left:80px;top:470px;font-size:116px;line-height:1.2;color:{C['gold']}">TOP {N}</div>
<div id="stat" class="a" style="top:520px;right:80px;font-weight:500;font-size:28px;line-height:1.45;color:{C['sub']};text-align:right">{esc(D['stat'])}</div>
<div class="a" style="left:80px;top:640px;width:920px;height:190px;border-radius:28px;background:{C['panel']};border:3px solid {C['gold']}"></div>
<svg class="a" style="left:118px;top:690px" width="110" height="70" viewBox="0 0 110 70"><path d="M 0 70 L 10 10 L 35 40 L 55 0 L 75 40 L 100 10 L 110 70 Z" fill="{C['gold']}"/></svg>
<div class="a bhs" style="left:120px;top:768px;width:110px;text-align:center;font-size:34px;color:{C['gold']}">1위</div>
<div class="a bhs" style="left:262px;top:650px;font-size:150px;line-height:1.1;color:{C['gold']}">?</div>
<div id="hint" class="a" style="left:500px;top:688px;width:470px;font-weight:700;font-size:36px;line-height:1.3;text-align:right;white-space:normal;word-break:keep-all">{esc(D['hint'])}</div>
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

def main(src, out):
    D = json.loads(pathlib.Path(src).read_text(encoding='utf-8'))
    page_html = build(D)
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
