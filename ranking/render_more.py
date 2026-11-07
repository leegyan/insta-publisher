# render.py 의 추가 모양 8가지(Gyan 2026-11-07 시안 8개 통과). render.py 가 "layout" 값으로 불러 쓴다. 자료 형식: 만드는법.md 2절
# podium 시상대 · bars 막대그래프 · vs 1위 vs 2위 맞히기 · tiers 티어표 · map 시도 타일 지도 · line 연도 꺾은선 · gauge 온도계 눈금 · quiz 4지선다
# + dots 100명 도트 · donut 도넛 점유율 · receipt 그때 vs 지금 영수증 · board 점수판 · agebars 나이대 세로 막대 · korea 한국은 몇 위
import html, math, sys, pathlib

C = dict(bg='#FFF7EB', panel='#FFFFFF', line='#F0E2CC', ink='#211A14', sub='#8A7461', gold='#F5A300',
         silver='#8E979F', bronze='#C8702E', accent='#FF6A13', pale='#FFF3D6')
CROWN = '<svg class="a" style="left:{x}px;top:{y}px" width="{w}" height="{h}" viewBox="0 0 110 70"><path d="M 0 70 L 10 10 L 35 40 L 55 0 L 75 40 L 100 10 L 110 70 Z" fill="{c}"/></svg>'
SIDO = [('인천', 0, 0), ('서울', 1, 0), ('경기', 2, 0), ('강원', 3, 0), ('충남', 0, 1), ('세종', 1, 1), ('충북', 2, 1), ('경북', 3, 1),
        ('전북', 0, 2), ('대전', 1, 2), ('대구', 2, 2), ('울산', 3, 2), ('광주', 0, 3), ('전남', 1, 3), ('경남', 2, 3), ('부산', 3, 3), ('제주', 1, 4)]

def esc(s): return html.escape(str(s)).replace('\n', '<br>')
def name_of(it): return it if isinstance(it, str) else it[0]
def need(cond, msg):
    if not cond: sys.exit(msg)

def page(D, body, cta_default, src_dir, fonts, img_at=(690, 170, 330)):
    t2 = D.get('title2')
    title_max = 600 if D.get('image') else 920
    hero = ''
    if D.get('image'):
        f = (src_dir / D['image']).resolve(); need(f.exists(), f'그림 없음: {f}'); x, y, s = img_at
        hero = (f'<img class="a" src="{f.as_uri()}" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px;object-fit:contain;mix-blend-mode:multiply;'
                f'-webkit-mask-image:radial-gradient(closest-side,#000 62%,transparent 100%);mask-image:radial-gradient(closest-side,#000 62%,transparent 100%)">')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:BHS;src:url("{(fonts/'BlackHanSans-Regular.ttf').as_uri()}")}}
