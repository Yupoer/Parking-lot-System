import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

from .util import get_parking_spots_bboxes, getCarList


def calc_diff(im1, im2):
    return np.abs(np.mean(im1) - np.mean(im2))


def init():
    """
    初始化停車位擷取參數
    """
    cwd = os.getcwd()
    mask = os.path.join(cwd, 'parking_space_counter', 'parking_crop.png')
    video_path = os.path.join(
        cwd, 'parking_space_counter', 'parking_crop.mp4')

    mask = cv2.imread(mask, 0)

    cap = cv2.VideoCapture(video_path)

    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

    connected_components = cv2.connectedComponentsWithStats(
        mask, 8, cv2.CV_32S)

    # with open('connected_components.txt', 'w') as f:
    #     f.write(str(connected_components))

    spots = get_parking_spots_bboxes(connected_components)

    print("spots:", spots)

    return spots, cap


def getSpace(spots, cap):
    """
    取得停車位的狀態
    1. 使用YOLOv8進行車輛檢測
    2. 使用pointPolygonTest函數判斷車輛BBOX是否在停車位內
    3. 顯示停車位的狀態
    """
    spots_status = [None for j in spots]
    diffs = [None for j in spots]

    previous_frame = None

    frame_nmr = 0
    ret = True
    step = 30

    while ret:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_nmr % step == 0 and previous_frame is not None:
            for spot_indx, spot in enumerate(spots):
                x1, y1, w, h = spot

                spot_crop = frame[y1:y1 + h, x1:x1 + w, :]

                diffs[spot_indx] = calc_diff(
                    spot_crop, previous_frame[y1:y1 + h, x1:x1 + w, :])

            print([diffs[j] for j in np.argsort(diffs)][::-1])

        if frame_nmr % step == 0:
            if previous_frame is None:
                arr_ = range(len(spots))
            else:
                arr_ = [j for j in np.argsort(
                    diffs) if diffs[j] / np.amax(diffs) > 0.4]
            
            """
            Steps:
            1. 取得該frame裡面所有車輛的BBOX
            2. 根據pointPolygonTest函數判斷車輛BBOX是否在停車位內
            3. 在spots_status中儲存該停車位的狀態
            TODO: 將spots_status傳回給GUI
            """
            carList = getCarList(frame)
            for spot_indx in arr_:
                spot = spots[spot_indx]
                x1, y1, w, h = spot
                area = [(x1, y1), (x1 + w, y1), (x1 + w, y1 + h), (x1, y1 + h)]
                spot_crop = frame[y1:y1 + h, x1:x1 + w, :]
                spot_status = True
                for cars in carList:
                    x2, y2 = cars
                    if cv2.pointPolygonTest(np.array(area), ((x2, y2)), False) >= 1.0:
                        spot_status = False
                        break

                spots_status[spot_indx] = spot_status

        if frame_nmr % step == 0:
            previous_frame = frame.copy()

        for spot_indx, spot in enumerate(spots):
            spot_status = spots_status[spot_indx]
            x1, y1, w, h = spots[spot_indx]

            if spot_status:
                frame = cv2.rectangle(
                    frame, (x1, y1), (x1 + w, y1 + h), (0, 255, 0), 2)
            else:
                frame = cv2.rectangle(
                    frame, (x1, y1), (x1 + w, y1 + h), (0, 0, 255), 2)

        cv2.rectangle(frame, (80, 20), (550, 80), (0, 0, 0), -1)
        cv2.putText(frame, 'Available spots: {} / {}'.format(str(sum(spots_status)), str(len(spots_status))), (100, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
        cv2.imshow('frame', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

        frame_nmr += 1

    cap.release()
    cv2.destroyAllWindows()