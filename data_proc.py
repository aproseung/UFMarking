from datetime import datetime
from collections import Counter
import torch

def init_memory():
    Dnmp = {}

    Dnmp['machine_code'] = ''
    Dnmp['summer_time'] = ''
    Dnmp['barcode_num'] = ''
    Dnmp['tire_spec'] = ''
    Dnmp['marking_type'] = ''
    Dnmp['inspection_code'] = ''

    return Dnmp

def print_Dnmp(Dnmp):
    print(f'data_proc) ======== SPEC INFO ========')
    print(f"           MACHINE CODE : {Dnmp['machine_code']}")
    print(f"           BARCODE NUM : {Dnmp['barcode_num']}")
    print(f"           TIRE SPEC : {Dnmp['tire_spec']}")
    print(f"           MARKING TYPE : {Dnmp['marking_type']}")
    print(f"           INSPECTION CODE : {Dnmp['inspection_code']}")
    print(f'           ===========================')
    return 

def get_date():
    d = datetime.now()
    str_d = d.strftime('%Y%m%d')
    return str_d

def get_datetime():
    dt = datetime.now()
    str_dt = dt.strftime('%Y%m%d%H%M%S')
    return str_dt


