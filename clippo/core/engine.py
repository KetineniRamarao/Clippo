import os
import re
import subprocess
from typing import Dict, Any, Optional

def locate_ffmpeg() -> str:
    candidates = [
        r"C:\Program Files\FormatFactory5.21.0.0\ffmpeg.exe",
        r"C:\Program Files\FormatFactory\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\tools\ffmpeg\bin\ffmpeg.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    try:
        res = subprocess.run(["where.exe", "ffmpeg"], capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            if lines and os.path.isfile(lines[0].strip()):
                return lines[0].strip()
    except Exception:
        pass
    return "ffmpeg"

def has_nvenc_acceleration(ffmpeg_bin: str) -> bool:
    try:
        res = subprocess.run([ffmpeg_bin, "-encoders"], capture_output=True, text=True, errors="replace")
        return "h264_nvenc" in res.stdout
    except Exception:
        return False

def probe_media(ffmpeg_bin: str, file_path: str) -> Dict[str, Any]:
    cmd = [ffmpeg_bin, "-hide_banner", "-i", file_path]
    res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    stderr = res.stderr

    duration = 0.0
    m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr)
    if m_dur:
        h, m, s = float(m_dur.group(1)), float(m_dur.group(2)), float(m_dur.group(3))
        duration = h * 3600 + m * 60 + s

    is_4k = "3840x2160" in stderr
    best_audio = "0:1"
    for s_idx in ["1", "2", "3", "4"]:
        if f"Stream #0:{s_idx}" in stderr and "Audio" in stderr:
            best_audio = f"0:{s_idx}"
            break

    return {
        "duration": duration,
        "is_4k": is_4k,
        "audio_stream": best_audio
    }
