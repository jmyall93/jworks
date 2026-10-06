from flask import Flask, Response, jsonify, request
from pyodide.ffi import run_sync
from workers import wsgi, fetch as worker_fetch, env as worker_env
from datetime import datetime, timedelta, timezone
import hashlib, hmac, secrets, uuid, json, io, zipfile, re
import xml.etree.ElementTree as ET

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
# Portable salted password KDF for Cloudflare Python Workers/Pyodide.
# hashlib.pbkdf2_hmac is not available in the deployed runtime, so use a
# deliberately repeated SHA-256 construction with a per-password random salt.
# The stored format is versioned so the KDF can be upgraded later.
_PASSWORD_ROUNDS=120000
def _portable_kdf(password,salt,rounds=_PASSWORD_ROUNDS):
    pwd=password.encode('utf-8'); salt_bytes=bytes.fromhex(salt)
    digest=hashlib.sha256(salt_bytes+b'\x00'+pwd).digest()
    for i in range(1,rounds):
        digest=hashlib.sha256(digest+salt_bytes+pwd+i.to_bytes(4,'big')).digest()
    return digest.hex()
def hash_password(p,salt=None):
    salt=salt or secrets.token_hex(16)
    return f'jworks_sha256_v1${_PASSWORD_ROUNDS}${salt}${_portable_kdf(p,salt,_PASSWORD_ROUNDS)}'
def verify_password(p,stored):
    try:
        scheme,n,salt,digest=stored.split('$',3)
        if scheme!='jworks_sha256_v1': return False
        got=_portable_kdf(p,salt,int(n))
        return hmac.compare_digest(got,digest)
    except Exception:return False
def current_user():
    sid=request.cookies.get('jworks_session');
    if not sid:return None
    r=first("SELECT u.id,u.username,s.csrf,s.expires_at,m.company_id,m.role,c.name AS company_name,c.login_code,c.logo_data_url,c.report_footer,c.status AS company_status FROM sessions s JOIN users u ON u.id=s.user_id LEFT JOIN company_memberships m ON m.user_id=u.id AND m.status='active' LEFT JOIN companies c ON c.id=m.company_id WHERE s.id=? ORDER BY CASE m.role WHEN 'platform_owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END LIMIT 1",sid)
    if not r:return None
    if str(val(r,'expires_at',''))<now(): q('DELETE FROM sessions WHERE id=?',sid); return None
    return r
def require_user(csrf=False):
    u=current_user()
    if not u:return None,(jsonify(error='Authentication required'),401)
    if csrf and request.headers.get('X-CSRF-Token','')!=str(val(u,'csrf','')):return None,(jsonify(error='Security token expired. Refresh and try again.'),403)
    return u,None
def session_response(u,sid,csrf):
    m=first("SELECT m.company_id,m.role,c.name AS company_name,c.login_code,c.logo_data_url,c.report_footer FROM company_memberships m JOIN companies c ON c.id=m.company_id WHERE m.user_id=? AND m.status='active' ORDER BY CASE m.role WHEN 'platform_owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END LIMIT 1",str(getattr(u,'id','')))
    r=jsonify(authenticated=True,username=str(u.username),csrf=csrf,company_id=str(val(m,'company_id','')),company_name=str(val(m,'company_name','')),company_code=str(val(m,'login_code','')),role=str(val(m,'role','user')),company_logo=str(val(m,'logo_data_url','')),report_footer=str(val(m,'report_footer','Generated with JWorks')))
    r.set_cookie('jworks_session',sid,max_age=604800,httponly=True,secure=True,samesite='Lax',path='/')
    return r

def create_session(user_id,username):
    sid=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(24); exp=(datetime.now(timezone.utc)+timedelta(days=7)).replace(microsecond=0).isoformat().replace('+00:00','Z')
    q('INSERT INTO sessions(id,user_id,csrf,expires_at,created_at) VALUES(?,?,?,?,?)',sid,user_id,csrf,exp,now())
    class U: pass
    u=U();u.username=username;u.id=user_id
    return session_response(u,sid,csrf)

@app.get('/api/health')
def health():
    try: ok=bool(first('SELECT 1 AS ok'))
    except Exception as e:return jsonify(ok=False,database=False,error=str(e)),503
    return jsonify(ok=True,app='JWorks',version='11.2.1-cloud',database=ok,storage=False)
@app.get('/api/setup-needed')
def setup_needed():
    try:r=first('SELECT COUNT(*) AS n FROM users');return jsonify(needed=(first('SELECT id FROM users LIMIT 1') is None))
    except Exception:return jsonify(needed=True,error='D1 migrations are not complete'),503
@app.get('/api/session')
def session_status():
    u=current_user()
    return jsonify(authenticated=bool(u),username=(str(val(u,'username','')) if u else None),csrf=(str(val(u,'csrf','')) if u else None),company_id=(str(val(u,'company_id','')) if u else None),company_name=(str(val(u,'company_name','')) if u else None),company_code=(str(val(u,'login_code','')) if u else None),role=(str(val(u,'role','')) if u else None),company_logo=(str(val(u,'logo_data_url','')) if u else None),report_footer=(str(val(u,'report_footer','Generated with JWorks')) if u else None))
