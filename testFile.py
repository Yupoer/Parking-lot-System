# testFile.py

import unittest

import parking_space_counter.detect as detect

from gui import *
from parkingUI import ParkingLot


class TestParkingSystem(unittest.TestCase):

    def setUp(self):
        spots, cap = detect.init()
        # 初始化 ParkingSystem 類的實例
        self.parking_system = MainWindow(ParkingLot, spots)

        # 清空數據庫文件，確保每次測試都是獨立的
        with open(self.parking_system.car_db_file, 'w', encoding='utf-8') as f:
            f.truncate()
        with open(self.parking_system.space_db_file, 'w', encoding='utf-8') as f:
            f.truncate()

    def test_valid_license_plate(self):
        # 測試有效車牌號碼
        self.parking_system.park_car("ABC1234", "18")
        self.assertIn("ABC1234", self.parking_system.car_db)

    def test_invalid_license_plate_short(self):
        # 測試車牌號碼過短
        with self.assertLogs(level='INFO') as log:
            self.parking_system.park_car("ABC", "18")
            self.assertIn("error", log.output[0])

    def test_invalid_license_plate_long(self):
        # 測試車牌號碼過長
        with self.assertLogs(level='INFO') as log:
            self.parking_system.park_car("ABCDEFGH", "18")
            self.assertIn("error", log.output[0])

    def test_invalid_license_plate_all_digits(self):
        # 測試車牌號碼全部為數字
        with self.assertLogs(level='INFO') as log:
            self.parking_system.park_car("1234567", "18")
            self.assertIn("error", log.output[0])

    def test_invalid_license_plate_all_letters(self):
        # 測試車牌號碼全部為字母
        with self.assertLogs(level='INFO') as log:
            self.parking_system.park_car("ABCDEFG", "18")
            self.assertIn("error", log.output[0])

    def test_invalid_license_plate_special_chars(self):
        # 測試車牌號碼包含特殊字符
        with self.assertLogs(level='INFO') as log:
            self.parking_system.park_car("ABC@123", "18")
            self.assertIn("error", log.output[0])


if __name__ == "__main__":
    unittest.main()
