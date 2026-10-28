"""Dedicated SQLite-backed single-worker queue. Run one process for this MVP."""
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timezone
from .db import connect, init_db, now
from .config import OUTPUT_DIR
from .scriptwriter import write_script
from .speech import synthesize
from .render import background, make_subs, render
from .youtube import upload

logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)


def autopilot_config():
    with connect() as db:
        row = db.execute("SELECT value FROM settings WHERE key='autopilot'").fetchone()
    return json.loads(row['value']) if row else {'enabled':False}


def schedule_approved_sources():
    """Schedule only user-approved sources; capped per UTC day."""
    config = autopilot_config()
    if not config.get('enabled'):
        return
    today = datetime.now(timezone.utc).date().isoformat()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        count = db.execute("SELECT count(*) FROM jobs WHERE kind='render' AND auto_created=1 AND created_at LIKE ?",(today+'%',)).fetchone()[0]
        if count >= config.get('daily_limit',2):
            return
        candidate = db.execute("""SELECT id FROM stories s WHERE rights_verified=1
          AND NOT EXISTS (SELECT 1 FROM jobs j WHERE j.story_id=s.id AND j.kind='render')
          ORDER BY s.id ASC LIMIT 1""").fetchone()
        if candidate:
            db.execute("INSERT INTO jobs(kind,story_id,status,auto_created,created_at,updated_at) VALUES (?,?,'queued',1,?,?)",
                       ('render', candidate['id'],now(),now()))
            log.info('Autopilot queued approved story %s',candidate['id'])


def schedule_auto_upload(render_job, story_id):
    cfg=autopilot_config()
    if not (cfg.get('enabled') and cfg.get('auto_upload') and cfg.get('upload_consent')):
        return
    with connect() as db:
        db.execute("INSERT INTO jobs(kind,story_id,parent_job_id,status,privacy,auto_created,created_at,updated_at) VALUES (?,?,?,?,?,1,?,?)",
                   ('publish',story_id,render_job,'queued',cfg['privacy'],now(),now()))


def next_job():
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY id ASC LIMIT 1").fetchone()
        if row:
            db.execute("UPDATE jobs SET status='running',updated_at=? WHERE id=?", (now(), row['id']))
        return dict(row) if row else None


def set_job(job_id, **updates):
    updates['updated_at'] = now()
    assignments = ','.join(k+'=?' for k in updates)
    with connect() as db:
        db.execute(f'UPDATE jobs SET {assignments} WHERE id=?', (*updates.values(), job_id))


def process(job):
    with connect() as db:
        story = db.execute('SELECT * FROM stories WHERE id=?',(job['story_id'],)).fetchone()
        story = dict(story) if story else None
    if not story or not story['rights_verified']:
        raise ValueError('Missing story or verified source rights')
    if job['kind'] == 'render':
        metadata = write_script(story)
        workdir = OUTPUT_DIR / f'job_{job["id"]}'
        workdir.mkdir(exist_ok=True,parents=True)
        timings = synthesize(metadata['script'], workdir / 'narration.wav')
        make_subs(timings, workdir / 'captions.ass')
        background(workdir / 'background.png',job['id'])
        result = render(workdir/'narration.wav',workdir/'captions.ass',workdir/'background.png',workdir/'short.mp4')
        set_job(job['id'], status='done',output_file=str(result),title=metadata['title'],description=metadata['description'])
        schedule_auto_upload(job['id'], story['id'])
    elif job['kind'] == 'publish':
        if job.get('auto_created'):
            cfg = autopilot_config()
            if not (cfg.get('enabled') and cfg.get('auto_upload') and cfg.get('upload_consent')):
                raise PermissionError('Autopilot upload consent was revoked before upload')
        with connect() as db:
            parent = db.execute('SELECT * FROM jobs WHERE id=?',(job['parent_job_id'],)).fetchone()
        if not parent or parent['status']!='done' or not parent['output_file']:
            raise ValueError('Rendered video unavailable')
        video_id = upload(Path(parent['output_file']),parent['title'],parent['description'],job['privacy'])
        set_job(job['id'],status='done',youtube_id=video_id,output_file=parent['output_file'],title=parent['title'])
    else:
        raise ValueError('Unknown job kind')


def tick():
    job = next_job()
    if not job:
        return False
    log.info('Processing %s job #%s',job['kind'],job['id'])
    try:
        process(job)
    except Exception as exc:
        log.exception('Job #%s failed',job['id'])
        set_job(job['id'],status='failed',error=str(exc)[:1200])
    return True


def main():
    init_db()
    log.info('Worker ready. Keep API on localhost until auth is implemented.')
    while True:
        schedule_approved_sources()
        if not tick():
            time.sleep(2)


if __name__ == '__main__':
    main()
