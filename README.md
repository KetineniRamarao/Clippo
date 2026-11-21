# CLIPPO // 01

```
   _____ _      _____ _____  _____   ____  
  / ____| |    |_   _|  __ \|  __ \ / __ \ 
 | |    | |      | | | |__) | |__) | |  | |
 | |    | |      | | |  ___/|  ___/| |  | |
 | |____| |____ _| |_| |    | |    | |__| |
  \_____|______|_____|_|    |_|     \____/ 
```

> **AUTONOMOUS PRODUCTION ENGINE FOR LONG-FORM FOOTAGE AND VIRAL 9:16 VERTICAL SHORTS.**  
> Built for raw broadcast camera files (MXF, ProRes, MP4, up to 10GB+) with multi-stream GPU hardware acceleration, dual-stage speech leveling, and sentence-boundary trimming.

---

## ⚡ BRUTALIST ARCHITECTURE

```
[ RAW FOOTAGE (10GB+ MXF/MP4) ]
               │
               ▼
   [ HARDWARE PROBE ENGINE ] ──────────────► Auto-Detects NVENC / CPU
               │
               ▼
  [ DUAL-STAGE AUDIO ENGINE ]
   ├─ dynaudnorm (Dynamic Gain AGC) ──────► Level field whispers vs shouting
   └─ loudnorm (-14 LUFS Limit)     ──────► Mobile broadcast loudness standard
               │
               ▼
[ SILENCE BOUNDARY SNAPPING ] ────────────► Snaps cuts to breath pauses (no mid-sentence cutoffs)
               │
               ▼
   [ MULTI-STREAM GPU RENDER ]
   ├─ 16:9 4K Master Video          ──────► Top-right broadcast safe watermark
   └─ 9:16 Vertical Mobile Shorts   ──────► Center-cropped, parallel NVENC batch
```

---

## 🚀 KEY CAPABILITIES

* **Zero-Touch Turnkey Execution:** Point to a raw camera file and execute. No manual slicing, no repetitive confirmation dialogs.
* **Dual-Stage Speech Leveling:** Solves real-world on-ground audio variance. Dynamic gain normalization boosts quiet field dialogue by up to +20 dB while preventing loud shouts from clipping.
* **Intelligent Sentence-Boundary Trimming:** Uses silence detection to ensure shorts start and end on complete thoughts rather than abrupt mid-word cuts.
* **Configurable Clip Schedulers:** Choose your exact clip count (`-n 4`, `-n 8`) or let Clippo's auto-scheduler calculate the optimal number based on video duration.
* **GPU NVENC Parallel Acceleration:** Multi-threaded worker pool renders 3+ video streams concurrently on modern GPUs.

---

## 📦 INSTALLATION

### Prerequisites
* **Python 3.9+**
* **FFmpeg** (with NVENC support recommended for ultra-fast GPU processing)

### Quick Setup
```bash
git clone https://github.com/KetineniRamarao/Clippo.git
cd Clippo
pip install -e .
```

---

## 🛠️ CLI USAGE

```bash
# Basic run with auto-detected clip count
clippo path/to/raw_footage.mxf

# Specify exact number of clips (e.g. 5 shorts)
clippo path/to/interview.mp4 -n 5

# Set custom duration limits (e.g. 30s to 50s for TikTok)
clippo path/to/talk.mov --min-duration 30 --max-duration 50

# Apply transparent animated watermark logo
clippo path/to/video.mxf --logo path/to/watermark.mov

# High-concurrency rendering (e.g. 4 GPU threads)
clippo path/to/video.mxf --concurrency 4
```

---

## ⚙️ CLI PARAMETERS

| Flag | Description | Default |
| :--- | :--- | :--- |
| `input_file` | Absolute or relative path to media | *(Required)* |
| `-n`, `--num-clips` | Number of shorts to extract (`auto` or integer) | `auto` |
| `-c`, `--concurrency` | Number of concurrent render workers | `3` |
| `--min-duration` | Minimum length per short in seconds | `45.0` |
| `--max-duration` | Maximum length per short in seconds | `65.0` |
| `--logo` | Path to transparent animated watermark | `None` |
| `--no-dynamic-audio` | Disable real-time dynamic AGC | `False` |
| `--skip-master` | Skip 16:9 landscape master rendering | `False` |

---

## 📄 LICENSE

This project is licensed under the MIT License - see the LICENSE file for details.
