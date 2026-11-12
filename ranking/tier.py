# 과몰입 티어표(유형 T, 만드는법.md 2-2절) 그림 1장(1080×1920 PNG). 판정은 Claude 가 한다(공식 순위 아님)
# 쓰는 법: python3 ranking/tier.py <자료.json> <결과.png>
# 자료: {"badge": "과몰입 티어표 #4", "title": "오디션 예능", "title2": "레전드 티어", "image": "사진.jpg"(자료 옆, Unsplash 가로 사진),
#        "pos": "50% 40%"(사진 자르는 위치), "tiers": {"S": [..2], "A": [..3], "B": [..4], "C": [..3~4]}, "cta": "고르기 쉬운 질문 한 줄"}
# 이미지에 "기준:" 줄 · "공식 순위가 아니라…" 꼬리말은 넣지 않는다(Gyan 2026-11-12). 기준은 캡션에 쓴다
import sys
import html, json, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
FONTS = HERE / 'fonts'  # ranking/fonts
C = dict(bg='#FFF7EB', panel='#FFFFFF', line='#F0E2CC', ink='#211A14', sub='#8A7461', gold='#F5A300',
         silver='#8E979F', bronze='#C8702E', accent='#FF6A13')
TIERCOL = {'S': C['gold'], 'A': C['accent'], 'B': C['silver'], 'C': C['bronze']}
def esc(s): return html.escape(str(s)).replace('\n', '<br>')

def page(e):
    rows = ''
    for t, names in e['tiers']:
        col = TIERCOL[t]
        chips = ''.join(f'<span class="chip">{esc(n)}</span>' for n in names)
        rows += (f'<div class="row"><div class="lab" style="background:{col}"><div class="bhs" style="font-size:100px;line-height:1">{t}</div></div>'
                 f'<div class="box" style="border-color:{col}">{chips}</div></div>')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:BHS;src:url("{(FONTS/'BlackHanSans-Regular.ttf').as_uri()}")}}
@font-face{{font-family:NSK;src:url("{(FONTS/'NotoSansKR-wght.ttf').as_uri()}");font-weight:100 900}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:{C['bg']};position:relative;overflow:hidden;font-family:NSK;color:{C['ink']}}}
.a{{position:absolute;white-space:nowrap}} .bhs{{font-family:BHS;font-weight:400}}
#tiers{{position:absolute;left:80px;top:690px;width:920px;display:flex;flex-direction:column;gap:24px}}
.row{{display:flex;min-height:170px}}
.lab{{width:150px;border-radius:24px 0 0 24px;display:flex;align-items:center;justify-content:center;color:#fff}}
.box{{flex:1;border:3px solid;border-left:none;border-radius:0 24px 24px 0;background:#FFFDF8;padding:22px 10px 8px 22px;display:flex;flex-wrap:wrap;align-content:center}}
.chip{{display:inline-flex;align-items:center;height:70px;padding:0 26px;margin:0 12px 14px 0;border-radius:35px;background:{C['panel']};border:2px solid {C['line']};font-weight:800;font-size:36px}}
</style></head><body>
<div class="a" style="left:0;top:0;width:1080px;height:600px;background:url('{e['img_uri']}') {e['pos']}/cover"></div>
<div class="a" style="left:0;top:120px;width:1080px;height:482px;background:linear-gradient(to bottom,rgba(255,247,235,0),rgba(255,247,235,.82) 45%,{C['bg']} 100%)"></div>
<div class="a" style="left:80px;top:250px;height:56px;padding:0 30px;border-radius:28px;background:{C['accent']};display:flex;align-items:center;font-weight:700;font-size:28px;color:#fff">{esc(e['badge'])}</div>
<div class="a bhs" style="left:80px;top:340px;font-size:110px;text-shadow:0 0 18px #FFF7EB;line-height:1.2">{esc(e['title'])}</div>
<div class="a bhs" style="left:80px;top:472px;font-size:104px;line-height:1.2;color:{C['gold']}">{esc(e['title2'])}</div>
<div id="tiers">{rows}</div>
<div id="cta" class="a" style="left:80px;top:1600px;width:920px;text-align:center;font-weight:800;font-size:40px;color:{C['accent']}">{esc(e['cta'])}</div>
</body></html>'''

def main(src, out):
    e = json.loads(pathlib.Path(src).read_text(encoding='utf-8'))
    e['img_uri'] = (pathlib.Path(src).resolve().parent / e['image']).as_uri()
    e['tiers'] = [(t, e['tiers'][t]) for t in 'SABC']
    h = pathlib.Path(out).with_suffix('.html'); h.write_text(page(e), encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        pg.goto(h.resolve().as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400)
        bottom = pg.evaluate("document.getElementById('tiers').getBoundingClientRect().bottom")
        over = pg.evaluate('''() => [...document.querySelectorAll('.a,.chip')].filter(e=>{const r=e.getBoundingClientRect();return r.right>1080||r.bottom>1920||r.left<0}).length''')
        pg.screenshot(path=out); b.close()
    h.unlink()
    if bottom > 1580 or over: sys.exit(f'티어 칸이 CTA 와 겹치거나(아래 끝 {bottom:.0f}px > 1580) 화면 밖 {over}개 — 이름 수를 줄일 것')
    print('그림', out, '티어 아래 끝', round(bottom))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
