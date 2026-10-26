# 인스타그램 자동 게시기 (Instagram API with Instagram Login, 공식 API)
# 사용:
#   python3 publish.py run      → queue 가지의 게시 시각이 지난 발간물을 캐러셀(post.json type=reel 이면 릴스, type=story 이면 스토리)로 게시하고, 게시한 발간물을 queue에서 뺀다
#   python3 publish.py refresh  → 계정마다 토큰을 갱신(60일 유효)하고 GitHub 비밀값을 새 토큰으로 바꾼다
# 이미지 이력 회피: queue 가지는 매번 부모 없는 커밋 1개로 덮어쓴다(force push). 지난 이미지는 가지 이력에 남지 않는다
# 토큰: GitHub Actions 비밀값(accounts.json의 token_secret 이름). 이 파일과 저장소에는 토큰을 적지 않는다
import json, os, sys, time, subprocess, urllib.request, urllib.parse, urllib.error, datetime, base64, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
KST = datetime.timezone(datetime.timedelta(hours=9))
CFG = json.loads((ROOT / 'accounts.json').read_text(encoding='utf-8'))
API = 'https://graph.instagram.com/' + CFG.get('api_version', 'v26.0')
REPO = os.environ.get('GITHUB_REPOSITORY', CFG.get('repo', ''))
# 토큰은 워크플로우가 이름별 환경변수(IG_TOKEN_...)로 넘긴다. SECRETS_JSON 은 시험용으로만 남김
# (toJSON(secrets) 로 비밀값 전체를 넘기면 GitHub 가 워크플로우를 악성 의심으로 막음, 2026-10-26 실측)
SECRETS = {**json.loads(os.environ.get('SECRETS_JSON', '{}')), **{k: v for k, v in os.environ.items() if k.startswith('IG_TOKEN_') and v}}
QUEUE = os.environ.get('QUEUE_DIR', str(ROOT / '_queue'))
LOG = ROOT / '기록' / '게시기록.jsonl'
HTTP = None  # 시험에서 가짜 함수로 바꿈


def http(method, url, data=None, token=None):
    if HTTP: return HTTP(method, url, data, token)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    if token: req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{method} {url.split("?")[0]} → HTTP {e.code}: {e.read().decode(errors="replace")[:500]}')


def git(*a, cwd=None, check=True):
    return subprocess.run(['git', *a], cwd=cwd or QUEUE, check=check, capture_output=True, text=True).stdout.strip()


def wait_finished(cid, token, tries=10, gap=30):
    # Meta 문서: status_code를 1분에 한 번, 5분 넘지 않게 확인 권장 → 30초 간격 10번(5분)
    for _ in range(tries):
        r = http('GET', f'{API}/{cid}?fields=status_code,status', token=token); st = r.get('status_code')
        if st == 'FINISHED': return
        if st in ('ERROR', 'EXPIRED'): raise RuntimeError(f'컨테이너 {cid} 상태 {st}: {r.get("status", "")}')  # status 에 오류 번호 · 설명이 옴
        time.sleep(gap)
    raise RuntimeError(f'컨테이너 {cid} 5분 안에 FINISHED가 되지 않음')


def published_ids():
    if not LOG.exists(): return set()
    return {json.loads(l)['post_id'] for l in LOG.read_text(encoding='utf-8').splitlines() if l.strip() and json.loads(l).get('media_id')}


def log(rec):
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f: f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def publish_post(pdir, sha, gap=30):
    meta = json.loads((pdir / 'post.json').read_text(encoding='utf-8'))
    acc = CFG['accounts'][meta['account']]
    token = SECRETS.get(acc['token_secret'])
    if not token: raise RuntimeError(f'비밀값 {acc["token_secret"]} 없음')
    if not acc.get('ig_user_id'): raise RuntimeError(f'accounts.json {meta["account"]} ig_user_id 비어 있음')
    ig = acc['ig_user_id']
    rel = pdir.relative_to(QUEUE).as_posix()
    if meta.get('type') == 'story':   # 스토리: 영상 1개 → STORIES 컨테이너 → 게시. 캡션 · 스티커는 API로 넣을 수 없음(화면 위 계정 이름을 누르면 프로필로 감)
        url = f'https://raw.githubusercontent.com/{REPO}/{sha}/{urllib.parse.quote(rel)}/{urllib.parse.quote(meta["video"])}'
        cid = http('POST', f'{API}/{ig}/media', {'media_type': 'STORIES', 'video_url': url}, token)['id']
        wait_finished(cid, token, tries=20, gap=gap)
        mid = http('POST', f'{API}/{ig}/media_publish', {'creation_id': cid}, token)['id']
        return meta, mid
    if meta.get('type') == 'reel':   # 릴스: 영상 1개(+ 커버 JPEG) → REELS 컨테이너 → 게시(피드에도 보이게 share_to_feed). 영상 처리는 사진보다 오래 걸려 30초 × 20번(10분)까지 기다림
        url = f'https://raw.githubusercontent.com/{REPO}/{sha}/{urllib.parse.quote(rel)}/{urllib.parse.quote(meta["video"])}'
        body = {'media_type': 'REELS', 'video_url': url, 'caption': meta['caption'], 'share_to_feed': True}
        if meta.get('cover'):  # 커버(썸네일) JPEG. Meta 문서: cover_url 은 thumb_offset 보다 우선, 게시 뒤에는 바꿀 수 없음
            body['cover_url'] = f'https://raw.githubusercontent.com/{REPO}/{sha}/{urllib.parse.quote(rel)}/{urllib.parse.quote(meta["cover"])}'
        cid = http('POST', f'{API}/{ig}/media', body, token)['id']
        wait_finished(cid, token, tries=20, gap=gap)
        mid = http('POST', f'{API}/{ig}/media_publish', {'creation_id': cid}, token)['id']
        return meta, mid
    kids = []
    for img in meta['images']:  # 장 순서 = images 순서
        url = f'https://raw.githubusercontent.com/{REPO}/{sha}/{urllib.parse.quote(rel)}/{urllib.parse.quote(img)}'  # 한글 폴더 이름도 주소 부호화
        kids.append(http('POST', f'{API}/{ig}/media', {'image_url': url, 'is_carousel_item': True}, token)['id'])
    for k in kids: wait_finished(k, token, gap=gap)
    car = http('POST', f'{API}/{ig}/media', {'media_type': 'CAROUSEL', 'children': ','.join(kids), 'caption': meta['caption']}, token)['id']
    wait_finished(car, token, gap=gap)
    mid = http('POST', f'{API}/{ig}/media_publish', {'creation_id': car}, token)['id']
    return meta, mid


