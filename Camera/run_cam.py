import time
import os
import threading
from Camera import HuarayCam
from datetime import datetime
import img_proc
import data_proc
from PyQt5.QtCore import QObject, pyqtSignal
import threading
import time
from PIL import Image
import cv2
from record_log import ResultLog

class CamRunner(QObject):
    image_signal = pyqtSignal()

    def __init__(self, args, nmp_comm):
        super().__init__()
        self.nmp_comm = nmp_comm
        self.camera = HuarayCam.HuarayCam(args)
        self.camera.resetCam()
        self.camera.openCam()
        self.camera.displayDeviceInfo()
        self.camera.setTrigger()
        self.camera.startGrabbing()
        self.camera.runThread = True
        self.log = ResultLog('D:\\min_UFM\\log', 'log')

    def executeCam(self, args, wk):
        # trigger_mode = args.trigger_mode
        # print(f'run_cam) trigger_mode: {"Software" if trigger_mode==1 else "Line"}')
        while self.camera.runThread:
            result = self.camera.get_frame()
            if result == 0:
                if self.nmp_comm.Dnmp['marking_type'] not in ['A', 'C']:
                    if self.nmp_comm.Dnmp['marking_type'] == '':
                        print('run_cam) Marking type Empty')
                    else:
                        print('run_cam) PASSING OTHER THAN "A" GRADE TIRE')
                    self.camera.release_frame()
                    continue
                else:
                    # with open('target.txt', 'r') as file:
                    #     targets = [line.strip() for line in file]
                    # if self.nmp_comm.Dnmp['inspection_code'] not in targets:
                    #     print(f'run_cam) {self.nmp_comm.Dnmp["inspection_code"]} IS NOT AN INSPECT TARGET, PASSING')
                    #     self.camera.release_frame()
                    #     continue
                    print('run_cam) EXECUTING CAMERA')
                    cv_image = self.camera.getImage(self.camera.frame)
                    image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(image_rgb)
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    if not os.path.exists(args.image_save_path):
                        os.makedirs(args.image_save_path, exist_ok=True)
                    save_path = os.path.join(args.image_save_path, 'image')
                    wk.img_name = current_time + '.jpg'
                    wk.img_path = os.path.join(save_path, wk.img_name)
                    wk.txt_name = wk.img_name.replace('jpg', 'txt')
                    img_proc.save_img(save_path, wk.img_name, img)
                    self.log.LogTextOut(f'img name : {current_time + ".jpg"}\t tire spec : {self.nmp_comm.Dnmp["tire_spec"]}\t marking type : {self.nmp_comm.Dnmp["marking_type"]}\n')
                    self.camera.release_frame()
                    self.image_signal.emit()
            else:
                time.sleep(0.1)
                continue

    def cam_monitoring(self, args, wk):
        t = threading.Thread(target=self.executeCam, args=(args, wk))
        try:
            t.start()
            print('run_cam) CAM THREAD START')
        except Exception as e:
            if t.is_alive():
                t.join()
            self.camera.runThread = False
            self.camera.closeCam()
            print('run_cam) CAM CLOSED')