@app.post('/api/setup')
def setup():
    # First-run administrator creation. Keep each stage explicit so Cloudflare/D1
    # failures return a useful JSON error instead of an opaque HTTP 500.
    try:
        if first('SELECT id FROM users LIMIT 1') is not None:
            return jsonify(error='Administrator already exists'),409
    except Exception as e:
        return jsonify(error='Could not check administrator state',stage='check-users',detail=str(e)),500

    d=body(); username=str(d.get('username','')).strip(); password=str(d.get('password',''))
    if len(username)<3:return jsonify(error='Username must be at least 3 characters'),400
    if not password:return jsonify(error='Password is required'),400

    try:
        password_hash=hash_password(password)
    except Exception as e:
        return jsonify(error='Could not securely hash the password',stage='password-hash',detail=str(e)),500

    i=uid()
    try:
        q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',i,username,password_hash,now())
        q("INSERT OR IGNORE INTO companies(id,login_code,name,status,plan,seat_limit,report_footer,created_at) VALUES(?,?,?,?,?,?,?,?)",'jworks-owner-company','JWORKS-OWNER','My JWorks Workspace','active','owner',999,'Generated with JWorks',now())
        q("INSERT INTO company_memberships(company_id,user_id,role,status,created_at) VALUES(?,?,?,?,?)",'jworks-owner-company',i,'platform_owner','active',now())
        q("INSERT OR IGNORE INTO subscriptions(id,company_id,status,plan,seat_limit,starts_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",'jworks-owner-subscription','jworks-owner-company','active','owner',999,now(),now(),now())
    except Exception as e:
        return jsonify(error='Could not save the administrator to D1',stage='insert-user',detail=str(e)),500

    try:
        return create_session(i,username)
    except Exception as e:
        # Do not leave a half-created administrator that prevents first-run setup.
        try:q('DELETE FROM sessions WHERE user_id=?',i)
        except Exception:pass
        try:q('DELETE FROM users WHERE id=?',i)
        except Exception:pass
        return jsonify(error='Administrator could not be signed in; setup was rolled back',stage='create-session',detail=str(e)),500
@app.post('/api/login')
def login():
    d=body(); code=str(d.get('company_id','')).strip().upper(); username=str(d.get('username','')).strip()
    if not code:return jsonify(error='Company ID is required'),400
    r=first("SELECT u.id,u.username,u.password_hash,c.status,m.status AS member_status FROM users u JOIN company_memberships m ON m.user_id=u.id JOIN companies c ON c.id=m.company_id WHERE UPPER(c.login_code)=? AND u.username=?",code,username)
    if not r or str(val(r,'status','')) not in ('active','trial') or str(val(r,'member_status',''))!='active' or not verify_password(str(d.get('password','')),str(val(r,'password_hash',''))):
        return jsonify(error='Invalid Company ID, username or password'),401
    return create_session(str(val(r,'id','')),str(val(r,'username','')))

@app.post('/api/trial')
def trial_signup():
    d=body(); company=str(d.get('company_name','')).strip(); username=str(d.get('username','')).strip(); password=str(d.get('password',''))
    if len(company)<2 or len(username)<3 or not password:return jsonify(error='Company name, username and password are required'),400
    cid=uid(); user_id=uid(); code=('JW-'+secrets.token_hex(4)).upper(); ts=now(); trial=(datetime.now(timezone.utc)+timedelta(days=14)).replace(microsecond=0).isoformat().replace('+00:00','Z')
    try:
        q('INSERT INTO companies(id,login_code,name,status,plan,seat_limit,trial_ends_at,report_footer,created_at) VALUES(?,?,?,?,?,?,?,?,?)',cid,code,company,'trial','trial',5,trial,'Generated with JWorks',ts)
        q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',user_id,username,hash_password(password),ts)
        q('INSERT INTO company_memberships(company_id,user_id,role,status,created_at) VALUES(?,?,?,?,?)',cid,user_id,'admin','active',ts)
        q('INSERT INTO subscriptions(id,company_id,status,plan,seat_limit,starts_at,trial_ends_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',uid(),cid,'trial','trial',5,ts,trial,ts,ts)
        return jsonify(ok=True,company_id=code,trial_ends_at=trial)
    except Exception as exc:return jsonify(error='Could not create trial workspace: '+str(exc)),400

@app.post('/api/forgot-password')
def forgot_password():
    d=body(); code=str(d.get('company_id','')).strip().upper(); username=str(d.get('username','')).strip()
    r=first("SELECT u.id,c.id AS company_id FROM users u JOIN company_memberships m ON m.user_id=u.id JOIN companies c ON c.id=m.company_id WHERE UPPER(c.login_code)=? AND u.username=?",code,username)
    # Always return the same response to avoid account enumeration. Email delivery is intentionally not faked.
    if r:
        token=secrets.token_urlsafe(32); q('INSERT INTO password_reset_tokens(id,company_id,user_id,token_hash,expires_at,created_at) VALUES(?,?,?,?,?,?)',uid(),str(val(r,'company_id','')),str(val(r,'id','')),hashlib.sha256(token.encode()).hexdigest(),(datetime.now(timezone.utc)+timedelta(minutes=30)).replace(microsecond=0).isoformat().replace('+00:00','Z'),now())
    return jsonify(ok=True,email_configured=False,message='Password reset request recorded. Email delivery is not configured yet; contact your company administrator.')

@app.post('/api/logout')
def logout():
    sid=request.cookies.get('jworks_session');
    if sid:q('DELETE FROM sessions WHERE id=?',sid)
    r=jsonify(ok=True);r.delete_cookie('jworks_session',path='/');return r



def openrouter_secret_state():
    # 10.3.3: read the binding through Cloudflare's documented Python Workers env
    # object. Keep diagnostics boolean-only so credentials can never be exposed.
    state={'secret_present':False,'secret_nonempty':False,'secret_is_text':False}
    try:
        raw=worker_env.OPENROUTER_API_KEY
        state['secret_present']=raw is not None
        try:
            key=str(raw).strip()
            state['secret_is_text']=isinstance(key,str)
            state['secret_nonempty']=bool(key)
        except Exception:
            key=''
        return key,state
    except Exception:
        return '',state

