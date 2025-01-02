import os
import socket
import selectors
import time
import data_proc
import threading

class NMPComm():
    def __init__(self, ip_addr, port, wk):
        self.ip_addr = ip_addr
        self.port = port
        self.Dnmp = data_proc.init_memory()
        self.worker = wk
        self.nmp_socket = None
        self.sel = selectors.DefaultSelector()
        self.stx = '\x02'
        self.etx = '\x03'
        self.last_data = ''
        self.error_cnt = 0
        self.start = 0

    def start_monitoring(self):
        t = threading.Thread(target=self.nmp_monitoring)
        t.start()
        return

    def nmp_monitoring(self):
        while True:
            try:
                self.nmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.nmp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
                # 서버가 비정상적으로 종료된 경우, 해당 포트가 일정 시간 동안 "TIME_WAIT" 상태로 남아있음. 
                # 이 상태에서 동일한 포트를 사용하려고 하면 에러가 발생. SO_REUSEADDR 옵션을 활성화해서 재사용하도록 함
                self.nmp_socket.bind((self.ip_addr, self.port))
                print(f'nmp) BOUND TO {self.ip_addr}:{self.port}')
                
                self.nmp_socket.listen()
                print(f'nmp) LISTENING FOR CONNECTION ...')

                self.sel.register(self.nmp_socket, selectors.EVENT_READ, self.accept_client)
                while True:
                    events = self.sel.select()
                    for key, _ in events:
                        callback = key.data
                        callback(key.fileobj)

            except socket.error as e:
                print(f'nmp) SOCKET ERROR : {e}. RESTARTING ...')
                time.sleep(1)
    
    def accept_client(self, server_socket) :
        client_socket, addr = server_socket.accept()
        self.client_socket = client_socket
        print(f"nmp) CONNECTION FROM: {addr}")
        self.client_socket.setblocking(False)
        self.sel.register(self.client_socket, selectors.EVENT_READ, self.communicate_message)

    def communicate_message(self, client_socket):
        try:
            data = client_socket.recv(1024)
            if data:
                print(f"nmp) RECEIVED: {data.decode()}")
                self.decode_data(data, client_socket)
            else:
                print('nmp) CLIENT DISCONNECTED')
                self.sel.unregister(client_socket)
                client_socket.close()
        except BlockingIOError:
            pass
        
        except socket.error as e:
            print(f'nmp) SOCKET ERROR WITH CLIENT: {e}. CLOSING CONNECTION')
            self.sel.unregister(client_socket)
            client_socket.close()
            self.error_cnt += 1
            print(f'nmp) NMP ERROR COUNT : {self.error_cnt}')
    
    def decode_data(self, data, client_socket):
        b_data = bytes(data)
        parsed_data = b_data.decode().split('|') # 
        start_code = parsed_data[0][-1] # [0] : \x02  [-1] : start_code
        status_code = parsed_data[4]
        # N|M2209|20241002095707|T|ZZ1
        if start_code == 'N':
            status_code = status_code[:-1]
            if status_code == 'ZZ1':
                print('nmp) COMMUNICATION CHECK')
                self.comm_check(parsed_data, client_socket)
        elif start_code == 'T':
            self.response_data(parsed_data, client_socket)
            if status_code == 'REQ':
                self.reply_REQ(client_socket)

        else: # R
            if status_code == 'VR1':
                self.Dnmp = data_proc.init_memory()
                self.worker.img = None
                self.mark = ''
                print('-- INIT MEMORY --')
                data_proc.print_Dnmp(self.Dnmp)
            pass
    
    def comm_check(self, parsed_data, client_socket):
        parsed_data[4] = 'ZZ9' + self.etx
        parsed_data[2] = data_proc.get_datetime()
        send_data = '|'.join(parsed_data)
        print(f'nmp) SEND : {send_data}')
        client_socket.sendall(send_data.encode('ascii'))
        self.last_data = send_data.encode('ascii')
        return 
    
    def response_data(self, parsed_data, client_socket):
        self.Dnmp['machine_code'] = parsed_data[1]
        self.Dnmp['summer_time'] = parsed_data[3]
        self.Dnmp['barcode_num'] = parsed_data[6]
        self.Dnmp['tire_spec'] = parsed_data[8]
        self.Dnmp['marking_type'] = parsed_data[10]
        self.Dnmp['inspection_code'] = parsed_data[11]
        print('-- SET DNMP --')
        data_proc.print_Dnmp(self.Dnmp)

        parsed_data[0] = parsed_data[0].replace('T','R')
        parsed_data[2] = data_proc.get_datetime()
        send_data = '|'.join(parsed_data)
        print(f'nmp) SEND : {send_data}')
        client_socket.sendall(send_data.encode('ascii'))
        self.last_data = send_data.encode('ascii')
        return

    # T|M2209|20240924155628|T|VI9||1698747598||KT11R22.5    16DM04 LB-HK  ||A|3509|
    # T|M2209|20240924155628|T|VR1||1698747598||1||\03
    def reply_REQ(self, client_socket):
        client_socket.sendall(self.last_data)
        return

    def reply_markResult(self, result, client_socket):
        signal = 1
        if result == 'OK':
            signal = 1
        elif result == 'NG':
            signal = 2
        else:
            signal = 0

        print(f'result : {result} / signal : {signal}')

        rxbuffer = ['T', self.Dnmp['machine_code'], data_proc.get_datetime(), self.Dnmp['summer_time'], 
                    'VR1', '', self.Dnmp['barcode_num'], '', str(signal), '']
        str_rxbuf = '|'.join(rxbuffer)
        send_data = self.stx + str_rxbuf + self.etx

        client_socket.sendall(send_data.encode('ascii'))
        print(f'SEND : {send_data}')
        self.last_data = send_data.encode('ascii')
        print('-- SEND TO NMP --')

    # def check_and_execute(self, count):
    #     if len(self.results_deque) == count and all(result == 'NG' for result in self.results_deque):
    #         print(f"Message 'NG' occurred 5 times consecutively. Executing specific function.")
    #         # Output 호출
    #         #self.Put_Out_value()
    #         return True
    #     else :
    #         return False

    # def initialize_serial(self, port, baudrate):
    #     try:
    #         ser = serial.Serial(port, baudrate, timeout=1000, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
    #         print(f"Serial port {port} opened successfully")
    #         return ser
    #     except serial.SerialException as e:
    #         print(f"Failed to open serial port {port}: {e}")
    #         return None

    # def send_command(self, ser, command):
    #     try:
    #         if ser.is_open:
    #             ser.write(command)
    #             print(f"Sent command: {command}")
    #             time.sleep(1)  # 데이터 전송 후 지연 시간
    #         else:
    #             print("Serial port is not open")
    #     except Exception as e:
    #         print(f"Error sending command: {e}")

    # def receive_data(self, ser):
    #     try:
    #         if ser.is_open:
    #             response = ser.read(3)  # 3바이트 데이터 수신
    #             print(f"Received data: {response}")
    #             return response
    #         else:
    #             print("Serial port is not open")
    #             return None
    #     except Exception as e:
    #         print(f"Error receiving data: {e}")
    #         return None

    # def Put_Out_value(self):
    #     port = 'COM1'  # 실제 사용하는 시리얼 포트로 변경
    #     baudrate = 115200  # PLC와 일치하는 보드레이트로 설정

    #     ser = self.initialize_serial(port, baudrate)
    #     if ser is None:
    #         return

    #     time.sleep(2)  # 시리얼 포트 초기화 대기

    #     try:
    #         # DO 1번 포트를 ON하는 명령어 전송
    #         command_on = bytearray([0x04, 0x02, 0x01])
    #         self.send_command(ser, command_on)

    #         time.sleep(6)
    #         # 필요한 경우 DO 1번 포트를 OFF하는 명령어 추가
    #         command_off = bytearray([0x04, 0x02, 0x00])
    #         self.send_command(ser, command_off)


    #     finally:
    #         ser.close()
    #         self.consecutive_ng_count = 0
    #         print("Serial port closed")








