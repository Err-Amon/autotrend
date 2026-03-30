import os
import subprocess
from config import FINAL_VIDEOS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.logger import get_logger

logger = get_logger(__name__)

FFMPEG_PRESET = "fast"
FFMPEG_CRF = "28"  # Slightly compressed to save disk space on 8GB RAM machines


def assemble_video(
    clips: list[str],
    audio_path: str,
    subtitle_path: str | None,
    job_id: str,
) -> str | None:
    if not clips:
        logger.error("No clips provided for video assembly")
        return None

    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return None

    os.makedirs(FINAL_VIDEOS_DIR, exist_ok=True)

    concat_file = os.path.join(FINAL_VIDEOS_DIR, f"{job_id}_concat.txt")
    merged_path = os.path.join(FINAL_VIDEOS_DIR, f"{job_id}_merged.mp4")
    output_path = os.path.join(FINAL_VIDEOS_DIR, f"{job_id}_final.mp4")

    try:
        # Step 1: Write concat list
        valid_clips = [c for c in clips if os.path.exists(c) and os.path.getsize(c) > 0]
        if not valid_clips:
            logger.error("None of the provided clips exist or are non-empty")
            return None

        with open(concat_file, "w") as f:
            for clip in valid_clips:
                f.write(f"file '{os.path.abspath(clip)}'\n")

        logger.info(f"Concatenating {len(valid_clips)} clips")

        # Step 2: Concatenate and scale clips to vertical format (no audio yet)
        scale_filter = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={VIDEO_FPS}"
        )

        _run_ffmpeg(
            [
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_file,
                "-vf",
                scale_filter,
                "-c:v",
                "libx264",
                "-preset",
                FFMPEG_PRESET,
                "-crf",
                FFMPEG_CRF,
                "-an",
                merged_path,
            ],
            step="concat+scale",
        )

        # Step 3: Build video filter for final output
        vf_parts = [scale_filter]

        if subtitle_path and os.path.exists(subtitle_path):
            # Escape path for FFmpeg subtitle filter
            escaped = os.path.abspath(subtitle_path).replace("\\", "/")
            if ":" in escaped:
                # Windows drive letter fix
                escaped = escaped.replace(":", "\\:")
            vf_parts.append(
                f"subtitles='{escaped}':force_style='FontSize=18,PrimaryColour=&Hffffff,"
                f"OutlineColour=&H000000,Outline=2,Alignment=2'"
            )

        vf_filter = ",".join(vf_parts)

        # Step 4: Merge video + audio, burn subtitles
        logger.info("Merging video with audio and subtitles")
        _run_ffmpeg(
            [
                "-y",
                "-i",
                merged_path,
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
                "128k",
                "-shortest",
                output_path,
            ],
            step="merge+audio",
        )

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("FFmpeg produced no output file")
            return None

        size_mb = os.path.getsize(output_path) / 1024 / 1024
        logger.info(f"Final video ready: {output_path} ({size_mb:.1f}MB)")
        return output_path

    except RuntimeError as e:
        logger.error(str(e))
        return None
    except Exception as e:
        logger.error(f"Video assembly failed: {e}")
        return None
    finally:
        _cleanup([concat_file, merged_path])


def get_audio_duration(audio_path: str) -> float:
    if not os.path.exists(audio_path):
        logger.warning(f"Audio file not found for duration check: {audio_path}")
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
    except (ValueError, subprocess.TimeoutExpired, Exception) as e:
        logger.warning(f"Could not get audio duration: {e}, defaulting to 30s")
        return 30.0


def _run_ffmpeg(args: list[str], step: str = ""):
    cmd = ["ffmpeg"] + args
    logger.info(f"FFmpeg [{step}]: {' '.join(cmd[:6])}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(
                f"FFmpeg [{step}] failed (exit {result.returncode}): {stderr[-500:]}"
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"FFmpeg [{step}] timed out after 300 seconds")


def _cleanup(paths: list[str]):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                logger.warning(f"Could not remove temp file {p}: {e}")
