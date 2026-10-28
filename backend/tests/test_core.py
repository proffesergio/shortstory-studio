from pathlib import Path
from app.render import make_subs
from app.speech import split_script
from app.source import rank


def test_script_sentence_splitting():
    assert split_script('First sentence. Second sentence!') == ['First sentence.','Second sentence!']


def test_ranking_prefers_relevant_candidate():
    a={'title':'A confession about friendship','selftext':'A surprising confession','score':500,'num_comments':100, 'created_utc': 1_700_000_000}
    b={**a,'title':'The weather today','selftext':'A sunny day'}
    assert rank(a,'confession') > rank(b,'confession')


def test_ass_file_generated(tmp_path):
    target=tmp_path/'captions.ass'
    make_subs([(0,2,'I made a very big mistake today.')], target)
    data=target.read_text()
    assert 'Dialogue:' in data and 'I made a' in data
