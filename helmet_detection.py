
from pathlib import Path

import cv2
import torch
from numpy import random


from models.experimental import attempt_load
from utils.datasets import LoadImages
from utils.general import (
    check_img_size,
    non_max_suppression,
    scale_coords,
    set_logging,
)
from utils.plots import plot_one_box
from utils.torch_utils import select_device


BASE_DIR = Path(__file__).resolve().parent

DEFAULT_WEIGHTS = (
    BASE_DIR
    / "runs"
    / "train"
    / "finalModel"
    / "weights"
    / "best.pt"
)


def detect_helmet(image_path, output_path):
    """Detect objects in an image and save the annotated result."""

    image_path = Path(image_path)
    output_path = Path(output_path)

    if not image_path.is_file():
        raise FileNotFoundError(
            f"Input image not found: {image_path}"
        )

    if not DEFAULT_WEIGHTS.is_file():
        raise FileNotFoundError(
            f"Model weights not found: {DEFAULT_WEIGHTS}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    set_logging()
    device = select_device("cpu")

    model = attempt_load(
        str(DEFAULT_WEIGHTS),
        map_location=device
    )
    model.eval()

    stride = int(model.stride.max())
    image_size = check_img_size(448, s=stride)

    names = (
        model.module.names
        if hasattr(model, "module")
        else model.names
    )

    colors = [
        [random.randint(0, 255) for _ in range(3)]
        for _ in names
    ]

    dataset = LoadImages(
        str(image_path),
        img_size=image_size,
        stride=stride
    )

    detections = []
    rider_count = 0
    helmet_count = 0
    no_helmet_count = 0
    plate_count = 0
    processed_image = None

    for path, image, original, video_capture in dataset:
        processed_image = original.copy()

        tensor = torch.from_numpy(image).to(device).float()
        tensor /= 255.0

        if tensor.ndimension() == 3:
            tensor = tensor.unsqueeze(0)

        with torch.no_grad():
            prediction = model(tensor)[0]

        prediction = non_max_suppression(
            prediction,
            conf_thres=0.25,
            iou_thres=0.45
        )

        for det in prediction:
            if not len(det):
                continue

            det[:, :4] = scale_coords(
                tensor.shape[2:],
                det[:, :4],
                processed_image.shape
            ).round()

            for *xyxy, confidence, cls in det:
                class_id = int(cls)
                class_name = str(names[class_id])
                score = float(confidence)

                detections.append({
                    "class": class_name,
                    "confidence": round(score, 3)
                })

                if class_name == "Rider":
                    rider_count += 1
                elif class_name == "Helmet":
                    helmet_count += 1
                elif class_name == "No Helmet":
                    no_helmet_count += 1
                elif class_name == "LP":
                    plate_count += 1

                label = f"{class_name} {score:.2f}"

                plot_one_box(
                    xyxy,
                    processed_image,
                    label=label,
                    color=colors[class_id],
                    line_thickness=2
                )

    if processed_image is None:
        raise RuntimeError("No image was processed.")

    saved = cv2.imwrite(
        str(output_path),
        processed_image
    )

    if not saved:
        raise RuntimeError("Could not save the result image.")

    if no_helmet_count > 0:
        helmet_status = "No Helmet detected"
    elif helmet_count > 0:
        helmet_status = "Helmet detected"
    else:
        helmet_status = "Helmet status not detected"

    return {
        "output_image": str(output_path),
        "rider_count": rider_count,
        "helmet_count": helmet_count,
        "no_helmet_count": no_helmet_count,
        "plate_count": plate_count,
        "helmet_status": helmet_status,
        "detections": detections
    }