def openrouter_key():
    return openrouter_secret_state()[0]

def provider_error(raw,status=None):
    """Return a useful provider error without ever exposing credentials."""
    msg='OpenRouter rejected the request.'
    try:
        data=raw if isinstance(raw,dict) else json.loads(str(raw))
        er=data.get('error',data) if isinstance(data,dict) else {}
        if isinstance(er,dict): msg=str(er.get('message') or er.get('code') or msg)
        elif er: msg=str(er)
    except Exception:
        t=str(raw).strip()
        if t: msg=t[:500]
    return msg[:500]

def ai_service_call(path,payload,diagnostics=None):
    """Call the internal jworks-ai Worker. Credentials are owned by jworks-ai only."""
    if diagnostics is not None:
        diagnostics['ai_service_binding']=True
        diagnostics['transport']='JWorks Python -> jworks-ai -> native JavaScript fetch -> OpenRouter'
    try:
        svc=env().AI
    except Exception:
        raise RuntimeError('JWorks AI service binding is not configured.')
    resp=run_sync(svc.fetch('https://jworks-ai.internal/'+path.lstrip('/'),method='POST',
                            headers={'Content-Type':'application/json'},body=json.dumps(dict(payload or {}))))
    try:
        parsed=run_sync(resp.json()); raw=dict(parsed) if parsed is not None else {}
    except Exception:
        try:
            txt=run_sync(resp.text()); raw=json.loads(str(txt))
        except Exception:
            raw={'error':'JWorks AI service returned an unreadable response.'}
    if diagnostics is not None:
        diagnostics['ai_service_reached']=True; diagnostics['ai_service_status']=int(resp.status)
    if not resp.ok:
        raise RuntimeError(str(raw.get('error','JWorks AI service rejected the request.'))[:500])
    return raw

def openrouter_chat(messages,model='openrouter/free',temperature=0.2,diagnostics=None):
    raw=ai_service_call('/chat',{'model':model,'messages':messages,'temperature':temperature},diagnostics)
    if diagnostics is not None:
        diagnostics['openrouter_reached']=bool(raw.get('openrouter_reached',True))
        diagnostics['openrouter_authenticated']=bool(raw.get('authenticated',True))
    try:
        content=raw.get('content') or raw['data']['choices'][0]['message']['content']
        if not content: raise ValueError('empty response')
        return str(content),raw.get('data') or {'model':raw.get('model',model)}
    except Exception:
        raise RuntimeError('OpenRouter returned a response JWorks could not read.')

@app.get('/api/ai-status')
def ai_status():
    u,e=require_user()
    if e:return e
    try:
        d=ai_service_call('/diagnostics',{})
        configured=bool(d.get('ai_worker_secret_nonempty'))
        return jsonify(enabled=configured,configured=configured,provider='OpenRouter',model='openrouter/free',message=('OpenRouter secret is configured on jworks-ai.' if configured else 'OPENROUTER_API_KEY is not configured on jworks-ai.'))
    except Exception as exc:
        return jsonify(enabled=False,configured=False,provider='OpenRouter',model='openrouter/free',message=str(exc)),200

@app.get('/api/ai-config')
def ai_config():
    u,e=require_user()
    if e:return e
    try:d=ai_service_call('/diagnostics',{})
    except Exception as exc:d={'error':str(exc)}
    return jsonify(provider='OpenRouter',model='openrouter/free',configured=bool(d.get('ai_worker_secret_nonempty')),
        secret_location='jworks-ai Cloudflare Worker secret',transport=d.get('transport','JWorks Python -> jworks-ai -> native JavaScript fetch -> OpenRouter'),
        ai_worker_secret_present=bool(d.get('ai_worker_secret_present')),ai_worker_secret_nonempty=bool(d.get('ai_worker_secret_nonempty')),
        authorization_header_present=bool(d.get('authorization_header_present')),diagnostic_version='11.2.7')

def openrouter_key_validation(diag):
    try:
        raw=ai_service_call('/key-test',{},diag)
        diag['key_endpoint_reached']=bool(raw.get('openrouter_reached',True)); diag['key_endpoint_status']=int(raw.get('status',200)); diag['key_authenticated']=bool(raw.get('authenticated',False))
        diag['key_probe_working_method']=str(raw.get('working_method',''))
        diag['key_probe_attempts']=raw.get('attempts') if isinstance(raw.get('attempts'),list) else []
        if not diag['key_authenticated']:diag['key_error']=str(raw.get('error','Authentication failed'))[:300]
        return diag['key_authenticated']
    except Exception as exc:
        diag['key_endpoint_reached']=False;diag['key_authenticated']=False;diag['key_error']=str(exc)[:300];return False

