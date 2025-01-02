from PIL import Image, ImageDraw
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QFont, QFontDatabase, QImage
from PyQt5.QtWidgets import QDialog, QLineEdit, QWidget, QTableWidget, QGridLayout, QVBoxLayout, \
    QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QMainWindow, QAction, QPushButton, QHeaderView, \
    QApplication, QTableWidgetItem, QMessageBox, QSizePolicy
import time
import os
import hashlib
from glob import glob
import json
from datetime import datetime
import stylesheet as ss

class HistoryWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('History')
        self.setFixedSize(700, 500)
        self.image_opened = False
        self.font = QFont("Hankook KR TTF", 10)

        # History table
        self.table = QTableWidget(self)
        self.init_table()

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def init_table(self):
        self.table.setRowCount(0)
        self.table.setColumnCount(2)
        self.table.setFont(self.font)
        self.table.setHorizontalHeaderLabels(['Image paths', 'Result'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.cellDoubleClicked.connect(self.open_image_window)

        with open('log.json', 'r') as json_file:
            data = json.load(json_file)
            if data:
                for record in reversed(data):
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    if record['image_path']:
                        self.table.setItem(row, 0, QTableWidgetItem(record['image_path']))
                    if record['result']:
                        self.table.setItem(row, 1, QTableWidgetItem(record['result']))

    def add_thres_change(self, threshold_type, oldval, newval):
        if not threshold_type or (oldval == newval):
            return
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        change_record = f'{timestamp} change {threshold_type}'
        change_value = f'{oldval:.2f} -> {newval:.2f}'

        self.table.insertRow(0)

        self.table.setItem(0, 0, QTableWidgetItem(change_record))
        self.table.setItem(0, 1, QTableWidgetItem(change_value))
        self.save_data()

    def add_image(self, image_path):
        if not image_path:
            return
        result_path = image_path.replace('image', 'result').replace('jpg', 'txt')
        with open(result_path, 'r') as file:
            ratio = file.readline().strip()
            result = file.readline()
            result_item = f'{ratio}%, {result}'
        self.table.insertRow(0)

        self.table.setItem(0, 0, QTableWidgetItem(image_path))
        self.table.setItem(0, 1, QTableWidgetItem(result_item))
        self.save_data()

    def save_data(self):
        data = []
        for row in range(self.table.rowCount()-1, -1, -1):
            image_path = self.table.item(row, 0).text() if self.table.item(row, 0) else ''
            result = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
            data.append({
                'image_path': image_path,
                'result': result
            })
        with open('log.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)   

    def delete_data(self):
        data = []
        with open('log.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print('ui) Deleted all data in log.json') 

    def open_image_window(self, row, col):
        if self.image_opened or col == 1:
            return
        item = self.table.item(row, col)
        image_path = item.text()
        if image_path.endswith('.jpg'):
            image_path = image_path.replace('image', 'cropped')
            self.history_image_window = HistoryImageWindow(image_path)
            self.history_image_window.finished.connect(self.close_image_window)
            self.history_image_window.show()
            self.image_opened = True
        
    def close_image_window(self):
        self.image_opened = False

class HistoryImageWindow(QDialog):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle(image_path)
        self.setFixedSize(500, 500)
        self.image = QLabel(self)
        self.image.resize(400, 400)

        image = Image.open(image_path)
        image = image.resize((400, 400))
        q_img = pil_to_qimg(image)

        pixmap = QPixmap.fromImage(q_img)
        self.image.setPixmap(pixmap)

class PasswordDialog(QDialog):
    correct_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('비밀번호 입력 창')
        self.setGeometry(100, 100, 200, 100)
        self.font = QFont("Hankook KR TTF", 10)
        
        layout = QVBoxLayout()
        self.label = QLabel("비밀번호를 입력하세요:")
        self.label.setFont(self.font)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.submit = QPushButton('확인')
        self.submit.setFont(self.font)

        layout.addWidget(self.label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.submit)
        self.setLayout(layout)

        self.submit.clicked.connect(self.check_password)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self):
        password_input = self.password_input.text()
        with open('password.txt', 'r') as file:
            password_hash = file.read()
        if self.hash_password(password_input) == password_hash:
            self.correct_signal.emit()
            self.accept()
        else:
            QMessageBox.warning(self, '오류', '비밀번호가 틀렸습니다.')
            self.password_input.clear()

class SettingsWindow(QDialog):
    save_signal = pyqtSignal(list)
    threschange_signal = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Settings')
        self.setFixedSize(500, 500)
        self.font = QFont("Hankook KR TTF", 10)
        layout = QVBoxLayout()
        self.load_saved_values()

        # Pixel threshold
        pt_layout = QHBoxLayout()
        pt_label = QLabel("Pixel threshold:")
        pt_label.setFont(self.font)
        self.pt_spinbox = self.create_spinbox(num_type='int', num_range=(0, 100), init_value=self.pixel_threshold)
        pt_layout.addWidget(pt_label)
        pt_layout.addWidget(self.pt_spinbox)

        # Image threshold
        it_layout = QHBoxLayout()
        it_label = QLabel("Image threshold:")
        it_label.setFont(self.font)
        self.it_spinbox = self.create_spinbox(num_type='float', num_range=(1.0, 99.0), init_value=self.image_threshold, 
                                              single_step=0.5, suffix='%')
        it_layout.addWidget(it_label)
        it_layout.addWidget(self.it_spinbox)

        # Queue length
        ql_layout = QHBoxLayout()
        ql_label = QLabel("Queue length:")
        ql_label.setFont(self.font)
        self.ql_spinbox = self.create_spinbox(num_type='int', num_range=(3, 10), init_value=self.queue_length)
        ql_layout.addWidget(ql_label)
        ql_layout.addWidget(self.ql_spinbox)

        # Save button 
        save_layout = QHBoxLayout()
        save_button = QPushButton('변경사항 저장')
        save_button.setFont(self.font)
        save_button.clicked.connect(self.send_save_values)
        save_layout.addWidget(save_button)

        # Change password
        changepw_layout = QHBoxLayout()
        self.new_pw = QLineEdit()
        self.change_pw = QPushButton('비밀번호 변경')
        self.change_pw.setFont(self.font)
        self.change_pw.clicked.connect(self.change_password)
        changepw_layout.addWidget(self.new_pw)
        changepw_layout.addWidget(self.change_pw)

        # Entire layout
        layout.addLayout(pt_layout)
        layout.addLayout(it_layout)
        layout.addLayout(ql_layout)
        layout.addLayout(save_layout)
        layout.addLayout(changepw_layout)
        self.setLayout(layout)

    def load_saved_values(self):
        with open('settings.json', 'r') as settings_json:
            data = json.load(settings_json)
        self.pixel_threshold = data['pixel_threshold']
        self.image_threshold = data['image_threshold']
        self.queue_length = data['queue_length']

    def send_save_values(self):
        pt = self.pt_spinbox.value()
        it = self.it_spinbox.value()
        ql = self.ql_spinbox.value()
        self.save_signal.emit([pt, it, ql])

    def delete_all_files(self):
        base_path = 'D:/min_ufm/log'
        folders = ['box', 'contour', 'cropped', 'image', 'result']
        for folder in folders:
            folder_path = os.path.join(base_path, folder)
            if not os.path.exists(folder_path):
                print('ui) FOLDER TO DELETE DOES NOT EXIST')
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                os.remove(file_path)
        print('ui) SUCCESSIVELY DELETED ALL FILES')
        return        

    def change_password(self):
        # 비밀번호 입력 칸 초기화
        new_password = self.new_pw.text()
        self.new_pw.clear()
        # password.txt 파일 열어 비밀번호 수정
        with open('password.txt', 'w') as file:
            new_password = hashlib.sha256(new_password.encode()).hexdigest()
            file.write(new_password)
        # QMessagebox 비밀번호 변경 알림
        QMessageBox.warning(self, ' ', f'비밀번호가 변경되었습니다.')

    def create_spinbox(self, num_type, num_range, init_value, single_step=0, suffix=None):
        if num_type == 'float':
            spinbox = QDoubleSpinBox()
        elif num_type == 'int':
            spinbox = QSpinBox()
        spinbox.setRange(*num_range)
        spinbox.setValue(init_value)
        if single_step != 0:
            spinbox.setSingleStep(single_step)
        if suffix:
            spinbox.setSuffix(suffix)
        spinbox.setAlignment(Qt.AlignCenter)
        return spinbox
    
class TargetWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('검사코드 목록')
        self.setGeometry(100, 100, 500, 500)
        self.font = QFont("Hankook KR TTF", 10)
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.init_table()

        self.target_label = QLabel('검사 코드 입력')
        self.target_label.setFont(self.font)
        self.target_box = QLineEdit()
        self.target_box.setEchoMode(QLineEdit.Normal)
        self.buttons_layout = QHBoxLayout()
        self.add_button = QPushButton('추가')
        self.add_button.setFont(self.font)
        self.add_button.clicked.connect(self.add_target)
        self.delete_button = QPushButton('삭제')
        self.delete_button.setFont(self.font)
        self.delete_button.clicked.connect(self.delete_target)
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.delete_button)

        layout.addWidget(self.table)
        layout.addWidget(self.target_label)
        layout.addWidget(self.target_box)
        layout.addLayout(self.buttons_layout)
        self.setLayout(layout)

    def init_table(self):
        self.table.setRowCount(0)
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderLabels(['검사 대상 코드 목록'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        with open('target.txt', 'r') as file:
            targets = file.readlines()
            for target in sorted(targets):
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(target))
    
    def add_target(self):
        target_to_add = self.target_box.text().split(' ')
        self.delete_target()
        with open('target.txt', 'a') as file:
            for target in target_to_add:
                file.write(f'{target}\n')
                QMessageBox.warning(self, ' ', f'검사코드 {target}이(가) 추가되었습니다.')
        self.init_table()
        self.target_box.clear()
    
    def delete_target(self):
        target_to_delete = self.target_box.text().split(' ')
        with open('target.txt', 'r') as file:
            targets = [line.strip() for line in file]
        with open('target.txt', 'w') as file:
            for target in targets:
                if target not in target_to_delete:
                    file.write(f'{target}\n')
                else:
                    QMessageBox.warning(self, ' ', f'검사코드 {target}이(가) 삭제되었습니다.')
        self.init_table()
        self.target_box.clear()

class MarkingUI(QMainWindow):
    def __init__(self):
        # Window title & image label
        super().__init__()
        self.setWindowTitle("Marking.exe")
        self.setGeometry(100, 100, 800, 600)
        self.center()
        self.setStyleSheet(ss.STYLESHEET)
        self.font = QFont("Hankook KR TTF", 15)
        center_widget = QWidget()
        self.setCentralWidget(center_widget)
        # self.centralWidget().resize(400, 400)
        self.centralWidget().setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QGridLayout()
        layout.setRowStretch(0, 1)
        layout.setRowStretch(1, 4)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        center_widget.setLayout(layout)

        self.image_list = sorted(glob('D:/min_ufm/log/image/*.jpg'))
        self.idx = len(self.image_list) - 1
        self._is_running = True
        self.wk = None
        self.tableitems = ['Marking 픽셀 비율', '-', '판정 결과', '-']
        self.recent_idx = [self.idx - 4, self.idx + 1]
        self.history_window = HistoryWindow()
        self.settings_window = SettingsWindow()
        self.settings_window.save_signal.connect(self.save_settings)
        self.target_window = TargetWindow()

        # Menu bar
        self.menu_bar = self.menuBar()

        history_action = QAction(' 판정 내역 ', self)
        history_action.triggered.connect(self.open_history_window)
        
        settings_action = QAction(' 설정 ', self)
        settings_action.triggered.connect(self.open_password_window)

        edit_target_action = QAction(' 검사코드 편집 ', self)
        edit_target_action.triggered.connect(self.open_target_window)

        self.menu_bar.addAction(history_action)
        self.menu_bar.addAction(settings_action)
        self.menu_bar.addAction(edit_target_action)
        
        # Image layout
        self.image_box = QWidget()
        image_layout = QVBoxLayout()
        self.image_box.setLayout(image_layout)

        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        image_layout.addWidget(self.label)

        self.image_label = QLabel()
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)
        layout.addWidget(self.image_box, 0, 0)

        # Control layout
        self.control_box = QWidget()
        self.control_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        control_layout = QHBoxLayout()
        self.control_box.setLayout(control_layout)

        # Prev button
        self.prevButton = QPushButton(self)
        self.prevIcon = QIcon('icons/Prev.png')
        self.prevButton.setIcon(self.prevIcon)
        self.prevButton.setIconSize(self.prevButton.size())
        self.prevButton.setFixedSize(80, 80)
        self.prevButton.clicked.connect(self.prev_image)
        control_layout.addWidget(self.prevButton)

        # Play button
        self.playButton = QPushButton(self)
        playPixmap = QPixmap('icons/Play.png')
        playIcon = QIcon(playPixmap)
        self.playButton.setIcon(playIcon)
        self.playButton.setIconSize(self.playButton.size())
        self.playButton.setFixedSize(80, 80)
        self.playButton.clicked.connect(self.start_ui)
        control_layout.addWidget(self.playButton)

        # Stop button
        self.stopButton = QPushButton(self)
        self.stopIcon = QIcon('icons/Stop.png')
        self.stopButton.setIcon(self.stopIcon)
        self.stopButton.setIconSize(self.stopButton.size())
        self.stopButton.setFixedSize(80, 80)
        self.stopButton.clicked.connect(self.pause_ui)
        control_layout.addWidget(self.stopButton)

        # Next button
        self.nextButton = QPushButton(self)
        self.nextIcon = QIcon('icons/Next.png')
        self.nextButton.setIcon(self.nextIcon)
        self.nextButton.setIconSize(self.nextButton.size())
        self.nextButton.setFixedSize(80, 80)
        self.nextButton.clicked.connect(self.next_image)
        control_layout.addWidget(self.nextButton)

        layout.addWidget(self.control_box, 1, 0)

        # Result layout
        self.result_box = QWidget()
        result_layout = QGridLayout()
        self.result_box.setLayout(result_layout)    

        # Cropped Marking image
        self.mark_crop_label = QLabel()
        self.mark_crop_label.setText("탐지 결과")
        self.mark_crop_label.setFont(self.font)
        self.mark_crop_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.mark_crop_label, 0, 0)

        self.mark_crop_image = QLabel()
        self.mark_crop_image.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.mark_crop_image, 1, 0)

        # Contour
        self.contour_label = QLabel()
        self.contour_label.setText("판정 결과")
        self.contour_label.setFont(self.font)
        self.contour_label.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.contour_label, 0, 1)

        self.contour_image = QLabel()
        self.contour_image.setAlignment(Qt.AlignCenter)
        result_layout.addWidget(self.contour_image, 1, 1)

        # Result table
        self.result_table = QTableWidget()
        self.result_table.setRowCount(2)
        self.result_table.setColumnCount(2)
        self.result_table.setSelectionMode(QTableWidget.NoSelection)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.horizontalHeader().setVisible(False)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setFont(self.font)
        result_layout.addWidget(self.result_table, 2, 0, 1, 2)
        result_layout.setRowStretch(0, 1)
        result_layout.setRowStretch(1, 3)
        result_layout.setRowStretch(2, 4)

        layout.addWidget(self.result_box, 0, 1)

        # Recent layout
        self.recent_box = QWidget()
        recent_layout = QVBoxLayout()
        self.recent_box.setLayout(recent_layout)

        layout.addWidget(self.recent_box, 1, 1)
        layout.setRowStretch(0, 4)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        # Recent 5 results
        self.recent_label = QLabel()
        n = self.settings_window.queue_length
        self.recent_label.setText(f'최근 {n}개 결과')
        self.recent_label.setFont(self.font)
        self.recent_label.setAlignment(Qt.AlignCenter)
        recent_layout.addWidget(self.recent_label)

        self.recent_widget = QWidget()
        self.recent_layout = QHBoxLayout()
        self.recent_widget.setLayout(self.recent_layout)
        recent_layout.addWidget(self.recent_widget)

        transform = lambda icon: icon.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.green = transform(QPixmap('icons/Green.png'))
        self.red = transform(QPixmap('icons/Red.png'))
        self.yellow = transform(QPixmap('icons/Yellow.png'))
        self.selected_green = transform(QPixmap('icons/SelectedGreen.png'))
        self.selected_red = transform(QPixmap('icons/SelectedRed.png'))
        self.selected_yellow = transform(QPixmap('icons/SelectedYellow.png'))
        self.update_recent_results()

    def get_recent_results(self):
        results = []
        start = max(0, self.idx - self.settings_window.queue_length + 1)
        end = self.idx + 1
        for i in range(start, end):
            image_path = self.image_list[i]
            result_path = image_path.replace('image', 'result').replace('jpg', 'txt')
            with open(result_path, 'r') as file:
                result = file.readline()
                result = file.readline()
            results.append(result)
        return results

    def update_recent_results(self):
        while self.recent_layout.count():
            child = self.recent_layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()

        recent_results = self.get_recent_results()
        for i, result in enumerate(recent_results):
            label = QLabel(self)
            if result == 'OK':
                if i == len(recent_results) - 1:
                    label.setPixmap(self.selected_green)
                else:
                    label.setPixmap(self.green)
            elif result == 'NO':
                if i == len(recent_results) - 1:
                    label.setPixmap(self.selected_red)
                else:
                    label.setPixmap(self.red)
            elif result == 'NG':
                if i == len(recent_results) - 1:
                    label.setPixmap(self.selected_yellow)
                else:
                    label.setPixmap(self.yellow)
            else:
                return None
            self.recent_layout.addWidget(label)
            self.recent_layout.addStretch()
   
    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.desktop().screen().rect().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def pause_ui(self):
        self._is_running = False

    def start_ui(self):
        self._is_running = True

    def show_image(self):
        image_path = self.image_list[self.idx]
        img_name = os.path.basename(image_path)
        txt_name = img_name.replace('jpg', 'txt')
        box_path = os.path.join(self.wk.save_box_dir, txt_name)
        self.label.setText(image_path)
        self.label.setFont(self.font)
        img_height = self.image_label.height()

        img = Image.open(image_path)
        if os.path.exists(box_path):
            with open(box_path, 'r') as file:
                line = file.readline()
                xyxy = list(map(int, line.split(' ')))
            img_w_box = self.draw_box(img.copy(), xyxy)
        else:
            img_w_box = img
        
        q_img = pil_to_qimg(img_w_box)
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(img_height, img_height)
        self.image_label.setPixmap(scaled_pixmap)

        return
    
    def clear_image(self):
        self.image_label.clear()
    
    def show_result(self):
        image_path = self.image_list[self.idx]
        img_name = os.path.basename(image_path)
        txt_name = img_name.replace('jpg', 'txt')
        cropped_path = os.path.join(self.wk.save_cropped_dir, img_name)
        contour_path = os.path.join(self.wk.save_contour_dir, img_name)
        result_path = os.path.join(self.wk.save_result_dir, txt_name)

        if os.path.exists(cropped_path):
            cropped = Image.open(cropped_path)
            q_cropped = pil_to_qimg(cropped)
            cropped_pixmap = QPixmap.fromImage(q_cropped)
            self.mark_crop_image.setPixmap(cropped_pixmap)
        else:
            self.mark_crop_image.clear()

        if os.path.exists(contour_path):
            contour = Image.open(contour_path)
            q_contour = pil_to_qimg(contour)
            contour_pixmap = QPixmap.fromImage(q_contour)
            self.contour_image.setPixmap(contour_pixmap)
        else:
            self.contour_image.clear()

        if os.path.exists(result_path):
            with open(result_path, 'r') as file:
                ratio = file.readline().strip()
                result = file.readline()
            self.tableitems[1] = f'{ratio} %'
            self.tableitems[3] = f'{result}'
            font = QFont()
            font.setPointSize(16)
            for n, item in enumerate(self.tableitems):
                item = QTableWidgetItem(item)
                item.setFont(font)
                item.setTextAlignment(Qt.AlignCenter)
                self.result_table.setItem(n//2, n%2, item) 

    def prev_image(self):
        if self.idx > 0:
            self.idx -= 1
            self.show_image()
            self.show_result()
            self.update_recent_results()
        return
    
    def next_image(self):
        if len(self.image_list) > 0 and self.idx < len(self.image_list) - 1:
            self.idx += 1
            self.show_image()
            self.show_result()
            self.update_recent_results()
        else:
            QMessageBox.warning(self, ' ', '마지막 이미지입니다.')
        return

    def open_history_window(self):
        self.history_window.init_table()
        self.history_window.show()

    def open_password_window(self):
        self.password_dialog = PasswordDialog()
        self.password_dialog.correct_signal.connect(self.open_settings_window)
        self.password_dialog.show()

    def open_settings_window(self):
        self.settings_window.load_saved_values()
        self.settings_window.show()

    def open_target_window(self):
        # self.target_window.load_target_info()
        self.target_window.show()

    def draw_box(self, imgcopy, xyxy, color=(255, 255, 0), width=10):
        img_w_box = imgcopy.copy()
        if len(xyxy) > 0:
            x1, y1, x2, y2 = xyxy
            x1 -= 50
            y1 -= 50
            x2 += 50
            y2 += 50
            xyxy = [x1, y1, x2, y2]
            draw = ImageDraw.Draw(img_w_box)
            draw.rectangle(xyxy, outline=color, width=width)
        return img_w_box
    
    @pyqtSlot(str)
    def load_image(self, image_path):
        self.image_list.append(image_path)
        self.idx += 1
        self.history_window.add_image(image_path)
        self.history_window.init_table()
        if self._is_running:
            self.show_image()
            self.show_result()
            self.update_recent_results()
            time.sleep(3)

    @pyqtSlot(list)
    def save_settings(self, values):
        pt, it, ql = values
        it = round(it, 2)
        
        with open('settings.json', 'r') as json_file:
            data = json.load(json_file)
            _changed = False
            if pt != data['pixel_threshold']:
                self.history_window.add_thres_change('pixel_threshold', data['pixel_threshold'], pt)
                _changed = True
            if it != data['image_threshold']:
                self.history_window.add_thres_change('image_threshold', data['image_threshold'], it)
                _changed = True
            if ql != data['queue_length']:
                self.history_window.add_thres_change('queue_length', data['queue_length'], ql)
                _changed = True
            if not _changed:
                return
            self.history_window.init_table()
            self.wk.setPixelThreshold(pt)
            self.wk.setImageThreshold(it)
            self.wk.setQueueLength(ql)
            data['pixel_threshold'] = pt
            data['image_threshold'] = round(it, 2)
            data['queue_length'] = ql
            QMessageBox.warning(self, ' ', '변경사항이 저장되었습니다.')

        with open('settings.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print('ui) SETTINGS SAVED :)')

def pil_to_qimg(img_pil):
        img_rgb = img_pil.convert('RGB')
        data = img_rgb.tobytes('raw', 'RGB')
        qimg = QImage(data, img_rgb.size[0], img_rgb.size[1], QImage.Format_RGB888)
        return qimg