@font-face{{font-family:NSK;src:url("{(fonts/'NotoSansKR-wght.ttf').as_uri()}");font-weight:100 900}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:{C['bg']};position:relative;overflow:hidden;font-family:NSK;color:{C['ink']}}}
.a{{position:absolute;white-space:nowrap}} .bhs{{font-family:BHS;font-weight:400}}
.chip{{display:inline-flex;align-items:center;height:64px;padding:0 24px;margin:0 12px 14px 0;border-radius:32px;background:{C['panel']};border:2px solid {C['line']};font-weight:700;font-size:32px}}
</style></head><body>
<div class="a" style="left:80px;top:250px;width:420px;height:56px;border-radius:28px;background:{C['accent']};display:flex;align-items:center;justify-content:center;font-weight:700;font-size:26px;color:#fff">{esc(D['badge'])}</div>
{hero}
<div class="a bhs fit" data-max="{title_max}" style="left:80px;top:330px;font-size:104px;line-height:1.2">{esc(D['title'])}</div>
{f'<div class="a bhs fit" data-max="{title_max}" style="left:80px;top:462px;font-size:104px;line-height:1.2;color:{C["gold"]}">{esc(t2)}</div>' if t2 else ''}
{body}
<div class="a" style="left:80px;top:1610px;width:920px;text-align:center;font-weight:700;font-size:34px;color:{C['accent']}">{esc(D.get('cta') or cta_default)}</div>
<div class="a" style="left:80px;top:1680px;width:920px;text-align:center;font-weight:400;font-size:19px;line-height:1.45;color:{C['sub']};white-space:normal;word-break:keep-all">{esc(D['source'])}</div>
<script>
document.fonts.ready.then(()=>{{
  for (const el of document.querySelectorAll('.fit')) {{ const m=+el.dataset.max; let fs=parseFloat(getComputedStyle(el).fontSize);
    while (el.scrollWidth>m && fs>12) {{ fs-=2; el.style.fontSize=fs+'px'; }} }}
  document.body.dataset.ready='1';
}});
</script></body></html>'''

def items_check(D, lo=10, hi=15):
    it = D['items']; need(lo <= len(it) <= hi, f'items 는 {lo}~{hi}개: {len(it)}'); return it

def podium(D, src, fonts):
    # 시상대: 1 · 2 · 3위 단상(1위 가림) + 4~N위 칩. items 10~15, hint 한 줄
    it = items_check(D); g = C['gold']; out = []
    for rank, x, h, col in [(2, 90, 300, C['silver']), (1, 390, 400, g), (3, 690, 230, C['bronze'])]:
        y = 1180 - h; nm = '?' if rank == 1 else name_of(it[rank - 1])
        out.append(f'<div class="a" style="left:{x}px;top:{y}px;width:300px;height:{h}px;border-radius:20px 20px 0 0;background:{col};display:flex;justify-content:center;padding-top:18px;font-family:BHS;font-size:90px;color:#fff">{rank}</div>')
        out.append(f'<div class="a bhs fit" data-max="300" style="left:{x}px;top:{y - (175 if rank == 1 else 70)}px;width:300px;text-align:center;font-size:{130 if rank == 1 else 44}px;color:{g if rank == 1 else C["ink"]}">{esc(nm)}</div>')
    out.append(f'<div class="a" style="left:80px;top:1180px;width:920px;height:6px;background:{C["ink"]}"></div>')
    out.append(f'<div class="a fit" data-max="920" style="left:80px;top:1210px;width:920px;text-align:center;font-weight:700;font-size:34px">{esc(D["hint"])}</div>')
    chips = ''.join(f'<span class="chip"><b class="bhs" style="color:{C["sub"]};margin-right:12px">{i + 4}</b>{esc(name_of(n))}</span>' for i, n in enumerate(it[3:]))
    out.append(f'<div class="a" style="left:80px;top:1285px;width:940px;white-space:normal;font-size:0">{chips}</div>')
    return page(D, ''.join(out), '1위는 어디일까요?  정답은 캡션에', src, fonts)

def bars(D, src, fonts):
    # 막대그래프: rows [["이름", "값 글자", 수치], …] 큰 값부터 6~10개. 1위 이름은 hide1 글자(기본 "? ? ?")로 가림
    rows = D['rows']; need(6 <= len(rows) <= 10, f'bars rows 는 6~10개: {len(rows)}')
    vals = [r[2] for r in rows]; need(vals == sorted(vals, reverse=True), 'bars rows 는 큰 값부터')
    top = 660; rh = min(92, 920 // len(rows)); mx = vals[0]; out = []
    for i, (k, vs, v) in enumerate(rows):
        y = top + i * rh; w = max(16, int(560 * v / mx)); first = i == 0
        col = C['gold'] if first else C['accent'] if i < 3 else '#F2C9A8'
        rc = C['gold'] if first else C['silver'] if i == 1 else C['bronze'] if i == 2 else C['sub']
        out.append(f'<div class="a bhs" style="left:70px;top:{y}px;width:70px;height:72px;display:flex;align-items:center;justify-content:center;font-size:48px;color:{rc}">{i + 1}</div>'
                   f'<div class="a fit" data-max="200" style="left:150px;top:{y}px;width:200px;height:72px;display:flex;align-items:center;font-weight:800;font-size:34px;color:{C["gold"] if first else C["ink"]}">{esc(D.get("hide1", "? ? ?") if first else k)}</div>'
                   f'<div class="a" style="left:360px;top:{y + 10}px;width:{w}px;height:52px;border-radius:0 26px 26px 0;background:{col}"></div>'
                   f'<div class="a bhs" style="left:{370 + w}px;top:{y}px;height:72px;display:flex;align-items:center;font-size:38px">{esc(vs)}</div>')
    return page(D, ''.join(out), '1위는 어디일까요?  정답은 캡션에', src, fonts)

def vs(D, src, fonts):
    # 1위 vs 2위 맞히기(Gyan 2026-11-07 "1위와 2위로"): 두 이름을 가나다순으로 놓아 순서로 답이 새지 않게 한다. 목록에서는 1 · 2위를 가림
    it = items_check(D); g = C['gold']; out = []
    pair = sorted([name_of(it[0]), name_of(it[1])])
    for x, nm in zip([80, 580], pair):
        out.append(f'<div class="a" style="left:{x}px;top:640px;width:420px;height:330px;border-radius:32px;background:{C["panel"]};border:4px solid {g};display:flex;flex-direction:column;align-items:center;justify-content:center">'
                   f'<div class="fit" data-max="380" style="font-weight:800;font-size:52px">{esc(nm)}</div><div class="bhs" style="font-size:110px;color:{g};margin-top:6px">?위</div></div>')
    out.append(f'<div class="a bhs" style="left:460px;top:735px;width:160px;height:160px;border-radius:80px;background:{C["accent"]};color:#fff;font-size:76px;line-height:160px;text-align:center;border:8px solid {C["bg"]}">VS</div>')
    out.append(f'<div class="a fit" data-max="920" style="left:80px;top:1000px;width:920px;text-align:center;font-weight:700;font-size:36px">{esc(D.get("hint") or "1위와 2위, 누가 1위일까요?")}</div>')
    half = -(-len(it) // 2); rh = min(64, 470 // half)
    for i, n in enumerate(it):
        hide = i < 2; col = 0 if i < half else 1; r = i if i < half else i - half; x = [80, 550][col]; y = 1075 + r * rh
        out.append(f'<div class="a" style="left:{x}px;top:{y}px;width:450px;height:{rh - 10}px;border-radius:14px;background:{C["pale"] if hide else C["panel"]};border:2px {"dashed " + g if hide else "solid " + C["line"]};display:flex;align-items:center;padding-left:18px;font-weight:700;font-size:30px">'
                   f'<b class="bhs" style="width:56px;color:{g if hide else C["sub"]}">{i + 1}</b>{"? ? ?" if hide else esc(name_of(n))}</div>')
    return page(D, ''.join(out), '누가 1위일까요? 댓글로 골라 주세요', src, fonts)

def tiers(D, src, fonts):
    # 티어표: 등급 = 순위 구간(S 1~2 · A 3~5 · B 6~9 · C 10~N). 등급 이름을 순위 말고 다른 근거로 나누지 않는다. S 첫 칸(1위) 가림
    it = items_check(D); groups = [('S', 0, 2, C['gold']), ('A', 2, 5, C['accent']), ('B', 5, 9, C['silver']), ('C', 9, len(it), C['bronze'])]
    # 칸 높이는 브라우저가 칩 줄 수에 맞춰 정한다(최소 180px, 칩은 위아래 · 줄 가운데 맞춤). 예전엔 이름 4개를 한 줄로 어림해
    # 6개가 한 줄에 들어가도 2줄 높이(250px)로 잡고 칩이 위로 붙었다(Gyan 2026-11-07 지적). 아래 글(1590px)과 겹치면 render.py 가 멈춘다(data-maxbottom)
    out = []
    for t, a, b, col in groups:
        chips = ''.join(f'<span class="chip" style="margin:0;{"background:" + C["pale"] + ";border:3px dashed " + C["gold"] + ";color:" + C["gold"] if (a + j == 0) else ""}">{"? ? ?" if a + j == 0 else esc(name_of(n))}</span>' for j, n in enumerate(it[a:b]))
        out.append(f'<div style="display:flex;min-height:180px">'
                   f'<div style="width:150px;flex:none;border-radius:24px 0 0 24px;background:{col};display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff">'
                   f'<div class="bhs" style="font-size:96px;line-height:1">{t}</div><div style="font-weight:700;font-size:24px">{a + 1}~{b}위</div></div>'
                   f'<div style="flex:1;border-radius:0 24px 24px 0;background:#FFFDF8;border:3px solid {col};padding:28px 0 28px 22px;display:flex;flex-wrap:wrap;align-content:center;align-items:center;gap:14px 12px;white-space:normal;font-size:0">{chips}</div></div>')
    out = [f'<div class="a" data-maxbottom="1590" style="left:80px;top:640px;width:920px;display:flex;flex-direction:column;gap:26px;white-space:normal">{"".join(out)}</div>']
    return page(D, ''.join(out), 'S티어 첫 자리는 어디일까요?  정답은 캡션에', src, fonts)

def tile_map(D, src, fonts):
    # 시도 타일 지도: regions {"서울": ["값 글자", 순위], …} 17개 시도 모두. 진할수록 높은 순위, 1위 칸은 "?"로 가림(hide1: false 면 보임)
    R = D['regions']; need(set(R) == {s[0] for s in SIDO}, f'map regions 는 17개 시도 이름 그대로: 빠짐 {sorted({s[0] for s in SIDO} - set(R))} · 남음 {sorted(set(R) - {s[0] for s in SIDO})}')
    ranks = sorted(r[1] for r in R.values()); out = []; S = 215; hide1 = D.get('hide1', True); worst = max(ranks)
    for n, cx, cy in SIDO:
        val, r = R[n]; t = (r - 1) / max(1, worst - 1)
        bg = C['gold'] if r == 1 else f'rgba(255,106,19,{0.85 - 0.72 * t:.2f})'; fg = '#fff' if (r == 1 or t < 0.45) else C['ink']
        mid = '?' if (r == 1 and hide1) else f'{r}위'
        out.append(f'<div class="a" style="left:{110 + cx * (S + 10)}px;top:{640 + cy * (S - 20)}px;width:{S}px;height:{S - 30}px;border-radius:22px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;color:{fg}">'
                   f'<div style="font-weight:800;font-size:36px;line-height:1.1">{n} <span class="bhs" style="font-size:36px">{mid}</span></div>'
                   f'<div class="bhs fit" data-max="200" style="font-size:34px;line-height:1.2;opacity:.9">{"" if (r == 1 and hide1) else esc(val)}</div></div>')
    out.append(f'<div class="a" style="left:560px;top:1460px;width:440px;text-align:right;font-weight:600;font-size:26px;color:{C["sub"]}">{esc(D.get("legend") or "진할수록 높은 순위")}</div>')
    return page(D, ''.join(out), '우리 동네는 몇 위인가요? 댓글로 알려주세요', src, fonts)

def line(D, src, fonts):
    # 연도 꺾은선: points [["2017", "6,470원", 6470], …] 옛날부터 5~12개. 마지막 값은 hide_last 글자(기본 "?")로 가림. label_every 칸마다 값 글자
    P = D['points']; n = len(P); need(5 <= n <= 12, f'line points 는 5~12개: {n}')
    vs_ = [p[2] for p in P]; lo, hi = min(vs_), max(vs_); pad = (hi - lo) * 0.12 or 1; lo -= pad; hi += pad
    X0, X1, Y0, Y1 = 150, 960, 1450, 760
    px = lambda i: X0 + (X1 - X0) * i / (n - 1); py = lambda v: Y0 - (Y0 - Y1) * (v - lo) / (hi - lo)
    pts = ' '.join(f'{px(i):.0f},{py(v):.0f}' for i, v in enumerate(vs_))
    svg = [f'<svg class="a" style="left:0;top:0" width="1080" height="1920"><polyline points="{pts}" fill="none" stroke="{C["accent"]}" stroke-width="8" stroke-linejoin="round"/>']
    for i, v in enumerate(vs_):
        last = i == n - 1
        svg.append(f'<circle cx="{px(i):.0f}" cy="{py(v):.0f}" r="{22 if last else 12}" fill="{C["gold"] if last else C["accent"]}" stroke="#fff" stroke-width="5"/>')
    svg.append(f'<line x1="{X0}" y1="{Y0 + 30}" x2="{X1}" y2="{Y0 + 30}" stroke="{C["line"]}" stroke-width="4"/></svg>')
    every = D.get('label_every', 3); lab = []
    for i, (k, vs1, v) in enumerate(P):
        big = i % every == 0 or i == n - 1
        lab.append(f'<div class="a" style="left:{px(i) - 60:.0f}px;top:{Y0 + 46}px;width:120px;text-align:center;font-weight:700;font-size:{26 if big else 22}px;color:{C["ink"] if big else C["sub"]}">{esc(k)}</div>')
        if i % every == 0 and i < n - 1:
            lab.append(f'<div class="a bhs" style="left:{px(i) - 110:.0f}px;top:{py(v) - 78:.0f}px;width:220px;text-align:center;font-size:40px">{esc(vs1)}</div>')
    lab.append(f'<div class="a bhs" style="left:{px(n - 1) - 250:.0f}px;top:{py(vs_[-1]) - 150:.0f}px;width:280px;height:96px;border-radius:24px;background:{C["gold"]};color:#fff;font-size:60px;line-height:96px;text-align:center">{esc(D.get("hide_last", "?"))}</div>')
    return page(D, ''.join(svg) + ''.join(lab), '올해는 얼마일까요?  정답은 캡션에', src, fonts)

def gauge(D, src, fonts):
    # 온도계 눈금: marks [["값 글자", "설명", 위치 수치], …] 위(큰 값)부터 4~8개. scale "log" | "linear". highlight = 강조할 눈금 번호(0부터)
    M = D['marks']; need(4 <= len(M) <= 8, f'gauge marks 는 4~8개: {len(M)}')
    pos_v = [m[2] for m in M]; need(pos_v == sorted(pos_v, reverse=True), 'gauge marks 는 큰 값부터')
    lg = D.get('scale', 'log') == 'log'; f = (lambda v: math.log(v)) if lg else (lambda v: v)
    a, b = f(pos_v[-1]), f(pos_v[0]); span = (b - a) or 1; a -= span * 0.08; b += span * 0.08
    YT, YB = 680, 1460; pos = lambda v: YB - (YB - YT) * (f(v) - a) / (b - a); hl = D.get('highlight', -1)
    out = [f'<div class="a" style="left:180px;top:{YT - 20}px;width:90px;height:{YB - YT + 40}px;border-radius:45px;background:linear-gradient(to top,#FFE2C2,{C["accent"]} 55%,{C["gold"]});border:5px solid #fff;box-shadow:0 0 0 3px {C["line"]}"></div>',
           f'<div class="a" style="left:160px;top:{YB + 10}px;width:130px;height:130px;border-radius:65px;background:#FFE2C2;border:5px solid #fff;box-shadow:0 0 0 3px {C["line"]}"></div>']
    for i, (v, n, p) in enumerate(M):
        y = pos(p); mid = i == hl
        out.append(f'<div class="a" style="left:270px;top:{y - 3:.0f}px;width:{90 if mid else 50}px;height:6px;background:{C["ink"] if mid else C["sub"]}"></div>'
                   f'<div class="a bhs" style="left:{380 if mid else 340}px;top:{y - 34:.0f}px;font-size:{60 if mid else 48}px;color:{C["accent"] if mid else C["ink"]}">{esc(v)}</div>'
                   f'<div class="a fit" data-max="{380 if mid else 420}" style="left:{700 if mid else 640}px;top:{y - 22:.0f}px;font-weight:700;font-size:{30 if mid else 26}px;color:{C["ink"] if mid else C["sub"]}">{esc(n)}</div>')
    return page(D, ''.join(out), '나는 눈금 어디쯤일까요? 댓글로 알려주세요', src, fonts)

def quiz(D, src, fonts):
    # 4지선다: 2~5위를 보여 주고 1위를 보기 4개에서 고르게 함. choices 4개에 1위가 꼭 있고 2~5위 이름은 없어야 함(답이 새지 않게)
    it = items_check(D); ch = D['choices']; first = name_of(it[0]); shown = [name_of(x) for x in it[1:5]]
    need(len(ch) == 4 and first in ch, 'quiz choices 는 4개이고 1위 이름이 들어 있어야 함')
    need(not set(ch) & set(shown), f'quiz choices 에 2~5위 이름이 있으면 안 됨: {set(ch) & set(shown)}')
    need(all(c in [name_of(x) for x in it] for c in ch), 'quiz choices 는 items 안의 이름만(자료에 없는 보기를 지어내지 않음)')
    g = C['gold']; out = []
    for i, n in enumerate(shown):
        x = 80 + (i % 2) * 470; y = 640 + (i // 2) * 84
        out.append(f'<div class="a" style="left:{x}px;top:{y}px;width:450px;height:70px;border-radius:16px;background:{C["panel"]};border:2px solid {C["line"]};display:flex;align-items:center;padding-left:20px;font-weight:700;font-size:32px">'
                   f'<b class="bhs" style="width:60px;color:{[C["silver"], C["bronze"], C["sub"], C["sub"]][i]}">{i + 2}</b><span class="fit" data-max="360">{esc(n)}</span></div>')
    out.append(f'<div class="a" style="left:80px;top:830px;width:920px;height:690px;border-radius:36px;background:{C["panel"]};border:4px solid {g}"></div>'
               + CROWN.format(x=150, y=880, w=90, h=57, c=g) + f'<div class="a bhs" style="left:260px;top:872px;font-size:62px">1위는 몇 번일까요?</div>')
    for i, n in enumerate(ch):
        y = 990 + i * 125
        out.append(f'<div class="a" style="left:140px;top:{y}px;width:800px;height:105px;border-radius:52px;background:{C["pale"]};display:flex;align-items:center;font-weight:800;font-size:44px">'
                   f'<span class="bhs" style="width:105px;height:105px;border-radius:52px;background:{g};color:#fff;font-size:58px;line-height:105px;text-align:center;margin-right:34px">{i + 1}</span><span class="fit" data-max="620">{esc(n)}</span></div>')
    return page(D, ''.join(out), '정답 번호를 댓글로!  정답은 캡션에', src, fonts)

LAYOUTS = {'podium': podium, 'bars': bars, 'vs': vs, 'tiers': tiers, 'map': tile_map, 'line': line, 'gauge': gauge, 'quiz': quiz}

# ---- 추가 6가지(Gyan 2026-11-07 시안 9~14 통과): dots · donut · receipt · board · agebars · korea ----
def dots(D, src, fonts):
    # 100명 도트: pct(0~100 정수, 자료의 비율을 반올림) 칸을 금색으로. big = 가릴 글자(기본 "??명"), question = 아래 한 줄
    pct = D['pct']; need(isinstance(pct, int) and 0 < pct < 100, 'dots pct 는 1~99 정수')
    out = []
    for i in range(100):
        r, c = divmod(i, 10)
        out.append(f'<div class="a" style="left:{150 + c * 80}px;top:{650 + r * 72}px;width:56px;height:56px;border-radius:28px;background:{C["gold"] if i < pct else "#EADCC8"}"></div>')
    out.append(f'<div class="a" style="left:80px;top:1395px;width:920px;text-align:center;font-weight:800;font-size:44px">{esc(D.get("lead", "노란 칸이"))} <span class="bhs" style="font-size:64px;color:{C["accent"]}">{esc(D.get("big", "??명"))}</span></div>')
    out.append(f'<div class="a fit" data-max="920" style="left:80px;top:1480px;width:920px;text-align:center;font-weight:600;font-size:28px;color:{C["sub"]}">{esc(D["question"])}</div>')
    return page(D, ''.join(out), '정답은 캡션에', src, fonts)

def donut(D, src, fonts):
    # 도넛 점유율: slices [["이름", 비율 수치, "비율 글자"], …] 큰 것부터 3~7개(합 100 이하, 남는 몫은 "그 밖"으로 그림). 첫 조각(1위) 이름은 가림
    S = D['slices']; need(3 <= len(S) <= 7, 'donut slices 는 3~7개'); tot = sum(x[1] for x in S); need(tot <= 100.5, f'donut 합 {tot} > 100')
    need([x[1] for x in S] == sorted([x[1] for x in S], reverse=True), 'donut slices 는 큰 것부터')
    cols = [C['gold'], C['accent'], '#F2A66E', C['bronze'], C['silver'], '#C9B79F', '#DCC9AE']
    S = [(x[0], x[1], x[2] if len(x) > 2 else f'{x[1]}%', cols[i]) for i, x in enumerate(S)]
    if tot < 99.5: S.append(('그 밖', 100 - tot, f'{100 - tot:.0f}%', '#E8DCCB'))
    cx, cy, R, r = 540, 1030, 330, 190; a0 = -90; segs = []
    pt = lambda a, rr: (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)))
    for nm, v, vs_, col in S:
        a1 = a0 + 360 * v / 100; la = 1 if a1 - a0 > 180 else 0
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = pt(a0, R), pt(a1, R), pt(a1, r), pt(a0, r)
        segs.append(f'<path d="M{x1:.0f},{y1:.0f} A{R},{R} 0 {la} 1 {x2:.0f},{y2:.0f} L{x3:.0f},{y3:.0f} A{r},{r} 0 {la} 0 {x4:.0f},{y4:.0f} Z" fill="{col}" stroke="{C["bg"]}" stroke-width="6"/>')
        if v >= 6:
            tx, ty = pt((a0 + a1) / 2, (R + r) / 2)
            segs.append(f'<text x="{tx:.0f}" y="{ty + 14:.0f}" text-anchor="middle" font-family="BHS" font-size="{44 if v > 12 else 30}" fill="#fff">{esc(vs_)}</text>')
        a0 = a1
    body = f'<svg class="a" style="left:0;top:0" width="1080" height="1920">{"".join(segs)}</svg>'
    body += f'<div class="a" style="left:{cx - 150}px;top:{cy - 70}px;width:300px;text-align:center"><div class="bhs" style="font-size:96px;color:{C["gold"]};line-height:1">?</div><div style="font-weight:800;font-size:32px">{esc(D.get("center", "1위"))}</div></div>'
    leg = ''.join(f'<span style="display:inline-flex;align-items:center;margin:0 18px 12px 0;font-weight:700;font-size:30px"><i style="width:26px;height:26px;border-radius:13px;background:{col};margin-right:10px"></i>{"? ? ?" if i == 0 else esc(nm)}</span>' for i, (nm, v, vs_, col) in enumerate(S))
    body += f'<div class="a" style="left:80px;top:1400px;width:920px;white-space:normal;text-align:center">{leg}</div>'
    return page(D, body, '1위는 어디일까요?  정답은 캡션에', src, fonts)

def receipt(D, src, fonts):
    # 그때 vs 지금 영수증: left · right = {"label": "2017년", "rows": [["시간당", "6,470원"], …]} 1~3줄. right 값은 "?"로 가림(hide_right: false 면 보임)
    L, Rr = D['left'], D['right']; need(1 <= len(L['rows']) <= 3 and len(L['rows']) == len(Rr['rows']), 'receipt rows 는 양쪽 같은 수 1~3줄')
    hide = D.get('hide_right', True); out = []
    for x, side, h in [(80, L, False), (570, Rr, hide)]:
        out.append(f'<div class="a" style="left:{x}px;top:660px;width:430px;height:640px;background:#fff;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.08)"></div>'
                   f'<div class="a fit" data-max="430" style="left:{x}px;top:700px;width:430px;text-align:center;font-weight:800;font-size:30px;color:{C["sub"]}">{esc(D.get("head", "영수증"))}</div>'
                   f'<div class="a" style="left:{x + 40}px;top:760px;width:350px;border-top:3px dashed {C["line"]}"></div>'
                   f'<div class="a bhs fit" data-max="430" style="left:{x}px;top:800px;width:430px;text-align:center;font-size:72px">{esc(side["label"])}</div>')
        for j, (k, v) in enumerate(side['rows']):
            y = 930 + j * 90
            out.append(f'<div class="a" style="left:{x + 40}px;top:{y}px;width:350px;display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:30px"><span>{esc(k)}</span>'
                       f'<span class="bhs" style="font-size:{52 if j == 0 else 40}px;color:{C["gold"] if h else C["ink"]}">{"?" if h else esc(v)}</span></div>')
        out.append(f'<div class="a" style="left:{x + 40}px;top:1220px;width:350px;border-top:3px dashed {C["line"]}"></div>')
    out.append(f'<div class="a bhs" style="left:490px;top:930px;width:100px;text-align:center;font-size:80px;color:{C["accent"]}">→</div>')
    out.append(f'<div class="a fit" data-max="920" style="left:80px;top:1360px;width:920px;text-align:center;font-weight:700;font-size:36px">{esc(D["question"])}</div>')
    return page(D, ''.join(out), '얼마일까요?  정답은 캡션에', src, fonts)

def board(D, src, fonts):
    # 점수판: cols ["이름 칸 제목", "값1 제목", …(값 칸 1~3개)], rows [["이름", "값1", …], …] 순위대로 6~10개. 1위 이름은 가림. 첫 값 칸이 순위 기준
    cols = D['cols']; rows = D['rows']; nv = len(cols) - 1
    need(1 <= nv <= 3, 'board cols 는 이름 + 값 1~3칸'); need(6 <= len(rows) <= 10, 'board rows 는 6~10개'); need(all(len(r) == nv + 1 for r in rows), 'board rows 칸 수가 cols 와 다름')
    wn = 400 if nv == 1 else 330 if nv == 2 else 270; wv = (820 - wn) // nv; rh = min(80, 860 // len(rows))
    head = ''.join(f'<span style="width:{wv}px;text-align:right">{esc(c)}</span>' for c in cols[1:])
    out = [f'<div class="a" style="left:60px;top:640px;width:960px;height:84px;border-radius:20px 20px 0 0;background:{C["ink"]};display:flex;align-items:center;color:#fff;font-weight:800;font-size:28px">'
           f'<span style="width:110px;text-align:center">순위</span><span style="width:{wn}px">{esc(cols[0])}</span>{head}</div>']
    for i, r in enumerate(rows):
        y = 724 + i * rh; first = i == 0
        vals = ''.join(f'<span class="{"bhs" if j == 0 else ""}" style="width:{wv}px;text-align:right;{"font-size:38px;color:" + C["accent"] if j == 0 else "color:" + C["sub"]}">{esc(v)}</span>' for j, v in enumerate(r[1:]))
        out.append(f'<div class="a" style="left:60px;top:{y}px;width:960px;height:{rh}px;background:{C["pale"] if first else (C["panel"] if i % 2 else "#FFFBF4")};border-bottom:2px solid {C["line"]};display:flex;align-items:center;font-weight:700;font-size:32px">'
                   f'<span class="bhs" style="width:110px;text-align:center;font-size:44px;color:{[C["gold"], C["silver"], C["bronze"]][i] if i < 3 else C["sub"]}">{i + 1}</span>'
                   f'<span class="fit" data-max="{wn}" style="width:{wn}px;overflow:hidden;color:{C["gold"] if first else C["ink"]}">{"? ? ?" if first else esc(r[0])}</span>{vals}</div>')
    return page(D, ''.join(out), '1위는 어디일까요?  정답은 캡션에', src, fonts)

def agebars(D, src, fonts):
    # 나이대 세로 막대: bars [["25~29", "290만", 290], …] 나이 순서대로 4~8개. highlight = 강조할 나이대 이름 목록(기본 25~29 · 30~34 · 25~34 가운데 있는 것)
    #   hide_highlight(기본 true) 면 강조 막대 값 글자를 "?"로 가림. 가장 큰 값 막대는 금색. note = 위쪽 알약 글자
    B = D['bars']; need(4 <= len(B) <= 8, 'agebars bars 는 4~8개')
    hl = D.get('highlight') or [b[0] for b in B if b[0] in ('25~29', '30~34', '25~34', '25~29세', '30~34세', '25~34세')]
    mx = max(b[2] for b in B) * 1.08; n = len(B); gap = 920 // n; w = int(gap * 0.8); base = 1440; H = 640; out = []
    for i, (k, vs_, v) in enumerate(B):
        x = 80 + i * gap + (gap - w) // 2; h = int(H * v / mx); me = k in hl; top = v == max(b[2] for b in B)
        col = C['accent'] if me else C['gold'] if top else '#EADCC8'
        out.append(f'<div class="a" style="left:{x}px;top:{base - h}px;width:{w}px;height:{h}px;border-radius:18px 18px 0 0;background:{col}"></div>'
                   f'<div class="a bhs" style="left:{x - 30}px;top:{base - h - 56}px;width:{w + 60}px;text-align:center;font-size:34px;color:{C["accent"] if me else C["ink"]}">{"?" if (me and D.get("hide_highlight", True)) else esc(vs_)}</div>'
                   f'<div class="a" style="left:{x - 30}px;top:{base + 14}px;width:{w + 60}px;text-align:center;font-weight:800;font-size:26px;line-height:1.2;white-space:normal">{esc(k)}</div>')
    out.append(f'<div class="a" style="left:80px;top:{base}px;width:920px;height:5px;background:{C["ink"]}"></div>')
    if D.get('note'): out.append(f'<div class="a" style="left:80px;top:690px;width:920px;text-align:center"><span style="padding:10px 22px;border-radius:30px;background:{C["accent"]};color:#fff;font-weight:800;font-size:28px">{esc(D["note"])}</span></div>')
    return page(D, ''.join(out), '내 나이대 값은 캡션에! 댓글로 비교해 보세요', src, fonts)

def korea(D, src, fonts):
    # 한국은 몇 위: rows [["나라", "값 글자"], …] 1위부터 6~10개, 한국은 rows 에 넣지 않음. me_rank(한국 실제 순위)는 rows 수보다 커야 함(목록 자리로 답이 새지 않게)
    rows = D['rows']; need(6 <= len(rows) <= 10, 'korea rows 는 6~10개'); need(D['me_rank'] > len(rows), 'korea me_rank 가 보여 주는 순위 안에 있음 — rows 를 줄이거나 다른 모양')
    need(all('한국' not in r[0] for r in rows), 'korea rows 에 한국을 넣지 않음'); out = []
    for i, (n, v) in enumerate(rows):
        y = 650 + i * 64
        out.append(f'<div class="a" style="left:120px;top:{y}px;width:840px;height:54px;border-radius:14px;background:{C["panel"]};border:2px solid {C["line"]};display:flex;align-items:center;padding:0 24px;font-weight:700;font-size:30px">'
                   f'<b class="bhs" style="width:70px;color:{C["sub"]}">{i + 1}</b><span style="flex:1;display:flex"><span class="fit" data-max="560">{esc(n)}</span></span><span class="bhs" style="font-size:34px;color:{C["accent"]}">{esc(v)}</span></div>')
    out.append(f'<div class="a" style="left:120px;top:1300px;width:840px;height:170px;border-radius:28px;background:{C["pale"]};border:4px dashed {C["gold"]};display:flex;align-items:center;justify-content:space-between;padding:0 50px">'
               f'<span style="font-weight:800;font-size:48px">{esc(D.get("me", "한국"))}</span><span class="bhs" style="font-size:96px;color:{C["gold"]}">?위</span></div>')
    out.append(f'<div class="a fit" data-max="920" style="left:80px;top:1500px;width:920px;text-align:center;font-weight:700;font-size:34px">{esc(D["question"])}</div>')
    return page(D, ''.join(out), '예상 순위를 댓글로!  정답은 캡션에', src, fonts)

LAYOUTS.update({'dots': dots, 'donut': donut, 'receipt': receipt, 'board': board, 'agebars': agebars, 'korea': korea})