@app.post('/api/ai-test')
def ai_test():
    u,e=require_user(True)
    if e:return e
    diag={'transport':'JWorks Python -> jworks-ai -> native JavaScript fetch -> OpenRouter','diagnostic_version':'11.2.7'}
    try:
        d=ai_service_call('/diagnostics',{},diag)
        diag['ai_worker_reached']=bool(d.get('ai_worker_reached',True));diag['ai_worker_secret_present']=bool(d.get('ai_worker_secret_present'));diag['ai_worker_secret_nonempty']=bool(d.get('ai_worker_secret_nonempty'));diag['authorization_header_present']=bool(d.get('authorization_header_present'))
        diag['key_format_openrouter']=bool(d.get('key_format_openrouter'))
        diag['key_length']=int(d.get('key_length',0) or 0)
        diag['outbound_header_style']=str(d.get('outbound_header_style',''))
        diag['auth_probe_authenticated']=bool(d.get('auth_probe_authenticated'))
        diag['auth_probe_working_method']=str(d.get('auth_probe_working_method',''))
        diag['auth_probe_attempts']=d.get('auth_probe_attempts') if isinstance(d.get('auth_probe_attempts'),list) else []
    except Exception as exc:
        return jsonify(error=str(exc),diagnostics=diag),503
    if not diag['ai_worker_secret_nonempty']:
        return jsonify(error='OPENROUTER_API_KEY is not configured on the jworks-ai Worker.',diagnostics=diag),503
    openrouter_key_validation(diag)
    try:
        answer,raw=openrouter_chat([{'role':'user','content':'Reply with exactly: JWorks AI connection successful'}],model='openrouter/free',temperature=0,diagnostics=diag)
        diag['openrouter_reached']=True;diag['openrouter_authenticated']=True
        return jsonify(ok=True,message='OpenRouter connection successful.',model=str(raw.get('model','openrouter/free')),response=answer[:160],diagnostics=diag)
    except Exception as exc:
        diag['openrouter_reached']=True;diag['openrouter_authenticated']=False
        return jsonify(error=str(exc),diagnostics=diag),502

@app.get('/api/system-status')
def system_status():
    u,e=require_user()
    if e:return e
    try:
        projects=int(val(first('SELECT COUNT(*) AS n FROM projects WHERE owner_id=?',str(u.id)),'n',0) or 0)
        tasks=int(val(first('SELECT COUNT(*) AS n FROM tasks WHERE owner_id=?',str(u.id)),'n',0) or 0)
        attachments=int(val(first('SELECT COUNT(*) AS n FROM attachments WHERE owner_id=?',str(u.id)),'n',0) or 0)
        return jsonify(database='D1 connected',database_size=0,upload_size=0,projects=projects,tasks=tasks,attachments=attachments,backup='Cloudflare D1 managed storage')
    except Exception as exc:return jsonify(error='Could not load system status: '+str(exc)),500

def company_user_ids(u):
    cid=user_company(u)
    if not cid:return [str(val(u,'id',''))]
    return [str(x.get('user_id')) for x in rows("SELECT user_id FROM company_memberships WHERE company_id=? AND status='active'",cid)]
def company_owns(u,table,idv):
    ids=company_user_ids(u)
    if not ids:return False
    marks=','.join(['?']*len(ids)); return bool(first(f'SELECT id FROM {table} WHERE id=? AND owner_id IN ({marks})',idv,*ids))

STATE_TABLES=['projects','tasks','checklist','milestones','attachments','activity','phases','costs','issues','baselines','inbox','notifications','meetings','changes','report_snapshots','saved_views','automation_rules','report_revisions','recurring_projects','decisions','procurement','field_reports','project_templates','approvals','scopes_of_work']
@app.get('/api/state')
def state():
    u,e=require_user();
    if e:return e
    out={}; ids=company_user_ids(u); marks=','.join(['?']*len(ids))
    for t in STATE_TABLES:
        try:out[t]=rows(f'SELECT * FROM {t} WHERE owner_id IN ({marks})',*ids)
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
    
    if not company_owns(u,'projects',idv):return jsonify(error='Project not found'),404
    d=body(); use=[f for f in PROJECT_FIELDS if f in d]
    if use:q('UPDATE projects SET '+','.join(f'{f}=?' for f in use)+' WHERE id=?',*[d[f] for f in use],idv)
    return jsonify(ok=True)
@app.delete('/api/projects/<idv>')
def project_delete(idv):
    u,e=require_user(True);
    if e:return e
    
    if not company_owns(u,'projects',idv):return jsonify(error='Project not found'),404
    q('DELETE FROM projects WHERE id=?',idv);return jsonify(ok=True)
@app.post('/api/tasks')
def task_create():
    u,e=require_user(True);
    if e:return e
    d=body();i=insert_named('tasks',str(u.id),TASK_FIELDS,d,{'name':d.get('name','Untitled task'),'status':'todo','priority':'medium','notes':'','recurring':'','progress':0,'duration_days':1,'dependency_type':'FS','created_at':now()});return jsonify(id=i)
@app.patch('/api/tasks/<idv>')
def task_patch(idv):
    u,e=require_user(True);
    if e:return e
    
    if not company_owns(u,'tasks',idv):return jsonify(error='Task not found'),404
    d=body(); use=[f for f in TASK_FIELDS if f in d]
    if use:q('UPDATE tasks SET '+','.join(f'{f}=?' for f in use)+' WHERE id=?',*[d[f] for f in use],idv)
    return jsonify(ok=True)
