import cv2
import numpy as np
import os
import subprocess
import imageio_ffmpeg
def clean_key(raw_key):
    if not raw_key: return ""
    return raw_key.replace("KEY:", "").replace(" ", "").strip()
def hash_str(s):
    h = 5381
    for c in s:
        h = (h * 33 + ord(c)) & 0xFFFFFFFF
    return h
def seeded_shuffle(arr, seed):
    rng_state = seed & 0xFFFFFFFF
    for i in range(len(arr) - 1, 0, -1):
        rng_state = (rng_state * 1103515245 + 12345) & 0xFFFFFFFF
        r = rng_state % (i + 1)
        arr[i], arr[r] = arr[r], arr[i]
    return arr
def process_visual(input_path, output_path, cols, rows, indices, is_video=True, reverse=False, target_w=None, target_h=None):
    current_indices = indices
    if reverse:
        rev_indices = [0] * len(indices)
        for i, val in enumerate(indices):
            rev_indices[val] = i
        current_indices = rev_indices
    if is_video:
        temp_output = output_path + ".temp.mp4"
        cap = cv2.VideoCapture(input_path)
        orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or np.isnan(fps): fps = 30.0
        out_w = target_w if target_w else orig_w
        out_h = target_h if target_h else orig_h
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_output, fourcc, fps, (out_w, out_h))
        tw, th = out_w // cols, out_h // rows
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            if target_w and target_h:
                frame = cv2.resize(frame, (out_w, out_h))
            new_frame = np.zeros_like(frame)
            for i, target_idx in enumerate(current_indices):
                src_col, src_row = target_idx % cols, target_idx // cols
                dst_col, dst_row = i % cols, i // cols
                tile = frame[src_row*th:(src_row+1)*th, src_col*tw:(src_col+1)*tw]
                h, w, _ = tile.shape
                new_frame[dst_row*th:dst_row*th+h, dst_col*tw:dst_col*tw+w] = tile
            out.write(new_frame)
        cap.release()
        out.release()
        try:
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            command =[
                ffmpeg_path, '-y',
                '-i', temp_output,   
                '-i', input_path,    
                '-c:v', 'copy',      
                '-map', '0:v:0',     
                '-map', '1:a:0?',    
                '-c:a', 'aac',       
                '-shortest',         
                output_path
            ]
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            os.remove(temp_output)
        except Exception as e:
            if os.path.exists(temp_output):
                if os.path.exists(output_path): os.remove(output_path)
                os.rename(temp_output, output_path)
    else:
        img = cv2.imread(input_path)
        if img is None: raise ValueError("Invalid image.")
        if target_w and target_h:
            img = cv2.resize(img, (target_w, target_h))
        height, width, _ = img.shape
        tw, th = width // cols, height // rows
        new_img = np.zeros_like(img)
        for i, target_idx in enumerate(current_indices):
            src_col, src_row = target_idx % cols, target_idx // cols
            dst_col, dst_row = i % cols, i // cols
            tile = img[src_row*th:(src_row+1)*th, src_col*tw:(src_col+1)*tw]
            h, w, _ = tile.shape
            new_img[dst_row*th:dst_row*th+h, dst_col*tw:dst_col*tw+w] = tile
        cv2.imwrite(output_path, new_img)
