import torch
from ultralytics import YOLO
import pandas as pd
import numpy as np
import cv2


EMPTY = True
NOT_EMPTY = False

model = YOLO("yolov8m.pt")

def getCarList(frame):
    """
    使用YOLOv8進行車輛檢測
    """
    car_list = []
    results = model.predict(frame, show=False)

    if torch.cuda.is_available():
        #print("CUDA is available")
        detects = results[0].boxes.data.cpu().numpy()
    else:
        #print("CUDA is unavailable")
        detects = results[0].boxes.data.numpy()
    names = results[0].names
    px = pd.DataFrame(detects).astype("float")
    for _, row in px.iterrows():
        x1, y1, x2, y2, _, d = row.astype("int")

        if names[d] == 'car':
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            car_list.append((cx, cy))

    #print("car_list:", car_list)
    return car_list


def get_parking_spots_bboxes(connected_components):
    (totalLabels, label_ids, values, centroid) = connected_components

    slots = []
    coef = 1
    for i in range(1, totalLabels):

        # Now extract the coordinate points
        x1 = int(values[i, cv2.CC_STAT_LEFT] * coef)
        y1 = int(values[i, cv2.CC_STAT_TOP] * coef)
        w = int(values[i, cv2.CC_STAT_WIDTH] * coef)
        h = int(values[i, cv2.CC_STAT_HEIGHT] * coef)

        slots.append([x1, y1, w, h])

    slots = sorted(slots, key=lambda spots: (spots[0], spots[1]))

    return slots

