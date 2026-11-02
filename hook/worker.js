// Instagram 웹훅 받는 곳(돈나무 연구소 · insta-publisher) — Cloudflare Workers 판
// 댓글 · DM 이 오면 GitHub 워크플로우 dm_hook.yml(repository_dispatch ig_event)을 깨운다
// 토큰 · 비밀값은 여기 적지 않는다. Cloudflare 의 Worker 설정 → 변수 및 비밀(Variables and Secrets)에 넣는다:
//   VERIFY_TOKEN       웹훅 확인 문자열(아무 무작위 문자열, Meta 웹훅 화면에도 같은 값)
//   APP_SECRET         Instagram 앱 시크릿(서명 확인)
//   GH_DISPATCH_TOKEN  GitHub 토큰(insta-publisher, Contents 읽기/쓰기)

const enc = new TextEncoder();

async function hmacHex(secret, raw) {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(raw));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, '0')).join('');
}

function sameText(a, b) {   // 길이가 같을 때 글자를 모두 비교(시간 차이로 값이 새지 않게)
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (request.method === 'GET') {   // Meta 가 웹훅 주소를 등록할 때 한 번 확인
      const q = url.searchParams;
      if (q.get('hub.mode') === 'subscribe' && env.VERIFY_TOKEN && q.get('hub.verify_token') === env.VERIFY_TOKEN)
        return new Response(q.get('hub.challenge') || '', { status: 200 });
      return new Response('forbidden', { status: 403 });
    }
    if (request.method !== 'POST') return new Response('', { status: 405 });

    const raw = await request.text();
    if (env.APP_SECRET) {   // Meta 가 보낸 것인지 서명 확인
      const sig = request.headers.get('x-hub-signature-256') || '';
      const mine = 'sha256=' + await hmacHex(env.APP_SECRET, raw);
      if (!sameText(sig, mine)) return new Response('bad signature', { status: 401 });
    }

    let body = {};
    try { body = JSON.parse(raw); } catch (e) {}
    const events = [];
    for (const en of body.entry || []) {
      for (const m of en.messaging || []) {   // DM(받은 메시지 · 빠른 답장 누름). 우리가 보낸 메시지(is_echo)는 뺀다
        if (m.message && !m.message.is_echo && m.sender && m.sender.id !== en.id)
          events.push({ kind: 'message', account_id: en.id, sender: m.sender.id });
      }
      for (const ch of en.changes || []) {   // 댓글
        if (ch.field === 'comments' && ch.value && ch.value.id && !(ch.value.from && ch.value.from.id === en.id))
          events.push({ kind: 'comment', account_id: en.id, comment_id: ch.value.id, media_id: (ch.value.media || {}).id });
      }
    }

    if (events.length && env.GH_DISPATCH_TOKEN) {   // 응답은 바로 하고 GitHub 호출은 뒤에서
      ctx.waitUntil(fetch('https://api.github.com/repos/leegyan/insta-publisher/dispatches', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + env.GH_DISPATCH_TOKEN, 'Accept': 'application/vnd.github+json', 'User-Agent': 'cashwood-hook' },
        body: JSON.stringify({ event_type: 'ig_event', client_payload: { events } })
      }).catch(() => {}));
    }
    return new Response('ok', { status: 200 });   // Meta 에는 항상 바로 200(늦으면 다시 보냄)
  }
};
