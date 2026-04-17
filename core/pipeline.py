import cv2
import numpy as np
import os
import subprocess
import imageio_ffmpeg
from core.crypto import seeded_shuffle
from core.audio import process_audio_file
def process_media(input_path, output_path, options, progress_dict, task_id):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    proc_vid, proc_aud, reverse = options.get('process_video'), options.get('process_audio'), options.get('reverse')
    cols, rows, seed = options.get('cols', 1), options.get('rows', 1), options.get('seed', 0)
    target_w, target_h = options.get('target_w'), options.get('target_h')
    is_image = input_path.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))
    is_audio = input_path.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a'))
    if is_image:
        img = cv2.imread(input_path)
        if target_w and target_h: img = cv2.resize(img, (target_w, target_h))
        if proc_vid:
            indices = list(range(cols * rows))
            if reverse:
                fwd = seeded_shuffle(list(range(cols*rows)), seed)
                current_indices = [0]*len(fwd)
                for i, v in enumerate(fwd): current_indices[v] = i
            else:
                current_indices = seeded_shuffle(indices, seed)
            h, w, _ = img.shape
            tw, th = w // cols, h // rows
            new_img = np.zeros_like(img)
            for i, target_idx in enumerate(current_indices):
                sc, sr = target_idx % cols, target_idx // cols
                dc, dr = i % cols, i // cols
                tile = img[sr*th:(sr+1)*th, sc*tw:(sc+1)*tw]
                new_img[dr*th:dr*th+tile.shape[0], dc*tw:dc*tw+tile.shape[1]] = tile
            img = new_img
        cv2.imwrite(output_path, img)
        progress_dict[task_id] = 100
        return
    if is_audio:
        temp_wav = input_path + "_temp.wav"
        subprocess.run([ffmpeg_exe, '-y', '-i', input_path, temp_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc_aud: process_audio_file(temp_wav, temp_wav, is_decrypt=reverse)
        progress_dict[task_id] = 50
        subprocess.run([ffmpeg_exe, '-y', '-i', temp_wav, '-c:a', options.get('aud_codec', 'aac'), '-b:a', options.get('aud_bitrate', '192k'), '-ar', options.get('aud_sr', '48000'), output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.path.exists(temp_wav): os.remove(temp_wav)
        progress_dict[task_id] = 100
        return
    temp_aud = input_path + "_aud.wav"
    has_audio = subprocess.run([ffmpeg_exe, '-y', '-i', input_path, '-vn', temp_aud], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if has_audio and not os.path.exists(temp_aud): has_audio = False
    if has_audio and proc_aud: process_audio_file(temp_aud, temp_aud, is_decrypt=reverse)
    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out_w = target_w if target_w else int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    out_h = target_h if target_h else int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    tw, th = out_w // cols, out_h // rows
    if proc_vid:
        indices = list(range(cols * rows))
        if reverse:
            fwd = seeded_shuffle(list(range(cols*rows)), seed)
            current_indices = [0]*len(fwd)
            for i, v in enumerate(fwd): current_indices[v] = i
        else: current_indices = seeded_shuffle(indices, seed)
    cmd =[ffmpeg_exe, '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-s', f'{out_w}x{out_h}', '-pix_fmt', 'bgr24', '-r', str(fps), '-i', '-']
    if has_audio: cmd.extend(['-i', temp_aud])
    cmd.extend(['-c:v', options.get('vid_codec'), '-b:v', options.get('vid_bitrate'), '-preset', options.get('vid_preset')])
    if has_audio: cmd.extend(['-c:a', options.get('aud_codec'), '-b:a', options.get('aud_bitrate'), '-ar', options.get('aud_sr')])
    else: cmd.extend(['-an'])
    cmd.append(output_path)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        if out_w != frame.shape[1] or out_h != frame.shape[0]:
            frame = cv2.resize(frame, (out_w, out_h))
        if proc_vid:
            new_frame = np.zeros_like(frame)
            for i, t_idx in enumerate(current_indices):
                sc, sr = t_idx % cols, t_idx // cols
                dc, dr = i % cols, i // cols
                tile = frame[sr*th:(sr+1)*th, sc*tw:(sc+1)*tw]
                new_frame[dr*th:dr*th+tile.shape[0], dc*tw:dc*tw+tile.shape[1]] = tile
            frame = new_frame
        proc.stdin.write(frame.tobytes())
        frame_count += 1
        if total_frames > 0 and frame_count % 5 == 0: progress_dict[task_id] = int((frame_count / total_frames) * 100)
    proc.stdin.close()
    proc.wait()
    cap.release()
    if has_audio and os.path.exists(temp_aud): os.remove(temp_aud)
    progress_dict[task_id] = 100
