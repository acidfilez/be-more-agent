"""Camera capture for Be More Agent."""
import subprocess
import logging
from PIL import Image

from config import CURRENT_CONFIG, BMO_IMAGE_FILE

logger = logging.getLogger(__name__)


def capture_image(rotation=None):
    """Capture an image from camera (rpicam-still or ffmpeg fallback)."""
    if rotation is None:
        rotation = CURRENT_CONFIG.get("camera_rotation", 0)
    cam_device = CURRENT_CONFIG.get("camera_device", "auto")

    try:
        # Try rpicam-still first (Raspberry Pi camera module)
        if cam_device in ("auto", "rpicam"):
            try:
                subprocess.run(
                    ["rpicam-still", "-t", "500", "-n", "--width", "640",
                     "--height", "480", "-o", BMO_IMAGE_FILE],
                    check=True, capture_output=True, timeout=10
                )
                logger.info("Captured with rpicam-still")
                return _rotate_and_return(rotation)
            except (FileNotFoundError, subprocess.CalledProcessError,
                    subprocess.TimeoutExpired) as e:
                if cam_device == "rpicam":
                    logger.warning(f"rpicam failed: {e}")
                    return None
                logger.info("rpicam not available, trying USB webcam...")

        # Fallback: ffmpeg USB webcam
        dev = cam_device if cam_device not in ("auto", "rpicam") else "/dev/video0"
        try:
            subprocess.run(
                ["ffmpeg", "-f", "v4l2", "-i", dev,
                 "-vframes", "1", "-s", "640x480", "-y", BMO_IMAGE_FILE],
                check=True, capture_output=True, timeout=10
            )
            logger.info(f"Captured with ffmpeg from {dev}")
            return _rotate_and_return(rotation)
        except (FileNotFoundError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired) as e:
            logger.warning(f"ffmpeg failed on {dev}: {e}")
            return None

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def _rotate_and_return(rotation):
    if rotation != 0:
        try:
            img = Image.open(BMO_IMAGE_FILE)
            img = img.rotate(rotation, expand=True)
            img.save(BMO_IMAGE_FILE)
        except Exception as e:
            logger.warning(f"Rotation failed: {e}")
    return BMO_IMAGE_FILE