@app.delete('/api/tasks/<idv>')
def task_delete(idv):
    u,e=require_user(True);
    if e:return e
    
    if not company_owns(u,'tasks',idv):return jsonify(error='Task not found'),404
    q('DELETE FROM tasks WHERE id=?',idv);return jsonify(ok=True)

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
    for f in ['title','status','source_mode','ai_prompt','document_project_code','revision_label','revision_date','revision_history_json']:
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
    d=body();prompt=str(d.get('prompt','')).strip();pid=str(d.get('project_id',''));p=first('SELECT name,description,asset,contractor,start_date,end_date FROM projects WHERE id=?',pid) if company_owns(u,'projects',pid) else None
    if not p:return jsonify(error='Project not found'),404
    try:
        system='You are a construction and maintenance scope-of-work drafting assistant. Produce contractor-bid-ready content. Never invent site facts. Mark unknowns as [TO CONFIRM] during drafting only; these markers are internal drafting flags and must be resolved before an approved-for-bid or issued contractor document is produced. Return ONLY JSON: {"title":"...","sections":[{"title":"...","body":"..."}],"review_flags":["..."]}. Include project overview, existing conditions, detailed scope, contractor and owner responsibilities, access/work restrictions, safety/permits/compliance, testing/commissioning, submittals, schedule/milestones, cleanup/restoration, warranty, bid/pricing requirements, exclusions/clarifications.'
        context=f"Project: {p.name}\nDescription: {p.description}\nAsset: {p.asset}\nStart: {p.start_date}\nTarget: {p.end_date}\nUser instructions: {prompt}"
        content,raw=openrouter_chat([{'role':'system','content':system},{'role':'user','content':context}],model='openrouter/free',temperature=0.2)
        content=content.strip().replace('```json','').replace('```','').strip()
        out=json.loads(content)
        if not isinstance(out.get('sections'),list):raise ValueError('AI response did not contain SOW sections.')
        return jsonify(out)
    except json.JSONDecodeError:
        return jsonify(error='OpenRouter responded, but the SOW was not valid structured JSON. Try Generate again.'),502
    except Exception as exc:return jsonify(error=str(exc)),502


def user_company(u): return str(val(u,'company_id',''))
def user_role(u): return str(val(u,'role','user'))
def platform_owner(u): return user_role(u)=='platform_owner'
def company_admin(u): return user_role(u) in ('platform_owner','admin')

@app.get('/api/company')
def company_get():
    u,e=require_user();
    if e:return e
    c=first('SELECT id,login_code,name,status,plan,seat_limit,trial_ends_at,logo_data_url,address,report_footer,created_at FROM companies WHERE id=?',user_company(u))
    return jsonify(company={k:val(c,k,'') for k in ['id','login_code','name','status','plan','seat_limit','trial_ends_at','logo_data_url','address','report_footer','created_at']},role=user_role(u))

@app.patch('/api/company')
def company_patch():
    u,e=require_user(True);
    if e:return e
    if not company_admin(u):return jsonify(error='Company administrator access required'),403
    d=body(); fields=[]; vals=[]
    for f in ['name','logo_data_url','address','report_footer']:
        if f in d: fields.append(f+'=?'); vals.append(str(d[f]))
    if fields:q('UPDATE companies SET '+','.join(fields)+' WHERE id=?',*vals,user_company(u))
    return jsonify(ok=True)

@app.get('/api/company-users')
def company_users():
    u,e=require_user();
    if e:return e
    if not company_admin(u):return jsonify(error='Company administrator access required'),403
    return jsonify(users=rows("SELECT u.id,u.username,m.role,m.status,u.created_at FROM users u JOIN company_memberships m ON m.user_id=u.id WHERE m.company_id=? ORDER BY u.username",user_company(u)))

@app.post('/api/company-users')
def company_user_create():
    u,e=require_user(True);
    if e:return e
    if not company_admin(u):return jsonify(error='Company administrator access required'),403
    cid=user_company(u); c=first('SELECT seat_limit FROM companies WHERE id=?',cid); used=first("SELECT COUNT(*) AS n FROM company_memberships WHERE company_id=? AND status='active'",cid)
    if int(val(used,'n',0))>=int(val(c,'seat_limit',0)):return jsonify(error='No available licenses. Increase the company seat limit before adding another active user.'),409
    d=body(); username=str(d.get('username','')).strip(); password=str(d.get('password','')); role=str(d.get('role','user'))
    if role not in ('admin','manager','user','viewer'):role='user'
    if len(username)<3 or not password:return jsonify(error='Username and password are required'),400
    i=uid()
    try:q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',i,username,hash_password(password),now());q('INSERT INTO company_memberships(company_id,user_id,role,status,created_at) VALUES(?,?,?,?,?)',cid,i,role,'active',now())
    except Exception as exc:return jsonify(error='Could not create user: '+str(exc)),400
    return jsonify(id=i)

@app.patch('/api/company-users/<idv>')
def company_user_update(idv):
    u,e=require_user(True)
    if e:return e
    if not company_admin(u):return jsonify(error='Company administrator access required'),403
    cid=user_company(u); d=body(); m=first('SELECT role,status FROM company_memberships WHERE company_id=? AND user_id=?',cid,idv)
    if not m:return jsonify(error='User not found in this company'),404
    role=str(d.get('role',val(m,'role','user'))); status=str(d.get('status',val(m,'status','active')))
    if role not in ('admin','manager','user','viewer'):return jsonify(error='Invalid role'),400
    if status not in ('active','disabled'):return jsonify(error='Invalid status'),400
    if status=='active' and str(val(m,'status',''))!='active':
        c=first('SELECT seat_limit FROM companies WHERE id=?',cid); used=first("SELECT COUNT(*) AS n FROM company_memberships WHERE company_id=? AND status='active'",cid)
        if int(val(used,'n',0))>=int(val(c,'seat_limit',0)):return jsonify(error='No available licenses.'),409
    q('UPDATE company_memberships SET role=?,status=? WHERE company_id=? AND user_id=?',role,status,cid,idv)
    if d.get('new_password'):
        q('UPDATE users SET password_hash=? WHERE id=?',hash_password(str(d['new_password'])),idv);q('DELETE FROM sessions WHERE user_id=?',idv)
    return jsonify(ok=True)

