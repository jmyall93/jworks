from flask import Flask, Response, jsonify, request
from pyodide.ffi import run_sync
from workers import wsgi
from datetime import datetime, timedelta, timezone
import hashlib, hmac, secrets, uuid, json

app=Flask(__name__)
def env(): return request.environ['workers.env']
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def uid(): return str(uuid.uuid4())
def q(sql,*args): return run_sync(env().DB.prepare(sql).bind(*args).run())
def first(sql,*args): return run_sync(env().DB.prepare(sql).bind(*args).first())
def py(v):
    try: return v.to_py()
    except Exception: return v
def val(r,key,default=None):
    if r is None:return default
    try:return py(getattr(r,key))
    except Exception:
        try:return py(r[key])
        except Exception:return default
def rows(sql,*args):
    r=q(sql,*args); x=py(r.results)
    return [dict(py(i)) for i in x]
def body(): return request.get_json(silent=True) or {}
def hash_password(p,salt=None):
    salt=salt or secrets.token_hex(16); dk=hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(salt),210000)
    return 'pbkdf2_sha256$210000$'+salt+'$'+dk.hex()
def verify_password(p,stored):
    try:
        _,n,salt,digest=stored.split('$',3); got=hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(salt),int(n)).hex(); return hmac.compare_digest(got,digest)
    except Exception:return False
def current_user():
    sid=request.cookies.get('jworks_session');
    if not sid:return None
    r=first("SELECT u.id,u.username,s.csrf,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.id=?",sid)
    if not r:return None
    if str(val(r,'expires_at',''))<now(): q('DELETE FROM sessions WHERE id=?',sid); return None
    return r
def require_user(csrf=False):
    u=current_user()
    if not u:return None,(jsonify(error='Authentication required'),401)
    if csrf and request.headers.get('X-CSRF-Token','')!=str(val(u,'csrf','')):return None,(jsonify(error='Security token expired. Refresh and try again.'),403)
    return u,None
def session_response(u,sid,csrf):
    r=jsonify(authenticated=True,username=str(u.username),csrf=csrf)
    r.set_cookie('jworks_session',sid,max_age=604800,httponly=True,secure=True,samesite='Lax',path='/')
    return r

def create_session(user_id,username):
    sid=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24); exp=(datetime.now(timezone.utc)+timedelta(days=7)).replace(microsecond=0).isoformat().replace('+00:00','Z')
    q('INSERT INTO sessions(id,user_id,csrf,expires_at,created_at) VALUES(?,?,?,?,?)',sid,user_id,csrf,exp,now())
    class U: pass
    u=U();u.username=username
    return session_response(u,sid,csrf)

@app.get('/api/health')
def health():
    try: ok=bool(first('SELECT 1 AS ok'))
    except Exception as e:return jsonify(ok=False,database=False,error=str(e)),503
    return jsonify(ok=True,app='JWorks',version='10.2.6-cloud',database=ok,storage=False)
@app.get('/api/setup-needed')
def setup_needed():
    try:r=first('SELECT COUNT(*) AS n FROM users');return jsonify(needed=(first('SELECT id FROM users LIMIT 1') is None))
    except Exception:return jsonify(needed=True,error='D1 migrations are not complete'),503
@app.get('/api/session')
def session_status():
    u=current_user()
    return jsonify(authenticated=bool(u),username=(str(val(u,'username','')) if u else None),csrf=(str(val(u,'csrf','')) if u else None))
@app.post('/api/setup')
def setup():
    if first('SELECT id FROM users LIMIT 1') is not None: return jsonify(error='Administrator already exists'),409
    d=body(); username=str(d.get('username','')).strip(); password=str(d.get('password',''))
    if len(username)<3:return jsonify(error='Username must be at least 3 characters'),400
    if len(password)<12:return jsonify(error='Password must be at least 12 characters'),400
    i=uid();q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',i,username,hash_password(password),now());return create_session(i,username)
@app.post('/api/login')
def login():
    d=body();r=first('SELECT id,username,password_hash FROM users WHERE username=?',str(d.get('username','')).strip())
    if not r or not verify_password(str(d.get('password','')),str(val(r,'password_hash',''))):return jsonify(error='Invalid username or password'),401
    return create_session(str(val(r,'id','')),str(val(r,'username','')))
