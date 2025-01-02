import logging
from logging.handlers import TimedRotatingFileHandler
import os

class LogSave():
    def __init__(self, dir, logname):
        self.dir = os.path.join(dir)
        self.logname = logname
        os.makedirs(self.dir, exist_ok=True)

        self.logger = logging.getLogger(logname)  # 여기서 로거 이름을 logname으로 설정
        self.logger.setLevel(logging.INFO)

        log_path = os.path.join(self.dir, self.logname+'.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        timedfilehandler = logging.handlers.TimedRotatingFileHandler(filename=log_path, when='midnight', interval=1, encoding='utf-8')
        timedfilehandler.setFormatter(formatter)
        timedfilehandler.suffix = "%Y%m%d"
        self.logger.addHandler(timedfilehandler)

    def LogTextOut(self,  msg):
        self.logger.info(str(msg))
        
class AWSLog():
    def __init__(self, dir, logname):
        self.dir = os.path.join(dir)
        self.logname = logname
        os.makedirs(self.dir, exist_ok=True)

        self.logger = logging.getLogger(logname)  # 여기서 로거 이름을 logname으로 설정
        self.logger.setLevel(logging.INFO)

        log_path = os.path.join(self.dir, self.logname+'.log')
        log_format = '%(asctime)s [%(levelname)s]: %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        handler = logging.FileHandler(filename=log_path, encoding='utf-8')
        handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        self.logger.addHandler(handler)
        self.log_path = log_path

    def LogTextOut(self,  msg):
        if os.path.exists(self.log_path):
            with open(self.log_path, 'r+', encoding='utf-8') as file:
                lines = file.readlines()
                if len(lines) >= 10:
                    file.seek(0)
                    file.truncate()
                    file.writelines(lines[-9:])
        self.logger.info(str(msg))

class ResultLog():
    def __init__(self, dir, logname):
        self.dir = os.path.join(dir)
        self.logname = logname
        os.makedirs(self.dir, exist_ok=True)

        self.logger = logging.getLogger(logname)  # 여기서 로거 이름을 logname으로 설정
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        log_path = os.path.join(self.dir, self.logname+'.log')
        log_format = '%(asctime)s [%(levelname)s]: %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        handler = logging.FileHandler(filename=log_path, encoding='utf-8')
        handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
        self.logger.addHandler(handler)
        self.log_path = log_path

    def LogTextOut(self,  msg):
        self.logger.info(msg)