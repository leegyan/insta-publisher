# 발간물을 게시 대기열(queue 가지)에 넣는다. Claude 작업 세션에서 실행
# python3 enqueue.py <발간물폴더> <계정> [게시시각 "2026-10-25T08:00:00+09:00" | now] [--repo-dir 경로] [--reel 릴스판폴더]
#   게시시각을 빼거나 now 면 지금 시각. 넣은 뒤 '인스타그램 게시' 워크플로우를 바로 실행한다(workflow_dispatch, 1~2분 안에 게시)
#   게시시각이 미래면 그 시각이 지난 뒤 실행될 때 게시된다(예약 실행 없음 — 그 시각에 따로 실행해야 함)
#   발간물폴더: 04_slides_v2/ 의 PNG 8장(이름순) + 06_캡션.txt
#   --reel: 캐러셀 대신 릴스 + 같은 영상의 스토리(게시 1건 = 캐러셀 + 릴스 + 스토리). 릴스판폴더의 mp4 1개 + 커버.jpg(공용/tools/reel_cover.py, 없으면 넣지 않음) + 캡션.txt(없으면 발간물 06_캡션.txt). 게시물ID 끝에 _릴스 · _스토리
#   --story: 스토리만(릴스판폴더의 mp4). 게시물ID 끝에 _스토리
#   --reel 은 accounts.json 계정에 youtube 설정이 있으면 유튜브 쇼츠도 넣는다(게시물ID 끝에 _쇼츠). 쇼츠는 <발간물>/쇼츠/<N판>/(INSTA 공용/tools/shorts_make.py: mp4 · 캡션.txt(구독하고) · 썸네일.jpg)을 쓰고, 릴스판과 어긋나면 넣지 않는다
#   --reel-only: --reel 에서 스토리 · 쇼츠 없이 릴스만(지운 릴스를 다시 올릴 때). --shorts-only: 쇼츠만
#   --id-suffix 문자: 게시물ID 끝에 덧붙임. 게시기록에 같은 게시물ID가 있으면 게시하지 않고 빼므로, 다시 올릴 때 씀(예: _재게시1)
#   PNG → JPEG(품질 90, Meta는 JPEG만 받음). queue 가지는 부모 없는 커밋 1개로 덮어씀(이미지 이력 없음)
import sys, json, pathlib, subprocess, shutil, tempfile, datetime
from PIL import Image

def git(*a, cwd): return subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def main(pub, account, at, repo_dir, reel=None, kinds=('reel',), suffix=''):
    pub = pathlib.Path(pub); repo_dir = pathlib.Path(repo_dir)
    datetime.datetime.fromisoformat(at)  # 형식 검사
    if reel:
        reel = pathlib.Path(reel); vids = sorted(reel.glob('*.mp4'))
        if len(vids) != 1: sys.exit(f'릴스판 폴더 mp4 {len(vids)}개(1개여야 함)')
        if 'reel' in kinds or 'youtube' in kinds:
            cv = reel / '커버.jpg'
            if not cv.exists(): sys.exit('릴스판 폴더에 커버.jpg 없음(python3 공용/tools/reel_cover.py <릴스판폴더>)')
            if cv.stat().st_size > 8 * 1024 * 1024: sys.exit('커버.jpg 8MB 초과(Meta 한도)')
        cf = reel / '캡션.txt'; cap = (cf if cf.exists() else pub / '06_캡션.txt').read_text(encoding='utf-8').strip()
        pngs = []
    else:
        pngs = sorted((pub / '04_slides_v2').glob('*.png'))
        if not 2 <= len(pngs) <= 20: sys.exit(f'PNG {len(pngs)}장: 캐러셀은 2~20장')
        cap = (pub / '06_캡션.txt').read_text(encoding='utf-8').strip()
    if len(cap) > 2200: sys.exit(f'캡션 {len(cap)}자(2,200자 초과)')
    url = git('remote', 'get-url', 'origin', cwd=repo_dir)
    q = pathlib.Path(tempfile.mkdtemp(prefix='queue_'))
    has = subprocess.run(['git', 'ls-remote', '--exit-code', '--heads', url, 'queue'], capture_output=True).returncode == 0
    if has:
        git('clone', '--depth', '1', '--branch', 'queue', url, str(q), cwd=repo_dir); lease = git('rev-parse', 'HEAD', cwd=q)
    else:
        git('init', '-b', 'queue', cwd=q); git('remote', 'add', 'origin', url, cwd=q); lease = ''
    cfg = json.loads((repo_dir / 'accounts.json').read_text(encoding='utf-8'))['accounts'][account]
    kinds = [k for k in kinds if k != 'youtube' or cfg.get('youtube')]
    todo = [(k, f'{account}_{pub.name}' + {'reel': '_릴스', 'story': '_스토리', 'youtube': '_쇼츠'}[k] + suffix) for k in kinds] if reel else [(None, f'{account}_{pub.name}' + suffix)]
    for kind, pid in todo:
        d = q / 'posts' / account / pid
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True)
        if kind == 'youtube': add_shorts(d, pid, account, at, reel, cap, vids[0])
        else: add(d, pid, kind, account, at, cap, pngs, vids if reel else None, reel)
    git('checkout', '--orphan', 'tmp_queue', cwd=q); git('add', '-A', cwd=q)
    git('-c', 'user.name=insta-publisher', '-c', 'user.email=bot@users.noreply.github.com', 'commit', '-m', 'enqueue ' + ' · '.join(p for _, p in todo), cwd=q)
    git('push', f'--force-with-lease=queue:{lease}', 'origin', 'tmp_queue:queue', cwd=q)
    print('대기열에 넣음', ' · '.join(p for _, p in todo), at)
    dispatch(url)

