# Architecture

## Computer Vision Layer

The Python code loads a YOLO checkpoint with `ultralytics.YOLO` and runs inference on OpenCV frames. Inference is implemented in two entry points:

- `src/webcam_fire_detection.py` reads from a local webcam with `cv2.VideoCapture`.
- `src/app.py` reads an ESP32-CAM MJPEG stream, decodes JPEG frames, runs YOLO inference, and stores the latest annotated frame for the Flask video feed.

## Camera / Stream Layer

`firmware/esp32_cam/cam.ino` configures an ESP32-CAM and serves an MJPEG stream at `/video_stream`. The Flask app expects this endpoint at `ESP32_CAM_BASE_URL + CAMERA_STREAM_PATH`.

## Monitoring / Control Layer

The Flask app serves `web/templates/index.html`. The dashboard displays the processed video feed from `/video_feed`, polls `/sensor`, and sends movement, servo, pump, and mode commands back to Flask. Flask forwards these commands to an ESP32 controller over HTTP.

## Data Flow

1. ESP32-CAM captures camera frames and serves MJPEG chunks.
2. Flask downloads the stream and extracts JPEG frames.
3. OpenCV decodes and resizes frames.
4. YOLO generates fire detections.
5. The app renders annotated frames and streams them to the dashboard.
6. Dashboard controls call Flask endpoints.
7. Flask forwards commands to the ESP32 controller endpoints.

## Unverified Components

The repository references ESP32 controller endpoints for movement, sensors, servo, pump, and mode handling, but the controller firmware implementing those endpoints was not present during cleanup.