@app.post('/api/logout')
def logout():
    sid=request.cookies.get('jworks_session');
    if sid:q('DELETE FROM sessions WHERE id=?',sid)
    r=jsonify(ok=True);r.delete_cookie('jworks_session',path='/');return r

STATE_TABLES=['projects','tasks','checklist','milestones','attachments','activity','phases','costs','issues','baselines','inbox','notifications','meetings','changes','report_snapshots','saved_views','automation_rules','report_revisions','recurring_projects','decisions','procurement','field_reports','project_templates','approvals','scopes_of_work']
@app.get('/api/state')
def state():
    u,e=require_user();
    if e:return e
    out={}
    for t in STATE_TABLES:
        try:out[t]=rows(f'SELECT * FROM {t} WHERE owner_id=?',str(u.id))
        except Exception:out[t]=[]
    return jsonify(out)

PROJECT_FIELDS=['created_at','name','description','start_date','end_date','status','asset','contractor','po_number','estimated_cost','actual_cost','shutdown_required','commissioning','closeout','notes','project_code','forecast_cost','contingency']
TASK_FIELDS=['created_at','project_id','name','start_date','due_date','status','priority','notes','depends_on','recurring','recurring_from','progress','duration_days','dependency_type']
def insert_named(table,owner,fields,d,defaults=None):
    defaults=defaults or {}; i=uid(); vals=[]; cols=['id','owner_id']
    for f in fields:
        if f in d or f in defaults: cols.append(f);vals.append(d.get(f,defaults.get(f)))
    q(f"INSERT INTO {table}({','.join(cols)}) VALUES({','.join(['?']*len(cols))})",i,owner,*vals);return i
def patch_named(table,idv,owner,fields,d):
    use=[f for f in fields if f in d]
    if use:q(f"UPDATE {table} SET "+','.join(f'{f}=?' for f in use)+' WHERE id=? AND owner_id=?',*[d[f] for f in use],idv,owner)

@app.post('/api/projects')
def project_create():
    u,e=require_user(True);
    if e:return e
    d=body();
    if not str(d.get('name','')).strip():return jsonify(error='Project name is required'),400
    n=first('SELECT COUNT(*) AS n FROM projects WHERE owner_id=?',str(u.id)); code=f"JW-{int(n.n)+1:04d}"
    i=insert_named('projects',str(u.id),PROJECT_FIELDS,d,{'name':d['name'],'description':'','status':'active','commissioning':'not_started','project_code':code,'created_at':now()})
    return jsonify(id=i)
@app.patch('/api/projects/<idv>')
def project_patch(idv):
    u,e=require_user(True);
    if e:return e
    patch_named('projects',idv,str(u.id),PROJECT_FIELDS,body());return jsonify(ok=True)
@app.delete('/api/projects/<idv>')
def project_delete(idv):
    u,e=require_user(True);
    if e:return e
    q('DELETE FROM projects WHERE id=? AND owner_id=?',idv,str(u.id));return jsonify(ok=True)
@app.post('/api/tasks')
def task_create():
    u,e=require_user(True);
    if e:return e
    d=body();i=insert_named('tasks',str(u.id),TASK_FIELDS,d,{'name':d.get('name','Untitled task'),'status':'todo','priority':'medium','notes':'','recurring':'','progress':0,'duration_days':1,'dependency_type':'FS','created_at':now()});return jsonify(id=i)
@app.patch('/api/tasks/<idv>')
def task_patch(idv):
    u,e=require_user(True);
    if e:return e
    patch_named('tasks',idv,str(u.id),TASK_FIELDS,body());return jsonify(ok=True)
@app.delete('/api/tasks/<idv>')
def task_delete(idv):
    u,e=require_user(True);
    if e:return e
    q('DELETE FROM tasks WHERE id=? AND owner_id=?',idv,str(u.id));return jsonify(ok=True)

