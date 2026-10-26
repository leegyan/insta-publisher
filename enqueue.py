# 발간물을 게시 대기열(queue 가지)에 넣는다. Claude 작업 세션에서 실행
# python3 enqueue.py <발간물폴더> <계정> <게시시각 "2026-10-25T08:00:00+09:00"> [--repo-dir 경로] [--reel 릴스판폴더]
#   발간물폴더: 04_slides_v2/ 의 PNG 8장(이름순) + 06_캡션.txt
#   --reel: 캐러셀 대신 릴스. 릴스판폴더의 mp4 1개 + 캡션.txt(없으면 발간물 06_캡션.txt). 게시물ID 끝에 _릴스
#   PNG → JPEG(품질 90, Meta는 JPEG만 받음). queue 가지는 부모 없는 커밋 1개로 덮어씀(이미지 이력 없음)
import sys, json, pathlib, subprocess, shutil, tempfile, datetime
from PIL import Image

def git(*a, cwd): return subprocess.run(['git', *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

def main(pub, account, at, repo_dir, reel=None):
    pub = pathlib.Path(pub); repo_dir = pathlib.Path(repo_dir)
    datetime.datetime.fromisoformat(at)  # 형식 검사
    if reel:
        reel = pathlib.Path(reel); vids = sorted(reel.glob('*.mp4'))
        if len(vids) != 1: sys.exit(f'릴스판 폴더 mp4 {len(vids)}개(1개여야 함)')
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
    pid = f'{account}_{pub.name}' + ('_릴스' if reel else '')
    d = q / 'posts' / account / pid
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    if reel:
        shutil.copy(vids[0], d / 'reel.mp4'); names = ['reel.mp4']
        meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': cap, 'type': 'reel', 'video': 'reel.mp4'}
    else:
        names = []
        for i, p in enumerate(pngs, 1):
            n = f'{i:02d}.jpg'; Image.open(p).convert('RGB').save(d / n, 'JPEG', quality=90); names.append(n)
        meta = {'post_id': pid, 'account': account, 'publish_at': at, 'caption': cap, 'images': names}
    (d / 'post.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    git('checkout', '--orphan', 'tmp_queue', cwd=q); git('add', '-A', cwd=q)
    git('-c', 'user.name=insta-publisher', '-c', 'user.email=bot@users.noreply.github.com', 'commit', '-m', f'enqueue {pid}', cwd=q)
    git('push', f'--force-with-lease=queue:{lease}', 'origin', 'tmp_queue:queue', cwd=q)
    print('대기열에 넣음', pid, at, f'{len(names)}장')

if __name__ == '__main__':
    a = sys.argv[1:]; rd = '.'; rl = None
    if '--repo-dir' in a: i = a.index('--repo-dir'); rd = a[i + 1]; a = a[:i] + a[i + 2:]
    if '--reel' in a: i = a.index('--reel'); rl = a[i + 1]; a = a[:i] + a[i + 2:]
    main(a[0], a[1], a[2], rd, rl)
