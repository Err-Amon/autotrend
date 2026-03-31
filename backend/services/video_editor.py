import os
import subprocess
from config import FINAL_VIDEOS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.logger import get_logger

logger = get_logger(__name__)

FFMPEG_PRESET = "ultrafast"  # Lowest CPU usage during encoding
FFMPEG_CRF = "30"  # Slightly lower quality but much less memory
FFMPEG_THREADS = "2"  # Cap at 2 threads — prevents CPU saturation
FFMPEG_TIMEOUT = 180  # 3 minute hard limit per FFmpeg call

# Process at lower resolution internally, final output is still 1080x1920
# but clips are scaled down before concat to reduce memory footprint
PROCESS_WIDTH = 540
PROCESS_HEIGHT = 960


def assemble_video(
    clips: list[str],
    audio_path: str,
    subtitle_path: str | None,
    job_id: str,
    output_dir: str = "",
) -> str | None:
    if not clips:
        logger.error(f"[{job_id}] No clips provided for assembly")
        return None

    if not os.path.exists(audio_path):
        logger.error(f"[{job_id}] Audio file not found: {audio_path}")
        return None

    out_dir = output_dir or FINAL_VIDEOS_DIR
    os.makedirs(out_dir, exist_ok=True)

    concat_file = os.path.join(out_dir, "concat.txt")
    output_path = os.path.join(out_dir, "final.mp4")

    try:
        # Validate clips
        valid_clips = [c for c in clips if os.path.exists(c) and os.path.getsize(c) > 0]
        if not valid_clips:
            logger.error(f"[{job_id}] No valid clip files found")
            return None

        logger.info(f"[{job_id}] Assembling {len(valid_clips)} clips")

        scaled_clips = []
        for i, clip in enumerate(valid_clips):
            scaled = os.path.join(out_dir, f"scaled_{i}.mp4")
            success = _scale_clip(clip, scaled, job_id, i)
            if success:
                scaled_clips.append(scaled)

        if not scaled_clips:
            logger.error(f"[{job_id}] All clip scaling failed")
            return None

        with open(concat_file, "w") as f:
            for clip in scaled_clips:
                f.write(f"file '{os.path.abspath(clip)}'\n")

        vf_filter = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={VIDEO_FPS}"
        )

        if subtitle_path and os.path.exists(subtitle_path):
            escaped = _escape_subtitle_path(subtitle_path)
            vf_filter += (
                f",subtitles='{escaped}'"
                f":force_style='FontSize=16,PrimaryColour=&Hffffff,"
                f"OutlineColour=&H000000,Outline=2,Alignment=2,MarginV=20'"
            )

        cmd = [
            "ffmpeg",
            "-y",
            "-threads",
            FFMPEG_THREADS,
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-i",
            audio_path,
            "-vf",
            vf_filter,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            FFMPEG_PRESET,
            "-crf",
            FFMPEG_CRF,
            "-threads",
            FFMPEG_THREADS,
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-shortest",
            "-movflags",
            "+faststart",  # Web-optimised MP4
            output_path,
        ]

        _run_ffmpeg(cmd, job_id, step="concat+audio+subtitles")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error(f"[{job_id}] FFmpeg produced no output")
            return None

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        logger.info(f"[{job_id}] Final video ready: {output_path} ({size_mb:.1f}MB)")
        return output_path

    except RuntimeError as e:
        logger.error(str(e))
        return None
    except Exception as e:
        logger.error(f"[{job_id}] Video assembly failed: {e}")
        return None
    finally:
        # Clean up scaled intermediates and concat file
        _cleanup([concat_file])
        for i in range(len(valid_clips) if "valid_clips" in dir() else 0):
            _cleanup([os.path.join(out_dir, f"scaled_{i}.mp4")])


def _scale_clip(input_path: str, output_path: str, job_id: str, index: int) -> bool:
    scale_filter = (
        f"scale={PROCESS_WIDTH}:{PROCESS_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={PROCESS_WIDTH}:{PROCESS_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"fps={VIDEO_FPS}"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-threads",
        FFMPEG_THREADS,
        "-i",
        input_path,
        "-vf",
        scale_filter,
        "-c:v",
        "libx264",
        "-preset",
        FFMPEG_PRESET,
        "-crf",
        FFMPEG_CRF,
        "-threads",
        FFMPEG_THREADS,
        "-an",
        output_path,
    ]
    try:
        _run_ffmpeg(cmd, job_id, step=f"scale-clip-{index}")
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except RuntimeError as e:
        logger.warning(f"[{job_id}] Clip {index} scaling failed: {e}")
        return False


def get_audio_duration(audio_path: str) -> float:
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found: {audio_path}, defaulting to 30s")
        return 30.0

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        duration = float(result.stdout.strip())
        logger.info(f"Audio duration: {duration:.2f}s")
        return duration
    except Exception as e:
        logger.warning(f"Could not get audio duration: {e}, defaulting to 30s")
        return 30.0


def _run_ffmpeg(cmd: list[str], job_id: str, step: str = ""):
    logger.info(f"[{job_id}] FFmpeg [{step}] starting")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,  # Discard stdout entirely
            stderr=subprocess.PIPE,  # Stream stderr — not buffer it
            text=True,
        )

        # Read stderr line by line — no memory accumulation
        stderr_tail = []
        for line in process.stderr:
            line = line.rstrip()
            if line:
                stderr_tail.append(line)
                if len(stderr_tail) > 20:
                    stderr_tail.pop(0)  # Keep only last 20 lines

        process.wait(timeout=FFMPEG_TIMEOUT)

        if process.returncode != 0:
            tail = "\n".join(stderr_tail)
            raise RuntimeError(
                f"[{job_id}] FFmpeg [{step}] failed (exit {process.returncode}):\n{tail}"
            )

        logger.info(f"[{job_id}] FFmpeg [{step}] complete")

    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError(
            f"[{job_id}] FFmpeg [{step}] killed after {FFMPEG_TIMEOUT}s timeout"
        )


def _escape_subtitle_path(path: str) -> str:
    escaped = os.path.abspath(path).replace("\\", "/")
    if ":" in escaped:
        escaped = escaped.replace(":", "\\:")
    return escaped


def _cleanup(paths: list[str]):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                logger.warning(f"Could not remove temp file {p}: {e}")