SIMPLE={
'checklist':('checklist',['task_id','title','done','sort_order']), 'milestones':('milestones',['project_id','title','due_date','done']),
'costs':('costs',['project_id','title','vendor','po_number','amount','status','cost_date','notes']), 'issues':('issues',['project_id','title','kind','severity','status','owner_name','due_date','notes']),
'inbox':('inbox',['title','notes']), 'meetings':('meetings',['project_id','title','meeting_date','attendees','notes','decisions']),
'changes':('changes',['project_id','title','description','cost_impact','schedule_days','status']), 'decisions':('decisions',['project_id','decision_no','title','decision','status','decided_by','decision_date']),
'procurement':('procurement',['project_id','item','vendor','status','rfq_date','po_number','delivery_date','amount','notes']), 'field-reports':('field_reports',['project_id','report_date','contractor','personnel','weather','work_completed','issues','safety','next_work'])}
@app.post('/api/<kind>')
def simple_create(kind):
    if kind not in SIMPLE:return jsonify(error='Not implemented in cloud yet'),503
    u,e=require_user(True);
    if e:return e
    table,fields=SIMPLE[kind];d=body();
    if kind=='decisions' and not d.get('decision_no'):
        r=first('SELECT COUNT(*) AS n FROM decisions WHERE project_id=? AND owner_id=?',str(d.get('project_id','')),str(u.id));d['decision_no']=f"DEC-{int(r.n)+1:03d}"
    if kind in ['costs','issues','inbox','meetings','changes','decisions','procurement','field-reports']:
        d['created_at']=now();fields=fields+['created_at']
    i=insert_named(table,str(u.id),fields,d);return jsonify(id=i)
@app.route('/api/<kind>/<idv>',methods=['PATCH','DELETE'])
def simple_change(kind,idv):
    if kind not in SIMPLE and kind!='notifications':return jsonify(error='Not implemented in cloud yet'),503
    u,e=require_user(True);
    if e:return e
    if kind=='notifications':
        if request.method=='PATCH':q('UPDATE notifications SET is_read=1 WHERE id=? AND owner_id=?',idv,str(u.id))
        return jsonify(ok=True)
    table,fields=SIMPLE[kind]
    if request.method=='DELETE':q(f'DELETE FROM {table} WHERE id=? AND owner_id=?',idv,str(u.id))
    else:patch_named(table,idv,str(u.id),fields,body())
    return jsonify(ok=True)

@app.post('/api/scopes')
def sow_create():
    u,e=require_user(True);
    if e:return e
    d=body(); pid=str(d.get('project_id','')); p=first('SELECT id,name,description,asset FROM projects WHERE id=? AND owner_id=?',pid,str(u.id))
    if not p:return jsonify(error='Project not found'),404
    sections=d.get('sections') or default_sow_sections(p)
    i=uid();t=str(d.get('title') or f'{p.name} - Scope of Work');ts=now();q('INSERT INTO scopes_of_work(id,project_id,owner_id,title,status,revision,content_json,source_mode,ai_prompt,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',i,pid,str(u.id),t,'draft',0,json.dumps(sections),str(d.get('source_mode','manual')),str(d.get('ai_prompt','')),ts,ts);return jsonify(id=i)
@app.patch('/api/scopes/<idv>')
def sow_patch(idv):
    u,e=require_user(True);
    if e:return e
    d=body(); fields=[];vals=[]
    for f in ['title','status','source_mode','ai_prompt']:
        if f in d:fields.append(f+'=?');vals.append(d[f])
    if 'sections' in d:fields.append('content_json=?');vals.append(json.dumps(d['sections']))
    if fields:fields.append('updated_at=?');vals.append(now());q('UPDATE scopes_of_work SET '+','.join(fields)+' WHERE id=? AND owner_id=?',*vals,idv,str(u.id))
    return jsonify(ok=True)
@app.delete('/api/scopes/<idv>')
def sow_delete(idv):
    u,e=require_user(True);
    if e:return e
    q('DELETE FROM scopes_of_work WHERE id=? AND owner_id=?',idv,str(u.id));return jsonify(ok=True)

