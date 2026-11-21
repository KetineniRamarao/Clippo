import os
import sys
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

from clippo.core.engine import locate_ffmpeg, has_nvenc_acceleration, probe_media
from clippo.audio.leveler import get_audio_filter_chain, extract_silences
from clippo.shorts.cropper import calculate_shorts_schedule

def main():
    parser = argparse.ArgumentParser(
        prog="clippo",
        description="CLIPPO: Autonomous High-Performance Video Ingestion & Shorts Production Engine."
    )
    parser.add_argument("input_file", help="Path to raw source footage (MXF, MP4, MOV, MKV)")
    parser.add_argument("-n", "--num-clips", default="auto", help="Number of shorts to generate (default: auto)")
    parser.add_argument("-c", "--concurrency", type=int, default=3, help="Concurrent encoding workers (default: 3)")
    parser.add_argument("--min-duration", type=float, default=45.0, help="Min short length in seconds")
    parser.add_argument("--max-duration", type=float, default=65.0, help="Max short length in seconds")
    parser.add_argument("--logo", default=None, help="Path to animated transparent logo or watermark")
    parser.add_argument("--no-dynamic-audio", action="store_true", help="Disable real-time speech dynamic leveling")
    parser.add_argument("--skip-master", action="store_true", help="Skip 16:9 master render")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_file)
    if not os.path.isfile(input_path):
        print(f"[!] Error: Target file not found: {input_path}")
        sys.exit(1)

    ffmpeg_bin = locate_ffmpeg()
    has_nvenc = has_nvenc_acceleration(ffmpeg_bin)
    out_dir = os.path.dirname(input_path)
    scratch_dir = os.path.join(out_dir, "_clippo_temp")
    os.makedirs(scratch_dir, exist_ok=True)

    print("==================================================")
    print(" CLIPPO ENGINE - INITIALIZING PIPELINE")
    print("==================================================")
    print(f" Source Video   : {input_path}")
    print(f" Output Folder  : {out_dir}")
    print(f" Hardware Accel : {'NVIDIA NVENC (GPU)' if has_nvenc else 'CPU (libx264)'}")
    print(f" Concurrency    : {args.concurrency} workers")
    print("--------------------------------------------------")

    info = probe_media(ffmpeg_bin, input_path)
    print(f" Duration: {info['duration']:.2f}s | 4K: {info['is_4k']} | Audio: {info['audio_stream']}")

    # Extract audio for silence mapping
    temp_audio = os.path.join(scratch_dir, "speech.mp3")
    subprocess.run([
        ffmpeg_bin, "-y", "-i", input_path,
        "-map", info["audio_stream"], "-ac", "2",
        "-vn", "-b:a", "64k", temp_audio
    ], check=True, capture_output=True)

    silences = extract_silences(ffmpeg_bin, temp_audio)
    num_req = int(args.num_clips) if args.num_clips != "auto" else None
    schedule = calculate_shorts_schedule(
        info["duration"], silences, num_req, args.min_duration, args.max_duration
    )
    print(f" Planned {len(schedule)} high-impact vertical shorts.")

    audio_chain = get_audio_filter_chain(dynamic=not args.no_dynamic_audio)
    v_enc = ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20"] if has_nvenc else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]

    # 1. Master Landscape Video
    master_path = os.path.join(out_dir, "Master_Landscape_Branded.mp4")
    if not args.skip_master and not os.path.exists(master_path):
        print("\n[*] Rendering 16:9 Landscape Master Video...")
        scale_logo = "560:-1" if info["is_4k"] else "280:-1"
        overlay_pos = "x=W-w-100:y=100" if info["is_4k"] else "x=W-w-50:y=50"
        
        if args.logo and os.path.isfile(args.logo):
            f_str = f"[0:v]setpts=PTS-STARTPTS[bg];[1:v]setpts=PTS-STARTPTS,scale={scale_logo}[logo];[bg][logo]overlay={overlay_pos}:shortest=1[v];[{info['audio_stream']}]{audio_chain}[a]"
            cmd = [ffmpeg_bin, "-y", "-i", input_path, "-stream_loop", "-1", "-i", args.logo, "-filter_complex", f_str, "-map", "[v]", "-map", "[a]", *v_enc, "-c:a", "aac", "-b:a", "192k", master_path]
        else:
            f_str = f"[0:v]setpts=PTS-STARTPTS[v];[{info['audio_stream']}]{audio_chain}[a]"
            cmd = [ffmpeg_bin, "-y", "-i", input_path, "-filter_complex", f_str, "-map", "[v]", "-map", "[a]", *v_enc, "-c:a", "aac", "-b:a", "192k", master_path]
        subprocess.run(cmd, check=True)
        print(f"[✓] Master complete: {master_path}")

    # 2. Render Vertical Shorts in Parallel
    print(f"\n[*] Rendering {len(schedule)} 9:16 Vertical Shorts...")
    def render_short(item):
        sid = item["id"]
        st = item["start"]
        dur = item["duration"]
        name = f"Short_{sid:02d}_{int(st)}s_to_{int(st+dur)}s.mp4"
        out_f = os.path.join(out_dir, name)

        if args.logo and os.path.isfile(args.logo):
            f_shorts = f"[0:v]crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,setpts=PTS-STARTPTS[bg];[1:v]setpts=PTS-STARTPTS,scale=260:-1[logo];[bg][logo]overlay=x=1080-w-60:y=80:shortest=1[v];[{info['audio_stream']}]{audio_chain}[a]"
            cmd = [ffmpeg_bin, "-y", "-ss", str(st), "-t", str(dur), "-i", input_path, "-stream_loop", "-1", "-i", args.logo, "-filter_complex", f_shorts, "-map", "[v]", "-map", "[a]", *v_enc, "-c:a", "aac", "-b:a", "192k", out_f]
        else:
            f_shorts = f"[0:v]crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920,setpts=PTS-STARTPTS[v];[{info['audio_stream']}]{audio_chain}[a]"
            cmd = [ffmpeg_bin, "-y", "-ss", str(st), "-t", str(dur), "-i", input_path, "-filter_complex", f_shorts, "-map", "[v]", "-map", "[a]", *v_enc, "-c:a", "aac", "-b:a", "192k", out_f]
        subprocess.run(cmd, check=True)
        print(f" [✓] Finished Short {sid:02d} ({dur}s): {name}")
        return name

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for f in as_completed([pool.submit(render_short, s) for s in schedule]):
            f.result()

    # Clean temporary scratch
    try:
        import shutil
        shutil.rmtree(scratch_dir, ignore_errors=True)
    except Exception:
        pass

    print("\n==================================================")
    print(" [✓] CLIPPO PIPELINE FINISHED SUCCESSFULLY")
    print(f" All outputs created in: {out_dir}")
    print("==================================================")

if __name__ == "__main__":
    main()
