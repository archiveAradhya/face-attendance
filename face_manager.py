import cv2
import os
import numpy as np
import threading
import time
from datetime import datetime
from PIL import Image
import pickle

class FaceManager:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Training data
        self.face_images = []
        self.face_labels = []
        self.label_names = {}
        self.name_to_label = {}
        
        # Configuration
        self.face_detection_confidence = 0.8
        self.recognition_threshold = 80  # LBPH threshold (lower = more strict)
        self.min_face_size = (100, 100)  # Minimum face size for detection
        self.max_face_size = (400, 400)  # Maximum face size for detection
        
        # Camera and detection state
        self.camera_active = False
        self.camera_thread = None
        self.frame_callback = None
        self.unknown_faces_detected = []
        self.last_detection_time = {}
        
        # Load known faces on initialization
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all known faces from the database and known_faces directory"""
        self.face_images = []
        self.face_labels = []
        self.label_names = {}
        self.name_to_label = {}
        
        known_faces_dir = "known_faces"
        if not os.path.exists(known_faces_dir):
            os.makedirs(known_faces_dir)
            return
        
        # Get face images from database
        users = self.database_manager.get_all_users()
        
        current_label = 0
        for user in users:
            user_id, name, employee_id, department, face_image_path, _, _ = user
            
            if face_image_path and os.path.exists(face_image_path):
                try:
                    # Load face image and detect face
                    face_image = self._load_and_preprocess_image(face_image_path)
                    if face_image is not None:
                        self.face_images.append(face_image)
                        self.face_labels.append(current_label)
                        self.label_names[current_label] = name
                        self.name_to_label[name] = current_label
                        current_label += 1
                        
                        # Also check for legacy images in known_faces folder
                        self._load_legacy_faces(name, current_label - 1)
                except Exception as e:
                    print(f"Error loading face image for {name}: {e}")
            elif os.path.exists(known_faces_dir):
                # Check for legacy face images in known_faces folder
                for filename in os.listdir(known_faces_dir):
                    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                        face_name = os.path.splitext(filename)[0]
                        if face_name.lower() == name.lower():
                            face_path = os.path.join(known_faces_dir, filename)
                            try:
                                face_image = self._load_and_preprocess_image(face_path)
                                if face_image is not None:
                                    self.face_images.append(face_image)
                                    self.face_labels.append(current_label)
                                    self.label_names[current_label] = name
                                    self.name_to_label[name] = current_label
                                    
                                    # Update database with face image path
                                    self.database_manager.update_user(user_id, face_image_path=face_path)
                                    current_label += 1
                            except Exception as e:
                                print(f"Error loading legacy face image {filename}: {e}")
        
        # Train the recognizer if we have faces
        if len(self.face_images) > 0:
            self.face_recognizer.train(self.face_images, np.array(self.face_labels))
            print(f"Trained recognizer with {len(self.face_images)} faces")
        else:
            print("No face images found for training")
    
    def _load_and_preprocess_image(self, image_path):
        """Load and preprocess image for face recognition"""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect face
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=self.min_face_size,
                maxSize=self.max_face_size
            )
            
            if len(faces) > 0:
                # Use the largest face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face
                
                # Extract face region
                face_roi = gray[y:y+h, x:x+w]
                
                # Resize to standard size (100x100)
                face_roi = cv2.resize(face_roi, (100, 100))
                
                return face_roi
            else:
                return None
                
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None
    
    def _load_legacy_faces(self, name, label):
        """Load legacy face images from known_faces folder"""
        known_faces_dir = "known_faces"
        if not os.path.exists(known_faces_dir):
            return
        
        for filename in os.listdir(known_faces_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                face_name = os.path.splitext(filename)[0]
                if face_name.lower() == name.lower():
                    face_path = os.path.join(known_faces_dir, filename)
                    try:
                        face_image = self._load_and_preprocess_image(face_path)
                        if face_image is not None:
                            self.face_images.append(face_image)
                            self.face_labels.append(label)
                    except Exception as e:
                        print(f"Error loading legacy face {filename}: {e}")
    
    def set_face_detection_confidence(self, confidence):
        """Set face detection confidence threshold"""
        self.face_detection_confidence = max(0.1, min(1.0, confidence))
    
    def set_recognition_threshold(self, threshold):
        """Set LBPH recognition threshold (lower = more strict)"""
        self.recognition_threshold = max(0, min(200, threshold))
        self.face_recognizer.setThreshold(self.recognition_threshold)
    
    def start_camera(self, camera_index=0):
        """Start camera capture in a separate thread"""
        if self.camera_active:
            return False
        
        self.camera_active = True
        self.camera_thread = threading.Thread(target=self._capture_camera_frames, args=(camera_index,))
        self.camera_thread.daemon = True
        self.camera_thread.start()
        return True
    
    def stop_camera(self):
        """Stop camera capture"""
        self.camera_active = False
        if self.camera_thread:
            self.camera_thread.join(timeout=2)
    
    def _capture_camera_frames(self, camera_index):
        """Capture camera frames and process them"""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            self.camera_active = False
            return
        
        # Set camera properties for better quality
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        while self.camera_active:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Process the frame for face detection
            processed_frame, detected_faces = self._process_frame(frame)
            
            # Call callback with results
            if self.frame_callback:
                self.frame_callback(processed_frame, detected_faces)
            
            # Control frame rate
            time.sleep(0.03)  # ~30 FPS
        
        cap.release()
    
    def _process_frame(self, frame):
        """Process a single frame for face detection and recognition"""
        # Create a copy of the frame to draw on
        processed_frame = frame.copy()
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=self.min_face_size,
            maxSize=self.max_face_size
        )
        
        detected_faces = []
        
        # Process each detected face
        for (x, y, w, h) in faces:
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size for recognition
            face_roi_resized = cv2.resize(face_roi, (100, 100))
            
            # Recognize face
            name = "Unknown"
            confidence = 0.0
            
            if len(self.face_images) > 0:
                try:
                    # Predict face
                    label, confidence = self.face_recognizer.predict(face_roi_resized)
                    
                    # Check if confidence is within threshold
                    if confidence < self.recognition_threshold:
                        name = self.label_names.get(label, "Unknown")
                        confidence = 1.0 - (confidence / 200.0)  # Convert to 0-1 scale
                    else:
                        name = "Unknown"
                        confidence = 0.0
                        
                except Exception as e:
                    print(f"Error recognizing face: {e}")
                    name = "Unknown"
                    confidence = 0.0
            
            # Store unknown face for potential registration
            if name == "Unknown":
                face_image = processed_frame[y:y+h, x:x+w]
                
                detected_faces.append({
                    'name': 'Unknown',
                    'location': (x, y, x+w, y+h),
                    'confidence': confidence,
                    'status': 'unknown',
                    'face_image': face_image,
                    'face_roi': face_roi_resized
                })
                
                # Store unknown face for potential registration
                current_time = time.time()
                if len(self.unknown_faces_detected) < 10:  # Limit storage
                    self.unknown_faces_detected.append({
                        'image': face_image,
                        'face_roi': face_roi_resized,
                        'timestamp': current_time,
                        'location': (x, y, x+w, y+h)
                    })
                
                # Clean up old unknown faces (older than 30 seconds)
                self.unknown_faces_detected = [
                    uf for uf in self.unknown_faces_detected 
                    if current_time - uf['timestamp'] < 30
                ]
            else:
                # Known face detected
                user = self.database_manager.get_user_by_name(name)
                if user:
                    user_id = user[0]
                    
                    # Mark attendance for this user (once per day)
                    current_time = time.time()
                    detection_key = f"{user_id}_{datetime.now().strftime('%Y-%m-%d')}"
                    
                    if detection_key not in self.last_detection_time or \
                       (current_time - self.last_detection_time[detection_key]) > 5:
                        self.last_detection_time[detection_key] = current_time
                        detected_faces.append({
                            'name': name,
                            'location': (x, y, x+w, y+h),
                            'confidence': confidence,
                            'status': 'known',
                            'user_id': user_id
                        })
            
            # Draw bounding box and label
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            # Draw rectangle around face
            cv2.rectangle(processed_frame, (x, y), (x+w, y+h), color, 2)
            
            # Draw background for text
            cv2.rectangle(processed_frame, (x, y-35), (x+w, y), color, -1)
            
            # Draw text
            label_text = f"{name}"
            if confidence > 0:
                label_text += f" ({confidence:.2f})"
            
            cv2.putText(processed_frame, label_text, (x+5, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return processed_frame, detected_faces
    
    def register_new_face(self, face_image, face_roi, name, employee_id, department):
        """Register a new face with the system"""
        try:
            # Save face image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.jpg"
            face_path = os.path.join("known_faces", filename)
            
            # Create known_faces directory if it doesn't exist
            os.makedirs("known_faces", exist_ok=True)
            
            # Save the face image
            cv2.imwrite(face_path, face_image)
            
            # Add user to database
            user_id = self.database_manager.add_user(name, employee_id, department, face_path)
            
            if user_id and face_roi is not None:
                # Get new label for this user
                new_label = len(self.face_images)
                
                # Add to training data
                self.face_images.append(face_roi)
                self.face_labels.append(new_label)
                self.label_names[new_label] = name
                self.name_to_label[name] = new_label
                
                # Retrain the recognizer
                self.face_recognizer.train(self.face_images, np.array(self.face_labels))
                
                return True
            
        except Exception as e:
            print(f"Error registering new face: {e}")
        
        return False
    
    def get_recent_unknown_faces(self, limit=5):
        """Get recent unknown faces for registration"""
        # Sort by timestamp (newest first)
        sorted_faces = sorted(
            self.unknown_faces_detected, 
            key=lambda x: x['timestamp'], 
            reverse=True
        )
        return sorted_faces[:limit]
    
    def clear_unknown_faces(self):
        """Clear stored unknown faces"""
        self.unknown_faces_detected = []
    
    def get_camera_devices(self):
        """Get available camera devices"""
        devices = []
        for i in range(10):  # Check first 10 devices
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append(i)
                cap.release()
        return devices
    
    def set_frame_callback(self, callback):
        """Set callback function for processed frames"""
        self.frame_callback = callback
    
    def get_statistics(self):
        """Get face recognition statistics"""
        return {
            'known_faces_count': len(self.face_images),
            'unknown_faces_count': len(self.unknown_faces_detected),
            'camera_active': self.camera_active,
            'recognition_threshold': self.recognition_threshold
        }
    
    def refresh_faces(self):
        """Reload known faces from database"""
        self.load_known_faces()
    
    def get_face_by_name(self, name):
        """Get face encoding by name"""
        if name in self.name_to_label:
            label = self.name_to_label[name]
            if label < len(self.face_images):
                return self.face_images[label]
        return None
    
    def save_recognizer(self, filepath="face_recognizer.xml"):
        """Save trained recognizer to file"""
        try:
            self.face_recognizer.save(filepath)
            return True
        except Exception as e:
            print(f"Error saving recognizer: {e}")
            return False
    
    def load_recognizer(self, filepath="face_recognizer.xml"):
        """Load trained recognizer from file"""
        try:
            if os.path.exists(filepath):
                self.face_recognizer.read(filepath)
                print(f"Loaded recognizer from {filepath}")
                return True
            return False
        except Exception as e:
            print(f"Error loading recognizer: {e}")
            return False
    
    def update_face_image(self, name, new_image_path):
        """Update face image for an existing user"""
        try:
            if name not in self.name_to_label:
                return False
            
            label = self.name_to_label[name]
            new_face_roi = self._load_and_preprocess_image(new_image_path)
            
            if new_face_roi is not None:
                # Update training data
                self.face_images[label] = new_face_roi
                
                # Retrain the recognizer
                self.face_recognizer.train(self.face_images, np.array(self.face_labels))
                
                return True
        
        except Exception as e:
            print(f"Error updating face image: {e}")
        
        return False
    
    def remove_face(self, name):
        """Remove a face from the recognition system"""
        try:
            if name not in self.name_to_label:
                return False
            
            label = self.name_to_label[name]
            
            # Remove from training data
            self.face_images.pop(label)
            self.face_labels.pop(label)
            del self.label_names[label]
            del self.name_to_label[name]
            
            # Relabel remaining faces
            new_label = 0
            new_face_images = []
            new_face_labels = []
            new_label_names = {}
            new_name_to_label = {}
            
            for i, (face_image, face_label) in enumerate(zip(self.face_images, self.face_labels)):
                if face_label < label:
                    # Keep original label
                    new_face_images.append(face_image)
                    new_face_labels.append(face_label)
                    new_label_names[face_label] = self.label_names[face_label]
                    new_name_to_label[self.label_names[face_label]] = face_label
                elif face_label > label:
                    # Decrement label
                    new_face_images.append(face_image)
                    new_face_labels.append(face_label - 1)
                    new_label_names[face_label - 1] = self.label_names[face_label]
                    new_name_to_label[self.label_names[face_label]] = face_label - 1
            
            # Update training data
            self.face_images = new_face_images
            self.face_labels = new_face_labels
            self.label_names = new_label_names
            self.name_to_label = new_name_to_label
            
            # Retrain the recognizer
            if len(self.face_images) > 0:
                self.face_recognizer.train(self.face_images, np.array(self.face_labels))
            
            return True
        
        except Exception as e:
            print(f"Error removing face: {e}")
        
        return False