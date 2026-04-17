import os
import subprocess
from config import (
    FINAL_VIDEOS_DIR,
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    OPENROUTER_API_KEY,
    GROQ_API_KEY,
)
from utils.logger import get_logger
from integrations.openrouter_client import openrouter_chat
from integrations.groq_client import groq_chat

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
            # Try to use ASS format if available (has fade effects)
            ass_path = subtitle_path.replace(".srt", ".ass")
            subtitle_file = ass_path if os.path.exists(ass_path) else subtitle_path

            escaped = _escape_subtitle_path(subtitle_file)

            # Check if using ASS (with effects) or SRT (basic)
            is_ass = subtitle_file.endswith(".ass")

            if is_ass:
                # ASS format with built-in fade effects - use simpler overlay
                vf_filter += f",subtitles='{escaped}'"
                logger.info(f"[{job_id}] Using ASS subtitles with fade effects")
            else:
                # SRT format - apply enhanced styling scaled for vertical video
                vf_filter += (
                    f",subtitles='{escaped}'"
                    f":force_style='"
                    f"FontName=Noto Sans Bold,"
                    f"FontSize=36,"
                    f"Bold=1,"
                    f"PrimaryColour=&H00FFFFFF,"
                    f"SecondaryColour=&H00FFFF00,"
                    f"OutlineColour=&H00000000,"
                    f"BackColour=&H88000000,"
                    f"Outline=4,"
                    f"Shadow=5,"
                    f"ShadowColour=&H99000000,"
                    f"BorderStyle=1,"
                    f"Alignment=2,"
                    f"MarginV=150,"
                    f"MarginL=60,"
                    f"MarginR=60,"
                    f"Spacing=3,"
                    f"Angle=0'"
                )
                logger.info(f"[{job_id}] Using SRT subtitles with enhanced styling")

            # Try OpenRouter Qwen 3.6 Plus for subtitle generation if no file exists
            if not os.path.exists(subtitle_path) and OPENROUTER_API_KEY:
                try:
                    # Read the script/assumed content and generate subtitles via OpenRouter
                    script_path = os.path.join(out_dir, "script.txt")
                    with open(script_path, "r") as f:
                        script_content = f.read()

                    messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are a subtitle generation expert. "
                                "Generate precise subtitles from video script content. "
                                "Output only the subtitle text with timing markers."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Generate subtitles for this video script:\n{script_content}\n"
                                f"Return in SRT format with proper timing."
                            ),
                        },
                    ]
                    subtitle_content = None
                    if OPENROUTER_API_KEY:
                        subtitle_content = openrouter_chat(messages, max_tokens=2000)
                    if not subtitle_content and GROQ_API_KEY:
                        subtitle_content = groq_chat(messages, max_tokens=2000)
                    if subtitle_content:
                        subtitle_path_srt = subtitle_path.replace(".srt", "_auto.srt")
                        with open(subtitle_path_srt, "w") as f:
                            f.write(subtitle_content)
                        subtitle_file = subtitle_path_srt
                        logger.info(
                            f"Generated OpenRouter subtitles: {subtitle_path_srt}"
                        )
                except Exception as e:
                    logger.error(f"OpenRouter subtitle generation failed: {e}")

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
        if process.stderr:
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
