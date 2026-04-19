import os
import cv2
import numpy as np
import mediapipe as mp
import joblib
from utils import crop_face

class FaceShapePredictor:
    def __init__(self, model_path="models/face_shape_model.pkl", encoder_path="models/label_encoder.pkl"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found. Run train_model.py first.")
        self.model = joblib.load(model_path)
        self.label_encoder = joblib.load(encoder_path)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)
    
    def extract_geometric_features(self, landmarks):
        left_cheek, right_cheek = 234, 454
        chin, forehead = 152, 10
        left_jaw, right_jaw = 172, 397
        
        left_cheek_point = np.array([landmarks[left_cheek].x, landmarks[left_cheek].y])
        right_cheek_point = np.array([landmarks[right_cheek].x, landmarks[right_cheek].y])
        chin_point = np.array([landmarks[chin].x, landmarks[chin].y])
        forehead_point = np.array([landmarks[forehead].x, landmarks[forehead].y])
        left_jaw_point = np.array([landmarks[left_jaw].x, landmarks[left_jaw].y])
        right_jaw_point = np.array([landmarks[right_jaw].x, landmarks[right_jaw].y])
        
        face_width = np.linalg.norm(left_cheek_point - right_cheek_point)
        face_height = np.linalg.norm(forehead_point - chin_point)
        jaw_width = np.linalg.norm(left_jaw_point - right_jaw_point)
        
        return [face_width/face_height, jaw_width/face_width, face_height/jaw_width, face_width, face_height, jaw_width]
    
    def predict_shape(self, frame):
        # Crop face for better accuracy
        face, bbox = crop_face(frame)
        if face is None:
            face = frame
        rgb = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            features = self.extract_geometric_features(landmarks)
            features_array = np.array(features).reshape(1, -1)
            pred = self.model.predict(features_array)[0]
            confidence = max(self.model.predict_proba(features_array)[0])
            face_shape = self.label_encoder.inverse_transform([pred])[0]
            return face_shape, confidence, bbox
        return None, 0, None
    
    def get_hairstyle_recommendation(self, face_shape):
        recommendations = {
            'oval': {'name': 'Textured Crop', 'description': 'Almost any hairstyle works!', 'image': 'oval_hairstyle.jpg'},
            'round': {'name': 'Pompadour', 'description': 'Add height to elongate your face.', 'image': 'round_hairstyle.jpg'},
            'square': {'name': 'Side Swept', 'description': 'Soften your jawline.', 'image': 'square_hairstyle.jpg'},
            'heart': {'name': 'Side Part', 'description': 'Balance your forehead.', 'image': 'heart_hairstyle.jpg'},
            'oblong': {'name': 'Fringe/Bangs', 'description': 'Add width with fringe.', 'image': 'oblong_hairstyle.jpg'}
        }
        return recommendations.get(face_shape, recommendations['oval'])
    
    def draw_bbox(self, frame, bbox):
        if bbox:
            (x, y, w, h) = bbox
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 105, 180), 2)
        return frame