@app.get('/api/platform/companies')
def platform_companies():
    u,e=require_user();
    if e:return e
    if not platform_owner(u):return jsonify(error='JWorks Platform Owner access required'),403
    return jsonify(companies=rows("SELECT c.id,c.login_code,c.name,c.status,c.plan,c.seat_limit,c.trial_ends_at,c.created_at,(SELECT COUNT(*) FROM company_memberships m WHERE m.company_id=c.id AND m.status='active') AS seats_used,(SELECT COUNT(*) FROM projects p JOIN company_memberships mm ON mm.user_id=p.owner_id WHERE mm.company_id=c.id) AS projects FROM companies c ORDER BY c.created_at DESC"))

@app.post('/api/platform/companies')
def platform_company_create():
    u,e=require_user(True)
    if e:return e
    if not platform_owner(u):return jsonify(error='JWorks Platform Owner access required'),403
    d=body(); name=str(d.get('name','')).strip(); seats=max(1,int(d.get('seat_limit',5) or 5)); plan=str(d.get('plan','professional')); code=str(d.get('login_code','')).strip().upper() or ('JW-'+secrets.token_hex(4)).upper()
    admin_username=str(d.get('admin_username','')).strip(); admin_password=str(d.get('admin_password',''))
    if not name:return jsonify(error='Company name is required'),400
    if len(admin_username)<3 or not admin_password:return jsonify(error='Initial administrator username and password are required'),400
    cid=uid(); aid=uid(); ts=now()
    try:
        q('INSERT INTO companies(id,login_code,name,status,plan,seat_limit,report_footer,created_at) VALUES(?,?,?,?,?,?,?,?)',cid,code,name,'active',plan,seats,'Generated with JWorks',ts)
        q('INSERT INTO subscriptions(id,company_id,status,plan,seat_limit,starts_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',uid(),cid,'active',plan,seats,ts,ts,ts)
        q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',aid,admin_username,hash_password(admin_password),ts)
        q('INSERT INTO company_memberships(company_id,user_id,role,status,created_at) VALUES(?,?,?,?,?)',cid,aid,'admin','active',ts)
    except Exception as exc:
        try:q('DELETE FROM companies WHERE id=?',cid)
        except Exception:pass
        try:q('DELETE FROM users WHERE id=?',aid)
        except Exception:pass
        return jsonify(error='Could not create company and administrator: '+str(exc)),400
    return jsonify(id=cid,company_id=code,admin_username=admin_username)

@app.get('/api/platform/companies/<idv>/users')
def platform_company_users(idv):
    u,e=require_user()
    if e:return e
    if not platform_owner(u):return jsonify(error='JWorks Platform Owner access required'),403
    return jsonify(users=rows("SELECT u.id,u.username,m.role,m.status,u.created_at FROM users u JOIN company_memberships m ON m.user_id=u.id WHERE m.company_id=? ORDER BY u.username",idv))

@app.post('/api/platform/companies/<idv>/users')
def platform_company_user_create(idv):
    u,e=require_user(True)
    if e:return e
    if not platform_owner(u):return jsonify(error='JWorks Platform Owner access required'),403
    c=first('SELECT seat_limit FROM companies WHERE id=?',idv)
    if not c:return jsonify(error='Company not found'),404
    used=first("SELECT COUNT(*) AS n FROM company_memberships WHERE company_id=? AND status='active'",idv)
    if int(val(used,'n',0))>=int(val(c,'seat_limit',0)):return jsonify(error='No available licenses. Increase the company seat limit first.'),409
    d=body(); username=str(d.get('username','')).strip(); password=str(d.get('password','')); role=str(d.get('role','user'))
    if role not in ('admin','manager','user','viewer'):role='user'
    if len(username)<3 or not password:return jsonify(error='Username and password are required'),400
    i=uid()
    try:q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',i,username,hash_password(password),now());q('INSERT INTO company_memberships(company_id,user_id,role,status,created_at) VALUES(?,?,?,?,?)',idv,i,role,'active',now())
    except Exception as exc:return jsonify(error='Could not create user: '+str(exc)),400
    return jsonify(id=i)

@app.patch('/api/platform/companies/<idv>/users/<uidv>')
def platform_company_user_update(idv,uidv):
    u,e=require_user(True)
    if e:return e
    if not platform_owner(u):return jsonify(error='JWorks Platform Owner access required'),403
    m=first('SELECT role,status FROM company_memberships WHERE company_id=? AND user_id=?',idv,uidv)
    if not m:return jsonify(error='User not found in this company'),404
    d=body(); role=str(d.get('role',val(m,'role','user'))); status=str(d.get('status',val(m,'status','active')))
    if role not in ('admin','manager','user','viewer') or status not in ('active','disabled'):return jsonify(error='Invalid role or status'),400
    if status=='active' and str(val(m,'status',''))!='active':
        c=first('SELECT seat_limit FROM companies WHERE id=?',idv); used=first("SELECT COUNT(*) AS n FROM company_memberships WHERE company_id=? AND status='active'",idv)
        if int(val(used,'n',0))>=int(val(c,'seat_limit',0)):return jsonify(error='No available licenses.'),409
    q('UPDATE company_memberships SET role=?,status=? WHERE company_id=? AND user_id=?',role,status,idv,uidv)
    if d.get('new_password'):
        q('UPDATE users SET password_hash=? WHERE id=?',hash_password(str(d['new_password'])),uidv);q('DELETE FROM sessions WHERE user_id=?',uidv)
    return jsonify(ok=True)

