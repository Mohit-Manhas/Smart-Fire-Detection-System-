from flask import Flask, render_template, request, jsonify, Response
import requests
import cv2
import numpy as np
import threading
import time
import torch
from ultralytics import YOLO

cv2.setNumThreads(0)  # Avoid OpenCV threading conflicts

app = Flask(__name__)

ESP32_IP = "http://192.168.4.1"      # ESP32-WROOM IP
ESP32_CAM_IP = "http://192.168.4.3"  # ESP32-CAM IP (must stream MJPEG)

# Load YOLO model (ensure it's CUDA-accelerated if available)
model = YOLO(r"C:\Users\Acer\OneDrive\Desktop\Capstone Project\fire_bot_flask\fire.pt")
print("CUDA Available:", torch.cuda.is_available())

latest_frame = None  # Global frame variable for streaming

# === Helper: Send Commands to ESP32 ===
def send_command(endpoint, params=None):
    try:
        url = f"{ESP32_IP}/{endpoint}"
        response = requests.get(url, params=params) if params else requests.get(url)
        return response.text if response.status_code == 200 else f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        print(f"ESP32 communication error: {e}")
        return f"Error: {e}"

# === Background thread: Stream + YOLO inference ===
def process_stream():
    global latest_frame
    stream_url = f"{ESP32_CAM_IP}/video_stream"

    try:
        r = requests.get(stream_url, stream=True, timeout=5)
        if r.status_code != 200:
            print("Failed to connect to ESP32-CAM stream")
            return

        byte_buffer = b""

        for chunk in r.iter_content(chunk_size=1024):
            byte_buffer += chunk
            a = byte_buffer.find(b'\xff\xd8')
            b = byte_buffer.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = byte_buffer[a:b+2]
                byte_buffer = byte_buffer[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                resized = cv2.resize(frame, (640, 480))  # Higher resolution

                results = model(resized, verbose=False)
                annotated = results[0].plot()

                _, buffer = cv2.imencode('.jpg', annotated)
                latest_frame = buffer.tobytes()

                time.sleep(0.01)  # Optional: frame throttle

    except Exception as e:
        print(f"Stream processing error: {e}")
        latest_frame = None

# Start stream thread
threading.Thread(target=process_stream, daemon=True).start()

# === Flask Routes ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/move', methods=['GET'])
def move():
    direction = request.args.get('direction')
    return jsonify({'status': send_command('move', {'dir': direction}) if direction else 'No direction provided'})

@app.route('/servo', methods=['GET'])
def servo():
    axis = request.args.get('axis')
    value = request.args.get('value', type=int)
    return jsonify({'status': send_command('servo', {'axis': axis, 'val': value}) if axis and value is not None else 'Missing axis or value'})

@app.route('/pump', methods=['GET'])
def pump():
    state = request.args.get('state')
    return jsonify({'status': send_command('pump', {'state': state}) if state else 'No state provided'})

@app.route('/mode', methods=['GET'])
def mode():
    mode = request.args.get('value')
    return jsonify({'status': send_command('mode', {'value': mode}) if mode else 'No mode value provided'})

@app.route('/sensor')
def sensor():
    try:
        response = requests.get(f"{ESP32_IP}/sensor_data")
        data = response.json() if response.status_code == 200 else {}
        return jsonify({
            "temp": data.get("temperature", "Error"),
            "humidity": data.get("humidity", "Error"),
            "fireDetected": data.get("fireDetected", False)
        })
    except Exception as e:
        print(f"Sensor fetch error: {e}")
        return jsonify({"temp": "Error", "humidity": "Error", "fireDetected": False})

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            if latest_frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
            else:
                time.sleep(0.01)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# === Run Server ===
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
