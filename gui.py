import os
import cv2
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from parking_space_counter.util import get_parking_spots_bboxes


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ParkingLot, spots):
        super().__init__()
        self.setWindowTitle("停車場管理系統")
        self.resize(1400, 720)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.input_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.input_layout)

        self.label = QtWidgets.QLabel("車牌號碼:")
        self.input_layout.addWidget(self.label)

        self.license_input = QtWidgets.QLineEdit()
        self.input_layout.addWidget(self.license_input)

        self.park_button = QtWidgets.QPushButton("停車")
        self.park_button.clicked.connect(self.park_car)
        self.input_layout.addWidget(self.park_button)

        self.leave_button = QtWidgets.QPushButton("離開")
        self.leave_button.clicked.connect(self.leave_car)
        self.input_layout.addWidget(self.leave_button)

        self.query_space_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.query_space_layout)

        self.query_space_label = QtWidgets.QLabel("查詢車位號碼:")
        self.query_space_layout.addWidget(self.query_space_label)

        self.space_input = QtWidgets.QLineEdit()
        self.query_space_layout.addWidget(self.space_input)

        self.query_space_button = QtWidgets.QPushButton("查詢")
        self.query_space_button.clicked.connect(self.query_space)
        self.query_space_layout.addWidget(self.query_space_button)

        self.result_space_label = QtWidgets.QLabel("")
        self.query_space_layout.addWidget(self.result_space_label)

        self.query_car_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.query_car_layout)

        self.query_car_label = QtWidgets.QLabel("查詢車牌號碼:")
        self.query_car_layout.addWidget(self.query_car_label)

        self.car_input = QtWidgets.QLineEdit()
        self.query_car_layout.addWidget(self.car_input)

        self.query_car_button = QtWidgets.QPushButton("查詢")
        self.query_car_button.clicked.connect(self.query_car)
        self.query_car_layout.addWidget(self.query_car_button)

        self.result_car_label = QtWidgets.QLabel("")
        self.query_car_layout.addWidget(self.result_car_label)

        '''
        影片與停車格顯示
        '''
        self.park_analyze_layout = QtWidgets.QHBoxLayout()
        self.park_video = QMediaPlayer()
        self.park_video.setMedia(QMediaContent(QtCore.QUrl('./parking_space_counter/parking_crop.avi')))
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(640, 480)
        self.park_video.setVideoOutput(self.video_widget)
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.park_analyze_layout.addWidget(self.video_widget)
        self.park_analyze_layout.addWidget(self.canvas)
        self.layout.addLayout(self.park_analyze_layout)

        self.park_spot = spots
        self.parkingLot = ParkingLot(capacity=len(spots))
        self.query_result = None

    def park_car(self):
        license_plate = self.license_input.text()
        if license_plate:
            self.parkingLot.enterParkingLot(license_plate)
            self.parkingLot.parkCar(license_plate)
            self.update_plot()

    def leave_car(self):
        license_plate = self.license_input.text()
        if license_plate:
            self.parkingLot.leaveCar(license_plate)
            self.parkingLot.leaveParkingLot(license_plate)
            self.update_plot()

    def query_space(self):
        space_id = self.space_input.text()
        if space_id.isdigit():
            space_id = int(space_id)
            car_license_plate = self.parkingLot.getCarBySpaceId(space_id)
            if car_license_plate:
                self.result_space_label.setText(
                    f"停車位 {space_id} 的車牌號碼為 {car_license_plate}")
            else:
                self.result_space_label.setText(f"停車位 {space_id} 沒有車輛停放。")
            self.update_plot(highlight_space=space_id)

    def query_car(self):
        license_plate = self.car_input.text()
        if license_plate:
            space_id = self.parkingLot.getSpaceIdByCar(license_plate)
            if space_id:
                self.result_car_label.setText(
                    f"車牌號碼為 {license_plate} 的車子停在 {space_id} 號車位。")
            else:
                self.result_car_label.setText(
                    f"車牌號碼為 {license_plate} 的車輛不在停車場內。")
            self.update_plot(highlight_space=space_id)

    def draw_parking_lot(self, parked_spaces):
        """
        TODO: 修改繪製方法，self.park_spot是根據二值化圖像得到的停車位座標
        """

        self.park_spot = self.park_spot[1:]
        # 先根據x座標進行排序，再根據y座標進行排序
        sorted_park_spot = sorted(self.park_spot, key=lambda spot: (spot[0], spot[1]))


        # 定義左側停車格的左下角座標(x, y)，以及長和寬
        x1 = 4
        width = 4
        height = 3  # 高度相同

        # 建立畫布和軸
        fig, ax = plt.subplots()

        # 繪製9個停車格
        spaceId = []

        for i in range(9):
            y1 = i * height + 1  # 根據索引計算y座標
            # 添加停車位編號
            if (i == 0):
                spaceId.append(16 - 2*i)
            else:
                spaceId.append(17 - 2*i)
            if spaceId[i] in parked_spaces:
                facecolor_Status = 'r'
            else:
                facecolor_Status = 'g'
            rectangle = plt.Rectangle(
                (x1, y1), width, height, linewidth=1, edgecolor='b', facecolor=facecolor_Status)
            ax.add_patch(rectangle)

            plt.text(x1 + width/2, y1 + height/2,
                     str(spaceId[i]), ha='center', va='center')

        # 定義右側停車格的左下角座標(x, y)，以及長和寬
        x2 = 12
        width = 4
        height = 3  # 高度相同

        # 繪製7個停車格
        for m in range(7):
            # 添加停車位編號
            spaceId.append(14 - 2*m)
            y2 = m * height + 6  # 根據索引計算y座標
            if spaceId[m+9] in parked_spaces:
                facecolor_Status = 'r'
            else:
                facecolor_Status = 'g'
            rectangle = plt.Rectangle(
                (x2, y2), width, height, linewidth=1, edgecolor='b', facecolor=facecolor_Status)
            ax.add_patch(rectangle)
            plt.text(x2 + width/2, y2 + height/2,
                     str(spaceId[m+9]), ha='center', va='center')

        # 設置圖形的範圍
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 30)

        # 顯示圖形
        plt.gca().set_aspect('equal', adjustable='box')
        plt.show()

    def update_plot(self, highlight_space=None):
        parked_spaces = self.parkingLot.getOccupiedSpaces()
        self.figure = self.draw_parking_lot(parked_spaces, highlight_space)
        self.canvas.figure = self.figure
        self.canvas.draw()
