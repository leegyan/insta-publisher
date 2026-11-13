# 댓글 낱말 → 공개 답글 자동 달기 (Instagram API with Instagram Login)
# 연재 릴스 캡션에 "다음 편이 궁금하면 '담핱' 댓글" 을 적어 두고, 그 낱말이 들어간 댓글에 다음 편 올라오는 시각을 답글로 알린다(Gyan 26.11.13.)
# 사용:
#   python3 comment_reply.py        → reply.json 의 mode 대로(off = 아무것도 안 함 / dry = 달지 않고 몇 개 달지만 셈 / run = 답글을 단다)
#   python3 comment_reply.py dry    → mode 와 상관없이 달지 않고 점검만
# 설정(reply.json): accounts.<계정>.keywords = 찾을 낱말들, posts.<게시물ID> = {next_at, before, after}
#   게시물ID 는 게시기록(기록/게시기록.jsonl)의 post_id — 거기서 media_id 를 찾는다(아직 안 올라간 게시물은 건너뜀)
#   완결편(final: true)에는 templates.final(다음 에피소드를 기다려 달라는 문장)을 단다
#   next_at(다음 편 게시 시각) 전에는 templates.before, 지난 뒤에는 templates.after 문장 가운데 하나를 차례로 돌려 단다({ep} = 다음 편 이름, {time} = 올라오는 시각)
# 달지 않는 댓글: 우리 계정이 쓴 댓글 · 이미 우리 답글이 달린 댓글(손으로 답한 것 포함) · 전에 이 도구가 답한 댓글
# 기록: 기록/reply_답글.json(답한 댓글 ID), 기록/reply_점검.txt(마지막 실행 결과 — 공개 저장소라 사용자 이름 · 댓글 내용은 적지 않는다)
# 댓글 좋아요(accounts.<계정>.like = true): 최근 like_days 일(기본 7) 안에 올린 릴스 · 캐러셀의 남의 댓글에 좋아요를 누른다(Gyan 26.11.13. '댓글 달리면 하트 자동으로')
#   Like Media and Comments API(2026-04): POST /<IG_USER_ID>/likes?comment_id=. 실패하면 그 실행에서는 더 누르지 않고 점검 파일에 이유를 적는다. 누른 댓글은 기록/reply_좋아요.json
# 필요한 권한: instagram_business_basic + instagram_business_manage_comments. 토큰은 GitHub Actions 비밀값(accounts.json 의 token_secret)
import json, os, sys, datetime, pathlib, urllib.request, urllib.parse, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'accounts.json').read_text(encoding='utf-8'))
API = 'https://graph.instagram.com/' + CFG.get('api_version', 'v26.0')
RULES_F = ROOT / 'reply.json'
PUB_F = ROOT / '기록' / '게시기록.jsonl'
DONE_F = ROOT / '기록' / 'reply_답글.json'
CHECK_F = ROOT / '기록' / 'reply_점검.txt'
LIKE_F = ROOT / '기록' / 'reply_좋아요.json'
KST = datetime.timezone(datetime.timedelta(hours=9))
HTTP = None  # 시험에서 가짜 함수로 바꿈
NOW = None   # 시험에서 시각을 고정


def http(method, url, data=None, token=None):
    if HTTP: return HTTP(method, url, data, token)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    if token: req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{method} {url.split("?")[0]} → HTTP {e.code}: {e.read().decode(errors="replace")[:300]}')


def comments(media_id, token):
    url = f'{API}/{media_id}/comments?' + urllib.parse.urlencode({'fields': 'id,text,timestamp,from{id,username},replies{id,from{id,username}}', 'limit': 50})
    while url:
        r = http('GET', url, token=token)
        yield from r.get('data', [])
        url = r.get('paging', {}).get('next')


def media_ids():
    """게시기록에서 post_id → media_id(같은 post_id 가 여러 번이면 마지막 것)."""
    out = {}
    if PUB_F.exists():
        for line in PUB_F.read_text(encoding='utf-8').splitlines():
            try: j = json.loads(line)
            except ValueError: continue
            if j.get('post_id') and j.get('media_id'): out[j['post_id']] = str(j['media_id'])
    return out


def recent_media(name, now, days):
    """게시기록에서 이 계정이 최근 days 일 안에 올린 인스타그램 게시물(릴스 · 캐러셀)의 post_id → media_id. 쇼츠 · 스토리는 뺀다."""
    out = {}
    if PUB_F.exists():
        for line in PUB_F.read_text(encoding='utf-8').splitlines():
            try: j = json.loads(line)
            except ValueError: continue
            pid = j.get('post_id', '')
            if j.get('account') != name or not j.get('media_id') or pid.endswith(('_쇼츠', '_스토리')): continue
            try: at = datetime.datetime.fromisoformat(j.get('published_at'))
            except (TypeError, ValueError): continue
            if (now - at).total_seconds() <= days * 86400: out[pid] = str(j['media_id'])
    return out


def norm(s): return ''.join(str(s or '').split()).lower()


def pick(rule, rules, now):
    """지금 달 문장 틀 목록. next_at(다음 편 게시 시각) 전이면 before 틀, 지났으면 after 틀. 틀의 {ep} · {time} 은 게시물 설정 값으로 채운다."""
    na = rule.get('next_at')
    kind = 'final' if rule.get('final') else 'before' if na and now < datetime.datetime.fromisoformat(na) else 'after'   # final: 완결편 — 다음 에피소드를 기다려 달라는 문장(Gyan 26.11.13.)
    own = rule.get(kind)   # 게시물에 따로 적은 문장이 있으면 그것을, 없으면 공통 문장(templates)을 쓴다
    tpls = (own if isinstance(own, (list, str)) else None) or rules.get('templates', {}).get(kind) or []
    if isinstance(tpls, str): tpls = [tpls]
    return [t.format(ep=rule.get('ep', '다음 편'), time=rule.get('time', '')) for t in tpls]


