import torch
from bs4 import BeautifulSoup
import xml.etree.ElementTree as xet
from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import numpy as np
import yaml
import random
import glob
import shutil
import os
import warnings
warnings.filterwarnings("ignore")


# import easyocr


class CFG:

    # paths
    out_folder = f'input/working'
    class_name = ['car_plate']
    video_test_path = '../parking_space_counter/parking_crop.mp4'

    weights = 'yolov8s.pt'
    exp_name = 'car_plate_detection'
    img_size = (240,400)
    vehicles_class = [2, 3, 5, 7] 
    
    #Yolo train parameters
    epochs = 50
    batch_size = 16
    optimizer = 'auto' # SGD, Adam, Adamax, AdamW, NAdam, RAdam, RMSProp, auto
    lr = 1e-3
    lr_factor = 0.01 #lo*lr_f
    weight_decay = 5e-4
    dropout = 0.0
    patience = int(0.7*epochs)
    profile = False
    label_smoothing = 0.0 
    
    #models Confidance
    vehicle_conf = 0.5
    plate_conf = 0.3
    ocr_conf = 0.1
    
    seed = 42


def get_bbox(file_path):

    info = xet.parse(file_path)
    root = info.getroot()
    member_object = root.find('object')

    labels_info = member_object.find('bndbox')
    xmin = int(labels_info.find('xmin').text)
    xmax = int(labels_info.find('xmax').text)
    ymin = int(labels_info.find('ymin').text)
    ymax = int(labels_info.find('ymax').text)

    return xmin, xmax, ymin, ymax

def parse_xml_tags(data):
    """Parse xml label file, return image file name, and its coordinates as a dictionary
    """
    tags = ['filename', 'width', 'height', 'xmin', 'ymin', 'xmax', 'ymax']
    Bs_data = BeautifulSoup(data, "xml")
    d = dict()
    for t in tags:
        text = Bs_data.find(t).text
        if all(c.isdigit() for c in text):
            d[t] = int(text)
        else:
            d[t] = text
    return d


def convert_xml_txt_yolo(file_path, w_image, h_image):
    with open(file_path,  'r') as f:
        label = parse_xml_tags(f.read())
    xmin = int(label['xmin'])
    xmax = int(label['xmax'])
    ymin = int(label['ymin'])
    ymax = int(label['ymax'])
    x_center = float((xmin+((xmax-xmin)/2))/w_image)
    y_center = float((ymin+((ymax-ymin)/2))/h_image)
    width = float((xmax-xmin)/w_image)
    height = float((ymax-ymin)/h_image)
    str_out = f'0 {x_center} {y_center} {width} {height}'
    return str_out


def create_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def gpu_report():
    if torch.cuda.is_available():
        # Get the number of available GPUs
        num_gpus = torch.cuda.device_count()
        print(f"Number of available GPUs: {num_gpus}")

        if num_gpus > 1:
            train_device, test_device = 0, 1

        else:
            train_device, test_device = 0, 0

        # Get information about each GPU
        for i in range(num_gpus):
            gpu_properties = torch.cuda.get_device_properties(i)
            print(f"\nGPU {i}: {gpu_properties.name}")
            print(
                f"  Total Memory: {gpu_properties.total_memory / (1024**3):.2f} GB")
            print(
                f"  CUDA Version: {gpu_properties.major}.{gpu_properties.minor}")
    else:
        print("CUDA is not available. You can only use CPU.")
        train_device, test_device = 'cpu', 'cpu'
    print('\n')

    return train_device, test_device

def main():
    """
    Main function to train the model
    Steps:
    1. Get the paths of the xml files and images
    2. Create the train and valid folders
    3. Create the yolo labels
    4. Train the model
    """
    anoattions_path_xml = glob.glob('./input/car-plate-detection/annotations/*.xml')
    image_paths = glob.glob('./input/car-plate-detection/images/*.png')
    info = xet.parse(anoattions_path_xml[0])
    xet.dump(info)

    index = np.arange(len(anoattions_path_xml))
    np.random.shuffle(index)

    val_index = index[:50]
    # test_index = index[50:100]
    train_index = index[50:]
    # val_index = np.random.choice(index, size=50, replace=False)

    print('Train Size: ', len(train_index))
    print('Valid Size: ', len(val_index))

    #crete paths for yolo labels
    create_dir(CFG.out_folder)
    datasets = ['train','valid']
    folders = ['images','labels']
    for datset in datasets:
        path_1 = CFG.out_folder + f'/{datset}'
        create_dir(path_1)
        for folder in folders:
            path_2 = CFG.out_folder + f'/{datset}/{folder}'

            create_dir(path_2)

            print(path_2)

    for i, img_path in enumerate(image_paths):
        image = cv2.imread(img_path)
        resize_image = cv2.resize(image,CFG.img_size)
        h_image,w_image,_ = image.shape

        label_path = img_path.replace('images','annotations').replace('.png','.xml')
        label_text = convert_xml_txt_yolo(label_path,w_image,h_image)

        text_file_name = img_path.split('\\')[-1].replace('.png','.txt')
        img_file_name = img_path.split('\\')[-1]

        if i in val_index:
            dataset = 'valid'
        elif i in train_index:
            dataset = 'train'

        text_path = f'{CFG.out_folder}/' + dataset + '/labels/' + text_file_name
        new_img_path = f'{CFG.out_folder}/' + dataset +'/images/'+ img_file_name

        shutil.copy2(img_path,new_img_path)
        #cv2.imwrite(new_img_path, resize_image)


        text_file = open(text_path, "w")
        text_file.write(label_text)
        text_file.close()

    dict_file = {
        'train': os.path.join(os.getcwd(), CFG.out_folder, 'train'),
        'val': os.path.join(os.getcwd(), CFG.out_folder, 'valid'),
        'nc': len(CFG.class_name),
        'names': CFG.class_name
        }

    with open(os.path.join(CFG.out_folder, 'data.yaml'), 'w+') as file:
        yaml.dump(dict_file, file)

    with open(os.path.join(CFG.out_folder, 'data.yaml'), 'r') as file:
        data_yaml = yaml.safe_load(file)

    print(yaml.dump(data_yaml))

    plate_model = YOLO(CFG.weights)

    train_device, _ = gpu_report()
    plate_model.to(train_device)

    print('\nModel Info')
    print('Model: ', CFG.weights)
    print('Device: ', plate_model.device)

    ### train
    plate_model.train(
        data = os.path.join(CFG.out_folder, 'data.yaml'),

        task = 'detect',

        #imgsz = (img_properties['height'], img_properties['width']),

        epochs = CFG.epochs,
        batch = CFG.batch_size,
        optimizer = CFG.optimizer,
        lr0 = CFG.lr,
        lrf = CFG.lr_factor,
        weight_decay = CFG.weight_decay,
        dropout = CFG.dropout,
        patience = CFG.patience,
        label_smoothing = CFG.label_smoothing,
        imgsz = 640,#CFG.img_size,

        name = CFG.exp_name,
        seed = CFG.seed,
        profile = False,

        val = True,
        amp = False,   #mixed precision 
        exist_ok = False, #overwrite experiment
        resume = False,
        device = train_device,
        verbose = False,
        single_cls = False,
    )

if __name__ == '__main__':
    main()