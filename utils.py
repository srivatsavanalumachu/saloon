import cv2

def crop_face(frame):
    """Detect the largest face and return cropped face + bounding box."""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        face = frame[y:y+h, x:x+w]
        return face, (x, y, w, h)
    return frame, None