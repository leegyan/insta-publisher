# 댓글 → DM 자료 자동 보내기 (Instagram API with Instagram Login, 공식 '비공개 답장' private reply)
# 사용(DM 을 보낸 댓글에는 '공개 답글'도 단다: dm.json comment_replies 5개를 돌려 씀):
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
            # DM 글은 하나(자료 링크 + footer). 댓글에는 짧은 공개 답글 comment_replies(5개)를 보낸 순서대로 돌려 단다(Gyan 26.11.02 09:22)
            text = res['message'].replace('{link}', res['link']) + ('\n\n' + res['footer'] if res.get('footer') else '')
            replies = DM.get('comment_replies', [])
            # 점검용: 게시물의 댓글 수(comments_count)와 API 가 돌려준 댓글 수를 찍는다(사용자 이름은 찍지 않음 — 공개 저장소 로그)
            try:
                cc = http('GET', f'{API}/{media["media_id"]}?fields=comments_count', token=tok).get('comments_count')
            except RuntimeError as e: cc = f'읽기 실패 {e}'
            got = list(comments(media['media_id'], tok))
            print(f'{name} {media["media_id"]}: 댓글 수 {cc} · API 가 돌려준 댓글 {len(got)}개')
            for c in got:
                cid = c['id']; who = c.get('from', {})
                if cid in done or cid == '_rot' or who.get('username') == name: continue   # 이미 보냄 · 내 댓글
                age = now - datetime.datetime.fromisoformat(c['timestamp'].replace('+0000', '+00:00'))
                if age.days >= 7: done[cid] = 'expired'; continue          # 7일 지나면 비공개 답장 불가
                if mode == 'dry':
                    print(f'[보낼 예정] {name} ← 댓글 {cid} @{who.get("username")}'); continue
                try:
                    # 1순위: PDF 파일 자체를 DM 에 첨부(링크가 아니라 파일 — Gyan 26.11.02 11:01 "그 파일만 다운받을 수 있게").
                    #   Meta 가 res['file_url'] 에서 파일을 받아 붙인다(pdf 25MB 이하, 2025-12-19 지원). 비공개 답장은 한 통뿐이라 안내문은 PDF 마지막 쪽에 있다
                    # 첨부가 거부되면(지원 안 됨 · 오류) 글 + 링크로 보낸다
                    sent_kind = 'file'
                    try:
                        http('POST', f'{API}/{acc["ig_user_id"]}/messages', {'recipient': {'comment_id': cid}, 'message': {'attachment': {'type': 'file', 'payload': {'url': res['file_url']}}}}, tok)
                    except RuntimeError as e:
                        print(f'{name} 댓글 {cid} 파일 첨부 실패 → 글로 보냄: {str(e)[:200]}'); sent_kind = 'text'
                        http('POST', f'{API}/{acc["ig_user_id"]}/messages', {'recipient': {'comment_id': cid}, 'message': {'text': text}}, tok)
                    if replies:   # 공개 답글(실패해도 DM 은 보낸 것으로 기록)
                        k = done.get('_rot', 0); done['_rot'] = k + 1
                        try: http('POST', f'{API}/{cid}/replies', {'message': replies[k % len(replies)]}, tok)
                        except RuntimeError as e: print(f'{name} 댓글 {cid} 공개 답글 실패: {e}')
                    done[cid] = now.isoformat(timespec='seconds'); sent += 1
                    logs.append({'at': datetime.datetime.now(KST).isoformat(timespec='seconds'), 'account': name, 'media': media['media_id'], 'comment': cid, 'resource': media['resource'], 'kind': sent_kind})
                except RuntimeError as e:
                    print(f'{name} 댓글 {cid} 실패: {e}')
                    if 'already' in str(e): done[cid] = 'already'          # 이미 한 번 보낸 댓글
                    elif '10903' in str(e): done[cid] = 'expired'          # 7일 지난 댓글
    if mode != 'dry':
        DONE_F.parent.mkdir(exist_ok=True); DONE_F.write_text(json.dumps(done, ensure_ascii=False, indent=0), encoding='utf-8')
        with LOG.open('a', encoding='utf-8') as f:
            for l in logs: f.write(json.dumps(l, ensure_ascii=False) + '\n')
    print(f'보냄 {sent}통')


