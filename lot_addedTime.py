from PyQt5 import QtWidgets, QtCore
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime

class Car:
    def __init__(self, licensePlate):
        self.licensePlate = licensePlate
        self.isPark = False
        self.inpark = "has not park yet"
        self.outpark = "has not leave yet"
        self.inspace = "not in space yet"
        self.outspace = "not out space yet"

    def park(self):
        if not self.isPark:
            self.inspace = datetime.datetime.now().replace(microsecond=0)
            self.isPark = True
            print(f"{self.inspace} 車牌號碼為 {self.licensePlate} 的車輛現已停放。")
        else:
            print("此車輛已經停放。")

    def leave(self):
        if self.isPark:
            self.isPark = False
            self.outspace = datetime.datetime.now().replace(microsecond=0)
            print(f"{self.outspace} 車牌號碼為 {self.licensePlate} 的車輛已開始離開停車位。")
        else:
            print("此車輛並未停放。")

    def __str__(self):
        return f"車牌號碼: {self.licensePlate}\n entertime: {self.inpark}\n enterspace: {self.inspace}\n leavespace: {self.outspace}\n leavetime: {self.outpark}\n"

class ParkingLot:
    def __init__(self, capacity):
        self.capacity = capacity
        self.availableSpaces = capacity
        self.parkingSpaces = [ParkingSpace(spaceId) for spaceId in range(1, capacity + 1)]
        self.parkedCars = []

    def enterParkingLot(self, license):
        if self.availableSpaces > 0:
            self.availableSpaces -= 1
            now = datetime.datetime.now().replace(microsecond=0)
            tempcar = Car(license)
            tempcar.inpark = now
            self.parkedCars.append(tempcar)
            print(f"{now} 車牌號碼為 {license} 的車輛進入停車場。")
            print(f"剩餘車位數：{self.availableSpaces}\n")
        else:
            print("停車場已滿，無法進入。")

    def leaveParkingLot(self, licensePlate):
        for car in self.parkedCars:
            if car.licensePlate == licensePlate:
                self.availableSpaces += 1
                if car.isPark:
                    car.leave()
                now = datetime.datetime.now().replace(microsecond=0)
                car.outpark = now
                print(f"{now} 車牌號碼為 {car.licensePlate} 的車輛離開停車場。")
                return car
        print("此車輛並未停放在此停車場。")
        return None

    def found(self, license):
        for car in self.parkedCars:
            if car.licensePlate == license:
                return car
        print("not found")
        return None

    def parkCar(self, licensePlate):
        for space in self.parkingSpaces:
            if not space.occupied:
                car = self.found(licensePlate)
                space.occupy(car)
                print(f"車牌號碼為 {licensePlate} 的車輛現已停放在停車位 {space.spaceId}。\n")
                return car

    def leaveCar(self, licensePlate):
        for space in self.parkingSpaces:
            if space.occupied and space.carLicensePlate == licensePlate:
                self.availableSpaces -= 1
                car = self.found(licensePlate)
                space.leave(car)
                return car
        print("此車輛並未停放在此停車場。")
        return None

    def getAvailableSpaces(self):
        return self.availableSpaces

    def getParkedCars(self):
        return [space.carLicensePlate for space in self.parkingSpaces if space.occupied]

    def getOccupiedSpaces(self):
        return [space.spaceId for space in self.parkingSpaces if space.occupied]

    def getCarBySpaceId(self, spaceId):
        for space in self.parkingSpaces:
            if space.spaceId == spaceId and space.occupied:
                return space.carLicensePlate
        return None

    def getSpaceIdByCar(self, licensePlate):
        for space in self.parkingSpaces:
            if space.occupied and space.carLicensePlate == licensePlate:
                return space.spaceId
        return None

class ParkingSpace:
    def __init__(self, spaceId):
        self.spaceId = spaceId
        self.occupied = False
        self.carLicensePlate = None

    def occupy(self, car):
        self.occupied = True
        self.carLicensePlate = car.licensePlate
        print(f"車牌號碼為 {self.carLicensePlate} 的車輛已進入停車位 {self.spaceId}。")
        car.park()

    def leave(self, car):
        if self.carLicensePlate:
            car.leave()
            print(f"車牌號碼為 {self.carLicensePlate} 的車輛已離開停車位 {self.spaceId}。")
            self.carLicensePlate = None
            self.occupied = False
        else:
            print(f"停車位 {self.spaceId} 為空。")

