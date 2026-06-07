import os
import queue
import re
import shutil
import threading
import time
from datetime import datetime

import cv2
import numpy as np


class CameraManager:
    def __init__(self, on_frame=None, on_error=None):
        self.on_frame = on_frame
        self.on_error = on_error
        self.cap = None
        self.camera_thread = None
        self.camera_running = False
        self.lock = threading.Lock()
        self.current_frame = None
        self.last_error = ""

    @property
    def running(self):
        return self.camera_running

    @property
    def thread(self):
        return self.camera_thread

    @property
    def capture(self):
        return self.cap

    def start(self):
        if self.camera_running:
            print("Camera already running")
            return True

        self.last_error = ""
        self.camera_running = True
        self.camera_thread = threading.Thread(target=self._loop, daemon=True)
        self.camera_thread.start()
        print("Camera started")
        return True

    def stop(self):
        if self.camera_running:
            print("Camera stopped by user")
        self.camera_running = False
        if (
            self.camera_thread
            and self.camera_thread.is_alive()
            and threading.current_thread() is not self.camera_thread
        ):
            self.camera_thread.join(timeout=2)
        self.camera_thread = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            print("Camera released safely")

    def get_frame(self):
        with self.lock:
            return None if self.current_frame is None else self.current_frame.copy()

    def set_frame_handler(self, handler):
        self.on_frame = handler

    def _set_error(self, message):
        self.last_error = message
        if self.on_error:
            self.on_error(message)

    def _loop(self):
        cap = cv2.VideoCapture(0)
        self.cap = cap

        if not cap.isOpened():
            print("Camera failed to open")
            self._set_error("Camera failed to open")
            self.camera_running = False
            cap.release()
            if self.cap is cap:
                self.cap = None
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        while self.camera_running:
            ok, frame = cap.read()
            if not ok:
                self._set_error("Camera 0 did not return a frame")
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)

            with self.lock:
                self.current_frame = frame.copy()

            if self.on_frame:
                self.on_frame(frame)

            time.sleep(0.015)

        cap.release()
        if self.cap is cap:
            self.cap = None
            print("Camera released safely")
        self.camera_running = False


