// Instagram 웹훅 받는 곳(돈나무 연구소 · insta-publisher). 댓글 · DM 이 오면 GitHub 워크플로우 'DM 즉시'를 깨운다
// 토큰 · 비밀값은 여기 적지 않는다 — Vercel 환경 변수: VERIFY_TOKEN(웹훅 확인 문자열) · APP_SECRET(Meta 앱 시크릿, 서명 확인) · GH_DISPATCH_TOKEN(GitHub 토큰, actions 쓰기)
const crypto = require('crypto');

module.exports = async (req, res) => {
  if (req.method === 'GET') {   // Meta 가 웹훅 주소를 등록할 때 한 번 확인
    const q = req.query || {};
    if (q['hub.mode'] === 'subscribe' && q['hub.verify_token'] === process.env.VERIFY_TOKEN) return res.status(200).send(q['hub.challenge']);
    return res.status(403).send('forbidden');
  }
  if (req.method !== 'POST') return res.status(405).end();
  const raw = await new Promise(r => { let b = ''; req.on('data', c => b += c); req.on('end', () => r(b)); });
  if (process.env.APP_SECRET) {   // Meta 가 보낸 것인지 서명 확인
    const sig = req.headers['x-hub-signature-256'] || '';
    const mine = 'sha256=' + crypto.createHmac('sha256', process.env.APP_SECRET).update(raw).digest('hex');
    if (sig.length !== mine.length || !crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(mine))) return res.status(401).send('bad signature');
  }
  let body = {}; try { body = JSON.parse(raw); } catch (e) {}
  const events = [];
  for (const en of body.entry || []) {
    for (const m of en.messaging || []) {   // DM(받은 메시지 · 빠른 답장 누름). 우리가 보낸 메시지(is_echo)는 뺀다
      if (m.message && !m.message.is_echo && m.sender && m.sender.id !== en.id) events.push({ kind: 'message', account_id: en.id, sender: m.sender.id });
    }
    for (const ch of en.changes || []) {   // 댓글
      if (ch.field === 'comments' && ch.value && ch.value.id && !(ch.value.from && ch.value.from.id === en.id))
        events.push({ kind: 'comment', account_id: en.id, comment_id: ch.value.id, media_id: (ch.value.media || {}).id });
    }
  }
  if (events.length && process.env.GH_DISPATCH_TOKEN) {
    await fetch('https://api.github.com/repos/leegyan/insta-publisher/dispatches', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + process.env.GH_DISPATCH_TOKEN, 'Accept': 'application/vnd.github+json', 'User-Agent': 'cashwood-hook' },
      body: JSON.stringify({ event_type: 'ig_event', client_payload: { events } })
    }).catch(() => {});
  }
  return res.status(200).send('ok');   // Meta 에는 항상 바로 200(늦으면 다시 보냄)
};
