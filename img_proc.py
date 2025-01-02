import os
from PIL import Image

def save_img(save_path, img_path, img):
    if not os.path.exists(save_path):
        os.makedirs(save_path, exist_ok=True)
    img.save(os.path.join(save_path, img_path))