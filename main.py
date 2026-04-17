import os
import secrets
import webbrowser
from flask import Flask, request, jsonify, render_template
from core.crypto import clean_key, hash_str
from core.pipeline import process_media
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'), static_folder=os.path.join(base_dir, 'static'))
PORT = 8080
UPLOAD_FOLDER = os.path.join(base_dir, 'media_crypto_vault')
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
task_progress = {}
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/api/progress')
def get_progress():
    return jsonify({"progress": task_progress.get(request.args.get('task_id'), 0)})
@app.route('/api/process', methods=['POST'])
def process_api():
    try:
        file = request.files['file']
        action = request.form['action']
        task_id = request.form['task_id']
        task_progress[task_id] = 0
        filename = file.filename
        base_name, _ = os.path.splitext(filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        options = {
            'vid_format': request.form.get('vid_format', '.mp4'),
            'vid_codec': request.form.get('vid_codec', 'libx264'),
            'vid_bitrate': request.form.get('vid_bitrate', '3000k'),
            'vid_preset': request.form.get('vid_preset', 'medium'),
            'aud_sr': request.form.get('aud_sr', '48000'),
            'aud_codec': request.form.get('aud_codec', 'aac'),
            'aud_bitrate': request.form.get('aud_bitrate', '192k'),
        }
        out_ext = options['vid_format'] if not filename.lower().endswith(('.mp3', '.wav', '.ogg')) else request.form.get('aud_format', '.wav')
        req_w, req_h = request.form.get('resize_w'), request.form.get('resize_h')
        if req_w and req_w.isdigit(): options['target_w'] = int(req_w)
        if req_h and req_h.isdigit(): options['target_h'] = int(req_h)
        if action == "scramble":
            options.update({
                'process_video': request.form.get('enc_video') == 'true',
                'process_audio': request.form.get('enc_audio') == 'true',
                'reverse': False,
                'cols': int(request.form.get('cols', 10)),
                'rows': int(request.form.get('rows', 10))
            })
            sid = request.form.get('sid', '').strip() or secrets.token_hex(4)
            options['seed'] = hash_str(sid)
            if options['process_video'] and options['process_audio']: key = f"{options['cols']}x{options['rows']}|{sid}|a"
            elif options['process_audio']: key = "|a"
            else: key = f"{options['cols']}x{options['rows']}|{sid}"
            out_path = os.path.join(UPLOAD_FOLDER, f"locked_{base_name}{out_ext}")
            process_media(path, out_path, options, task_progress, task_id)
            return jsonify({"status": "ok", "key": key, "file": out_path})
        elif action == "unscramble":
            raw_key = clean_key(request.form.get('key'))
            options.update({'process_audio': False, 'process_video': False, 'reverse': True})
            if raw_key == "|a":
                options['process_audio'] = True
            else:
                if raw_key.endswith("|a"):
                    options['process_audio'] = True
                    raw_key = raw_key[:-2]
                options['process_video'] = True
                dim, seed_str = raw_key.split('|', 1)
                options['cols'], options['rows'] = map(int, dim.split('x'))
                options['seed'] = hash_str(seed_str)
            out_path = os.path.join(UPLOAD_FOLDER, f"restored_{base_name}{out_ext}")
            process_media(path, out_path, options, task_progress, task_id)
            return jsonify({"status": "ok", "file": out_path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
@app.route('/api/open_folder', methods=['POST'])
def open_folder():
    os.startfile(os.path.abspath(UPLOAD_FOLDER))
    return jsonify({"status": "ok"})
if __name__ == '__main__':
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    app.run(port=PORT, debug=False)
