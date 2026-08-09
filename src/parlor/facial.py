"""Facial Micro-Expression & Action Unit (AU) Feature Extraction Pipeline.

Uses MediaPipe Face Mesh (468 3D landmarks) to derive real-time facial stress
biomarkers (brow furrow, lid tightening, lip depression, jaw tension, and head pose).
Includes graceful error fallbacks for unlit frames or missing faces.
"""

import time
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np

# Compatibility patch for MediaPipe solutions on Python 3.12 + Protobuf v4/v5
try:
    import google.protobuf.message_factory
    import google.protobuf.symbol_database
    if not hasattr(google.protobuf.message_factory.MessageFactory, 'GetPrototype'):
        google.protobuf.message_factory.MessageFactory.GetPrototype = lambda self, d: getattr(d, '_concrete_class', None)
    if not hasattr(google.protobuf.symbol_database.SymbolDatabase, 'GetPrototype'):
        google.protobuf.symbol_database.SymbolDatabase.GetPrototype = lambda self, d: getattr(d, '_concrete_class', None)
    import google._upb._message
    if not hasattr(google._upb._message.FieldDescriptor, 'label'):
        google._upb._message.FieldDescriptor.label = property(lambda self: getattr(self, 'number', 0))
except Exception:
    pass

try:
    import cv2
    import mediapipe as mp
    MP_AVAILABLE = True
except ImportError:
    MP_AVAILABLE = False


