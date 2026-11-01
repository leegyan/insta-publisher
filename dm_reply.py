# 댓글 → DM 자료 자동 보내기 (Instagram API with Instagram Login, 공식 '비공개 답장' private reply)
# 사용:
#   python3 dm_reply.py run        → dm.json 에 적은 게시물마다 새 댓글을 읽고, 아직 답하지 않은 댓글 작성자에게 DM 한 통(글 + 자료 링크)을 보낸다
#   python3 dm_reply.py dry        → 보내지 않고 누구에게 보낼지만 찍는다(권한 · 설정 점검용)
# 규칙(인스타 공식 문서 · 2026-11-02 확인):
#   · 비공개 답장은 댓글 하나에 한 번만, 댓글 단 지 7일 안에만 보낼 수 있다 → 7일 지난 댓글은 건너뛴다
#   · 받는 사람이 답장하기 전에는 메시지 한 통만 → 첫 통에 자료 링크(PDF)를 넣는다. 파일 첨부는 상대가 답장해 24시간 창이 열린 뒤에만
#   · 필요한 권한: instagram_business_basic + instagram_business_manage_comments(댓글 읽기) + instagram_business_manage_messages(보내기)
#     문서: developers.facebook.com/docs/instagram-platform/private-replies (2026-06-30 갱신본)
#     (앱이 '개발 중'이면 앱 역할이 있는 계정에게만 보내짐 → 일반 시청자에게는 앱 검수(고급 액세스) 통과 뒤)
# 자료는 모든 분께 같은 내용(작성기준 2절) — 댓글 내용에 따라 다른 답을 하지 않는다(개별 상담 금지)
# 토큰: GitHub Actions 비밀값(accounts.json 의 token_secret). 출력에 토큰을 적지 않는다
import json, os, sys, datetime, pathlib, urllib.request, urllib.parse, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'accounts.json').read_text(encoding='utf-8'))
API = 'https://graph.instagram.com/' + CFG.get('api_version', 'v26.0')
DM = json.loads((ROOT / 'dm.json').read_text(encoding='utf-8'))
DONE_F = ROOT / '기록' / 'dm_보낸댓글.json'
LOG = ROOT / '기록' / 'dm기록.jsonl'
KST = datetime.timezone(datetime.timedelta(hours=9))
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
        raise RuntimeError(f'{method} {url.split("?")[0]} → HTTP {e.code}: {e.read().decode(errors="replace")[:400]}')


def comments(media_id, token):
    url = f'{API}/{media_id}/comments?' + urllib.parse.urlencode({'fields': 'id,timestamp,from{id,username}', 'limit': 50})
    while url:
        r = http('GET', url, token=token)
        yield from r.get('data', [])
        url = r.get('paging', {}).get('next')


def main(mode):
    done = json.loads(DONE_F.read_text(encoding='utf-8')) if DONE_F.exists() else {}
    now = datetime.datetime.now(datetime.timezone.utc); sent = 0; logs = []
    for name, acc_dm in DM['accounts'].items():
        acc = CFG['accounts'][name]; tok = os.environ.get(acc['token_secret'])
        if not tok: print(f'{name}: 토큰 비밀값 없음 — 건너뜀'); continue
        for media in acc_dm['media']:
            if not media.get('on', True): continue
            res = DM['resources'][media['resource']]
            text = res['message'].replace('{link}', res['link'])
            for c in comments(media['media_id'], tok):
                cid = c['id']; who = c.get('from', {})
                if cid in done or who.get('username') == name: continue   # 이미 보냄 · 내 댓글
                age = now - datetime.datetime.fromisoformat(c['timestamp'].replace('+0000', '+00:00'))
                if age.days >= 7: done[cid] = 'expired'; continue          # 7일 지나면 비공개 답장 불가
                if mode == 'dry':
                    print(f'[보낼 예정] {name} ← 댓글 {cid} @{who.get("username")}'); continue
                try:
                    http('POST', f'{API}/{acc["ig_user_id"]}/messages', {'recipient': {'comment_id': cid}, 'message': {'text': text}}, tok)
                    done[cid] = now.isoformat(timespec='seconds'); sent += 1
                    logs.append({'at': datetime.datetime.now(KST).isoformat(timespec='seconds'), 'account': name, 'media': media['media_id'], 'comment': cid, 'resource': media['resource']})
                except RuntimeError as e:
                    print(f'{name} 댓글 {cid} 실패: {e}')
                    if 'already' in str(e): done[cid] = 'already'          # 이미 한 번 보낸 댓글
                    elif '10903' in str(e): done[cid] = 'expired'          # 7일 지난 댓글
    if mode != 'dry':
        DONE_F.parent.mkdir(exist_ok=True); DONE_F.write_text(json.dumps(done, ensure_ascii=False, indent=0), encoding='utf-8')
        with LOG.open('a', encoding='utf-8') as f:
            for l in logs: f.write(json.dumps(l, ensure_ascii=False) + '\n')
    print(f'보냄 {sent}통')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'dry')