FILE_F = ROOT / '기록' / 'dm_파일보냄.json'


def followup(mode):
    # 2단계: 댓글 DM 을 받은 사람이 답장(버튼 · 아무 글)을 보내면 24시간 대화 창이 열린다 → 그 사람에게 PDF 파일 자체를 보낸다
    # 지금은 DM 목록을 읽어 찾는다(웹훅 서버가 생기면 그쪽이 같은 일을 즉시 한다). 같은 사람에게는 자료마다 한 번만
    sent = json.loads(FILE_F.read_text(encoding='utf-8')) if FILE_F.exists() else {}
    now = datetime.datetime.now(datetime.timezone.utc); n = 0
    for name, acc_dm in DM['accounts'].items():
        acc = CFG['accounts'][name]; tok = os.environ.get(acc['token_secret'])
        if not tok: continue
        res_key = next((m['resource'] for m in acc_dm['media'] if m.get('on', True)), None)
        if not res_key: continue
        res = DM['resources'][res_key]
        url = f'{API}/me/conversations?' + urllib.parse.urlencode({'platform': 'instagram', 'fields': 'participants,messages.limit(5){from,created_time}', 'limit': 25})
        convs = http('GET', url, token=tok).get('data', [])
        print(f'{name}: 대화 {len(convs)}개')
        for c in convs:
            msgs = c.get('messages', {}).get('data', [])
            print('  최근 메시지:', ' / '.join(f"{'상대' if m.get('from', {}).get('id') != acc['ig_user_id'] else '우리'} {m.get('created_time', '')[11:16]}" for m in msgs))
            theirs = [m for m in msgs if m.get('from', {}).get('id') != acc['ig_user_id'] and m.get('from', {}).get('username') != name]
            if not theirs: continue
            last = theirs[0]; uid = last['from']['id']
            age = now - datetime.datetime.fromisoformat(last['created_time'].replace('+0000', '+00:00'))
            key = f'{name}:{uid}:{res_key}'
            if key in sent or age.total_seconds() > 23.5 * 3600: continue
            if mode == 'dry': print(f'[파일 보낼 예정] {name} → 대화 상대 1명'); continue
            try:
                http('POST', f'{API}/{acc["ig_user_id"]}/messages', {'recipient': {'id': uid}, 'message': {'attachment': {'type': 'file', 'payload': {'url': res['file_url']}}}}, tok)
                sent[key] = now.isoformat(timespec='seconds'); n += 1
            except RuntimeError as e:
                print(f'{name} 파일 보내기 실패: {str(e)[:300]}')
                # 원인 가르기: 같은 상대에게 짧은 글은 가는지(가면 첨부 문제, 안 가면 대화 창 · 받는 사람 ID 문제)
                try:
                    http('POST', f'{API}/{acc["ig_user_id"]}/messages', {'recipient': {'id': uid}, 'message': {'text': '가이드 파일을 보내드릴게요.'}}, tok); print('  글은 감 → 첨부 문제')
                except RuntimeError as e2: print(f'  글도 실패 → 대화 창 · ID 문제: {str(e2)[:200]}')
    if mode != 'dry':
        FILE_F.parent.mkdir(exist_ok=True); FILE_F.write_text(json.dumps(sent, ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'파일 보냄 {n}통')


if __name__ == '__main__':
    m = sys.argv[1] if len(sys.argv) > 1 else 'dry'
    if m in ('followup', 'followup_dry'): followup('dry' if m == 'followup_dry' else 'run')
    else: main(m)
