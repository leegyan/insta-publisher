# Cloudflare Workers AI(무료 하루 10,000 뉴런)로 주제 그림을 만든다. GitHub Actions(.github/workflows/gen_image.yml)에서 실행한다
# 환경 변수: CF_ACCOUNT_ID, CF_API_TOKEN (GitHub 저장소 Secret — Gyan 이 직접 넣음. 값은 출력하지 않는다)
# 쓰는 법: python3 ranking/cf_image.py <요청.json> <결과폴더>
#   요청.json: [{"name": "라면", "prompt": "…"}, …]  → <결과폴더>/<name>.png
import base64, json, os, sys, urllib.request, urllib.error, pathlib

MODEL = os.environ.get('CF_MODEL', '@cf/black-forest-labs/flux-1-schnell')
STYLE = ('Glossy 3D emoji-style icon, a single object centered, soft studio lighting, '
         'on a completely plain flat warm cream background (#FFF7EB), lots of empty space around the object, '
         'no text, no letters, no logos, no watermark.')

def run(prompt):
    acc, tok = os.environ['CF_ACCOUNT_ID'], os.environ['CF_API_TOKEN']
    url = f'https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/{MODEL}'
    body = json.dumps({'prompt': f'{prompt}. {STYLE}', 'steps': 8}).encode()
    req = urllib.request.Request(url, data=body, headers={'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(req, timeout=120)
    except urllib.error.HTTPError as e:
        sys.exit(f'Cloudflare 오류 HTTP {e.code}: {e.read()[:300].decode(errors="replace")}')
    raw = r.read()
    if r.headers.get('Content-Type', '').startswith('image/'):
        return raw
    d = json.loads(raw)
    if not d.get('success', True) and 'result' not in d:
        sys.exit(f'Cloudflare 실패: {str(d)[:300]}')
    return base64.b64decode(d['result']['image'])

def main(req_path, out):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    for it in json.loads(pathlib.Path(req_path).read_text(encoding='utf-8')):
        png = run(it['prompt'])
        f = out / f"{it['name']}.png"; f.write_bytes(png)
        print('그림', f, len(png), '바이트')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
