import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .db import init_db, connect, now, rows, one
from .config import OUTPUT_DIR
from .source import preview_community


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title='StoryShorts Studio API',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:3000','http://127.0.0.1:3000'],
                   allow_credentials=False,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

class StoryIn(BaseModel):
    title: str = Field(min_length=5,max_length=200)
    body: str = Field(min_length=50,max_length=14000)
    niche: str = Field(min_length=3,max_length=120)
    community: str = Field(default='',max_length=120)
    source_url: str = Field(default='',max_length=1200)
    rights_verified: bool = False

class AutoPilotIn(BaseModel):
    enabled: bool = False
    auto_upload: bool = False
    explicit_upload_consent: bool = False
    privacy: str = 'private'
    daily_limit: int = Field(default=2,ge=1,le=3)

class ConsentIn(BaseModel):
    explicit_consent: bool
    privacy: str = 'private'

class SettingsIn(BaseModel):
    niches: list[str]
    communities: list[str]

@app.get('/api/health')
def health():
    return {'status':'ok','service':'storyshorts-studio'}

@app.get('/api/settings')
def settings():
    with connect() as db:
        all_settings = {r['key']:json.loads(r['value']) for r in db.execute('SELECT key,value FROM settings')}
    return all_settings

@app.post('/api/settings')
def update_settings(s:SettingsIn):
    if any(not re.fullmatch(r'[A-Za-z0-9_]{2,30}', c) for c in s.communities):
        raise HTTPException(422,'Community names must be valid subreddit names')
    with connect() as db:
        for key,value in [('niches',s.niches[:30]),('communities',s.communities[:30])]:
            db.execute('INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,json.dumps(value)))
    return settings()

@app.post('/api/autopilot')
def configure_autopilot(body:AutoPilotIn):
    if body.privacy not in ('private','unlisted','public'):
        raise HTTPException(422,'Invalid visibility')
    if body.auto_upload and (not body.enabled or not body.explicit_upload_consent):
        raise HTTPException(403,'Automatic YouTube publishing needs enabled autopilot and explicit prior upload consent')
    payload={'enabled':body.enabled, 'auto_upload':body.auto_upload,
             'upload_consent':bool(body.auto_upload and body.explicit_upload_consent),
             'privacy':body.privacy, 'daily_limit':body.daily_limit}
    with connect() as db:
        db.execute('INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('autopilot',json.dumps(payload)))
    return payload

@app.get('/api/stories')
def stories():
    return rows('SELECT id,title,niche,community,source_url,rights_verified,created_at FROM stories ORDER BY id DESC LIMIT 100')

@app.post('/api/stories', status_code=201)
def create_story(story:StoryIn):
    # A declaration by the owner is a process gate, not verification by this software.
    with connect() as db:
        cur = db.execute('INSERT INTO stories(title,body,niche,community,source_url,rights_verified,created_at) VALUES (?,?,?,?,?,?,?)',
                         (story.title.strip(),story.body.strip(),story.niche.strip(),story.community.strip(),story.source_url.strip(),int(story.rights_verified),now()))
        return {'id':cur.lastrowid,'created':True}

@app.post('/api/stories/{story_id}/render',status_code=202)
def queue_render(story_id:int):
    story = one('SELECT * FROM stories WHERE id=?',(story_id,))
    if not story: raise HTTPException(404,'Story not found')
    if not story['rights_verified']: raise HTTPException(403,'Confirm rights for the source before rendering')
    pending = one("SELECT id FROM jobs WHERE story_id=? AND kind='render' AND status IN ('queued','running')",(story_id,))
    if pending: raise HTTPException(409,'Story already has an active render job')
    with connect() as db:
        cur=db.execute('INSERT INTO jobs(kind,story_id,status,created_at,updated_at) VALUES (?,?,?,?,?)',
                       ('render',story_id,'queued',now(),now()))
        return {'job_id':cur.lastrowid,'status':'queued'}

@app.get('/api/jobs')
def jobs():
    return rows('''SELECT j.*, s.title AS source_title FROM jobs j JOIN stories s ON s.id=j.story_id ORDER BY j.id DESC LIMIT 100''')

@app.post('/api/jobs/{job_id}/publish',status_code=202)
def queue_publish(job_id:int,consent:ConsentIn):
    if not consent.explicit_consent:
        raise HTTPException(403,'Express authorization to upload to your YouTube channel is required')
    if consent.privacy not in ('private','unlisted','public'):
        raise HTTPException(422,'Invalid privacy')
    source=one('SELECT * FROM jobs WHERE id=? AND kind=?',(job_id,'render'))
    if not source or source['status']!='done' or not source['output_file']:
        raise HTTPException(409,'Render must finish first')
    if not Path(source['output_file']).is_file():
        raise HTTPException(404,'Rendered video file unavailable')
    with connect() as db:
        cur=db.execute('INSERT INTO jobs(kind,story_id,parent_job_id,status,privacy,created_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                       ('publish',source['story_id'],job_id,'queued',consent.privacy,now(),now()))
    return {'job_id':cur.lastrowid,'status':'queued'}

@app.get('/api/jobs/{job_id}/video')
def video(job_id:int):
    job = one('SELECT * FROM jobs WHERE id=?',(job_id,))
    if not job or job['status']!='done' or not job['output_file']:
        raise HTTPException(404,'Video not available')
    path=Path(job['output_file']).resolve()
    if not path.is_relative_to(OUTPUT_DIR) or not path.is_file():
        raise HTTPException(404,'Video path is not valid')
    return FileResponse(path,media_type='video/mp4',filename=f'short_{job_id}.mp4')

@app.get('/api/reddit/preview')
def reddit_preview(community:str=Query(min_length=2,max_length=30,pattern=r'^[A-Za-z0-9_]+$'),niche:str='Storytime'):
    configured=settings().get('communities',[])
    if community not in configured:
        raise HTTPException(403,'Community not on admin allowlist')
    try:
        return preview_community(community,niche)
    except PermissionError as e:
        raise HTTPException(403,str(e)) from e
    except Exception as e:
        raise HTTPException(502,'Reddit preview failed: '+str(e)[:200]) from e
