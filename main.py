import os
import sys
import webbrowser
import secrets
from flask import Flask, request, render_template
from processor import process_visual, clean_key, hash_str, seeded_shuffle
if '__compiled__' in globals():
    base_dir = os.path.dirname(os.path.abspath(__file__))
else:
    base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')
app = Flask(__name__, template_folder=template_dir)
PORT = 8080
EXECUTION_DIR = os.getcwd() 
UPLOAD_FOLDER = os.path.join(EXECUTION_DIR, 'scrambler_vault')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.ts')
@app.route('/', methods=['GET', 'POST'])
def index():
    generated_key = None
    error_msg = None
    cols = request.form.get('cols', '10')
    rows = request.form.get('rows', '10')
    sid = request.form.get('sid', '').strip()
    resize_w = request.form.get('resize_w', '')
    resize_h = request.form.get('resize_h', '')
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            file = request.files.get('file')
            if file and file.filename:
                filename = file.filename
                base_name, ext = os.path.splitext(filename)
                is_video = filename.lower().endswith(VIDEO_EXTENSIONS)
                path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(path)
                target_w = int(resize_w) if resize_w and resize_w.strip().isdigit() else None
                target_h = int(resize_h) if resize_h and resize_h.strip().isdigit() else None
                if action == "scramble":
                    cols_int = int(cols)
                    rows_int = int(rows)
                    if not sid:
                        sid = secrets.token_hex(4) # Generates an 8-character hex string
                    hash_val = hash_str(sid)
                    indices = list(range(cols_int * rows_int))
                    seeded_shuffle(indices, hash_val)
                    generated_key = f"{cols_int}x{rows_int}|{sid}"
                    out_name = f"locked_{base_name}.mp4" if is_video else f"locked_{filename}"
                    out_path = os.path.join(UPLOAD_FOLDER, out_name)
                    process_visual(path, out_path, cols_int, rows_int, indices, is_video=is_video, target_w=target_w, target_h=target_h)
                    os.startfile(os.path.abspath(UPLOAD_FOLDER))
                elif action == "unscramble":
                    raw_key = clean_key(request.form.get('key'))
                    dim, seed_str = raw_key.split('|', 1)
                    k_cols, k_rows = map(int, dim.split('x'))
                    hash_val = hash_str(seed_str)
                    indices = list(range(k_cols * k_rows))
                    seeded_shuffle(indices, hash_val)
                    out_name = f"restored_{base_name}.mp4" if is_video else f"restored_{filename}"
                    out_path = os.path.join(UPLOAD_FOLDER, out_name)
                    process_visual(path, out_path, k_cols, k_rows, indices, is_video=is_video, reverse=True, target_w=target_w, target_h=target_h)
                    os.startfile(os.path.abspath(UPLOAD_FOLDER))
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
    return render_template('index.html', 
                           key=generated_key, error=error_msg, 
                           cols=cols, rows=rows, sid=sid, 
                           resize_w=resize_w, resize_h=resize_h)
if __name__ == '__main__':
    try:
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        app.run(port=PORT, debug=False)
    except Exception as e:
        print(f"CRASH LOG: {e}")
        input("Press Enter to exit...")
