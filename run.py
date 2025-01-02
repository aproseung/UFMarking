import os
from nmp import NMPComm
import time
import yaml
from types import SimpleNamespace as SN
from Camera import run_cam
from PyQt5.QtCore import QObject,  pyqtSlot
import time
import worker
import data_proc

class Runner(QObject):
    def __init__(self):
        super().__init__()
        with open('D:\\min_UFM\\config.yaml') as f:
            config = yaml.safe_load(f)
        self.conf_args = SN(**config)
        self.wk = worker.Worker(self.conf_args)
        self.nmp_proc = NMPComm(ip_addr='10.82.225.242', port=2209, wk=self.wk)
        self.camera = run_cam.CamRunner(self.conf_args, self.nmp_proc)
    
    def start_monitoring(self):
        self.nmp_proc.start_monitoring()
        self.camera.cam_monitoring(self.conf_args, self.wk)

    @pyqtSlot()
    def evaluate(self):
        if not os.path.exists(self.wk.img_path):
            print('run) IMAGE PATH DOESN\'T EXIST')
            return
        elif self.nmp_proc.Dnmp['marking_type'] == '':
            print('run) NO MARKING TYPE IN Dnmp, CAN\'t EVALUATE')
            return
        else:
            self.wk.mark = self.nmp_proc.Dnmp['marking_type']
            cropped, resize_mark = self.wk.detect_marking()
            result = self.wk.classify_marking(cropped, resize_mark)
            if self.nmp_proc.Dnmp['marking_type'] == 'A':
                self.nmp_proc.reply_markResult(result, self.nmp_proc.client_socket)
        time.sleep(5)
        return