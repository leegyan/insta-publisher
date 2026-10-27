# 릴스 성적표 수집 (Instagram API with Instagram Login, 읽기만 함 · 게시하지 않음)
# 사용: python3 insights.py   (워크플로우 '릴스 성적표' 가 하루 한 번 실행)
# 하는 일
#   1. 기록/게시기록.jsonl 에서 게시된 릴스(post_id 에 '_릴스')의 media_id 를 모은다
#   2. 릴스마다 GET /{media_id}?fields=… 와 /{media_id}/insights 로 지표를 읽는다. 한꺼번에 실패하면 지표마다 따로 읽고, 실패한 지표는 오류 내용을 남긴다
#   3. 계정 단위 reach · views 를 팔로워/비팔로워(follow_type) · 형식(media_product_type)으로 나눠 최근 7일 하루씩 읽는다
#   4. 결과 JSON 을 암호화해 기록/성적표/<KST 시각>.enc.json 에 쓰고, 기록/성적표/목록.txt 에 파일 이름을 더한다
# 암호화: 실행마다 새 AES-256-GCM 키로 내용을 잠그고, 그 키를 insights_pub.pem(RSA-OAEP SHA-256 공개키)으로 잠근다.
#   여는 개인키는 저장소에 없다(Gyan PC INSTA/공용/tools/insights_key.pem). 공개 저장소에는 잠긴 파일만 남는다
# 로그(공개)에는 지표 수치를 찍지 않는다. 지표 이름별로 읽힘 · 실패와 HTTP 오류 번호만 찍는다
import json, os, sys, base64, datetime, pathlib, urllib.request, urllib.parse, urllib.error

ROOT = pathlib.Path(__file__).resolve().parent
KST = datetime.timezone(datetime.timedelta(hours=9))
CFG = json.loads((ROOT / 'accounts.json').read_text(encoding='utf-8'))
API = 'https://graph.instagram.com/' + CFG.get('api_version', 'v26.0')
LOG = ROOT / '기록' / '게시기록.jsonl'
OUT = ROOT / '기록' / '성적표'
# Meta 문서(Instagram Media Insights, v26.0) 의 REELS 지표
REEL_METRICS = ['views', 'reach', 'ig_reels_avg_watch_time', 'ig_reels_video_view_total_time', 'reels_skip_rate',
                'likes', 'comments', 'saved', 'shares', 'reposts', 'total_interactions']
REEL_FIELDS = 'id,media_type,media_product_type,timestamp,permalink,like_count,comments_count'
# Meta 문서(Instagram User Insights): reach 는 follow_type · media_product_type, views 는 follow_type(문서에 follower_type 표기도 있음) · media_product_type
ACCOUNT_QUERIES = [('reach', 'follow_type'), ('reach', 'media_product_type'), ('views', 'follow_type'), ('views', 'follower_type'), ('views', 'media_product_type')]


def get(url, token):
    req = urllib.request.Request(url)
    req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return True, json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')[:400]
        try: err = json.loads(body).get('error', {})
        except Exception: err = {}
        return False, {'http': e.code, 'code': err.get('code'), 'subcode': err.get('error_subcode'), 'message': err.get('message', body)}
    except Exception as e:
        return False, {'http': None, 'message': str(e)[:300]}


def reels(account):
    if not LOG.exists(): return []
    seen, out = set(), []
    for l in LOG.read_text(encoding='utf-8').splitlines():
        if not l.strip(): continue
        r = json.loads(l)
        if r.get('account') != account or not r.get('media_id') or '_릴스' not in r.get('post_id', ''): continue
        if r['media_id'] in seen: continue
        seen.add(r['media_id']); out.append({'post_id': r['post_id'], 'media_id': r['media_id'], 'published_at': r.get('published_at')})
    return out


