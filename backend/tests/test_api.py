import json
from fastapi.testclient import TestClient
from app import db
from app.main import app
from app import worker


def test_api_approved_story_and_autopilot(tmp_path,monkeypatch):
    monkeypatch.setattr(db,'DB_PATH',tmp_path/'test.sqlite3')
    monkeypatch.setattr(db,'OUTPUT_DIR',tmp_path/'outputs')
    db.init_db()
    with TestClient(app) as client:
        result=client.post('/api/stories',json={
            'title':'My own original story','body':'One afternoon I decided to build a tiny app. ' * 8,
            'niche':'Confessions','rights_verified':True})
        assert result.status_code==201
        sid=result.json()['id']
        assert client.get('/api/stories').json()[0]['id']==sid
        denied=client.post('/api/autopilot',json={'enabled':True,'auto_upload':True,'explicit_upload_consent':False})
        assert denied.status_code==403
        allowed=client.post('/api/autopilot',json={'enabled':True,'auto_upload':False,'daily_limit':1})
        assert allowed.status_code==200
        worker.schedule_approved_sources()
        jobs=client.get('/api/jobs').json()
        assert len(jobs)==1 and jobs[0]['kind']=='render' and jobs[0]['auto_created']==1
        worker.schedule_approved_sources()
        assert len(client.get('/api/jobs').json())==1
        # Publish is never allowed without a finished render and explicit per-upload approval.
        publish=client.post('/api/jobs/1/publish',json={'explicit_consent':True,'privacy':'private'})
        assert publish.status_code==409
