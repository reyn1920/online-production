import os, subprocess, time, random, textwrap
from backend.core.ci import cap_reel_minutes

FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

def make_title_slide(text, out_path, w=1920, h=1080, dur=6):
    cmd = [
        "ffmpeg","-y","-f","lavfi","-i",f"color=c=black:s={w}x{h}:d={dur}",
        "-vf", f"drawtext=fontfile='{FONT}':text='{textwrap.fill(text,40)}':x=(w-tw)/2:y=(h-th)/2:fontsize=48:fontcolor=white",
        out_path
    ]
    subprocess.run(cmd, check=True)

def concat_videos(parts, out_path):
    lst = out_path+".lst"
    with open(lst,"w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",lst,"-c","copy",out_path], check=True)

def tts_to_wav(text, wav_path):
    import pyttsx3
    eng = pyttsx3.init()
    eng.save_to_file(text, wav_path)
    eng.runAndWait()

def make_slideshow_with_audio(lines, out_dir, total_minutes=None):
    if total_minutes is None:
        total_minutes = cap_reel_minutes(20)
    os.makedirs(out_dir, exist_ok=True)
    parts = []
    per = 15
    slides = max(8, min(80, int((total_minutes*60)//per)))
    for i in range(min(slides, len(lines))):
        slide = os.path.join(out_dir, f"slide_{i:03d}.mp4")
        make_title_slide(lines[i], slide, dur=per)
        parts.append(slide)

    video = os.path.join(out_dir, "video.mp4")
    concat_videos(parts, video)

    wav = os.path.join(out_dir, "narration.wav")
    tts_to_wav(" ".join(lines[:slides]), wav)

    out = os.path.join(out_dir, "capability_reel.mp4")
    subprocess.run(["ffmpeg","-y","-i",video,"-i",wav,"-shortest","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",out], check=True)
    return out