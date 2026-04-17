const upload = document.getElementById('mediaUpload');
const encVideo = document.getElementById('encVideo');
const encAudio = document.getElementById('encAudio');
const vidSettings = document.getElementById('vidSettings');
const audSettings = document.getElementById('audSettings');
const encParams = document.getElementById('encryptionParams');
const exportSection = document.getElementById('exportSettings');
let origRatio = 1;

function updateVisibility() {
    encVideo.checked ? (vidSettings.classList.remove('hidden'), encParams.classList.remove('hidden')) : (vidSettings.classList.add('hidden'), encParams.classList.add('hidden'));
    encAudio.checked ? audSettings.classList.remove('hidden') : audSettings.classList.add('hidden');
    (!encVideo.checked && !encAudio.checked) ? exportSection.classList.add('hidden') : exportSection.classList.remove('hidden');
}

encVideo.addEventListener('change', updateVisibility);
encAudio.addEventListener('change', updateVisibility);

function setRatio(w, h) {
    origRatio = w / h;
    document.getElementById('resW').placeholder = w + " (Orig)";
    document.getElementById('resH').placeholder = h + " (Orig)";
}

document.getElementById('resW').addEventListener('input', function() {
    if (document.getElementById('aspectLock').checked && this.value) document.getElementById('resH').value = Math.round(this.value / origRatio);
});
document.getElementById('resH').addEventListener('input', function() {
    if (document.getElementById('aspectLock').checked && this.value) document.getElementById('resW').value = Math.round(this.value * origRatio);
});

upload.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    document.getElementById('fileList').innerText = files.map(f => f.name).join(', ');
    if (!files.length) return;
    
    const isAudio = files[0].name.match(/\.(mp3|wav|ogg|flac)$/i);
    encVideo.checked = !isAudio;
    document.getElementById('v_fmt').innerHTML = isAudio ? '<option value=".wav">.wav</option><option value=".mp3">.mp3</option>' : '<option value=".mp4">.mp4</option><option value=".mkv">.mkv</option><option value=".avi">.avi</option>';
    
    const url = URL.createObjectURL(files[0]);
    if (files[0].type.startsWith('image/')) {
        const img = new Image(); img.onload = () => setRatio(img.width, img.height); img.src = url;
    } else if (files[0].type.startsWith('video/')) {
        const vid = document.createElement('video'); vid.onloadedmetadata = () => setRatio(vid.videoWidth, vid.videoHeight); vid.src = url;
    }
    updateVisibility();
});

async function startBatch(action) {
    const files = upload.files;
    if (!files.length) return alert("Select files first!");
    if (action === 'scramble' && !encVideo.checked && !encAudio.checked) return alert("Select at least one encryption method!");
    
    document.getElementById('progBox').style.display = 'block';
    const keysOut = document.getElementById('keysOutput');
    keysOut.innerHTML = '';
    
    for (let i = 0; i < files.length; i++) {
        document.getElementById('progTitle').innerText = `Processing ${i+1}/${files.length}: ${files[i].name}`;
        document.getElementById('progFill').style.width = '0%';
        
        const fd = new FormData();
        fd.append('file', files[i]); fd.append('action', action); fd.append('task_id', `task_${Date.now()}`);
        fd.append('enc_video', encVideo.checked); fd.append('enc_audio', encAudio.checked);
        fd.append('cols', document.getElementById('cols').value); fd.append('rows', document.getElementById('rows').value);
        fd.append('sid', document.getElementById('sid').value); fd.append('key', document.getElementById('decKey').value);
        fd.append('vid_format', document.getElementById('v_fmt').value); fd.append('aud_format', document.getElementById('v_fmt').value);
        fd.append('vid_codec', document.getElementById('v_codec') ? document.getElementById('v_codec').value : '');
        fd.append('vid_bitrate', document.getElementById('v_bit') ? document.getElementById('v_bit').value : '');
        fd.append('aud_sr', document.getElementById('a_sr').value); fd.append('aud_codec', document.getElementById('a_codec').value);
        fd.append('aud_bitrate', document.getElementById('a_bit').value);
        
        fd.append('resize_w', document.getElementById('resW').value); fd.append('resize_h', document.getElementById('resH').value);

        const poll = setInterval(async () => {
            const res = await fetch(`/api/progress?task_id=${fd.get('task_id')}`);
            const data = await res.json();
            document.getElementById('progFill').style.width = `${data.progress}%`;
            document.getElementById('progText').innerText = `${data.progress}%`;
        }, 500);

        const res = await fetch('/api/process', { method: 'POST', body: fd });
        clearInterval(poll);
        const result = await res.json();
        
        document.getElementById('progFill').style.width = `100%`;
        document.getElementById('progText').innerText = `100%`;
        if (result.key) keysOut.innerHTML += `${files[i].name}: <b>${result.key}</b><br>`;
    }
    document.getElementById('progTitle').innerText = "All Files Processed!";
    fetch('/api/open_folder', {method: 'POST'});
}