class FacialExtractor:
    """Extracts Action Units (AUs) and facial biomarkers from image frames."""

    # Key Landmark Indices (MediaPipe Face Mesh 468 schema):
    # Left Pupil: 468 / Left Eye Corner: 33, Right Eye Corner: 263
    # Left Eye Top/Bottom: 159, 145 / Right Eye Top/Bottom: 386, 374
    # Eyebrow Inner Left: 70, Right: 300
    # Mouth Left: 61, Right: 291, Top: 13, Bottom: 14, Nose Tip: 1

    def __init__(self, max_faces: int = 1, min_detection_confidence: float = 0.5):
        self.mp_available = MP_AVAILABLE
        self.face_mesh = None
        if MP_AVAILABLE:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=max_faces,
                    refine_landmarks=True,
                    min_detection_confidence=min_detection_confidence
                )
            except Exception as e:
                print(f"[FACIAL EXTRACTOR WARNING] Failed to initialize MediaPipe FaceMesh: {e}")
                self.mp_available = False

        # 3D Model Points for solvePnP Head Pose Estimation (Nose tip, Chin, Left Eye, Right Eye, Left Mouth, Right Mouth)
        self.model_points_3d = np.array([
            (0.0, 0.0, 0.0),             # Nose tip (1)
            (0.0, -330.0, -65.0),        # Chin (152)
            (-225.0, 170.0, -135.0),     # Left eye left corner (33)
            (225.0, 170.0, -135.0),      # Right eye right corner (263)
            (-150.0, -150.0, -125.0),    # Left Mouth corner (61)
            (150.0, -150.0, -125.0)      # Right Mouth corner (291)
        ], dtype=np.float64)

    def extract(self, image_input: Any) -> Dict[str, Any]:
        """Extract facial feature vector from numpy image array (BGR or RGB) or Base64 JPEG.
        
        Returns:
            Dict containing:
                - face_detected: bool
                - confidence: float (0.0 to 1.0)
                - au04_brow_furrow: float (0.0 to 1.0, higher = furrowed brow / stress)
                - au07_lid_tightener: float (0.0 to 1.0, lower EAR = eye strain/squinting)
                - au15_lip_depressor: float (0.0 to 1.0, higher = depressed mouth corners)
                - au20_lip_stretcher: float (0.0 to 1.0, higher = horizontal mouth tension)
                - ear: float (Eye Aspect Ratio, normal ~0.28-0.35, <0.20 = blink)
                - head_pitch: float (degrees, up/down)
                - head_yaw: float (degrees, left/right)
                - head_roll: float (degrees, tilt)
                - latency_ms: float
        """
        t0 = time.time()
        fallback_res = {
            "face_detected": False,
            "confidence": 0.0,
            "au04_brow_furrow": 0.0,
            "au07_lid_tightener": 0.0,
            "au15_lip_depressor": 0.0,
            "au20_lip_stretcher": 0.0,
            "ear": 0.30,
            "head_pitch": 0.0,
            "head_yaw": 0.0,
            "head_roll": 0.0,
            "latency_ms": 0.0
        }

        if not self.mp_available or image_input is None:
            fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
            return fallback_res

        # Convert image input if necessary
        try:
            if isinstance(image_input, str):
                import base64
                img_data = base64.b64decode(image_input)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            elif isinstance(image_input, np.ndarray):
                frame = image_input
            else:
                fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
                return fallback_res

            if frame is None or frame.size == 0:
                fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
                return fallback_res

            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if len(frame.shape) == 3 and frame.shape[2] == 3 else frame
            results = self.face_mesh.process(rgb_frame)

            if not results.multi_face_landmarks:
                fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
                return fallback_res

            face_landmarks = results.multi_face_landmarks[0]
            landmarks = face_landmarks.landmark

            # 1. Inter-pupillary distance (IPD) as normalization factor (Landmarks 33 & 263)
            p33 = np.array([landmarks[33].x * w, landmarks[33].y * h])
            p263 = np.array([landmarks[263].x * w, landmarks[263].y * h])
            ipd = np.linalg.norm(p33 - p263)
            if ipd < 1e-5:
                ipd = 1.0

            # 2. AU04 (Brow Lowerer / Furrow): Inner Eyebrow distance (70 to 300) / IPD
            p70 = np.array([landmarks[70].x * w, landmarks[70].y * h])
            p300 = np.array([landmarks[300].x * w, landmarks[300].y * h])
            brow_dist = np.linalg.norm(p70 - p300) / ipd
            # Normal brow_dist is ~0.45-0.55; smaller distance = brow furrowing / tension
            au04_furrow = float(np.clip(1.0 - (brow_dist / 0.50), 0.0, 1.0))

            # 3. Eye Aspect Ratio (EAR) -> AU07 (Lid Tightener)
            # Left Eye: 159 (top), 145 (bottom), 33 (left), 133 (right)
            p159 = np.array([landmarks[159].x * w, landmarks[159].y * h])
            p145 = np.array([landmarks[145].x * w, landmarks[145].y * h])
            p133 = np.array([landmarks[133].x * w, landmarks[133].y * h])
            left_ear = np.linalg.norm(p159 - p145) / max(np.linalg.norm(p33 - p133), 1e-5)

            # Right Eye: 386 (top), 374 (bottom), 362 (left), 263 (right)
            p386 = np.array([landmarks[386].x * w, landmarks[386].y * h])
            p374 = np.array([landmarks[374].x * w, landmarks[374].y * h])
            p362 = np.array([landmarks[362].x * w, landmarks[362].y * h])
            right_ear = np.linalg.norm(p386 - p374) / max(np.linalg.norm(p362 - p263), 1e-5)
            avg_ear = float((left_ear + right_ear) / 2.0)
            au07_lid_tight = float(np.clip(1.0 - (avg_ear / 0.32), 0.0, 1.0))

            # 4. AU15 (Lip Corner Depressor): Mouth Corners (61, 291) drop relative to Nose (1)
            p1 = np.array([landmarks[1].x * w, landmarks[1].y * h])
            p61 = np.array([landmarks[61].x * w, landmarks[61].y * h])
            p291 = np.array([landmarks[291].x * w, landmarks[291].y * h])
            mouth_corners_y = (p61[1] + p291[1]) / 2.0
            nose_to_mouth_dist = (mouth_corners_y - p1[1]) / ipd
            au15_depressor = float(np.clip((nose_to_mouth_dist - 0.70) / 0.30, 0.0, 1.0))

            # 5. AU20 (Lip Stretcher): Horizontal mouth width (61 to 291) / IPD
            mouth_width = np.linalg.norm(p61 - p291) / ipd
            au20_stretcher = float(np.clip((mouth_width - 0.65) / 0.35, 0.0, 1.0))

            # 6. Head Pose via solvePnP
            image_points_2d = np.array([
                (landmarks[1].x * w, landmarks[1].y * h),     # Nose tip
                (landmarks[152].x * w, landmarks[152].y * h), # Chin
                (p33[0], p33[1]),                             # Left eye left corner
                (p263[0], p263[1]),                           # Right eye right corner
                (p61[0], p61[1]),                             # Left mouth corner
                (p291[0], p291[1])                            # Right mouth corner
            ], dtype=np.float64)

            focal_length = w
            center = (w / 2.0, h / 2.0)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype=np.float64)
            dist_coeffs = np.zeros((4, 1))

            success, rot_vec, trans_vec = cv2.solvePnP(
                self.model_points_3d, image_points_2d, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
            )

            pitch, yaw, roll = 0.0, 0.0, 0.0
            if success:
                rmat, _ = cv2.Rodrigues(rot_vec)
                angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
                pitch, yaw, roll = float(angles[0]), float(angles[1]), float(angles[2])

            latency = round((time.time() - t0) * 1000, 2)
            return {
                "face_detected": True,
                "confidence": 0.95,
                "au04_brow_furrow": round(au04_furrow, 4),
                "au07_lid_tightener": round(au07_lid_tight, 4),
                "au15_lip_depressor": round(au15_depressor, 4),
                "au20_lip_stretcher": round(au20_stretcher, 4),
                "ear": round(avg_ear, 4),
                "head_pitch": round(pitch, 2),
                "head_yaw": round(yaw, 2),
                "head_roll": round(roll, 2),
                "latency_ms": latency
            }
        except Exception as e:
            print(f"[FACIAL EXTRACTION ERROR] {e}")
            fallback_res["latency_ms"] = round((time.time() - t0) * 1000, 2)
            return fallback_res
