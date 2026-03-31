import os
import subprocess
from config import FINAL_VIDEOS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.logger import get_logger

logger = get_logger(__name__)

FFMPEG_PRESET = "ultrafast"
FFMPEG_CRF = "30"
FFMPEG_THREADS = "2"
FFMPEG_TIMEOUT = 180

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
    scaled_clips: list[str] = []

    try:
        valid_clips = [c for c in clips if os.path.exists(c) and os.path.getsize(c) > 0]
        if not valid_clips:
            logger.error(f"[{job_id}] No valid clip files found")
            return None

        logger.info(f"[{job_id}] Assembling {len(valid_clips)} clips")

        for i, clip in enumerate(valid_clips):
            scaled = os.path.join(out_dir, f"scaled_{i}.mp4")
            if _scale_clip(clip, scaled, job_id, i):
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
            # ── Subtitle style: clean, modern, mobile-friendly ─────────────
            # FontName=DejaVu Sans — crisp, open-source, always on Linux;
            #                        much more readable than Arial at small sizes
            # FontSize=28          — proportionate for 1080×1920 portrait video
            # Bold=1               — bold weight for impact
            # PrimaryColour        — warm white (slightly off-white) text
            # OutlineColour        — pure black outline for contrast on any bg
            # Outline=2            — solid outline so text pops on busy clips
            # Shadow=1             — subtle drop-shadow for depth
            # ShadowColour         — semi-transparent black shadow
            # BackColour           — transparent (no opaque box)
            # BorderStyle=1        — outline+shadow mode (no box)
            # Alignment=2          — bottom-centre (standard subtitle position)
            # MarginV=55           — comfortable distance from the bottom edge
            # MarginL/R=35         — side margins so text never clips the edge
            vf_filter += (
                f",subtitles='{escaped}'"
                f":force_style='"
                f"FontName=DejaVu Sans,"
                f"FontSize=28,"
                f"Bold=1,"
                f"PrimaryColour=&H00F5F5F5,"
                f"OutlineColour=&H00000000,"
                f"Outline=2,"
                f"Shadow=1,"
                f"ShadowColour=&HA0000000,"
                f"BackColour=&H00000000,"
                f"BorderStyle=1,"
                f"Alignment=2,"
                f"MarginV=55,"
                f"MarginL=35,"
                f"MarginR=35'"
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
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            "-shortest",
            "-movflags",
            "+faststart",
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
        _cleanup([concat_file] + scaled_clips)


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
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")
        duration_str = result.stdout.strip()
        if not duration_str:
            raise RuntimeError("ffprobe returned empty duration")
        duration = float(duration_str)
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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Read stderr line by line — prevents pipe buffer deadlock
        # and avoids loading entire stderr into RAM
        stderr_tail: list[str] = []
        for line in process.stderr:
            line = line.rstrip()
            if line:
                stderr_tail.append(line)
                if len(stderr_tail) > 20:
                    stderr_tail.pop(0)

        # stderr pipe is now drained — wait is safe, no deadlock possible
        try:
            process.wait(timeout=FFMPEG_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise RuntimeError(
                f"[{job_id}] FFmpeg [{step}] killed after {FFMPEG_TIMEOUT}s timeout"
            )

        if process.returncode != 0:
            tail = "\n".join(stderr_tail)
            raise RuntimeError(
                f"[{job_id}] FFmpeg [{step}] failed (exit {process.returncode}):\n{tail}"
            )

        logger.info(f"[{job_id}] FFmpeg [{step}] complete")

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"[{job_id}] FFmpeg [{step}] unexpected error: {e}")


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
