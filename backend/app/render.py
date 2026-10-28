import math
import random
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def background(target: Path, seed: int):
    # Original, license-independent gradient and floating lights; no borrowed gameplay.
    random.seed(seed)
    w, h = 1400, 2400
    pic = Image.new('RGB',(w,h))
    px = pic.load()
    for y in range(h):
        t = y/h
        rgb = (int(11+14*t), int(13+8*t), int(46+22*t))
        for x in range(w):
            px[x,y] = rgb
    drawing = ImageDraw.Draw(pic, 'RGBA')
    for i in range(30):
        x = random.randrange(-150,w+100)
        y = random.randrange(-100,h+100)
        radius = random.randrange(55,320)
        color = random.choice([(36, 190, 230, 56),(185,56,255,42),(255,79,172,44),(48,255,157,32)])
        drawing.ellipse((x-radius,y-radius,x+radius,y+radius), fill=color)
    pic = pic.filter(ImageFilter.GaussianBlur(55))
    pic.save(target)


def clock(sec):
    hours = int(sec // 3600)
    minutes = int(sec % 3600 // 60)
    seconds = sec % 60
    return f'{hours}:{minutes:02}:{seconds:05.2f}'


def make_subs(timings, path: Path):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,DejaVu Sans,62,&H00FFFFFF,&H0000FFFF,&H00100B0D,&H64000000,-1,0,0,0,100,100,0,0,1,4,1,2,65,65,335,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
    lines = []
    for start, end, sentence in timings:
        words = sentence.split()
        groups = [' '.join(words[i:i+6]) for i in range(0,len(words),6)]
        weight = sum(len(g) for g in groups)
        cursor = start
        for group in groups:
            chunk_end = min(end, cursor + (end-start) * len(group)/max(weight,1))
            clean = group.replace('{','').replace('}','').replace('\\','').replace('\n',' ')
            lines.append(f'Dialogue: 0,{clock(cursor)},{clock(chunk_end)},Default,,0,0,0,,{clean}')
            cursor = chunk_end
    path.write_text(header + '\n'.join(lines) + '\n', encoding='utf8')


def render(wav: Path, captions: Path, background_png: Path, result: Path):
    # A gentle moving crop and word-group captions, encoded as YouTube-compatible H.264.
    vf = "crop=1080:1920:x='160+90*sin(n/70)':y='240+150*cos(n/100)',subtitles=" + str(captions.resolve()).replace('\\','\\\\').replace(':','\\:')
    command = ['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate','30','-i',str(background_png),
               '-i',str(wav),'-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p',
               '-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart','-shortest',str(result)]
    subprocess.run(command, check=True, timeout=540)
    return result
