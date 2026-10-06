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
    'X-Title': 'JWorks'
  };
}

async function parseProviderResponse(response) {
  const text = await response.text();
  try { return text ? JSON.parse(text) : {}; }
  catch { return { message: text || 'OpenRouter returned an unreadable response.' }; }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method !== 'POST') return json({ error: 'Service binding only.' }, 405);

    const input = await readJson(request);
    const rawSecretPresent = env?.OPENROUTER_API_KEY !== undefined && env?.OPENROUTER_API_KEY !== null;
    const key = normalizeKey(env?.OPENROUTER_API_KEY);
    const headers = openRouterHeaders(key);

    if (url.pathname === '/diagnostics') {
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
      const response = await fetch('https://openrouter.ai/api/v1/key', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${key}`,
          'Accept': 'application/json'
        }
      });
      const data = await parseProviderResponse(response);
      return json({
        ok: response.ok,
        openrouter_reached: true,
        authenticated: response.ok,
        status: response.status,
        provider: 'OpenRouter',
        key_format_openrouter: /^sk-or-/i.test(key),
        outbound_header_style: 'plain-object-literal',
        error: response.ok ? '' : providerMessage(data)
      });
    }

    if (url.pathname === '/chat') {
      const payload = {
        model: input.model || 'openrouter/free',
        messages: Array.isArray(input.messages) ? input.messages : [],
        temperature: Number(input.temperature ?? 0.2)
      };

      // This is deliberately the same native fetch shape shown in OpenRouter docs.
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${key}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'HTTP-Referer': 'https://jworks.jeffmyall6.workers.dev',
          'X-Title': 'JWorks'
        },
        body: JSON.stringify(payload)
      });

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
