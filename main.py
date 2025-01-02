from run import Runner
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, Qt
import threading
import ui

def main():
    app = QApplication(sys.argv)
    marking_ui = ui.MarkingUI()

    runner = Runner()
    runner_thread = QThread()
    runner.moveToThread(runner_thread)
    runner_thread.start()
    runner.camera.image_signal.connect(runner.evaluate, Qt.QueuedConnection)
    print('main) CONNECTED CAM-RUN')
    runner.wk.result_signal.connect(marking_ui.load_image, Qt.QueuedConnection)
    print('main) CONNECTED RUN-UI')
    runner.start_monitoring()
    marking_ui.wk = runner.wk
    
    marking_ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()