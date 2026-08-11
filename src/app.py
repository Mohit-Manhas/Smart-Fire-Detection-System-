"""Flask monitoring and control interface for the fire detection prototype."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import cv2
import numpy as np
import requests
import torch
from flask import Flask, Response, jsonify, render_template, request
from ultralytics import YOLO

from config import (
    CAMERA_STREAM_PATH,
    CONFIDENCE_THRESHOLD,
    ESP32_BASE_URL,
    ESP32_CAM_BASE_URL,
    model_path,
)


cv2.setNumThreads(0)

app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / "web" / "templates"))
latest_frame: bytes | None = None


def load_model() -> YOLO:
    model_file = model_path()
    if not model_file.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found at {model_file}. Set MODEL_PATH or place fire.pt in models/."
        )
    print("CUDA Available:", torch.cuda.is_available())
    return YOLO(str(model_file))


model = load_model()


def send_command(endpoint: str, params: dict[str, object] | None = None) -> str:
    try:
        response = requests.get(f"{ESP32_BASE_URL}/{endpoint}", params=params, timeout=5)
        if response.status_code == 200:
            return response.text
        return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as exc:
        print(f"ESP32 communication error: {exc}")
        return f"Error: {exc}"


def process_stream() -> None:
    global latest_frame
    stream_url = f"{ESP32_CAM_BASE_URL}{CAMERA_STREAM_PATH}"

    try:
        response = requests.get(stream_url, stream=True, timeout=5)
        if response.status_code != 200:
            print("Failed to connect to ESP32-CAM stream")
            return

        byte_buffer = b""
        for chunk in response.iter_content(chunk_size=1024):
            byte_buffer += chunk
            start = byte_buffer.find(b"\xff\xd8")
            end = byte_buffer.find(b"\xff\xd9")
            if start == -1 or end == -1:
                continue

            jpg = byte_buffer[start : end + 2]
            byte_buffer = byte_buffer[end + 2 :]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue

            resized = cv2.resize(frame, (640, 480))
            results = model(resized, conf=CONFIDENCE_THRESHOLD, verbose=False)
            annotated = results[0].plot()

            ok, buffer = cv2.imencode(".jpg", annotated)
            if ok:
                latest_frame = buffer.tobytes()

            time.sleep(0.01)
    except Exception as exc:
        print(f"Stream processing error: {exc}")
        latest_frame = None


@app.route("/")
def index() -> str:
    return render_template("index.html")


@app.route("/move")
def move() -> Response:
    direction = request.args.get("direction")
    status = send_command("move", {"dir": direction}) if direction else "No direction provided"
    return jsonify({"status": status})


@app.route("/servo")
def servo() -> Response:
    axis = request.args.get("axis")
    value = request.args.get("value", type=int)
    status = send_command("servo", {"axis": axis, "val": value}) if axis and value is not None else "Missing axis or value"
    return jsonify({"status": status})


@app.route("/pump")
def pump() -> Response:
    state = request.args.get("state")
    status = send_command("pump", {"state": state}) if state else "No state provided"
    return jsonify({"status": status})


@app.route("/mode")
def mode() -> Response:
    mode_value = request.args.get("value")
    status = send_command("mode", {"value": mode_value}) if mode_value else "No mode value provided"
    return jsonify({"status": status})


@app.route("/sensor")
def sensor() -> Response:
    try:
        response = requests.get(f"{ESP32_BASE_URL}/sensor_data", timeout=5)
        data = response.json() if response.status_code == 200 else {}
        return jsonify(
            {
                "temp": data.get("temperature", "Error"),
                "humidity": data.get("humidity", "Error"),
                "fireDetected": data.get("fireDetected", False),
            }
        )
    except Exception as exc:
        print(f"Sensor fetch error: {exc}")
        return jsonify({"temp": "Error", "humidity": "Error", "fireDetected": False})


@app.route("/video_feed")
def video_feed() -> Response:
    def generate():
        while True:
            if latest_frame:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + latest_frame + b"\r\n"
            else:
                time.sleep(0.01)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


def start_background_stream() -> None:
    threading.Thread(target=process_stream, daemon=True).start()


if __name__ == "__main__":
    start_background_stream()
    app.run(debug=True, host="0.0.0.0", port=5000)
