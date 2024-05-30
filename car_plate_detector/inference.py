from glob import glob
import cv2
import torch
import os
import pandas as pd
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from matplotlib import pyplot as plt
import easyocr

from ultralytics import YOLO
from train import CFG, gpu_report


def extract_roi(image, bounding_box):
    """
    Crop the input image based on the provided bounding box coordinates.

    Args:
        image (numpy.ndarray): The input image.
        bounding_box (tuple): A tuple containing (x_min, y_min, x_max, y_max)
            coordinates of the bounding box.

    Returns:
        numpy.ndarray: The cropped image.
    """
    x_min, x_max, y_min, y_max = bounding_box
    cropped_image = image[y_min:y_max, x_min:x_max]
    return cropped_image


def extract_ocr(roi_img, reader):
    """
    OCR extraction from a given image.
    """
    ocr_result = reader.readtext(np.asarray(
        roi_img), allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    text_plate = ''
    if len(ocr_result) > 0:

        for item in ocr_result:
            text, conf = item[-2], item[-1]
            text = text if conf > CFG.ocr_conf else ''
            text_plate += text
    else:
        text_plate, conf = 'unreco_plate', 0

    text_plate = text_plate.lower()

    # text_plate = isValidNumberPlate(text_plate)

    return text_plate, conf


def inference_inside_roi(df_coords, img, model, device, display=False):

    bboxs = df_coords[['xmin', 'xmax', 'ymin', 'ymax']].values.astype(int)
    classes = df_coords['class'].values

    df_plate = pd.DataFrame()
    for i, bbox in enumerate(bboxs):

        vehicle_img = extract_roi(img, bbox)
        results = model.predict(vehicle_img,
                                conf=CFG.plate_conf,
                                classes=[0],
                                device=device,
                                verbose=False)
        position_frame = pd.DataFrame(results[0].cpu().numpy().boxes.data,
                                      columns=['xmin', 'ymin', 'xmax',
                                               'ymax', 'conf', 'class'])
        position_frame['class'] = position_frame['class'].replace({0: 'car_plate'})
        position_frame['plate_number'] = 'unreco_plate'

        # Filter cases with more them one plate per vehicle
        position_frame = position_frame.loc[position_frame['conf']
                                            == position_frame['conf'].max(), :]

        # adjust bbox of plate for complete image
        position_frame['xmin'] += bbox[0]
        position_frame['xmax'] += bbox[0]
        position_frame['ymin'] += bbox[2]
        position_frame['ymax'] += bbox[2]

        if len(position_frame) > 0:

            plate_bbox = position_frame[[
                'xmin', 'xmax', 'ymin', 'ymax']].values.squeeze().astype(int)
            plate_img = extract_roi(img, plate_bbox)
            text_plate, conf_ocr = extract_ocr(plate_img, reader)
            position_frame['plate_number'] = text_plate

            if display:
                display_image(plate_img, hide_axis=True, figsize=(
                    10, 10), title=f'ROI Plate | Nº: {text_plate}')

        position_frame = position_frame[[
            'xmin', 'ymin', 'xmax', 'ymax', 'conf', 'class', 'plate_number']]

        df_plate = pd.concat([df_plate, position_frame], axis=0)

    return img, df_plate

def drawBBox(df_coords, img, title = '' ,thickness=1):

    cords = df_coords[['xmin','xmax','ymin','ymax']].values.astype(int)
    classes = df_coords['class'].values

    for i,detection in enumerate(cords): 
        start_point = (detection[0], detection[-1]) # x_min, y_max
        end_point = (detection[1], detection[2]) # x_max, y_min
        class_detected = classes[i]
    
        
        if class_detected == 'car_plate':
            number_plate = df_coords['plate_number'].values[i]
            cv2.rectangle(img, start_point, end_point, (0,0,190), thickness)
            cv2.putText(img=img, text=f'{class_detected} ', 
                org= (detection[0], detection[2]-20),
                fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(0, 0, 255),thickness=2)
            cv2.putText(img=img, text=f'{number_plate}', 
                org= (detection[0]-10, detection[-1]+30),
                fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(0, 0, 255),thickness=2)
        else:
            cv2.rectangle(img, start_point, end_point, (255,0,0), thickness)
        
            cv2.putText(img=img, text=f'{class_detected}', 
                org= (detection[0], detection[2]-20),
                fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(255, 255, 0),thickness=2)
        
    return img


def display_image(image, print_info=True, hide_axis=False, figsize=(15, 15), title=None):
    fig = plt.figure(figsize=figsize)
    if isinstance(image, str):  # Check if it's a file path
        img = Image.open(image)

        plt.imshow(img)
    elif isinstance(image, np.ndarray):  # Check if it's a NumPy array
        if image.shape[-1] == 3:
            image = image[..., ::-1]  # BGR to RGB
            img = Image.fromarray(image)
            plt.imshow(img)
        else:
            img = np.copy(image)
            plt.imshow(img, cmap='gray')

    else:
        raise ValueError("Unsupported image format")

    if print_info:
        print('Type: ', type(img), '\n')
        print('Shape: ', np.array(img).shape, '\n')

    if hide_axis:
        plt.axis('off')
    if title is not None:
        plt.title(title)

    plt.show()


def run_pipeline(path, display=False):
    '''
    1. 在輸入圖像中檢測車輛。 
    2. 使用車輛檢測的 BBOX 裁剪 ROI。
    3. 從裁剪的車輛圖像中檢測車牌。
    4. 使用車牌檢測的 BBOX 裁剪 ROI。
    5. 使用 OCR 從裁剪的車牌檢測中提取車牌號碼。
    TODO: 尋找更好的OCR模型來判斷車牌號碼，目前使用easyOCR
    '''

    image = cv2.imread(path)

    # 1. Detect vehicles from a input image.
    vehicle_results = vehicle_model.predict(image,
                                            conf=CFG.vehicle_conf,
                                            classes=CFG.vehicles_class,
                                            device=test_device,
                                            verbose=False,
                                            )

    df_vehicles = pd.DataFrame(vehicle_results[0].cpu().numpy().boxes.data,
                               columns=['xmin', 'ymin', 'xmax',
                                        'ymax', 'conf', 'class'])
    df_vehicles['class'] = df_vehicles['class'].replace(dict_classes)

    # 2. Crop the ROIs with BBOX of vehicles detections.
    # 3. Detect plates from croped vehicle images.
    # 4. Crop the ROIs with BBOX of plate detections.
    # 5. Extract the plate number with OCR from croped plate detections.
    image, df_plates = inference_inside_roi(df_vehicles,
                                            image,
                                            plate_model,
                                            test_device,
                                            display=display)

    df_frame = pd.concat([df_vehicles, df_plates],
                         axis=0).reset_index(drop=True)

    # Draw results in output images
    image = drawBBox(df_frame, image, thickness=5)

    if display:
        display_image(image,
                      hide_axis=True,
                      figsize=(10, 10),
                      title='Output Image')

    return df_frame, image


plate_model = YOLO('runs/detect/'+os.listdir('runs/detect')[-1]+'/weights/best.pt')
vehicle_model = YOLO(CFG.weights)
_, test_device = gpu_report()
reader = easyocr.Reader(['en'],  gpu=True if test_device != 'cpu' else False)

plate_model.to(test_device)
vehicle_model.to(test_device)

print('\nModels Info')
print('Plate Model: ', plate_model.device,
      'Vehicle Model: ', plate_model.device)

dict_all_classes = vehicle_model.model.names
dict_classes = {}
for id_class in CFG.vehicles_class:
    dict_classes[id_class] = dict_all_classes[id_class]

# 測試結果
test_images = glob('car.png')
df_frame, out_image  = run_pipeline(path = 'car.png', display=True)

"""
df_frame: DataFrame with the following columns:
    - xmin: The minimum x-coordinate of the bounding box
    - ymin: The minimum y-coordinate of the bounding box
    - xmax: The maximum x-coordinate of the bounding box
    - ymax: The maximum y-coordinate of the bounding box
    - conf: The confidence score of the detection
    - class: The class of the detection
    - plate_number: The license plate number (if available)
"""
print(df_frame)
