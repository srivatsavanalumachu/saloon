import os
import cv2
import numpy as np
import mediapipe as mp
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
from sklearn.preprocessing import LabelEncoder

# Suppress MediaPipe warnings
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("Starting face shape classifier training (RandomForest)...")

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5)

def extract_geometric_features(landmarks):
    """Extract 6 geometric features from face landmarks."""
    # Key landmark indices
    left_cheek = 234
    right_cheek = 454
    chin = 152
    forehead = 10
    left_jaw = 172
    right_jaw = 397
    
    left_cheek_point = np.array([landmarks[left_cheek].x, landmarks[left_cheek].y])
    right_cheek_point = np.array([landmarks[right_cheek].x, landmarks[right_cheek].y])
    chin_point = np.array([landmarks[chin].x, landmarks[chin].y])
    forehead_point = np.array([landmarks[forehead].x, landmarks[forehead].y])
    left_jaw_point = np.array([landmarks[left_jaw].x, landmarks[left_jaw].y])
    right_jaw_point = np.array([landmarks[right_jaw].x, landmarks[right_jaw].y])
    
    face_width = np.linalg.norm(left_cheek_point - right_cheek_point)
    face_height = np.linalg.norm(forehead_point - chin_point)
    jaw_width = np.linalg.norm(left_jaw_point - right_jaw_point)
    
    features = [
        face_width / face_height,      # width-to-height ratio
        jaw_width / face_width,        # jaw-to-cheek ratio
        face_height / jaw_width,       # height-to-jaw ratio
        face_width,                    # absolute width
        face_height,                   # absolute height
        jaw_width                      # absolute jaw width
    ]
    return features

def process_dataset(dataset_path):
    """Loop through dataset folders and extract features."""
    features = []
    labels = []
    shape_categories = ['heart', 'oval', 'round', 'square', 'oblong']
    
    for shape in shape_categories:
        shape_path = os.path.join(dataset_path, shape)
        if not os.path.exists(shape_path):
            print(f"Warning: {shape_path} not found, skipping.")
            continue
        for img_file in os.listdir(shape_path):
            if img_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(shape_path, img_file)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(img_rgb)
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0].landmark
                    feat = extract_geometric_features(landmarks)
                    features.append(feat)
                    labels.append(shape)
                    print(f"Processed {img_file} -> {shape}")
    return np.array(features), np.array(labels)

def train_model():
    dataset_path = "dataset"
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset folder '{dataset_path}' not found!")
        return
    
    X, y = process_dataset(dataset_path)
    if len(X) == 0:
        print("No valid images found. Check dataset structure.")
        return
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {acc:.2f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/face_shape_model.pkl")
    joblib.dump(label_encoder, "models/label_encoder.pkl")
    print("\n✅ Model saved to 'models/face_shape_model.pkl'")

if __name__ == "__main__":
    train_model()