def dispatch(url):
    # 넣은 즉시 게시 워크플로우 실행(Gyan 26.10.30.: 넣으면 바로 게시). 실패하면 수동 실행 명령을 알린다
    import os, urllib.request, re as _re
    m = _re.search(r'github\.com[:/]([^/]+)/([^/.]+)', url); repo = f'{m.group(1)}/{m.group(2)}' if m else 'leegyan/insta-publisher'
    api = f'https://api.github.com/repos/{repo}/actions/workflows/publish.yml/dispatches'
    h = {'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'}
    tok = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if tok: h['Authorization'] = f'Bearer {tok}'
    try:
        r = urllib.request.urlopen(urllib.request.Request(api, data=b'{"ref":"main"}', headers=h, method='POST'), timeout=30)
        print('게시 워크플로우 실행 요청', r.status, '(1~2분 뒤 기록/게시기록.jsonl 확인)')
    except Exception as e:
        print('게시 워크플로우 실행 실패:', e, f'→ 수동: curl -X POST -H "Content-Type: application/json" {api} -d \'{{"ref":"main"}}\'')

def add(d, pid, kind, account, at, cap, pngs, vids, reel=None):
    if kind in ('reel', 'story', 'youtube'):
        shutil.copy(vids[0], d / 'reel.mp4'); names = ['reel.mp4']
        meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': cap if kind != 'story' else '', 'type': kind, 'video': 'reel.mp4'}
        if kind == 'reel': shutil.copy(reel / '커버.jpg', d / 'cover.jpg'); meta['cover'] = 'cover.jpg'  # 릴스 cover_url
    else:
        names = []
        for i, p in enumerate(pngs, 1):
            n = f'{i:02d}.jpg'; Image.open(p).convert('RGB').save(d / n, 'JPEG', quality=90); names.append(n)
        meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': cap, 'images': names}
    (d / 'post.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')

def add_shorts(d, pid, account, at, reel, cap, reel_mp4):
    # 쇼츠 폴더 검사: 영상 · 썸네일이 릴스판과 같은 파일이고, 캡션이 릴스 캡션의 "팔로우하고" 줄만 "구독하고"로 바꾼 글이어야 한다
    s = reel.parent.parent / '쇼츠' / reel.name
    mp4 = sorted(s.glob('*.mp4')) if s.is_dir() else []
    if len(mp4) != 1 or not (s / '캡션.txt').exists() or not (s / '썸네일.jpg').exists(): sys.exit(f'쇼츠 폴더 {s} 없음 또는 불완전 — python3 공용/tools/shorts_make.py {reel}')
    lines = cap.splitlines(); i = [k for k, l in enumerate(lines) if l.startswith('팔로우하고')]
    want = '\n'.join(lines[:i[0]] + ['구독하고' + lines[i[0]][len('팔로우하고'):]] + lines[i[0] + 1:]) if len(i) == 1 else None
    scap = (s / '캡션.txt').read_text(encoding='utf-8').strip()
    bad = [n for n, ok in [('영상', mp4[0].read_bytes() == reel_mp4.read_bytes()), ('썸네일', (s / '썸네일.jpg').read_bytes() == (reel / '커버.jpg').read_bytes()), ('캡션', scap == want)] if not ok]
    if bad: sys.exit(f'쇼츠 폴더가 릴스판과 다름({", ".join(bad)}) — python3 공용/tools/shorts_make.py {reel} 다시')
    shutil.copy(mp4[0], d / 'reel.mp4'); shutil.copy(s / '썸네일.jpg', d / 'cover.jpg')
    meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': scap, 'type': 'youtube', 'video': 'reel.mp4', 'cover': 'cover.jpg'}
    (d / 'post.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    a = sys.argv[1:]; rd = '.'; rl = None; sf = ''
    if '--id-suffix' in a: i = a.index('--id-suffix'); sf = a[i + 1]; a = a[:i] + a[i + 2:]
    if '--repo-dir' in a: i = a.index('--repo-dir'); rd = a[i + 1]; a = a[:i] + a[i + 2:]
    kinds = ('reel', 'story', 'youtube')
    if '--reel' in a: i = a.index('--reel'); rl = a[i + 1]; a = a[:i] + a[i + 2:]
    if '--story' in a: i = a.index('--story'); rl = a[i + 1]; a = a[:i] + a[i + 2:]; kinds = ('story',)
    if '--reel-only' in a: a.remove('--reel-only'); kinds = ('reel',)
    if '--shorts-only' in a: a.remove('--shorts-only'); kinds = ('youtube',)
    at = a[2] if len(a) > 2 and a[2] != 'now' else datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(microsecond=0).isoformat()
    main(a[0], a[1], at, rd, rl, kinds, sf)
