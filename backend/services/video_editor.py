import os
import subprocess
from config import FINAL_VIDEOS_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.logger import get_logger

logger = get_logger(__name__)

def assemble_video(clips: list[str], audio_path: str, subtitle_path: str | None, job_id: str) -> str | None:
    try:
        output_path = os.path.join(FINAL_VIDEOS_DIR, f"{job_id}_final.mp4")
        concat_file = os.path.join(FINAL_VIDEOS_DIR, f"{job_id}_concat.txt")

        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{os.path.abspath(clip)}'\n")

        concat_output = os.path.join(FINAL_VIDEOS_DIR, f"{job_id}_merged.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
                   f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-r", str(VIDEO_FPS), "-c:v", "libx264", "-preset", "fast",
            "-an", concat_output,
        ], check=True, capture_output=True)

        filter_complex = "anull"
        vf_filter = f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease," \
                    f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2"

        if subtitle_path and os.path.exists(subtitle_path):
            abs_sub = os.path.abspath(subtitle_path).replace("\\", "/").replace(":", "\\:")
            vf_filter += f",subtitles='{abs_sub}'"

        subprocess.run([
            "ffmpeg", "-y",
            "-i", concat_output,
            "-i", audio_path,
            "-vf", vf_filter,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac", "-shortest",
            output_path,
        ], check=True, capture_output=True)

        os.remove(concat_file)
        os.remove(concat_output)
        logger.info(f"Final video: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        return None
    except Exception as e:
        logger.error(f"Video assembly failed: {e}")
        return None

def get_audio_duration(audio_path: str) -> float:
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path,
        ], capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Could not get audio duration: {e}")
        return 30.0
