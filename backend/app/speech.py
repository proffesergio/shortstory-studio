"""Local-first text to speech. Kokoro models downloaded on first run."""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from .config import TTS_ENGINE, KOKORO_VOICE


def split_script(script: str):
    parts = re.split(r'(?<=[.!?])\s+', script.strip())
    return [s.strip() for s in parts if s.strip()]


def synthesize(script: str, wav_path: Path):
    sentences = split_script(script)
    if not sentences:
        raise ValueError('Script is empty')
    sample_rate = 24000
    clips = []
    timings = []
    current = 0.0
    pipeline = None
    if TTS_ENGINE == 'kokoro':
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code='a')
    for sentence in sentences:
        if TTS_ENGINE == 'kokoro':
            pieces = [audio for _gr, _ph, audio in pipeline(sentence, voice=KOKORO_VOICE, speed=1.02)]
            if not pieces:
                raise RuntimeError('Kokoro returned empty audio')
            audio = np.concatenate([np.asarray(p, dtype=np.float32) for p in pieces])
        elif TTS_ENGINE == 'espeak':
            if not shutil.which('espeak-ng'):
                raise RuntimeError('espeak-ng is not installed')
            with tempfile.NamedTemporaryFile(suffix='.wav') as temp:
                subprocess.run(['espeak-ng', '-s','165','-w',temp.name, sentence], check=True)
                audio, original_sr = sf.read(temp.name, dtype='float32')
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if original_sr != sample_rate:
                    # Simple interpolation for this optional quick smoke-test backend.
                    x = np.arange(len(audio)) / original_sr
                    audio = np.interp(np.arange(round(len(audio)*sample_rate/original_sr))/sample_rate, x, audio).astype(np.float32)
        else:
            raise ValueError('TTS_ENGINE must be kokoro or espeak')
        begin = current
        length = len(audio) / sample_rate
        current += length
        timings.append((begin, current, sentence))
        clips += [audio, np.zeros(int(sample_rate * 0.20), dtype=np.float32)]
        current += 0.20
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(wav_path, np.concatenate(clips), sample_rate)
    return timings
