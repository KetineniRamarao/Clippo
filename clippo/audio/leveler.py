import re
import subprocess
from typing import List, Tuple

def get_audio_filter_chain(dynamic: bool = True, target_lufs: float = -14.0) -> str:
    if dynamic:
        return f"dynaudnorm=f=150:g=15:p=0.9:m=12.0,loudnorm=I={target_lufs}:TP=-1.5:LRA=9"
    return f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11"

def extract_silences(ffmpeg_bin: str, audio_path: str) -> List[Tuple[float, float]]:
    cmd = [
        ffmpeg_bin, "-i", audio_path,
        "-af", "silencedetect=noise=-30dB:d=0.35",
        "-f", "null", "-"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")

    silences = []
    start = None
    for line in res.stderr.splitlines():
        if "silence_start:" in line:
            m = re.search(r"silence_start:\s*([0-9.]+)", line)
            if m:
                start = float(m.group(1))
        elif "silence_end:" in line:
            m = re.search(r"silence_end:\s*([0-9.]+)", line)
            if m and start is not None:
                silences.append((start, float(m.group(1))))
                start = None
    return silences

def snap_timestamp_to_silence(target_time: float, silences: List[Tuple[float, float]], tolerance: float = 5.0) -> float:
    best = target_time
    min_dist = float("inf")
    for s_start, s_end in silences:
        mid = (s_start + s_end) / 2.0
        dist = abs(mid - target_time)
        if dist < min_dist and dist <= tolerance:
            min_dist = dist
            best = mid
    return round(best, 2)
