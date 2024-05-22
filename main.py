# -*- coding: utf-8 -*-
"""testLotUI.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1J3BwQLohyPhmdAn0l736731C_LQuBj-i
"""

# -*- coding: utf-8 -*-
"""parkinglot_detection.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1SuWeBw01GugMXEvFZLR1YQtq2otYF8E5
"""



import sys
import matplotlib.pyplot as plt
from parking_space_counter import detect
from PyQt5.QtWidgets import QLabel
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from gui import MainWindow
import parking_space_counter.detect as detect


class Car:
    def __init__(self, licensePlate):
        self.licensePlate = licensePlate
        self.parked = False

    def park(self):
        if not self.parked:
            self.parked = True
            print(f"車牌號碼為 {self.licensePlate} 的車輛現已停放。")
        else:
            print("此車輛已經停放。")

    def leave(self):
        if self.parked:
            self.parked = False
            print(f"車牌號碼為 {self.licensePlate} 的車輛已離開停車場。")
        else:
            print("此車輛並未停放。")

    def __str__(self):
        return f"車輛 (車牌號碼: {self.licensePlate})"


class ParkingLot:
    def __init__(self, capacity):
        self.capacity = capacity
        self.availableSpaces = capacity

        # List to store all parking spaces
        self.parkingSpaces = [ParkingSpace(spaceId)
                              for spaceId in range(1, capacity + 1)]
        self.parkedCars = []

    def enterParkingLot(self, car):
        if self.availableSpaces > 0:
            self.availableSpaces -= 1
            self.parkedCars.append(car)
            print(f"車牌號碼為 {car.licensePlate} 的車輛進入停車場。")

            # Automatically park the car upon entering the parking lot
            self.parkCar(car)
        else:
            print("停車場已滿，無法進入。")

    def leaveParkingLot(self, licensePlate):
        for car in self.parkedCars:
            if car.licensePlate == licensePlate:

                # Increment available spaces when a car leaves the parking lot
                self.availableSpaces += 1
                self.parkedCars.remove(car)
                print(f"車牌號碼為 {car.licensePlate} 的車輛離開停車場。")
                return
        print("此車輛並未停放在此停車場。")

    def parkCar(self, car):
        for space in self.parkingSpaces:
            if not space.occupied:
                space.occupy(car)
                print(f"車牌號碼為 {car.licensePlate} 的車輛現已停放在停車位 {space.spaceId}。")
                return

    def leaveCar(self, licensePlate):
        for space in self.parkingSpaces:
            if space.occupied and space.car.licensePlate == licensePlate:
                space.leave()
                return
        print("此車輛並未停放在此停車場。")

    def getAvailableSpaces(self):
        return self.availableSpaces

    def getParkedCars(self):
        return [car for car in self.parkedCars if car in [space.car for space in self.parkingSpaces if space.occupied]]


class ParkingSpace:
    def __init__(self, spaceId):
        self.spaceId = spaceId
        self.occupied = False

        # Variable to store the occupying car
        self.car = None

    def occupy(self, car):
        self.occupied = True
        self.car = car
        print(f"車牌號碼為 {car.licensePlate} 的車輛已進入停車位 {self.spaceId}。")

    def leave(self):
        if self.car:
            print(f"車牌號碼為 {self.car.licensePlate} 的車輛已離開停車位 {self.spaceId}。")
            self.car = None
        else:
            print(f"停車位 {self.spaceId} 為空。")

if __name__ == "__main__":
    spots, cap = detect.init()
    #detect.getSpace(spots, cap)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(ParkingLot, spots)
    window.show()
    window.park_video.play()
    detect.getSpace(spots, cap)
    sys.exit(app.exec_())