def media_insights(mid, token):
    status = {}
    ok, info = get(f'{API}/{mid}?fields={REEL_FIELDS}', token)
    rec = {'fields': info if ok else None, 'fields_error': None if ok else info, 'metrics': {}}
    ok, r = get(f'{API}/{mid}/insights?metric={",".join(REEL_METRICS)}', token)
    if ok:
        for m in r.get('data', []): rec['metrics'][m['name']] = m.get('values', [{}])[0].get('value', m.get('total_value', {}).get('value'))
        for m in REEL_METRICS: status[m] = '읽힘' if m in rec['metrics'] else '응답에 없음'
    else:  # 하나라도 안 되는 지표가 있으면 전체가 실패하므로 하나씩
        for m in REEL_METRICS:
            ok1, r1 = get(f'{API}/{mid}/insights?metric={m}', token)
            if ok1 and r1.get('data'):
                d = r1['data'][0]; rec['metrics'][m] = d.get('values', [{}])[0].get('value', d.get('total_value', {}).get('value')); status[m] = '읽힘'
            else:
                rec.setdefault('metric_errors', {})[m] = r1 if not ok1 else '빈 응답'
                status[m] = f'실패 HTTP {r1.get("http")} code {r1.get("code")}' if not ok1 else '빈 응답'
    return rec, status


def account_insights(ig, token, days=7):
    rows, status = [], {}
    today = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    for metric, bd in ACCOUNT_QUERIES:
        key = f'{metric}/{bd}'
        for i in range(days, 0, -1):
            since = int((today - datetime.timedelta(days=i)).timestamp()); until = since + 86400
            q = urllib.parse.urlencode({'metric': metric, 'period': 'day', 'metric_type': 'total_value', 'breakdown': bd, 'since': since, 'until': until})
            ok, r = get(f'{API}/{ig}/insights?{q}', token)
            if ok:
                rows.append({'metric': metric, 'breakdown': bd, 'since_utc': since, 'data': r.get('data', [])}); status[key] = '읽힘'
            else:
                status[key] = f'실패 HTTP {r.get("http")} code {r.get("code")}'
                rows.append({'metric': metric, 'breakdown': bd, 'since_utc': since, 'error': r}); break
    return rows, status


def encrypt(obj):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    pub = serialization.load_pem_public_key((ROOT / 'insights_pub.pem').read_bytes())
    key = AESGCM.generate_key(bit_length=256); nonce = os.urandom(12)
    data = AESGCM(key).encrypt(nonce, json.dumps(obj, ensure_ascii=False).encode('utf-8'), None)
    wrapped = pub.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    b = lambda x: base64.b64encode(x).decode()
    return {'v': 1, 'alg': 'RSA-OAEP-SHA256 + AES-256-GCM', 'key': b(wrapped), 'nonce': b(nonce), 'data': b(data)}


def main():
    now = datetime.datetime.now(KST)
    result = {'collected_at': now.isoformat(timespec='seconds'), 'api': API, 'accounts': {}}
    for name, acc in CFG['accounts'].items():
        tok = os.environ.get(acc['token_secret'])
        if not tok: print(f'{name}: 토큰 비밀값 없음'); continue
        ig = acc.get('ig_user_id')
        media = []
        for rl in reels(name):
            rec, st = media_insights(rl['media_id'], tok)
            media.append({**rl, **rec})
            print(f'{name} {rl["post_id"]}: ' + ', '.join(f'{k} {v}' for k, v in st.items()))
        acc_rows, ast = account_insights(ig, tok) if ig else ([], {})
        print(f'{name} 계정: ' + ', '.join(f'{k} {v}' for k, v in ast.items()))
        result['accounts'][name] = {'reels': media, 'account_daily': acc_rows}
    OUT.mkdir(parents=True, exist_ok=True)
    fn = now.strftime('%Y%m%d_%H%M') + '.enc.json'
    (OUT / fn).write_text(json.dumps(encrypt(result)), encoding='utf-8')
    with open(OUT / '목록.txt', 'a', encoding='utf-8') as f: f.write(fn + '\n')
    print('저장', fn)


if __name__ == '__main__':
    main()
