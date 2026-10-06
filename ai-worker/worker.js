const ORIGIN = 'https://openrouter.ai';

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store'
    }
  });
}

async function readJson(request) {
  try { return await request.json(); } catch { return {}; }
}

function providerMessage(data) {
  if (data && typeof data === 'object') {
    if (typeof data.error === 'string') return data.error;
    if (data.error && typeof data.error.message === 'string') return data.error.message;
    if (typeof data.message === 'string') return data.message;
  }
  return 'OpenRouter rejected the request.';
}

function normalizeKey(value) {
  let key = typeof value === 'string' ? value.trim() : '';
  // Protect against pasting a quoted value or "Bearer <key>" into Cloudflare.
  if ((key.startsWith('"') && key.endsWith('"')) || (key.startsWith("'") && key.endsWith("'"))) {
    key = key.slice(1, -1).trim();
  }
  key = key.replace(/^Bearer\s+/i, '').trim();
  return key;
}

function openRouterHeaders(key) {
  // Intentionally mirrors OpenRouter's documented fetch/cURL request shape.
  // Use a plain object so the exact Authorization field is passed directly to fetch().
  return {
    'Authorization': `Bearer ${key}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'HTTP-Referer': 'https://jworks.jeffmyall6.workers.dev',
    'X-OpenRouter-Title': 'JWorks'
  };
}

async function parseProviderResponse(response) {
  const text = await response.text();
  try { return text ? JSON.parse(text) : {}; }
  catch { return { message: text || 'OpenRouter returned an unreadable response.' }; }
}


async function authProbe(key) {
  const url = 'https://openrouter.ai/api/v1/key';
  const attempts = [];

  async function run(name, makeRequest) {
    try {
      const response = await makeRequest();
      const data = await parseProviderResponse(response);
      attempts.push({
        name,
        status: response.status,
        ok: response.ok,
        redirected: response.redirected,
        response_url: response.url,
        error: response.ok ? '' : providerMessage(data)
      });
      return response.ok;
    } catch (error) {
      attempts.push({name, status: 0, ok: false, redirected: false, response_url: '', error: String(error).slice(0, 240)});
      return false;
    }
  }

  if (await run('literal-headers', () => fetch(url, {
    method: 'GET',
    redirect: 'manual',
    headers: { Authorization: `Bearer ${key}`, Accept: 'application/json' }
  }))) return {authenticated: true, working_method: 'literal-headers', attempts};

  if (await run('headers-object', () => {
    const h = new Headers();
    h.set('Authorization', `Bearer ${key}`);
    h.set('Accept', 'application/json');
    return fetch(url, {method: 'GET', redirect: 'manual', headers: h});
  })) return {authenticated: true, working_method: 'headers-object', attempts};

  if (await run('request-object', () => {
    const req = new Request(url, {
      method: 'GET', redirect: 'manual',
      headers: { Authorization: `Bearer ${key}`, Accept: 'application/json' }
    });
    return fetch(req);
  })) return {authenticated: true, working_method: 'request-object', attempts};

  if (await run('lowercase-authorization', () => fetch(url, {
    method: 'GET', redirect: 'manual',
    headers: { authorization: `Bearer ${key}`, accept: 'application/json' }
  }))) return {authenticated: true, working_method: 'lowercase-authorization', attempts};

  return {authenticated: false, working_method: '', attempts};
}

async function openRouterFetch(url, init, key) {
  // Prefer the standard literal-header request. If the runtime behaves differently,
  // the diagnostic probe tells us exactly which construction authenticated.
  const headers = {...(init.headers || {}), Authorization: `Bearer ${key}`};
  return fetch(url, {...init, headers, redirect: 'manual'});
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== 'POST') return json({ error: 'Service binding only.' }, 405);

    const input = await readJson(request);
    if (url.pathname === '/support-email') {
      const resendKey = normalizeKey(env?.RESEND_API_KEY);
      if (!resendKey) return json({ok:false,error:'RESEND_API_KEY is not configured on jworks-ai.'}, 503);
      const to = String(input.to || '').trim();
      if (!to) return json({ok:false,error:'Support destination is not configured.'}, 400);
      const from = String(env?.SUPPORT_FROM_EMAIL || 'JWorks Support <support@jworks.app>');
      const response = await fetch('https://api.resend.com/emails', {method:'POST',headers:{'Authorization':`Bearer ${resendKey}`,'Content-Type':'application/json'},body:JSON.stringify({from,to:[to],subject:String(input.subject||'JWorks Support'),text:String(input.text||'')})});
      const data = await parseProviderResponse(response);
      return json({ok:response.ok,status:response.status,id:data?.id||'',error:response.ok?'':providerMessage(data)}, response.ok?200:502);
    }
    const rawSecretPresent = env?.OPENROUTER_API_KEY !== undefined && env?.OPENROUTER_API_KEY !== null;
    const key = normalizeKey(env?.OPENROUTER_API_KEY);
    const headers = openRouterHeaders(key);

    if (url.pathname === '/diagnostics') {
      const probe = key ? await authProbe(key) : {authenticated:false,working_method:'',attempts:[]};
      return json({
        ok: Boolean(key),
        ai_worker_reached: true,
        ai_worker_secret_present: rawSecretPresent,
        ai_worker_secret_nonempty: Boolean(key),
        authorization_header_present: typeof headers.Authorization === 'string' && headers.Authorization.startsWith('Bearer ') && headers.Authorization.length > 7,
        key_format_openrouter: /^sk-or-/i.test(key),
        key_length: key.length,
        key_normalized: true,
        outbound_header_style: 'plain-object-literal',
        auth_probe_authenticated: probe.authenticated,
        auth_probe_working_method: probe.working_method,
        auth_probe_attempts: probe.attempts,
        transport: 'JWorks Python -> jworks-ai -> native JavaScript fetch -> OpenRouter'
      });
    }

    if (!key) {
      return json({
        error: 'OPENROUTER_API_KEY is not configured on the jworks-ai Worker.',
        ai_worker_secret_present: rawSecretPresent,
        ai_worker_secret_nonempty: false
      }, 503);
    }

    if (url.pathname === '/key-test') {
      const probe = await authProbe(key);
      const last = probe.attempts[probe.attempts.length - 1] || {};
      return json({
        ok: probe.authenticated,
        openrouter_reached: probe.attempts.length > 0,
        authenticated: probe.authenticated,
        status: probe.authenticated ? 200 : Number(last.status || 0),
        provider: 'OpenRouter',
        key_format_openrouter: /^sk-or-/i.test(key),
        key_length: key.length,
        working_method: probe.working_method,
        attempts: probe.attempts,
        error: probe.authenticated ? '' : String(last.error || 'All OpenRouter authentication probes failed.')
      });
    }

    if (url.pathname === '/chat') {
      const payload = {
        model: input.model || 'openrouter/free',
        messages: Array.isArray(input.messages) ? input.messages : [],
        temperature: Number(input.temperature ?? 0.2)
      };

      // This is deliberately the same native fetch shape shown in OpenRouter docs.
      const response = await openRouterFetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'HTTP-Referer': 'https://jworks.jeffmyall6.workers.dev',
          'X-OpenRouter-Title': 'JWorks'
        },
        body: JSON.stringify(payload)
      }, key);

      const data = await parseProviderResponse(response);
      if (!response.ok) {
        return json({
          openrouter_reached: true,
          authenticated: false,
          status: response.status,
          key_format_openrouter: /^sk-or-/i.test(key),
          outbound_header_style: 'plain-object-literal',
          error: `OpenRouter HTTP ${response.status}: ${providerMessage(data)}`
        }, 502);
      }

      const content = data?.choices?.[0]?.message?.content;
      if (typeof content !== 'string' || !content.trim()) {
        return json({
          ok: false,
          openrouter_reached: true,
          authenticated: true,
          status: response.status,
          error: 'OpenRouter returned HTTP 200 but no readable assistant message.',
          response_shape: Object.keys(data || {})
        }, 502);
      }

      return json({
        ok: true,
        openrouter_reached: true,
        authenticated: true,
        status: response.status,
        content,
        model: data?.model || payload.model,
        data
      });
    }

    return json({ error: 'Unknown AI service route.' }, 404);
  }
};