def rebuild_queue(remove, lease):
    # 게시한 발간물을 뺀 나머지로 부모 없는 커밋 1개를 새로 만들어 queue 가지를 덮어씀
    for r in remove: subprocess.run(['rm', '-rf', r], cwd=QUEUE, check=True)
    git('checkout', '--orphan', 'tmp_queue'); git('add', '-A')
    git('-c', 'user.name=insta-publisher', '-c', 'user.email=bot@users.noreply.github.com', 'commit', '--allow-empty', '-m', 'queue ' + datetime.datetime.now(KST).isoformat(timespec='minutes'))
    # lease: 읽기 시작할 때의 queue 커밋. 그사이 다른 쪽(enqueue)이 queue를 바꿨으면 push가 거절되고 이번 실행은 실패로 끝남 → 다음 실행에서 다시 함
    git('push', f'--force-with-lease=queue:{lease}', 'origin', 'tmp_queue:queue')


def run(now=None, gap=30):
    now = now or datetime.datetime.now(KST)
    sha = git('rev-parse', 'HEAD')
    done = published_ids(); remove = []; errors = []
    for pj in sorted(pathlib.Path(QUEUE).glob('posts/*/*/post.json')):
        pdir = pj.parent; meta = json.loads(pj.read_text(encoding='utf-8')); pid = meta['post_id']
        if pid in done: remove.append(str(pdir.relative_to(QUEUE))); continue  # 이미 게시됨(지난 실행에서 queue 정리 실패)
        if datetime.datetime.fromisoformat(meta['publish_at']) > now: continue
        try:
            meta, mid = publish_post(pdir, sha, gap=gap)
            log({'post_id': pid, 'account': meta['account'], 'media_id': mid, 'published_at': datetime.datetime.now(KST).isoformat(timespec='seconds')})
            remove.append(str(pdir.relative_to(QUEUE))); print('게시', pid, mid)
        except Exception as e:
            errors.append(f'{pid}: {e}')
            log({'post_id': pid, 'account': meta.get('account'), 'error': str(e)[:500], 'at': datetime.datetime.now(KST).isoformat(timespec='seconds')})
    if remove: rebuild_queue(remove, sha)
    if errors: print('실패:\n' + '\n'.join(errors)); sys.exit(1)


def refresh():
    from nacl import encoding, public  # PyNaCl: GitHub 비밀값 암호화
    gh = os.environ['GH_ADMIN_TOKEN']
    def ghapi(method, path, data=None):
        req = urllib.request.Request('https://api.github.com' + path, data=json.dumps(data).encode() if data else None, method=method)
        req.add_header('Authorization', 'Bearer ' + gh); req.add_header('Accept', 'application/vnd.github+json')
        with urllib.request.urlopen(req) as r: b = r.read(); return json.loads(b) if b else {}
    key = ghapi('GET', f'/repos/{REPO}/actions/secrets/public-key')
    box = public.SealedBox(public.PublicKey(key['key'].encode(), encoding.Base64Encoder()))
    errors = []
    for name, acc in CFG['accounts'].items():
        tok = SECRETS.get(acc['token_secret'])
        if not tok: errors.append(f'{name}: 비밀값 없음'); continue
        try:
            r = http('GET', 'https://graph.instagram.com/refresh_access_token?' + urllib.parse.urlencode({'grant_type': 'ig_refresh_token', 'access_token': tok}))
            enc = base64.b64encode(box.encrypt(r['access_token'].encode())).decode()
            ghapi('PUT', f'/repos/{REPO}/actions/secrets/{acc["token_secret"]}', {'encrypted_value': enc, 'key_id': key['key_id']})
            print(name, '토큰 갱신, 남은 일수', r['expires_in'] // 86400)
        except Exception as e: errors.append(f'{name}: {str(e)[:300]}')
    if errors: print('실패:\n' + '\n'.join(errors)); sys.exit(1)


if __name__ == '__main__':
    {'run': run, 'refresh': refresh}[sys.argv[1]]()
