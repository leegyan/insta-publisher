# 발간물을 게시 대기열(queue 가지)에 넣는다. Claude 작업 세션에서 실행
# python3 enqueue.py <발간물폴더> <계정> <게시시각 "2026-10-25T08:00:00+09:00"> [--repo-dir 경로] [--reel 릴스판폴더]
#   발간물폴더: 04_slides_v2/ 의 PNG 8장(이름순) + 06_캡션.txt
#   --reel: 캐러셀 대신 릴스 + 같은 영상의 스토리(게시 1건 = 캐러셀 + 릴스 + 스토리). 릴스판폴더의 mp4 1개 + 커버.jpg(공용/tools/reel_cover.py, 없으면 넣지 않음) + 캡션.txt(없으면 발간물 06_캡션.txt). 게시물ID 끝에 _릴스 · _스토리
#   --story: 스토리만(릴스판폴더의 mp4). 게시물ID 끝에 _스토리
#   --reel 은 accounts.json 계정에 youtube 설정이 있으면 같은 영상을 유튜브 쇼츠로도 넣는다(게시물ID 끝에 _쇼츠, 캡션의 "팔로우하고" 줄은 youtube.outro 로)
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
        if 'reel' in kinds:
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
        c = cap
        if kind == 'youtube':  # 쇼츠: 인스타 아웃트로 줄("팔로우하고 …")을 accounts.json youtube.outro 로 바꿈(유튜브는 구독)
            lines = cap.splitlines(); i = [k for k, l in enumerate(lines) if l.startswith('팔로우하고')]
            if len(i) != 1: sys.exit(f'캡션에 "팔로우하고" 줄이 {len(i)}개(1개여야 쇼츠 아웃트로로 바꿈)')
            lines[i[0]] = cfg['youtube']['outro']; c = '\n'.join(lines)
        add(d, pid, kind, account, at, c, pngs, vids if reel else None, reel)
    git('checkout', '--orphan', 'tmp_queue', cwd=q); git('add', '-A', cwd=q)
    git('-c', 'user.name=insta-publisher', '-c', 'user.email=bot@users.noreply.github.com', 'commit', '-m', 'enqueue ' + ' · '.join(p for _, p in todo), cwd=q)
    git('push', f'--force-with-lease=queue:{lease}', 'origin', 'tmp_queue:queue', cwd=q)
    print('대기열에 넣음', ' · '.join(p for _, p in todo), at)

def add(d, pid, kind, account, at, cap, pngs, vids, reel=None):
    if kind in ('reel', 'story', 'youtube'):
        shutil.copy(vids[0], d / 'reel.mp4'); names = ['reel.mp4']
        meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': cap if kind != 'story' else '', 'type': kind, 'video': 'reel.mp4'}
        if kind == 'reel': shutil.copy(reel / '커버.jpg', d / 'cover.jpg'); meta['cover'] = 'cover.jpg'
    else:
        names = []
        for i, p in enumerate(pngs, 1):
            n = f'{i:02d}.jpg'; Image.open(p).convert('RGB').save(d / n, 'JPEG', quality=90); names.append(n)
        meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': cap, 'images': names}
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
    main(a[0], a[1], a[2], rd, rl, kinds, sf)