@app.patch('/api/platform/companies/<idv>')
def platform_company_patch(idv):
    u,e=require_user(True);
    if e:return e
    if not platform_owner(u):return jsonify(error='JWorks Platform Owner access required'),403
    d=body(); fields=[];vals=[]
    for f in ['name','status','plan','seat_limit','logo_data_url','address','report_footer']:
        if f in d:fields.append(f+'=?');vals.append(d[f])
    if fields:q('UPDATE companies SET '+','.join(fields)+' WHERE id=?',*vals,idv)
    if 'seat_limit' in d or 'plan' in d or 'status' in d:q('UPDATE subscriptions SET seat_limit=COALESCE(?,seat_limit),plan=COALESCE(?,plan),status=COALESCE(?,status),updated_at=? WHERE company_id=?',d.get('seat_limit'),d.get('plan'),d.get('status'),now(),idv)
    return jsonify(ok=True)

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


def is_admin(u):
    try:
        r=first('SELECT id FROM users ORDER BY created_at ASC LIMIT 1')
        return bool(r and str(val(r,'id',''))==str(val(u,'id','')))
    except Exception:return False

@app.get('/api/users')
def users_list():
    u,e=require_user();
    if e:return e
    if not is_admin(u):return jsonify(error='Administrator access required'),403
    return jsonify(users=rows('SELECT id,username,created_at FROM users ORDER BY created_at ASC'),current_user_id=str(val(u,'id','')))

@app.post('/api/users')
def users_create():
    u,e=require_user(True);
    if e:return e
    if not is_admin(u):return jsonify(error='Administrator access required'),403
    d=body(); username=str(d.get('username','')).strip(); password=str(d.get('password',''))
    if len(username)<3:return jsonify(error='Username must be at least 3 characters'),400
    if not password:return jsonify(error='Password is required'),400
    try:q('INSERT INTO users(id,username,password_hash,created_at) VALUES(?,?,?,?)',uid(),username,hash_password(password),now())
    except Exception as exc:return jsonify(error='Could not create user: '+str(exc)),400
    return jsonify(ok=True)

@app.delete('/api/users/<idv>')
def users_delete(idv):
    u,e=require_user(True);
    if e:return e
    if not is_admin(u):return jsonify(error='Administrator access required'),403
    if idv==str(val(u,'id','')):return jsonify(error='You cannot delete the account you are currently using.'),400
    q('DELETE FROM users WHERE id=?',idv);return jsonify(ok=True)

@app.post('/api/change-password')
def change_password():
    u,e=require_user(True);
    if e:return e
    d=body(); current=str(d.get('current_password','')); new=str(d.get('new_password',''))
    if not new:return jsonify(error='New password is required'),400
    r=first('SELECT password_hash FROM users WHERE id=?',str(val(u,'id','')))
    if not r or not verify_password(current,str(val(r,'password_hash',''))):return jsonify(error='Current password is incorrect'),400
    q('UPDATE users SET password_hash=? WHERE id=?',hash_password(new),str(val(u,'id','')))
    q('DELETE FROM sessions WHERE user_id=? AND id<>?',str(val(u,'id','')),request.cookies.get('jworks_session',''))
    return jsonify(ok=True)

@app.get('/api/preferences')
def preferences_get():
    u,e=require_user()
    if e:return e
    r=first('SELECT config_json FROM user_preferences WHERE user_id=?',str(val(u,'id','')))
    try: cfg=json.loads(str(val(r,'config_json','{}') or '{}')) if r else {}
    except Exception: cfg={}
    return jsonify(config=cfg)

@app.post('/api/preferences')
def preferences_save():
    u,e=require_user(True)
    if e:return e
    cfg=body().get('config') or {}
    q('INSERT INTO user_preferences(user_id,config_json,updated_at) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET config_json=excluded.config_json,updated_at=excluded.updated_at',str(val(u,'id','')),json.dumps(cfg),now())
    return jsonify(ok=True)

@app.get('/api/report-templates')
def report_templates_list():
    u,e=require_user();
    if e:return e
    return jsonify(items=rows('SELECT id,title,config_json,created_at FROM custom_report_templates WHERE owner_id=? ORDER BY created_at DESC',str(val(u,'id',''))))

@app.post('/api/report-templates')
def report_templates_create():
    u,e=require_user(True);
    if e:return e
    d=body(); title=str(d.get('title','')).strip()
    if not title:return jsonify(error='Report name is required'),400
    i=uid();q('INSERT INTO custom_report_templates(id,owner_id,title,config_json,created_at) VALUES(?,?,?,?,?)',i,str(val(u,'id','')),title,json.dumps(d.get('config') or {}),now());return jsonify(id=i)

@app.delete('/api/report-templates/<idv>')
def report_templates_delete(idv):
    u,e=require_user(True);
    if e:return e
    q('DELETE FROM custom_report_templates WHERE id=? AND owner_id=?',idv,str(val(u,'id','')));return jsonify(ok=True)


