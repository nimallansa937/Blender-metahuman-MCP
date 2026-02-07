"""
Face Landmark Detection

Uses Google MediaPipe FaceLandmarker (Tasks API) to detect 478 facial landmarks
from a single 2D photo. Returns normalized (x, y, z) coordinates.

MediaPipe FaceLandmarker coordinates:
  - x, y: Normalized to [0.0, 1.0] by image dimensions
  - z: Depth estimate (head center = origin, smaller = closer to camera)
  - z scale is roughly comparable to x/y
"""

import os
import logging
import urllib.request

logger = logging.getLogger("face_reconstruction.landmark_detector")

# Path to the face landmarker model (auto-downloaded on first use)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def _ensure_model():
    """Download the face landmarker model if it doesn't exist."""
    if os.path.isfile(MODEL_PATH):
        return True
    try:
        logger.info(f"Downloading face landmarker model ({MODEL_URL})...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        logger.info(f"Downloaded face landmarker model ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        return False


def detect_face_landmarks(image_path: str) -> dict:
    """Detect 478 face landmarks from a photo using MediaPipe FaceLandmarker.

    Args:
        image_path: Absolute path to a face photo (JPG, PNG, BMP, etc.).
                    The face should be front-facing, well-lit, and clearly visible.

    Returns:
        dict with keys:
            success: bool — whether a face was detected
            landmarks: list of (x, y, z) tuples — 478 normalized coordinates
            confidence: float — face detection confidence [0, 1]
            image_width: int — original image width in pixels
            image_height: int — original image height in pixels
            error: str or None — error message if unsuccessful
    """
    # Validate file exists
    if not image_path:
        return _error_result("No image path provided")

    if not os.path.isfile(image_path):
        return _error_result(f"File not found: {image_path}")

    # Validate extension
    supported_ext = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    _, ext = os.path.splitext(image_path.lower())
    if ext not in supported_ext:
        return _error_result(
            f"Unsupported image format '{ext}'. "
            f"Supported: {', '.join(sorted(supported_ext))}"
        )

    # Ensure model is downloaded
    if not _ensure_model():
        return _error_result(
            f"Face landmarker model not found at {MODEL_PATH} and auto-download failed. "
            f"Download manually from: {MODEL_URL}"
        )

    # Import dependencies (lazy to avoid import errors if not installed)
    try:
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions, vision
    except ImportError:
        return _error_result(
            "MediaPipe not installed. Run: pip install mediapipe"
        )

    # Load image using MediaPipe's own Image class
    try:
        mp_image = mp.Image.create_from_file(image_path)
        image_width = mp_image.width
        image_height = mp_image.height
    except Exception as e:
        return _error_result(
            f"Could not read image: {image_path}. "
            f"Error: {e}"
        )

    logger.info(f"Loaded image: {image_width}x{image_height} from {image_path}")

    # Configure FaceLandmarker
    options = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )

    # Run detection
    with vision.FaceLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(mp_image)

    # Check if face was detected
    if not result.face_landmarks or len(result.face_landmarks) == 0:
        return _error_result(
            "No face detected in the image. Tips:\n"
            "  - Use a front-facing photo with the face clearly visible\n"
            "  - Ensure good lighting without harsh shadows\n"
            "  - The face should fill a significant portion of the image\n"
            "  - Avoid heavy occlusion (sunglasses, masks, etc.)"
        )

    # Extract landmarks from the first detected face
    face_landmarks = result.face_landmarks[0]
    landmarks = []

    for lm in face_landmarks:
        landmarks.append((lm.x, lm.y, lm.z))

    # Estimate detection confidence
    confidence = _estimate_confidence(landmarks, image_width, image_height)

    num_faces = len(result.face_landmarks)
    if num_faces > 1:
        logger.warning(f"Multiple faces detected ({num_faces}), using the first one")

    logger.info(
        f"Detected {len(landmarks)} landmarks with confidence {confidence:.2f}"
    )

    return {
        "success": True,
        "landmarks": landmarks,
        "confidence": confidence,
        "image_width": image_width,
        "image_height": image_height,
        "num_landmarks": len(landmarks),
        "error": None,
    }


def _estimate_confidence(landmarks, image_width, image_height):
    """Estimate detection confidence based on landmark quality.

    Heuristics:
      - Face should occupy at least 10% of the image
      - Landmarks should be within image bounds
      - Face should be roughly symmetric
    """
    if not landmarks or len(landmarks) < 468:
        return 0.3

    # Check face coverage
    xs = [lm[0] for lm in landmarks]
    ys = [lm[1] for lm in landmarks]
    face_width_norm = max(xs) - min(xs)
    face_height_norm = max(ys) - min(ys)
    face_area = face_width_norm * face_height_norm

    # Face should cover at least 5% of image for good detection
    coverage_score = min(1.0, face_area / 0.05)

    # Check that landmarks are within bounds (some small overflow is ok)
    in_bounds = sum(1 for x, y, z in landmarks if -0.05 <= x <= 1.05 and -0.05 <= y <= 1.05)
    bounds_score = in_bounds / len(landmarks)

    # Check rough symmetry using eye landmarks
    # Left eye: 33 (outer), 133 (inner)
    # Right eye: 263 (outer), 362 (inner)
    left_eye_x = (landmarks[33][0] + landmarks[133][0]) / 2
    right_eye_x = (landmarks[263][0] + landmarks[362][0]) / 2
    nose_x = landmarks[4][0]  # Nose tip

    # Eyes should be roughly equidistant from nose
    left_dist = abs(nose_x - left_eye_x)
    right_dist = abs(nose_x - right_eye_x)
    symmetry_score = 1.0 - min(1.0, abs(left_dist - right_dist) / max(left_dist, right_dist, 0.001))

    # Weighted confidence
    confidence = (
        coverage_score * 0.3 +
        bounds_score * 0.3 +
        symmetry_score * 0.4
    )

    return round(min(1.0, max(0.1, confidence)), 2)


def _error_result(error_msg):
    """Return a standardized error result dict."""
    logger.error(error_msg)
    return {
        "success": False,
        "landmarks": [],
        "confidence": 0.0,
        "image_width": 0,
        "image_height": 0,
        "num_landmarks": 0,
        "error": error_msg,
    }
