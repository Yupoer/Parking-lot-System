import os
import re

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
        self.park_video = Figure(figsize=(5, 5), dpi=100)
        self.park_video_canvas = FigureCanvas(self.park_video)
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.park_analyze_layout.addWidget(self.park_video_canvas)
        self.park_analyze_layout.addWidget(self.canvas)
        self.layout.addLayout(self.park_analyze_layout)
        
        self.park_spot = spots
        self.parkingLot = ParkingLot(capacity=len(spots))
        self.query_result = None

        self.car_db_file = 'carTestFile.txt'
        #self.car_db_file = 'carDB.txt'
        self.car_db = self.load_car_db()
        #self.space_db_file = 'spaceDB.txt'
        self.space_db_file = 'spaceTestFile.txt'
        self.space_db = self.load_space_db()

    def load_car_db(self):
        car_db = {}
        # 如果車輛數據庫文件存在
        if os.path.exists(self.car_db_file):
            # 打開車輛數據庫文件以讀模式
            with open(self.car_db_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()  # 去掉行尾空白並分割為列表
                    if len(parts) >= 3:
                        # 提取車牌號碼、進場時間和停車位
                        license_plate = parts[0]
                        enter_time = parts[1] + ' ' + parts[2]
                        parking_spot = parts[3]
                        # 添加到車輛數據庫字典中
                        car_db[license_plate] = (enter_time, parking_spot)
        return car_db

    def load_space_db(self):
        space_db = {}
        # 如果空間數據庫文件存在
        if os.path.exists(self.space_db_file):
            # 打開空間數據庫文件以讀模式
            with open(self.space_db_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()  # 去掉行尾空白並分割為列表
                    if len(parts) >= 2:
                        # 提取停車位和對應的車牌號碼
                        parking_spot = parts[0]
                        if parts[1].lower() == 'null':
                            license_plate = None
                        else:
                            license_plate = parts[1]
                        # 添加到空間數據庫字典中
                        space_db[parking_spot] = license_plate
        return space_db

    def park_car(self, license_plate, parking_spot):
        try:
            # 檢查車牌號碼是否符合要求
            if len(license_plate) < 6 or len(license_plate) > 7:
                print(f"{license_plate} lens not satisfy the plate format\n")
                return

            if license_plate.isdigit() or license_plate.isalpha() or \
               not re.match("^[A-Z0-9]+$", license_plate):
                print(f"{license_plate} not satisfy the plate format\n")
                return

            # 如果車牌號碼不在車輛數據庫中
            if license_plate not in self.car_db:
                # 獲取當前時間並格式化
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # 在車輛數據庫中添加車牌號碼、時間和停車位的信息
                self.car_db[license_plate] = (current_time, parking_spot)
                # 打開車輛數據庫文件並追加新記錄
                with open(self.car_db_file, 'a', encoding='utf-8') as f:
                    f.write(f"{license_plate} {current_time} {parking_spot}\n")

            # 如果停車位在空間數據庫中
            if parking_spot in self.space_db:
                # 將停車位對應的車牌號碼更新為當前車牌號碼
                self.space_db[parking_spot] = license_plate
                # 打開空間數據庫文件以讀寫模式
                with open(self.space_db_file, 'r+', encoding='utf-8') as f:
                    lines = f.readlines()
                    f.seek(0)  # 回到文件開始位置
                    for line in lines:
                        parts = line.strip().split()
                        if parts[0] == parking_spot:
                            line = f"{parking_spot} {license_plate}\n"
                        f.write(line)
                    f.truncate()  # 截斷文件以移除多餘內容

        except Exception as e:
            # 捕獲異常並打印
            print(f"Exception occurred: {e}")

    def leave_car(self, license_plate, parking_spot):
        try:
            car_exists = license_plate in self.car_db
            spot_exists = parking_spot in self.space_db

            # 情況 1: 車牌號碼在車輛數據庫中且停車位在空間數據庫中
            if car_exists and spot_exists:
                self._remove_car_from_db(license_plate)
                self._clear_parking_spot(parking_spot)
                print(f"車牌號碼 {license_plate} 已從停車位 {parking_spot} 移除")

            # 情況 2: 車牌號碼在車輛數據庫中但停車位不在空間數據庫中
            elif car_exists and not spot_exists:
                self._remove_car_from_db(license_plate)
                print(f"車牌號碼 {license_plate} 已從車輛數據庫中移除，但停車位"
                      f" {parking_spot} 不在空間數據庫中")

            # 情況 3: 車牌號碼不在車輛數據庫中但停車位在空間數據庫中
            elif not car_exists and spot_exists:

                car_in_spot = self.space_db[parking_spot]
                self._clear_parking_spot(parking_spot)
                if car_in_spot:
                    del self.car_db[car_in_spot]
                    with open(self.car_db_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    with open(self.car_db_file, 'w', encoding='utf-8') as f:
                        for line in lines:
                            parts = line.strip().split()
                            if parts[0] != car_in_spot:
                                f.write(line)

                print(f"停車位 {parking_spot} 已清空，但車牌號碼 {license_plate}"
                      f" 不在車輛數據庫中")

            # 情況 4: 車牌號碼和停車位都不在數據庫中
            else:
                raise Exception("車輛和停車位都不在數據庫中")

        except Exception as e:
            print(f"Exception occurred: {e}")

    def _remove_car_from_db(self, license_plate):
        with open(self.car_db_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        with open(self.car_db_file, 'w', encoding='utf-8') as f:
            for line in lines:
                parts = line.strip().split()
                if parts[0] != license_plate:
                    f.write(line)
        del self.car_db[license_plate]

    def _clear_parking_spot(self, parking_spot):
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

    def update_video(self, frame):
        self.park_video.clf()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        ax = self.park_video.add_subplot(111)
        ax.imshow(frame)
        self.park_video_canvas.draw()