def default_sow_sections(p):
    return [
      {'title':'1. Project Overview','body':str(getattr(p,'description','') or 'Describe the purpose, background, and desired outcome of the work.')},
      {'title':'2. Existing Conditions','body':'Document relevant existing site and equipment conditions.'},
      {'title':'3. Detailed Scope of Work','body':'Define the work the contractor shall provide, including labour, materials, equipment, supervision, and coordination.'},
      {'title':'4. Contractor Responsibilities','body':'Define contractor responsibilities, protection of existing facilities, housekeeping, and coordination.'},
      {'title':'5. Owner Responsibilities','body':'Define owner-furnished information, access, utilities, escorts, shutdown approvals, or materials.'},
      {'title':'6. Site Access & Work Restrictions','body':'Define permitted work hours, access routes, operational restrictions, security requirements, and required notices.'},
      {'title':'7. Safety, Permits & Compliance','body':'Identify applicable safety requirements, permits, codes, standards, and site-specific procedures.'},
      {'title':'8. Testing & Commissioning','body':'Define inspections, testing, startup, commissioning, acceptance criteria, and deficiency correction.'},
      {'title':'9. Submittals & Documentation','body':'List drawings, product data, procedures, schedules, reports, as-builts, O&M manuals, and closeout documents.'},
      {'title':'10. Schedule & Milestones','body':'Define required start/completion dates, sequencing, milestones, outage windows, and coordination requirements.'},
      {'title':'11. Cleanup & Restoration','body':'Define cleanup, disposal, restoration, and protection requirements.'},
      {'title':'12. Warranty','body':'Define required warranty period and warranty response obligations.'},
      {'title':'13. Bid / Pricing Requirements','body':'Define lump-sum or unit pricing, allowances, alternates, exclusions, taxes, and required bid breakdown.'},
      {'title':'14. Exclusions / Clarifications','body':'Record explicit exclusions, assumptions, owner-supplied items, and required bidder clarifications.'}
    ]

@app.post('/api/scopes/ai-draft')
def sow_ai():
    u,e=require_user(True);
    if e:return e
    d=body();prompt=str(d.get('prompt','')).strip();pid=str(d.get('project_id',''));p=first('SELECT name,description,asset,contractor,start_date,end_date FROM projects WHERE id=? AND owner_id=?',pid,str(u.id))
    if not p:return jsonify(error='Project not found'),404
    try:key=str(env().OPENROUTER_API_KEY)
    except Exception:key=''
    if not key:return jsonify(error='AI is not configured yet. Add OPENROUTER_API_KEY as a Cloudflare Worker secret, or use Manual/Hybrid mode.'),503
    try:
        from js import fetch, Headers
        system='You are a construction and maintenance scope-of-work drafting assistant. Produce contractor-bid-ready content. Never invent site facts. Mark unknowns as [TO CONFIRM]. Return ONLY JSON: {"title":"...","sections":[{"title":"...","body":"..."}],"review_flags":["..."]}. Include project overview, existing conditions, detailed scope, contractor and owner responsibilities, access/work restrictions, safety/permits/compliance, testing/commissioning, submittals, schedule/milestones, cleanup/restoration, warranty, bid/pricing requirements, exclusions/clarifications.'
        context=f"Project: {p.name}\nDescription: {p.description}\nAsset: {p.asset}\nStart: {p.start_date}\nTarget: {p.end_date}\nUser instructions: {prompt}"
        payload=json.dumps({'model':'openrouter/auto','messages':[{'role':'system','content':system},{'role':'user','content':context}],'temperature':0.2})
        headers=Headers.new();headers.set('Authorization','Bearer '+key);headers.set('Content-Type','application/json')
        resp=run_sync(fetch('https://openrouter.ai/api/v1/chat/completions',{'method':'POST','headers':headers,'body':payload}))
        txt=run_sync(resp.text()); raw=json.loads(str(txt))
        if not resp.ok:return jsonify(error='AI provider error',detail=raw),502
        content=raw['choices'][0]['message']['content'].strip();content=content.replace('```json','').replace('```','').strip();out=json.loads(content);return jsonify(out)
    except Exception as exc:return jsonify(error='AI draft failed',detail=str(exc)),502

@app.route('/api/<path:path>',methods=['GET','POST','PUT','PATCH','DELETE'])
def pending(path):return jsonify(error='This feature is still being converted to the JWorks cloud backend.',route=path),503
@app.get('/')
@app.get('/<path:path>')
def frontend(path=''):
    # Cloudflare ASSETS resolves against the request pathname. Using a synthetic
    # assets.local hostname caused deployed /static/* requests to return 404.
    a=env().ASSETS
    ap=path or 'index.html'
    origin=request.host_url.rstrip('/')
    r=run_sync(a.fetch(f'{origin}/{ap}'))
    if r.status==404 and '.' not in ap:
        r=run_sync(a.fetch(f'{origin}/index.html'))
    return Response(run_sync(r.bytes()),status=r.status,headers=r.headers)
Default=wsgi.entrypoint(app)
