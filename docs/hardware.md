# Hardware Notes

This document describes only hardware that is directly supported or referenced by the repository code.

## Confirmed Firmware

### ESP32-CAM

`firmware/esp32_cam/cam.ino` initializes the ESP32-CAM, connects to Wi-Fi, and starts an HTTP MJPEG stream at `/video_stream`.

The sketch uses the common AI Thinker ESP32-CAM pin mapping:

- PWDN: 32
- XCLK: 0
- SIOD: 26
- SIOC: 27
- Y9-Y2: 35, 34, 39, 36, 21, 19, 18, 5
- VSYNC: 25
- HREF: 23
- PCLK: 22

## Referenced Controller API

The Flask app expects a separate ESP32/controller at `ESP32_BASE_URL` with these HTTP endpoints:

- `/move?dir=forward|back|left|right|stop`
- `/servo?axis=pan|tilt&val=0..180`
- `/pump?state=on|off`
- `/mode?value=manual|auto`
- `/sensor_data`

`/sensor_data` is expected to return JSON with `temperature`, `humidity`, and `fireDetected` fields.

## Not Present

The repository does not currently include the firmware for the separate ESP32 controller that handles movement, sensors, pump, or servo control. Treat those endpoints as an integration contract inferred from the Flask code, not as verified firmware in this repository.
