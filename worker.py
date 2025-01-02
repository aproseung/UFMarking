import os
import sys
import torch
import cv2
import numpy as np
import data_proc
import img_proc
from ultralytics import YOLO
from collections import deque
from PIL import Image
from PyQt5.QtCore import QObject, pyqtSignal
import img_proc
import json

class Worker(QObject):
    result_signal = pyqtSignal(str) # Signal that tells image evaluation is done

    def __init__(self, args):
        super().__init__()
        self.save_dir = args.image_save_path
        self.save_image_dir = os.path.join(self.save_dir, 'images')
        self.save_box_dir = os.path.join(self.save_dir, 'box')
        self.save_cropped_dir = os.path.join(self.save_dir, 'cropped')
        self.save_contour_dir = os.path.join(self.save_dir, 'contour')
        self.save_result_dir = os.path.join(self.save_dir, 'result')

        self.detect_model = YOLO('detector.pt')

        with open('settings.json', 'r') as json_file:
            settings = json.load(json_file)

        # Threshold for classifying a pixel as marking
        self.pixel_threshold = settings['pixel_threshold']
        # Threshold for classifying an image as OK
        self.image_threshold = settings['image_threshold']
        # Queue length
        self.queue_length = settings['queue_length']
        # Brightness of the contour
        self.contour_factor = 1.5

        self.mark_size = 200
        self.px_to_mm = 0.16216

        self.img_name = ''
        self.txt_name = ''
        self.img_path = ''
        self.args = args

        self.mark = ''
    
    def detect_marking(self):
        img = Image.open(self.img_path)
        print('save to --',os.path.join(self.save_dir, 'full', self.mark + '_'+self.img_name))
        img_proc.save_img(os.path.join(self.save_dir, 'full'), self.mark +'_'+self.img_name, img)
        results = self.detect_model(img)
        boxes = results[0].boxes

        if len(boxes.cls) > 0:
            conf = boxes.conf
            _, maxidx = torch.max(conf, dim=0)
            xmin, ymin, xmax, ymax = map(int, boxes.xyxy[maxidx])
            box_file_path = os.path.join(self.save_box_dir, self.txt_name)
            with open(box_file_path, 'w') as file:
                file.write(f'{xmin} {ymin} {xmax} {ymax}')
            cropped = img.crop((xmin, ymin, xmax, ymax))
            cropped_w, cropped_h = abs(xmax - xmin), abs(ymax - ymin)
            # print('MARK TYPE !!!! >>>> ',self.img_path) # D:/min_UFM/log\image\20241230_140120.jpg
            mm_mark_size = max([cropped_w, cropped_h]) * self.px_to_mm
            if self.mark == 'C':
                if mm_mark_size > 10: # ng
                    img_proc.save_img(os.path.join(self.save_dir,'size_ng'), self.mark + '_' + self.img_name.split('.')[0] + '_' + '{:.2f}'.format(mm_mark_size) +'.jpg', cropped)
                else: # ok
                    img_proc.save_img(os.path.join(self.save_dir,'size_ok'), self.mark + '_' + self.img_name.split('.')[0] + '_' + '{:.2f}'.format(mm_mark_size) +'.jpg', cropped)
            else:
                if mm_mark_size <= 10:
                    img_proc.save_img(os.path.join(self.save_dir,'size_ng'), self.mark + '_' + self.img_name.split('.')[0] + '_' + '{:.2f}'.format(mm_mark_size) +'.jpg', cropped)
                else: # ok
                    img_proc.save_img(os.path.join(self.save_dir,'size_ok'), self.mark + '_' + self.img_name.split('.')[0] + '_' + '{:.2f}'.format(mm_mark_size) +'.jpg', cropped)

            img_proc.save_img(os.path.join(self.save_cropped_dir, self.mark), self.img_name, cropped)
            resize_mark = cropped.resize((self.mark_size, self.mark_size), Image.LANCZOS)
            img_proc.save_img(self.save_cropped_dir, self.img_name, resize_mark)
        else:
            cropped = None
            resize_mark = None
        return cropped, resize_mark
    
    def classify_marking(self, cropped, resize_mark):
        if (cropped is None) or (resize_mark is None):
            ratio = -1
            result = 'NO'
        else:
            contour_path = os.path.join(self.save_contour_dir, self.img_name)
            mark_np = np.array(resize_mark.copy())
            contour_np = np.copy(mark_np)
            r_channel = mark_np[:, :, 0]
            b_channel = mark_np[:, :, 2]
            r = self.mark_size / 2
            mark_pixels = 0
            total_pixels = 0
            for x in range(self.mark_size):
                for y in range(self.mark_size):
                    if (x - r) ** 2 + (y - r) ** 2 <= r ** 2:
                        # if current coordinate is inside the incircle of image
                        total_pixels += 1
                        diff = np.clip(r_channel[x, y] - b_channel[x, y] - self.pixel_threshold, 0, 255)
                        if diff > 0:
                            mark_pixels += 1
                            green = np.clip(int(self.contour_factor * diff), 0, 255)
                            contour_np[x, y] = [0, green, 0]
            contour = Image.fromarray(contour_np)
            contour.save(contour_path)
            ratio = round(mark_pixels / total_pixels * 100, 2)
            result = 'OK' if ratio >= self.image_threshold else 'NG'
            if result == 'OK':
                img_proc.save_img(os.path.join(self.save_dir,'ok'), self.mark + '_' + self.img_name, cropped)
            else:
                img_proc.save_img(os.path.join(self.save_dir,'ng', data_proc.get_date()), self.mark + '_' + self.img_name, cropped)

        result_file_path = os.path.join(self.save_result_dir, self.txt_name)
        with open(result_file_path, 'w') as file:
            file.write(f'{ratio}\n{result}') 
        self.result_signal.emit(self.img_path) # Send result signal
        return result

    def setPixelThreshold(self, newPixelThreshold):
        self.pixel_threshold = newPixelThreshold
        return

    def setImageThreshold(self, newImageThreshold):
        self.image_threshold = newImageThreshold
        return
    
    def setQueueLength(self, newQueueLength):
        self.queue_length = newQueueLength
        return
    