def draw_parking_lot(parked_spaces=[], highlight_space=None):
    x1 = 2
    y1 = 22
    width = 6
    height = 8

    fig, ax = plt.subplots(figsize=(10, 6))  # Adjust the figsize to control the size
    spaceId = []

    for i in range(13):
        x1 = i * width + 1
        spaceId.append(i + 1)
        facecolor_Status = 'b' if spaceId[i] == highlight_space else ('g' if spaceId[i] not in parked_spaces else 'r')
        rectangle = plt.Rectangle((x1, y1), width, height, linewidth=1, edgecolor='b', facecolor=facecolor_Status)
        ax.add_patch(rectangle)
        plt.text(x1 + width / 2, y1 + height / 2, str(spaceId[i]), ha='center', va='center')

    x2 = 10
    y2 = 2
    width = 8
    height = 6

    for m in range(3):
        spaceId.append(m + 14)
        if m < 2:
            x2 = m * width + 18
        else:
            x2 = m * width + 36
        facecolor_Status = 'b' if spaceId[m + 13] == highlight_space else ('g' if spaceId[m + 13] not in parked_spaces else 'r')
        rectangle = plt.Rectangle((x2, y2), width, height, linewidth=1, edgecolor='b', facecolor=facecolor_Status)
        ax.add_patch(rectangle)
        plt.text(x2 + width / 2, y2 + height / 2, str(spaceId[m + 13]), ha='center', va='center')

    ax.set_xlim(0, 80)
    ax.set_ylim(0, 35)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.tick_params(top=False, bottom=False, left=False, right=False)
    plt.tick_params(labeltop=False, labelbottom=False, labelleft=False, labelright=False)
    return fig

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("停車場管理系統")
        self.resize(1000, 800)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        self.input_layout = QtWidgets.QHBoxLayout()
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
        self.input_layout.addWidget(self.leave_button)

        self.query_space_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.query_space_layout)

        self.query_space_input_layout = QtWidgets.QHBoxLayout()
        self.query_space_layout.addLayout(self.query_space_input_layout)

        self.query_space_label = QtWidgets.QLabel("查詢車位號碼:")
        self.query_space_label.setStyleSheet("font-size: 16px;")
        self.query_space_input_layout.addWidget(self.query_space_label)

        self.space_input = QtWidgets.QLineEdit()
        self.space_input.setStyleSheet("font-size: 16px;")
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
        self.query_car_input_layout.addWidget(self.car_input)

        self.query_car_button = QtWidgets.QPushButton("查詢")
        self.query_car_button.setStyleSheet("font-size: 16px;")
        self.query_car_button.clicked.connect(self.query_car)
        self.query_car_input_layout.addWidget(self.query_car_button)

        self.result_car_label = QtWidgets.QLabel("")
        self.result_car_label.setStyleSheet("font-size: 16px;")
        self.query_car_layout.addWidget(self.result_car_label)

        self.figure = draw_parking_lot()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.parkingLot = ParkingLot(capacity=16)
        self.query_result = None

    def park_car(self):
        inputLicense = self.license_input.text()
        car_in_lot = any(car == inputLicense for car in self.parkingLot.getParkedCars())
    
        if not car_in_lot:
            self.parkingLot.enterParkingLot(inputLicense)
            car = self.parkingLot.parkCar(inputLicense)
            if car:
                msg = QtWidgets.QMessageBox()
                msg.setWindowTitle("停車時間")
                msg.setText(f"車牌號碼為 {inputLicense} 的車輛已停放，當前時間為 {car.inspace}")
                msg.exec_()
            self.update_plot()
        else:
            print("車輛已在停車場內")

    def leave_car(self):
        inputLicense = self.license_input.text()
        car_in_lot = any(car.licensePlate == inputLicense for car in self.parkingLot.parkedCars)
        
        if car_in_lot:
            car = self.parkingLot.leaveCar(inputLicense)
            self.parkingLot.leaveParkingLot(inputLicense)
            if car:
                park_duration = car.outspace - car.inspace
                msg = QtWidgets.QMessageBox()
                msg.setWindowTitle("離開時間與停車時長")
                msg.setText(f"車牌號碼為 {inputLicense} 的車輛已離開，當前時間為 {car.outspace}，停車時長為 {park_duration}")
                msg.exec_()
            self.update_plot()
        else:
            print("車輛不在停車場內")

    def query_space(self):
        space_id = self.space_input.text()
        if space_id.isdigit():
            space_id = int(space_id)
            car_license_plate = self.parkingLot.getCarBySpaceId(space_id)
            if car_license_plate:
                self.result_space_label.setText(f">停車位 {space_id} 的車牌號碼為 {car_license_plate}。")
            else:
                self.result_space_label.setText(f">停車位 {space_id} 沒有車輛停放。")
            self.update_plot(highlight_space=space_id)

    def query_car(self):
        license_plate = self.car_input.text()
        if license_plate:
            space_id = self.parkingLot.getSpaceIdByCar(license_plate)
            if space_id:
                self.result_car_label.setText(f">車牌號碼為 {license_plate} 的車子停在 {space_id} 號車位。")
            else:
                self.result_car_label.setText(f">車牌號碼為 {license_plate} 的車輛不在停車場內。")
            self.update_plot(highlight_space=space_id)

    def update_plot(self, highlight_space=None):
        parked_spaces = self.parkingLot.getOccupiedSpaces()
        self.figure = draw_parking_lot(parked_spaces, highlight_space)
        self.canvas.figure = self.figure
        self.canvas.draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
