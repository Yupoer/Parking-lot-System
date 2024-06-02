from parkingUI import ParkingLot

import sys
from PyQt5 import QtWidgets, QtCore

from gui import MainWindow
import parking_space_counter.detect as detect

class ParkingThread(QtCore.QThread):
    """
    自定義的執行緒類，用於在後台運行 detect.getSpace(spots, cap, window)
    """
    def __init__(self, spots, cap, window):
        super().__init__()
        self.spots = spots
        self.cap = cap
        self.window = window

    def run(self):
        detect.getSpace(self.spots, self.cap, self.window)

if __name__ == "__main__":
    spots, cap = detect.init()
    #detect.getSpace(spots, cap)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(ParkingLot, spots)
    window.show()

    window.park_car("##", "14")
    window.park_car("333333", "11")
    window.park_car("124EE", "10")
    window.park_car(33, "12")


    #window.park_video.play()
    #window.leave_car("ABC123","17")
    """
    detect.getSpace(spots, cap) -> 這個是用來測試的函數
    TODO: 需要讓他在park_video.play()執行時同步執行
    """
    # 創建並啟動執行緒
    thread = ParkingThread(spots, cap, window)
    thread.start()

    sys.exit(app.exec_())
