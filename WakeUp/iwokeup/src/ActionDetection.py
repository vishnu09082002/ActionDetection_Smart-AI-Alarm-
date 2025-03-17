'''from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import cv2
import mediapipe as mp
import math
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})  # Allow requests from localhost:3000

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Global variables to track pushup progress
pushup_count = 0
pushup_in_progress = False
target_count = 0
detection_running = False
completed = False

# Angle calculation function
def calculate_angle(a, b, c):
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

# Function to label pushups based on elbow angle
def label_pushup(angle):
    return 1 if angle < 90 else 0

# Pushup detection function
def detect_pushups():
    global pushup_count, pushup_in_progress, detection_running, completed
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access the camera.")
        return

    print(f"Starting pushup detection for {target_count} pushups...")
    while detection_running and pushup_count < target_count:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb_frame)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks.landmark
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]

            angle = calculate_angle(shoulder, elbow, wrist)
            pushup_label = label_pushup(angle)

            if pushup_label == 1 and not pushup_in_progress:
                pushup_in_progress = True
            if pushup_label == 0 and pushup_in_progress:
                pushup_count += 1
                pushup_in_progress = False
                print(f"Pushup count: {pushup_count}/{target_count}")

            mp_drawing.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.putText(frame, f'Pushups: {pushup_count}/{target_count}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Pushup Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    detection_running = False
    completed = True
    print(f"Pushup detection completed: {pushup_count} pushups detected.")

# Start detection endpoint
@app.route('/start-detection', methods=['POST'])
def start_detection():
    global pushup_count, target_count, detection_running, completed
    data = request.get_json()
    exercise = data.get('exercise')
    target_count = data.get('count')

    if exercise != "Pushups":
        return jsonify({"error": "Only Pushups are supported currently"}), 400

    # Reset variables
    pushup_count = 0
    detection_running = True
    completed = False

    # Start detection in a separate thread
    threading.Thread(target=detect_pushups, daemon=True).start()
    return jsonify({"message": "Pushup detection started", "target": target_count})

# Check pushup status endpoint
@app.route('/check-pushup-status', methods=['GET'])
def check_pushup_status():
    global pushup_count, target_count, completed
    return jsonify({
        "current_count": pushup_count,
        "target_count": target_count,
        "completed": completed
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    '''
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import cv2
import mediapipe as mp
import math
import threading

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

pushup_count = 0
pushup_in_progress = False
target_count = 0
detection_running = False
completed = False
cap = None

def calculate_angle(a, b, c):
    radians = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / math.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

def label_pushup(angle):
    return 1 if angle < 90 else 0

def generate_video_feed():
    global pushup_count, pushup_in_progress, detection_running, completed, cap
    print("Starting video feed generation...")
    while detection_running:
        if not cap or not cap.isOpened():
            print("Camera not initialized in video feed!")
            break
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb_frame)

        if result.pose_landmarks:
            landmarks = result.pose_landmarks.landmark
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y]

            angle = calculate_angle(shoulder, elbow, wrist)
            pushup_label = label_pushup(angle)

            if pushup_label == 1 and not pushup_in_progress:
                pushup_in_progress = True
            if pushup_label == 0 and pushup_in_progress:
                pushup_count += 1
                pushup_in_progress = False
                print(f"Pushup count: {pushup_count}/{target_count}")

            if pushup_count >= target_count:
                detection_running = False
                completed = True

            mp_drawing.draw_landmarks(frame, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.putText(frame, f'Pushups: {pushup_count}/{target_count}', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    print(f"Pushup detection completed: {pushup_count} pushups detected.")

@app.route('/start-detection', methods=['POST'])
def start_detection():
    global pushup_count, target_count, detection_running, completed, cap
    data = request.get_json()
    exercise = data.get('exercise')
    target_count = data.get('count')

    if exercise != "Pushups":
        return jsonify({"error": "Only Pushups are supported currently"}), 400

    pushup_count = 0
    detection_running = True
    completed = False

    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return jsonify({"error": "Could not access the camera"}), 500

    print(f"Detection started with target: {target_count}")
    return jsonify({"message": "Pushup detection started", "target": target_count})

@app.route('/video-feed')
def video_feed():
    if detection_running:
        return Response(generate_video_feed(), mimetype='multipart/x-mixed-replace; boundary=frame')
    print("Video feed requested but detection not running!")
    return jsonify({"error": "Detection not running"}), 400

@app.route('/check-pushup-status', methods=['GET'])
def check_pushup_status():
    global pushup_count, target_count, completed
    return jsonify({
        "current_count": pushup_count,
        "target_count": target_count,
        "completed": completed
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    