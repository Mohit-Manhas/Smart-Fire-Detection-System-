"""Run YOLO fire detection on a local webcam."""

from __future__ import annotations

import argparse

import cv2
from ultralytics import YOLO

from config import CONFIDENCE_THRESHOLD, model_path


def run_webcam(camera_index: int = 0) -> None:
    model_file = model_path()
    if not model_file.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found at {model_file}. Set MODEL_PATH or place fire.pt in models/."
        )

    model = YOLO(str(model_file))
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open camera index {camera_index}.")

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
            annotated_frame = results[0].plot()
            cv2.imshow("Fire Detection", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fire detection on a webcam.")
    parser.add_argument("--camera-index", type=int, default=0, help="OpenCV camera index.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_webcam(args.camera_index)
