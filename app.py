import os
import sys
import csv
import secrets
import uuid
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from flask import Flask, render_template, Response, jsonify, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import cv2
import numpy as np

if not os.path.exists("models/face_shape_model.pkl"):
    print("\n❌ Model not found. Run: python train_model.py")
    sys.exit(1)

from predict_shape import FaceShapePredictor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-very-secret-key-change-in-production'
predictor = FaceShapePredictor()

# ---------- CSV Setup ----------
USERS_CSV = 'users.csv'
CHALLENGE_CSV = 'challenges.csv'
COMMENTS_CSV = 'comments.csv'
SHOUTBOX_CSV = 'shoutbox.csv'

for csv_file, headers in [
    (USERS_CSV, ['email', 'password_hash', 'name', 'phone', 'created_at']),
    (CHALLENGE_CSV, ['id', 'name', 'email', 'phone', 'challenge_days', 'instagram_url', 'submitted_at', 'verified', 'discount_code']),
    (COMMENTS_CSV, ['id', 'user_email', 'user_name', 'comment', 'likes', 'created_at']),
    (SHOUTBOX_CSV, ['id', 'user_email', 'user_name', 'message', 'created_at'])
]:
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

# ---------- Helper Functions ----------
def get_user(email):
    with open(USERS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['email'] == email:
                return row
    return None

def create_user(email, password, name, phone):
    password_hash = generate_password_hash(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(USERS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([email, password_hash, name, phone, created_at])

# ---------- Services ----------
SERVICES = {
    'haircut': {'name': 'Haircut', 'base_price': 500, 'description': 'Professional haircut by expert stylists'},
    'hair_color': {'name': 'Hair Color', 'base_price': 1500, 'description': 'Premium hair color (single process)'},
    'bridal_wedding': {'name': 'Bridal Wedding Package', 'base_price': 5000, 'description': 'Full bridal hair + makeup + draping'},
    'keratin': {'name': 'Keratin Treatment', 'base_price': 3999, 'description': 'Smooth frizzy hair'},
    'facial': {'name': 'Bridal Facial', 'base_price': 1499, 'description': 'Gold + Pearl facial'},
    'deep_conditioning': {'name': 'Deep Conditioning', 'base_price': 799, 'description': 'Moroccan oil treatment'}
}

# ---------- Routes ----------
@app.route('/')
def home():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', user=session)

@app.route('/hairstyle-scan')
def scan():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('scan.html')

@app.route('/services')
def services():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    return render_template('services.html', services=SERVICES)

# ---------- Authentication ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        if not all([name, email, phone, password]):
            return render_template('register.html', error='All fields required.')
        if get_user(email):
            return render_template('register.html', error='Email already registered.')
        create_user(email, password, name, phone)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = get_user(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_email'] = email
            session['user_name'] = user['name']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- Grow the Glow Challenge ----------
@app.route('/grow-the-glow')
def challenge():
    return render_template('challenge.html')

@app.route('/submit-challenge', methods=['POST'])
def submit_challenge():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        challenge_days = request.form.get('challenge_days', '4')
        instagram_url = request.form.get('instagram_url', '').strip()
        if not name or not email or not instagram_url:
            return jsonify({'success': False, 'message': 'Name, Email, and Instagram URL are required.'}), 400
        
        submission_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(CHALLENGE_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([submission_id, name, email, phone, challenge_days, instagram_url, timestamp, 'no', ''])
        return jsonify({'success': True, 'message': 'Challenge submitted! We will verify your Instagram post and email you the discount code within 24 hours.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Server error.'}), 500

ADMIN_TOKEN = "glowadmin2025"
@app.route('/admin/verify')
def admin_panel():
    token = request.args.get('token')
    if token != ADMIN_TOKEN:
        return "Unauthorized", 401
    submissions = []
    with open(CHALLENGE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            submissions.append(row)
    return render_template('admin.html', submissions=submissions)

@app.route('/admin/verify-submission', methods=['POST'])
def verify_submission():
    token = request.form.get('token')
    if token != ADMIN_TOKEN:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    submission_id = request.form.get('id')
    if not submission_id:
        return jsonify({'success': False, 'message': 'Missing ID'}), 400
    discount_code = f"GLOW{secrets.token_hex(4).upper()}"
    rows = []
    updated = False
    with open(CHALLENGE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row[0] == submission_id and row[7] == 'no':
                row[7] = 'yes'
                row[8] = discount_code
                updated = True
            rows.append(row)
    if updated:
        with open(CHALLENGE_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        return jsonify({'success': True, 'discount_code': discount_code})
    else:
        return jsonify({'success': False, 'message': 'Already verified or not found'})

# ---------- Comments & Shoutbox ----------
@app.route('/comments')
def comments_page():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    comments = []
    with open(COMMENTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        comments = list(reader)
    comments.reverse()
    messages = []
    with open(SHOUTBOX_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        messages = list(reader)
    messages.reverse()
    return render_template('comments.html', comments=comments, messages=messages, user=session)

@app.route('/api/post-comment', methods=['POST'])
def post_comment():
    if 'user_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    if not comment_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    comment_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(COMMENTS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([comment_id, session['user_email'], session['user_name'], comment_text, '0', created_at])
    return jsonify({'success': True})

@app.route('/api/like-comment', methods=['POST'])
def like_comment():
    if 'user_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    comment_id = request.get_json().get('comment_id')
    if not comment_id:
        return jsonify({'error': 'Missing comment ID'}), 400
    rows = []
    updated = False
    with open(COMMENTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if row[0] == comment_id:
                row[4] = str(int(row[4]) + 1)
                updated = True
            rows.append(row)
    if updated:
        with open(COMMENTS_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        new_likes = rows[[r[0] for r in rows].index(comment_id)][4]
        return jsonify({'success': True, 'new_likes': new_likes})
    return jsonify({'error': 'Comment not found'}), 404

@app.route('/api/post-shout', methods=['POST'])
def post_shout():
    if 'user_email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    msg_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SHOUTBOX_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([msg_id, session['user_email'], session['user_name'], message, created_at])
    return jsonify({'success': True})

# ---------- Video Feed & Face Detection ----------
camera = None
def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
    return camera

def generate_frames():
    cap = get_camera()
    while True:
        success, frame = cap.read()
        if not success:
            break
        face_shape, confidence, bbox = predictor.predict_shape(frame)
        frame = predictor.draw_bbox(frame, bbox)
        if face_shape:
            cv2.putText(frame, f"{face_shape.upper()} ({confidence:.2f})", (10,30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,105,180), 2)
        else:
            cv2.putText(frame, "No face detected", (10,30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/detect_shape', methods=['POST'])
def detect_shape():
    if 'image' not in request.files:
        return jsonify({'error': 'No image'}), 400
    file = request.files['image']
    img_bytes = file.read()
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    face_shape, confidence, bbox = predictor.predict_shape(frame)
    if face_shape:
        rec = predictor.get_hairstyle_recommendation(face_shape)
        return jsonify({
            'face_shape': face_shape,
            'confidence': float(confidence),
            'recommendation': rec
        })
    return jsonify({'error': 'No face detected'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)