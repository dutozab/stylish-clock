from src.clock_widget import AnalogClock
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
clock = AnalogClock()
clock.show()
sys.exit(app.exec())