def main(arg=None):
    rules = json.loads(RULES_F.read_text(encoding='utf-8')); mode = arg or rules.get('mode', 'off')
    if mode not in ('dry', 'run'): print('mode off — 아무것도 하지 않음'); return 0
    done = json.loads(DONE_F.read_text(encoding='utf-8')) if DONE_F.exists() else {}
    liked = json.loads(LIKE_F.read_text(encoding='utf-8')) if LIKE_F.exists() else {}
    n_liked0 = len(liked)
    now = NOW or datetime.datetime.now(KST); mids = media_ids(); lines = []; n_sent = 0
    for name, ar in rules.get('accounts', {}).items():
        acc = CFG['accounts'][name]; tok = os.environ.get(acc['token_secret']); me = str(acc['ig_user_id'])
        if not tok: lines.append(f'{name}: 토큰 비밀값 없음 — 건너뜀'); continue
        keys = [norm(k) for k in ar.get('keywords', []) if norm(k)]
        cache = {}   # media_id → 댓글 목록(답글과 좋아요가 같은 게시물을 두 번 읽지 않게)

        def read(mid):
            if mid not in cache: cache[mid] = list(comments(mid, tok))
            return cache[mid]

        for pid, rule in ar.get('posts', {}).items():
            mid = mids.get(pid)
            if not mid: lines.append(f'{pid}: 아직 게시 기록 없음'); continue
            msgs = pick(rule, rules, now)
            try: got = read(mid)
            except RuntimeError as e: lines.append(f'{pid}: 댓글 읽기 실패 {str(e)[:200]}'); continue
            hit = todo = sent = fail = 0
            for c in got:
                if str(c.get('from', {}).get('id')) == me: continue                      # 우리 계정 댓글
                if not any(k in norm(c.get('text')) for k in keys): continue
                hit += 1
                if c['id'] in done or c['id'] == '_rot': continue
                if any(str(r.get('from', {}).get('id')) == me for r in c.get('replies', {}).get('data', [])):
                    done[c['id']] = 'answered'; continue                                 # 이미 우리 답글이 있음(손으로 답함)
                if not msgs: continue
                todo += 1
                if mode == 'dry': continue
                k = done.get('_rot', 0); done['_rot'] = k + 1   # 같은 문장이 이어지지 않게 준비한 문장을 차례로 돌려 쓴다(Gyan 26.11.13. '자동 댓글 같지 않게 10가지')
                try:
                    http('POST', f'{API}/{c["id"]}/replies', {'message': msgs[k % len(msgs)]}, tok)
                    done[c['id']] = now.isoformat(timespec='seconds'); sent += 1; n_sent += 1
                except RuntimeError as e:
                    fail += 1; lines.append(f'{pid}: 답글 실패 {str(e)[:200]}')
            lines.append(f'{pid}: 댓글 {len(got)}개 · 낱말 든 댓글 {hit}개 · 달 차례 {todo}개 · 이번에 단 답글 {sent}개' + (f' · 실패 {fail}개' if fail else '') + f' · 준비한 문장 {len(msgs)}가지')
        if ar.get('like'):
            rec = recent_media(name, now, ar.get('like_days', 7)); seen = todo = ok = 0; err = ''
            for pid, mid in rec.items():
                try: got = read(mid)
                except RuntimeError as e: lines.append(f'{pid}: 댓글 읽기 실패 {str(e)[:200]}'); continue
                for c in got:
                    if str(c.get('from', {}).get('id')) == me: continue
                    seen += 1
                    if c['id'] in liked: continue
                    todo += 1
                    if mode == 'dry' or err: continue                                    # 한 번 실패하면 이 실행에서는 더 누르지 않는다
                    try:
                        http('POST', f'{API}/{me}/likes?' + urllib.parse.urlencode({'comment_id': c['id']}), None, tok)
                        liked[c['id']] = now.isoformat(timespec='seconds'); ok += 1
                    except RuntimeError as e: err = str(e)[:300]
            lines.append(f'{name} 댓글 좋아요: 최근 게시물 {len(rec)}개 · 남의 댓글 {seen}개 · 누를 차례 {todo}개 · 이번에 누름 {ok}개' + (f' · 실패 「{err}」' if err else ''))
    DONE_F.parent.mkdir(exist_ok=True)
    if mode == 'run' or any(v == 'answered' for k, v in done.items() if k != '_rot'):
        DONE_F.write_text(json.dumps(done, ensure_ascii=False, indent=0), encoding='utf-8')
    if len(liked) != n_liked0: LIKE_F.write_text(json.dumps(liked, ensure_ascii=False, indent=0), encoding='utf-8')
    text = f'mode {mode}\n' + '\n'.join(lines) + '\n'
    old = CHECK_F.read_text(encoding='utf-8') if CHECK_F.exists() else ''
    if text != old.split('\n', 1)[-1]:   # 내용이 바뀐 때만 새로 적는다(10분마다 빈 커밋이 생기지 않게)
        CHECK_F.write_text(f'점검 시각 {now.isoformat(timespec="seconds")}\n' + text, encoding='utf-8')
    print(text); return n_sent


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None)