def _xlsx_rows(blob):
    """Small dependency-free XLSX reader for the JWorks import templates."""
    z=zipfile.ZipFile(io.BytesIO(blob)); ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
    shared=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        root=ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall('m:si',ns): shared.append(''.join(t.text or '' for t in si.iter('{%s}t'%ns['m'])))
    root=ET.fromstring(z.read('xl/worksheets/sheet1.xml')); out=[]
    for row in root.findall('.//m:sheetData/m:row',ns):
        vals={}
        for c in row.findall('m:c',ns):
            ref=c.attrib.get('r','A1'); col=re.match(r'[A-Z]+',ref).group(0); typ=c.attrib.get('t'); v=c.find('m:v',ns); inline=c.find('m:is',ns)
            value=''
            if typ=='inlineStr' and inline is not None:value=''.join(t.text or '' for t in inline.iter('{%s}t'%ns['m']))
            elif v is not None:
                value=v.text or ''
                if typ=='s': value=shared[int(value)] if value else ''
            vals[col]=value
        out.append(vals)
    def ci(col):
        n=0
        for ch in col:n=n*26+ord(ch)-64
        return n-1
    if not out:return []
    headers={k:str(v).strip() for k,v in out[0].items()}; result=[]
    for r in out[1:]:
        item={headers.get(k,k):str(v).strip() for k,v in r.items() if headers.get(k)}
        if any(item.values()):result.append(item)
    return result

def _norm_status(v,kind):
    x=str(v or '').strip().lower().replace(' ','_')
    if kind=='projects': return {'active':'active','planned':'planned','planning':'planned','complete':'complete','completed':'complete','on_hold':'on_hold','on hold':'on_hold'}.get(x,x or 'active')
    return {'to_do':'todo','todo':'todo','not_started':'todo','in_progress':'doing','in progress':'doing','doing':'doing','done':'done','complete':'done','completed':'done'}.get(x,x or 'todo')

@app.post('/api/import-xlsx/preview')
def import_xlsx_preview():
    u,e=require_user(True)
    if e:return e
    kind=str(request.form.get('kind','')); f=request.files.get('file')
    if kind not in ('projects','tasks') or not f:return jsonify(error='Choose a valid JWorks Excel template.'),400
    try: raw=_xlsx_rows(f.read())
    except Exception as exc:return jsonify(error='Could not read this .xlsx file. Use the current JWorks import template. '+str(exc)),400
    out=[]; codes={str(x.get('project_code') or '').lower():x['id'] for x in rows('SELECT id,project_code FROM projects WHERE owner_id IN ('+','.join(['?']*len(company_user_ids(u)))+')',*company_user_ids(u)) if x.get('project_code')}
    for idx,r in enumerate(raw,2):
        if kind=='projects':
            x={'row':idx,'name':r.get('Project Name',''),'project_code':r.get('Project Code',''),'description':r.get('Description',''),'status':_norm_status(r.get('Status'),kind),'priority':r.get('Priority',''),'start_date':r.get('Start Date',''),'end_date':r.get('Target Date',''),'estimated_cost':r.get('Budget','') or 0,'notes':r.get('Notes',''),'errors':[]}
            if not x['name']:x['errors'].append('Project Name is required')
            if x['project_code'] and x['project_code'].lower() in codes:x['errors'].append('Project Code already exists')
        else:
            code=r.get('Project Code',''); x={'row':idx,'name':r.get('Task Name',''),'project_code':code,'description':r.get('Description',''),'status':_norm_status(r.get('Status'),kind),'priority':str(r.get('Priority','medium') or 'medium').lower(),'start_date':r.get('Start Date',''),'due_date':r.get('Due Date',''),'notes':r.get('Notes',''),'project_id':codes.get(code.lower()) if code else None,'errors':[]}
            if not x['name']:x['errors'].append('Task Name is required')
            if code and not x['project_id']:x['errors'].append('Project Code does not match an existing project')
        out.append(x)
    return jsonify(kind=kind,rows=out,valid_count=sum(not x['errors'] for x in out),error_count=sum(bool(x['errors']) for x in out))

@app.post('/api/import-xlsx/commit')
def import_xlsx_commit():
    u,e=require_user(True)
    if e:return e
    d=body();kind=d.get('kind');items=d.get('rows') or []
    if kind not in ('projects','tasks'):return jsonify(error='Invalid import type'),400
    count=0
    for x in items:
        if x.get('errors'):continue
        if kind=='projects':
            data={k:x.get(k) for k in ['name','project_code','description','status','start_date','end_date','estimated_cost','notes']}; data['created_at']=now(); insert_named('projects',str(u.id),PROJECT_FIELDS,data);count+=1
        else:
            data={k:x.get(k) for k in ['project_id','name','start_date','due_date','status','priority','notes']};data['created_at']=now();insert_named('tasks',str(u.id),TASK_FIELDS,data);count+=1
    return jsonify(count=count)

Default=wsgi.entrypoint(app)


# ===== JWorks V12 support =====
@app.get('/api/support-tickets')
def support_tickets_get():
    u=auth_user()
    if not u:return jsonify(error='Unauthorized'),401
    return jsonify(tickets=rows('SELECT id,ticket_number,subject,category,priority,status,created_at FROM support_tickets WHERE company_id=? ORDER BY created_at DESC LIMIT 100',user_company(u)))

@app.post('/api/support-tickets')
def support_tickets_post():
    u=auth_user()
    if not u:return jsonify(error='Unauthorized'),401
    if not csrf_ok(u):return jsonify(error='Invalid CSRF token'),403
    d=body(); subject=str(d.get('subject','')).strip(); desc=str(d.get('description','')).strip()
    if not subject or not desc:return jsonify(error='Subject and description are required'),400
    ts=now(); ident=uid(); number='JW-'+datetime.now(timezone.utc).strftime('%y%m%d')+'-'+ident[:5].upper()
    q('INSERT INTO support_tickets(id,ticket_number,company_id,user_id,subject,category,priority,description,diagnostics,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',ident,number,user_company(u),str(val(u,'id','')),subject,str(d.get('category','General')),str(d.get('priority','Normal')),desc,str(d.get('diagnostics','')),'open',ts,ts)
    return jsonify(ok=True,ticket_number=number)
