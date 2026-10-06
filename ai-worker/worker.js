const ORIGIN = 'https://openrouter.ai';
function json(data, status=200){ return new Response(JSON.stringify(data), {status, headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store'}}); }
async function readJson(request){ try { return await request.json(); } catch { return {}; } }
function providerMessage(data){
  if (data && typeof data === 'object') {
    if (typeof data.error === 'string') return data.error;
    if (data.error && typeof data.error.message === 'string') return data.error.message;
    if (typeof data.message === 'string') return data.message;
  }
  return 'OpenRouter rejected the request.';
}
export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method !== 'POST') return json({error:'Service binding only.'},405);
    const input = await readJson(request);
    const key = String(input.api_key || '').trim();
    if (!key) return json({error:'AI service did not receive the server-side OpenRouter key.'},503);
    const headers = new Headers();
    headers.set('Authorization', `Bearer ${key}`);
    headers.set('Accept','application/json');
    headers.set('Content-Type','application/json');
    headers.set('HTTP-Referer','https://jworks.jeffmyall6.workers.dev');
    headers.set('X-Title','JWorks');
    if (url.pathname === '/key-test') {
      const r = await fetch(`${ORIGIN}/api/v1/key`, {method:'GET', headers, redirect:'manual'});
      let data; try { data=await r.json(); } catch { data={}; }
      return json({ok:r.ok,openrouter_reached:true,authenticated:r.ok,status:r.status,provider:'OpenRouter',error:r.ok?'':providerMessage(data)},200);
    }
    if (url.pathname === '/chat') {
      const payload={model:input.model||'openrouter/free',messages:Array.isArray(input.messages)?input.messages:[],temperature:Number(input.temperature??0.2)};
      const r=await fetch(`${ORIGIN}/api/v1/chat/completions`,{method:'POST',headers,body:JSON.stringify(payload),redirect:'manual'});
      let data; try { data=await r.json(); } catch { data={}; }
      if(!r.ok) return json({openrouter_reached:true,authenticated:false,status:r.status,error:`OpenRouter HTTP ${r.status}: ${providerMessage(data)}`},502);
      const content=data?.choices?.[0]?.message?.content;
      if(typeof content!=='string' || !content.trim()) return json({ok:false,openrouter_reached:true,authenticated:true,status:r.status,error:'OpenRouter returned HTTP 200 but no readable assistant message.',response_shape:Object.keys(data||{})},502);
      return json({ok:true,openrouter_reached:true,authenticated:true,status:r.status,content,model:data?.model||payload.model,data});
    }
    return json({error:'Unknown AI service route.'},404);
  }
};
