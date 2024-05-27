import os
import cv2
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
from parking_space_counter.util import get_parking_spots_bboxes

plt.rcParams['font.family'] = ['Microsoft JhengHei']

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, ParkingLot, spots):
        super().__init__()
        self.setWindowTitle("停車場管理系統")
        self.resize(1400, 720)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        '''self.input_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.input_layout)

        self.label = QtWidgets.QLabel("車牌號碼:")
        self.label.setStyleSheet("font-size: 16px;")
        self.input_layout.addWidget(self.label)

        self.license_input = QtWidgets.QLineEdit()
        self.license_input.setStyleSheet("font-size: 16px;")
        self.input_layout.addWidget(self.license_input)

        self.park_button = QtWidgets.QPushButton("停車")
        self.park_button.setStyleSheet("font-size: 16px;")
        self.park_button.clicked.connect(self.park_car)
        self.input_layout.addWidget(self.park_button)

        self.leave_button = QtWidgets.QPushButton("離開")
        self.leave_button.setStyleSheet("font-size: 16px;")
        self.leave_button.clicked.connect(self.leave_car)
        self.input_layout.addWidget(self.leave_button)'''

        self.query_space_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.query_space_layout)

        self.query_space_input_layout = QtWidgets.QHBoxLayout()
        self.query_space_layout.addLayout(self.query_space_input_layout)

        self.query_space_label = QtWidgets.QLabel("查詢車位號碼:")
        self.query_space_label.setStyleSheet("font-size: 16px;")
        self.query_space_input_layout.addWidget(self.query_space_label)

        self.space_input = QtWidgets.QLineEdit()
        self.space_input.setStyleSheet("font-size: 16px;")
        self.space_input.setPlaceholderText("請輸入車位號碼(1~17的整數)")
        self.query_space_input_layout.addWidget(self.space_input)

        self.query_space_button = QtWidgets.QPushButton("查詢")
        self.query_space_button.setStyleSheet("font-size: 16px;")
        self.query_space_button.clicked.connect(self.query_space)
        self.query_space_input_layout.addWidget(self.query_space_button)

        self.result_space_label = QtWidgets.QLabel("")
        self.result_space_label.setStyleSheet("font-size: 16px;")
        self.query_space_layout.addWidget(self.result_space_label)

        self.query_car_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.query_car_layout)

        self.query_car_input_layout = QtWidgets.QHBoxLayout()
        self.query_car_layout.addLayout(self.query_car_input_layout)

        self.query_car_label = QtWidgets.QLabel("查詢車牌號碼:")
        self.query_car_label.setStyleSheet("font-size: 16px;")
        self.query_car_input_layout.addWidget(self.query_car_label)

        self.car_input = QtWidgets.QLineEdit()
        self.car_input.setStyleSheet("font-size: 16px;")
        self.car_input.setPlaceholderText("請輸入您的車牌號碼(如ABC123)")
        self.query_car_input_layout.addWidget(self.car_input)

        self.query_car_button = QtWidgets.QPushButton("查詢")
        self.query_car_button.setStyleSheet("font-size: 16px;")
        self.query_car_button.clicked.connect(self.query_car)
        self.query_car_input_layout.addWidget(self.query_car_button)

        self.result_car_label = QtWidgets.QLabel("")
        self.result_car_label.setStyleSheet("font-size: 16px;")
        self.query_car_layout.addWidget(self.result_car_label)

        '''
        影片與停車格顯示，目前是以左邊放影片，右邊放停車格狀態的方式呈現
        可修改方向: 將停車格和車輛的偵測疊在一起
        '''
        self.park_analyze_layout = QtWidgets.QHBoxLayout()
        self.park_video = QMediaPlayer()
        self.park_video.setMedia(QMediaContent(QtCore.QUrl('./parking_space_counter/spot_detect_trim.avi')))
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
        
        self.car_db_file = 'carDB.txt'
        self.car_db = self.load_car_db()
        self.space_db_file = 'spaceDB.txt'
        self.space_db = self.load_space_db()
        
    def load_car_db(self):
        car_db = {}
        if os.path.exists(self.car_db_file):
            with open(self.car_db_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        license_plate = parts[0]
                        enter_time = parts[1] + ' ' + parts[2] 
                        parking_spot = parts[3]
                        car_db[license_plate] = (enter_time, parking_spot)
        return car_db
    
    def load_space_db(self):
        space_db = {}
        if os.path.exists(self.space_db_file):
            with open(self.space_db_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        parking_spot = parts[0]
                        if parts[1].lower() == 'null': 
                            license_plate = None
                        else:
                            license_plate = parts[1]
                        space_db[parking_spot] = license_plate
        return space_db

    def park_car(self, license_plate, parking_spot):
        if license_plate not in self.car_db:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.car_db[license_plate] = (current_time, parking_spot)
            with open(self.car_db_file, 'a', encoding='utf-8') as f:
                f.write(f"{license_plate} {current_time} {parking_spot}\n")
        
        if parking_spot in self.space_db:
            self.space_db[parking_spot] = license_plate
            with open(self.space_db_file, 'r+', encoding='utf-8') as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    parts = line.strip().split()
                    if parts[0] == parking_spot:
                        line = f"{parking_spot} {license_plate}\n"
                    f.write(line)
                f.truncate()
        

    def leave_car(self, license_plate, parking_spot):
        if license_plate in self.car_db:
            # Remove entry from carDB.txt
            with open(self.car_db_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open(self.car_db_file, 'w', encoding='utf-8') as f:
                for line in lines:
                    parts = line.strip().split()
                    if parts[0] != license_plate:
                        f.write(line)

            # Update spaceDB.txt to set corresponding parking spot to 'null'
            if parking_spot in self.space_db:
                self.space_db[parking_spot] = None
                with open(self.space_db_file, 'r+', encoding='utf-8') as f:
                    lines = f.readlines()
                    f.seek(0)
                    for line in lines:
                        parts = line.strip().split()
                        if parts[0] == parking_spot:
                            line = f"{parking_spot} null\n"
                        f.write(line)
                    f.truncate()

            # Remove entry from car_db dictionary
            del self.car_db[license_plate]

    def query_space(self):
        space_id = self.space_input.text().strip()
        if space_id in self.space_db:
            car_license_plate = self.space_db[space_id]
            if car_license_plate is None:
                self.result_space_label.setText(f">停車位 {space_id} 沒有車輛停放。")
            else:
                self.result_space_label.setText(f">停車位 {space_id} 的車牌號碼為 {car_license_plate}。")
        else:
            self.result_space_label.setText(f">停車位 {space_id} 不存在。")

    def query_car(self):
        license_plate = self.car_input.text().strip()
        if license_plate in self.car_db:
            enter_time_str, parking_spot = self.car_db[license_plate]
            enter_time = datetime.strptime(enter_time_str, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            stay_duration = current_time - enter_time
            hours, remainder = divmod(stay_duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            stay_time_str = f"{int(hours)} 小時 {int(minutes)} 分鐘 {int(seconds)} 秒"
            formatted_enter_time = enter_time.strftime("%Y年%m月%d日 %H時%M分%S秒")
            self.result_car_label.setText(f">車牌號碼為 {license_plate} 的車子停在 {parking_spot} 號車位，進入時間為 {formatted_enter_time}，已停留時間為 {stay_time_str}。")
        else:
            self.result_car_label.setText(f">車牌號碼為 {license_plate} 的車輛不在停車場內。")

    def draw_parking_lot(self, parked_spaces):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        """
        Parameters:
            parked_spaces: list[int] - 已停車位的編號列表
            self.park_spot - 根據二值化圖像得到的停車位座標
        """
        # Count True values in parked_spaces
        num_parked = sum(parked_spaces)
        num_total_spots = len(parked_spaces)-1
        for spot_indx, spot in enumerate(self.park_spot):
            if spot_indx==0:
                continue
            
            x, y, w, h = spot

            if parked_spaces[spot_indx]==False:
                facecolor_Status = 'r'
            else:
                facecolor_Status = 'g'

            rectangle = plt.Rectangle(
                (x, y), w, h, linewidth=1, edgecolor='b', facecolor=facecolor_Status)
            ax.add_patch(rectangle)
            ax.text(x + w/2, y + h/2,
                    str(spot_indx), ha='center', va='center')

        ax.set_xlim(0, 1350)
        ax.set_ylim(100, 700)
        ax.invert_yaxis()
        ax.set_aspect('equal', adjustable='box')
        remaining_spots_text = f'當前剩餘車位 : {num_parked} / {num_total_spots}'
        ax.set_title(remaining_spots_text)
        
        # 移除 x 和 y 軸刻度
        ax.set_xticks([])
        ax.set_yticks([])

        self.figure.tight_layout()
        return self.figure

    def update_plot(self, parked_spaces):
        updated_figure = self.draw_parking_lot(parked_spaces)
        self.canvas.figure = updated_figure
        self.canvas.draw()