class FaceManager:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.known_faces_dir = "known_faces"
        self.model_name = "Facenet512"
        self.distance_threshold = 0.38
        self.min_face_size = (80, 80)
        self.unknown_cooldown = 10.0
        self.unknown_clear_delay = 2.0
        self.unknown_min_face_size = (110, 110)
        self.recognition_cooldown = 1.0
        self.result_ttl = 2.8

        self.known_faces = []
        self.embedding_ready = False
        self.deepface = None
        self.deepface_error = None

        self.camera_manager = CameraManager(
            on_frame=self._handle_camera_frame,
            on_error=self._handle_camera_error,
        )
        self.is_registering = False
        self.camera_index = 0
        self.frame_callback = None

        self.frame_lock = threading.Lock()
        self.latest_raw_frame = None
        self.latest_processed_frame = None
        self.latest_faces = []

        self.result_lock = threading.Lock()
        self.latest_result = None
        self.recognition_busy = False
        self.last_submit_time = 0

        self.recognition_queue = queue.Queue(maxsize=1)
        self.worker_active = True
        self.worker_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.worker_thread.start()

        self.attendance_callback = None
        self.marked_cache = {}
        self.recognized_today_date = self._today_key()
        self.recognized_today_set = set()
        self.last_recognized = {}
        self.unknown_event_date = self.recognized_today_date
        self.recognized_event_count = 0
        self.unknown_event_count = 0
        self.last_unknown_time = 0
        self.last_face_seen_time = 0
        self.unknown_active = False
        self.last_error = ""

        self.load_known_faces()
        self._load_recognized_today_from_attendance()

    @property
    def running(self):
        return self.camera_manager.camera_running

    @property
    def camera_active(self):
        return self.camera_manager.camera_running

    def set_attendance_callback(self, callback):
        self.attendance_callback = callback

    def set_registering(self, is_registering):
        self.is_registering = bool(is_registering)
        with self.result_lock:
            self.latest_result = None

    def set_camera_index(self, camera_index):
        self.camera_index = 0
        return True

    def set_face_detection_confidence(self, confidence):
        return True

    def set_recognition_confidence(self, confidence):
        confidence = max(0.1, min(0.95, float(confidence)))
        self.distance_threshold = max(0.2, min(0.55, 0.62 - (confidence * 0.3)))
        return True

    def set_recognition_threshold(self, threshold):
        self.distance_threshold = max(0.2, min(0.55, float(threshold)))
        return True

    def load_known_faces(self):
        os.makedirs(self.known_faces_dir, exist_ok=True)
        self.known_faces = []
        self.embedding_ready = False

        users = self.database_manager.get_all_users()
        for user in users:
            user_id, name, student_id, department, face_image_path, _, _ = user
            profile_path = face_image_path

            if not profile_path:
                candidate = os.path.join(self.known_faces_dir, self._safe_person_folder(name), "profile.jpg")
                if os.path.exists(candidate):
                    profile_path = candidate
                    self.database_manager.update_user(user_id, face_image_path=profile_path)

            if profile_path and os.path.exists(profile_path):
                self.known_faces.append(
                    {
                        "user_id": user_id,
                        "name": name,
                        "student_id": student_id,
                        "department": department or "",
                        "path": profile_path,
                        "embedding": None,
                    }
                )

    def refresh_faces(self):
        self.load_known_faces()

    def start_camera(self, camera_index=None):
        self.camera_index = 0
        if self.camera_manager.camera_running:
            print("Camera already running")
            return True

        with self.frame_lock:
            self.latest_raw_frame = None
            self.latest_processed_frame = None
            self.latest_faces = []

        self.last_error = ""
        return self.camera_manager.start()

    def stop_camera(self):
        self.camera_manager.stop()
        self.unknown_active = False
        self.last_face_seen_time = 0

    def shutdown(self):
        self.stop_camera()
        self.worker_active = False
        try:
            self.recognition_queue.put_nowait(None)
        except queue.Full:
            pass
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)

    def set_frame_callback(self, callback):
        self.frame_callback = callback

    def _handle_camera_error(self, message):
        self.last_error = message

    def _handle_camera_frame(self, frame):
        with self.frame_lock:
            self.latest_raw_frame = frame.copy()

        processed_frame, faces = self._process_frame(frame)

        with self.frame_lock:
            self.latest_processed_frame = processed_frame.copy()
            self.latest_faces = faces

        callback = self.frame_callback
        if callback:
            callback(processed_frame, faces)

    def _process_frame(self, frame):
        processed = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self._detect_faces(gray)

        faces = sorted(detections, key=lambda item: item[2] * item[3], reverse=True)
        now = time.time()
        if faces:
            self.last_face_seen_time = now
        elif self.last_face_seen_time and now - self.last_face_seen_time >= self.unknown_clear_delay:
            self.unknown_active = False

        if (
            not self.is_registering
            and len(faces)
            and len(self.known_faces)
            and self._can_submit_recognition(now)
        ):
            x, y, w, h = faces[0]
            crop = self._expanded_crop(frame, x, y, w, h)
            self._submit_for_recognition(crop, now)

        result = self._fresh_result(now)
        detected_faces = []
        unknown_visible = False

        for x, y, w, h in faces:
            if self.is_registering:
                status = "checking"
                name = "Registering"
                confidence = 0.0
            elif not len(self.known_faces):
                status = "unknown"
                name = "Unknown"
                confidence = 0.0
            elif result is None:
                status = "checking"
                name = "Checking"
                confidence = 0.0
            else:
                status = result["status"]
                name = result["name"]
                confidence = result.get("confidence", 0.0)

            if status == "unknown" and self._countable_unknown_face(x, y, w, h):
                unknown_visible = True

            color = self._box_color(status)
            self._draw_face_label(processed, x, y, w, h, color, name, confidence, status)

            detected_faces.append(
                {
                    "name": name,
                    "location": (int(x), int(y), int(x + w), int(y + h)),
                    "confidence": confidence,
                    "status": status,
                    "face_image": self._expanded_crop(frame, x, y, w, h),
                    "user_id": result.get("user_id") if result and status == "known" else None,
                }
            )

        if unknown_visible:
            self._record_unknown_event(now)

        return processed, detected_faces

    def _can_submit_recognition(self, now):
        if self.is_registering:
            return False
        if self.recognition_busy:
            return False
        if now - self.last_submit_time < self.recognition_cooldown:
            return False
        return self.recognition_queue.empty()

    def _submit_for_recognition(self, face_crop, now):
        try:
            self.recognition_queue.put_nowait({"crop": face_crop.copy(), "timestamp": now})
            self.recognition_busy = True
            self.last_submit_time = now
            with self.result_lock:
                self.latest_result = {"status": "checking", "name": "Checking", "timestamp": now}
        except queue.Full:
            pass

    def _recognition_loop(self):
        while self.worker_active:
            item = self.recognition_queue.get()
            if item is None:
                break

            try:
                if self.is_registering:
                    result = {"status": "checking", "name": "Registering", "confidence": 0.0}
                else:
                    result = self._match_face(item["crop"])
            except Exception as exc:
                result = {
                    "status": "unknown",
                    "name": "Unknown",
                    "confidence": 0.0,
                    "error": str(exc),
                }
                self.last_error = str(exc)

            result["timestamp"] = time.time()
            with self.result_lock:
                self.latest_result = result
                self.recognition_busy = False

    def _fresh_result(self, now):
        with self.result_lock:
            if self.latest_result is None:
                return None
            if now - self.latest_result.get("timestamp", 0) > self.result_ttl:
                return None
            return self.latest_result.copy()

    def _detect_faces(self, gray_frame, min_size=None):
        min_size = min_size or self.min_face_size
        detections = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=min_size,
        )
        filtered = []
        for x, y, w, h in detections:
            x, y, w, h = int(x), int(y), int(w), int(h)
            if w < 80 or h < 80:
                continue
            filtered.append((x, y, w, h))
        return filtered

    def _match_face(self, face_crop):
        if not self.known_faces:
            return {"status": "unknown", "name": "Unknown", "confidence": 0.0}

        self._prepare_known_embeddings()
        candidates = [face for face in self.known_faces if face.get("embedding") is not None]
        if not candidates:
            return {"status": "unknown", "name": "Unknown", "confidence": 0.0}

        probe_embedding = self._embedding_for_image(face_crop)
        if probe_embedding is None:
            return {"status": "unknown", "name": "Unknown", "confidence": 0.0}

        best = None
        best_distance = float("inf")
        for candidate in candidates:
            distance = self._cosine_distance(probe_embedding, candidate["embedding"])
            if distance < best_distance:
                best_distance = distance
                best = candidate

        if self.is_registering:
            return {"status": "checking", "name": "Registering", "confidence": 0.0}

        if best and best_distance <= self.distance_threshold:
            confidence = max(0.0, min(1.0, 1.0 - (best_distance / self.distance_threshold)))
            self._mark_attendance(best["user_id"], best["name"])
            self._record_recognized_event(best["user_id"], best["name"])
            return {
                "status": "known",
                "name": best["name"],
                "user_id": best["user_id"],
                "confidence": confidence,
                "distance": best_distance,
            }

        return {"status": "unknown", "name": "Unknown", "confidence": 0.0, "distance": best_distance}

    def _ensure_deepface(self):
        if self.deepface is not None:
            return self.deepface
        if self.deepface_error:
            raise RuntimeError(self.deepface_error)
        try:
            cache_root = os.path.abspath(".deepface_cache")
            os.environ.setdefault("DEEPFACE_HOME", cache_root)
            os.environ.setdefault("MPLCONFIGDIR", os.path.join(cache_root, "matplotlib"))
            os.makedirs(os.environ["DEEPFACE_HOME"], exist_ok=True)
            os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

            from deepface import DeepFace

            self.deepface = DeepFace
            return self.deepface
        except Exception as exc:
            self.deepface_error = (
                "DeepFace is not available. Install dependencies with: "
                "pip install -r requirements.txt"
            )
            raise RuntimeError(self.deepface_error) from exc

    def _prepare_known_embeddings(self):
        if self.embedding_ready:
            return

        for face in self.known_faces:
            if face.get("embedding") is not None:
                continue
            try:
                face["embedding"] = self._embedding_for_image(face["path"])
            except Exception as exc:
                face["embedding"] = None
                print(f"Unable to load embedding for {face['name']}: {exc}")

        self.embedding_ready = True

    def _embedding_for_image(self, image):
        deepface = self._ensure_deepface()
        representation = deepface.represent(
            img_path=image,
            model_name=self.model_name,
            detector_backend="skip",
            enforce_detection=False,
        )

        if not representation:
            return None
        embedding = np.asarray(representation[0]["embedding"], dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return None
        return embedding / norm

    @staticmethod
    def _cosine_distance(left, right):
        return float(1.0 - np.dot(left, right))

    @staticmethod
    def _today_key():
        return datetime.now().strftime("%Y-%m-%d")

    def _reset_daily_counters_if_needed(self):
        today = self._today_key()
        if self.recognized_today_date != today:
            self.recognized_today_date = today
            self.recognized_today_set.clear()
            self.last_recognized.clear()
            self.recognized_event_count = 0
        if self.unknown_event_date != today:
            self.unknown_event_date = today
            self.unknown_event_count = 0
            self.last_unknown_time = 0

    def _load_recognized_today_from_attendance(self):
        if not hasattr(self.database_manager, "get_today_attendance"):
            return
        try:
            records = self.database_manager.get_today_attendance()
        except Exception:
            return

        self._reset_daily_counters_if_needed()
        for record in records:
            if len(record) < 6 or record[5] != "Present":
                continue
            user_id = record[1]
            self.recognized_today_set.add(user_id)
            self.marked_cache[(user_id, self.recognized_today_date)] = time.time()
        self.recognized_event_count = len(self.recognized_today_set)

    def _mark_attendance(self, user_id, name):
        today = self._today_key()
        key = (user_id, today)
        if key in self.marked_cache:
            return
        self.marked_cache[key] = time.time()

        if self.attendance_callback:
            self.attendance_callback(user_id, name)
        else:
            self.database_manager.mark_attendance(user_id, name)

    def _record_recognized_event(self, user_id, name):
        self._reset_daily_counters_if_needed()
        now = time.time()
        key = user_id if user_id is not None else name
        self.last_recognized[key] = now
        if key not in self.recognized_today_set:
            self.recognized_today_set.add(key)
            self.recognized_event_count = len(self.recognized_today_set)

    def _record_unknown_event(self, now):
        self._reset_daily_counters_if_needed()
        if self.is_registering or not self.camera_active:
            return
        if self.unknown_active:
            return
        self.unknown_active = True
        if now - self.last_unknown_time >= self.unknown_cooldown:
            self.last_unknown_time = now
            self.unknown_event_count += 1

    def _countable_unknown_face(self, _x, _y, w, h):
        min_width, min_height = self.unknown_min_face_size
        return int(w) >= min_width and int(h) >= min_height

    @staticmethod
    def _box_color(status):
        if status == "known":
            return (88, 209, 60)
        if status == "checking":
            return (10, 214, 255)
        return (58, 69, 255)

    @staticmethod
    def _draw_face_label(frame, x, y, w, h, color, name, confidence, status):
        x, y, w, h = int(x), int(y), int(w), int(h)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

        if status == "known":
            label = f"Recognized: {name}"
        elif status == "checking":
            label = "Checking..."
        else:
            label = "Unknown"

        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.72, 2)
        label_width = max(w, label_size[0] + 18)
        top = max(y - 38, 0)
        cv2.rectangle(frame, (x, top), (x + label_width, top + 34), color, -1)
        cv2.putText(
            frame,
            label,
            (x + 9, top + 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            (5, 7, 11),
            2,
            cv2.LINE_AA,
        )

    @staticmethod
    def _expanded_crop(frame, x, y, w, h, margin=0.22):
        height, width = frame.shape[:2]
        pad_x = int(w * margin)
        pad_y = int(h * margin)
        left = max(int(x) - pad_x, 0)
        top = max(int(y) - pad_y, 0)
        right = min(int(x + w) + pad_x, width)
        bottom = min(int(y + h) + pad_y, height)
        return frame[top:bottom, left:right].copy()

    def capture_registration_face(self):
        if not self.camera_manager.camera_running:
            return None, "Start the camera before capturing a face."

        frame = self.camera_manager.get_frame()
        if frame is None:
            return None, "Camera frame is not ready yet."

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._detect_faces(gray, min_size=(110, 110))

        if len(faces) == 0:
            return None, "No clear face found. Face the camera and try again."
        if len(faces) > 1:
            return None, "Only one face should be visible during registration."

        x, y, w, h = faces[0]
        face_image = self._expanded_crop(frame, x, y, w, h, margin=0.28)
        if face_image.size == 0:
            return None, "Unable to capture a usable face crop."

        return {"face_image": face_image, "frame": frame, "location": (x, y, w, h)}, "Face captured."

    def register_face(self, face_image, name, student_id, department):
        name = name.strip()
        student_id = student_id.strip()
        department = department.strip()

        if not name or not student_id or not department:
            return False, "Name, Student ID, and Department are required.", None

        if self.database_manager.get_user_by_employee_id(student_id):
            return False, "A profile with this Student ID already exists.", None

        person_folder = os.path.join(self.known_faces_dir, self._safe_person_folder(name))
        os.makedirs(person_folder, exist_ok=True)
        profile_path = os.path.join(person_folder, "profile.jpg")

        if face_image is None or face_image.size == 0:
            return False, "Capture a face photo before saving.", None

        if not cv2.imwrite(profile_path, face_image):
            return False, "Could not save the profile image.", None

        user_id = self.database_manager.add_user(name, student_id, department, profile_path)
        if not user_id:
            return False, "Could not save the user to the database.", None

        self.load_known_faces()
        return True, "Face profile saved.", profile_path

    def register_new_face(self, face_image, name, employee_id, department):
        success, _, _ = self.register_face(face_image, name, employee_id, department)
        return success

    @staticmethod
    def _safe_person_folder(name):
        cleaned = re.sub(r'[\\/:"*?<>|]+', "_", name.strip())
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or "profile"

    def get_recent_unknown_faces(self, limit=5):
        with self.frame_lock:
            faces = list(self.latest_faces)
        unknown = [face for face in faces if face.get("status") == "unknown"]
        return unknown[:limit]

    def clear_unknown_faces(self):
        self._reset_daily_counters_if_needed()
        self.unknown_event_count = 0
        self.last_unknown_time = 0
        self.last_face_seen_time = 0
        self.unknown_active = False

    def get_camera_devices(self):
        return [0]

    def get_statistics(self):
        self._reset_daily_counters_if_needed()
        return {
            "known_faces_count": len(self.known_faces),
            "registered_count": len(self.known_faces),
            "unknown_faces_count": self.unknown_event_count,
            "recognized_count": self.recognized_event_count,
            "camera_active": self.camera_active,
            "camera_running": self.camera_manager.camera_running,
            "camera_index": self.camera_index,
            "recognition_threshold": self.distance_threshold,
            "recognition_status": self._fresh_result(time.time()) or {},
            "last_error": self.last_error,
        }

    def get_face_by_name(self, name):
        for face in self.known_faces:
            if face["name"].lower() == name.lower():
                return face
        return None

    def remove_face(self, name):
        user = self.database_manager.get_user_by_name(name)
        if not user:
            return False
        return self.delete_registered_face(user[0])

    def delete_registered_face(self, user_id):
        user = self.database_manager.get_user_by_id(user_id)
        if not user:
            return False

        deleted_assets = self._delete_profile_assets(user)
        deleted = self.database_manager.delete_user(user_id)
        if not deleted:
            return False

        self.load_known_faces()
        self.embedding_ready = False
        self.recognized_today_set.discard(user_id)
        self.last_recognized.pop(user_id, None)
        self.marked_cache = {
            key: value
            for key, value in self.marked_cache.items()
            if not (isinstance(key, tuple) and key[0] == user_id)
        }
        self.recognized_event_count = len(self.recognized_today_set)
        if not deleted_assets:
            print(f"No profile assets found for deleted user {user[1]}")
        return True

    def _delete_profile_assets(self, user):
        _, name, _, _, face_image_path, _, _ = user
        known_root = os.path.abspath(self.known_faces_dir)
        deleted_any = False
        candidates = []

        if face_image_path:
            profile_path = os.path.abspath(face_image_path)
            if profile_path.startswith(known_root + os.sep):
                candidates.append(os.path.dirname(profile_path))
                if os.path.isfile(profile_path):
                    os.remove(profile_path)
                    deleted_any = True

        candidates.append(os.path.join(known_root, self._safe_person_folder(name)))

        for folder in dict.fromkeys(candidates):
            folder = os.path.abspath(folder)
            if folder == known_root or not folder.startswith(known_root + os.sep):
                continue
            if os.path.isdir(folder):
                shutil.rmtree(folder)
                deleted_any = True

        return deleted_any

    def update_face_image(self, name, new_image_path):
        user = self.database_manager.get_user_by_name(name)
        if not user or not os.path.exists(new_image_path):
            return False
        updated = self.database_manager.update_user(user[0], face_image_path=new_image_path)
        self.load_known_faces()
        return updated
