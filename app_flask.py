import os
import shutil
import subprocess
import threading
import uuid
import json
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, send_from_directory
from src.gradio_demo import SadTalker

app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

UPLOAD_DIR = "uploads"
RESULT_DIR = "static/results"
PREVIEW_DIR = "static/previews"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

# Initialize SadTalker once when the app starts
sadtalker = SadTalker("checkpoints", "src/config", lazy_load=True)

# Global dictionary to store processing status: {video_filename: {progress: int, message: str}}
processing_status = {}

def generate_video_background(img_path, aud_path, preprocess, still_mode, use_enhancer, batch_size, size, pose_style, exp_scale, use_ref_video, ref_vid_path, ref_info, use_idle_mode, length_of_audio, use_blink, final_name):
    # Event to control the progress simulator
    stop_event = threading.Event()

    def progress_simulator():
        current_progress = 0
        while not stop_event.is_set():
            if current_progress < 20:
                current_progress += 2
                msg = "Initializing and Preprocessing..."
            elif current_progress < 50:
                current_progress += 1
                msg = "Generating Face Animation..."
            elif current_progress < 80:
                current_progress += 0.5
                msg = "Rendering Video Frames..."
            elif current_progress < 95:
                current_progress += 0.2
                msg = "Finalizing Video..."
            
            # Update status
            processing_status[final_name] = {
                "progress": round(current_progress, 1),
                "message": msg
            }
            time.sleep(0.5)

    try:
        # Start the simulator
        sim_thread = threading.Thread(target=progress_simulator)
        sim_thread.start()
        
        video_path = sadtalker.test(
            source_image=img_path,
            driven_audio=aud_path,
            preprocess=preprocess,
            still_mode=still_mode,
            use_enhancer=use_enhancer,
            batch_size=batch_size,
            size=size,
            pose_style=pose_style,
            exp_scale=exp_scale,
            use_ref_video=use_ref_video,
            ref_video=ref_vid_path,
            ref_info=ref_info,
            use_idle_mode=use_idle_mode,
            length_of_audio=length_of_audio,
            use_blink=use_blink
        )
        
        # Stop simulator once done
        stop_event.set()
        sim_thread.join()
        
        processing_status[final_name] = {"progress": 98, "message": "Saving result..."}
        
        # Copy result into static folder so it can be served
        final_path = os.path.join(RESULT_DIR, final_name)
        shutil.copy(video_path, final_path)
        processing_status[final_name] = {"progress": 100, "message": "Complete"}
    except Exception as e:
        stop_event.set()
        print(f"Error generating video: {e}")
        processing_status[final_name] = {"progress": -1, "message": f"Error: {str(e)}"}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 1. Handle Source Image (Required)
        if 'image' not in request.files:
            return redirect(request.url)
        image = request.files["image"]
        if image.filename == '':
            return redirect(request.url)
        img_path = os.path.join(UPLOAD_DIR, image.filename)
        image.save(img_path)

        # 2. Handle Audio (Optional if Idle Mode is on)
        aud_path = None
        if 'audio' in request.files:
            audio = request.files["audio"]
            if audio.filename != '':
                aud_path = os.path.join(UPLOAD_DIR, audio.filename)
                audio.save(aud_path)

        # 3. Handle Reference Video (Optional)
        ref_vid_path = None
        if 'ref_video' in request.files:
            ref_video = request.files["ref_video"]
            if ref_video.filename != '':
                ref_vid_path = os.path.join(UPLOAD_DIR, ref_video.filename)
                ref_video.save(ref_vid_path)

        # 4. Get Form Settings
        preprocess = request.form.get("preprocess", "crop")
        still_mode = "still_mode" in request.form
        use_enhancer = "enhancer" in request.form
        batch_size = int(request.form.get("batch_size", 1))
        size = int(request.form.get("size", 256))
        pose_style = int(request.form.get("pose_style", 0))
        exp_scale = float(request.form.get("exp_scale", 1.0))
        
        use_idle_mode = "use_idle_mode" in request.form
        length_of_audio = int(request.form.get("length_of_audio", 5))
        use_blink = "use_blink" in request.form
        
        use_ref_video = "use_ref_video" in request.form
        ref_info = request.form.get("ref_info", "pose")

        # Basic Validation
        if not aud_path and not use_idle_mode and not (use_ref_video and ref_vid_path):
            return "Error: Please upload audio, enable idle mode, or provide a reference video.", 400

        # Generate a unique filename for the result
        final_name = f"{uuid.uuid4()}.mp4"

        # Start background generation
        thread = threading.Thread(target=generate_video_background, args=(
            img_path, aud_path, preprocess, still_mode, use_enhancer, batch_size, size, pose_style, exp_scale,
            use_ref_video, ref_vid_path, ref_info, use_idle_mode, length_of_audio, use_blink, final_name
        ))
        thread.start()

        return redirect(url_for("result", video=final_name))

    return render_template("unified.html")

@app.route("/result/<video>")
def result(video):
    return render_template("unified.html", video=video)

@app.route("/stream/<video>")
def stream(video):
    def event_stream():
        while True:
            # Check in-memory status or file existence (fallback)
            if video in processing_status:
                status = processing_status[video]
            elif os.path.exists(os.path.join(RESULT_DIR, video)):
                status = {"progress": 100, "message": "Complete"}
            else:
                status = {"progress": 0, "message": "Waiting..."}
            
            # Yield data in SSE format
            yield f"data: {json.dumps(status)}\n\n"
            
            if status["progress"] >= 100 or status["progress"] < 0:
                break
            time.sleep(1) # Send update every second
    return Response(event_stream(), mimetype="text/event-stream")

def convert_for_preview(video_path):
    """Converts a video to a browser-friendly format (H.264/AAC) for preview."""
    filename = os.path.basename(video_path)
    # Create a unique preview name
    preview_filename = os.path.splitext(filename)[0] + "_preview.mp4"
    preview_path = os.path.join(PREVIEW_DIR, preview_filename)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "baseline",
        "-level", "3.0",
        "-movflags", "+faststart",
        "-c:a", "aac",
        preview_path
    ]
    # Run ffmpeg silently
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return preview_filename

@app.route("/upload_preview", methods=["POST"])
def upload_preview():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(temp_path)
    
    preview_filename = convert_for_preview(temp_path)
    return jsonify({"url": url_for('static', filename=f'previews/{preview_filename}')})

@app.route("/history")
def history():
    files = []
    if os.path.exists(RESULT_DIR):
        files = [f for f in os.listdir(RESULT_DIR) if f.endswith(('.mp4', '.webm'))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(RESULT_DIR, x)), reverse=True)
    return jsonify(files)

# Serve example files
@app.route('/static/examples/<path:filename>')
def serve_examples(filename):
    return send_from_directory('examples', filename)

if __name__ == "__main__":
    print("Launching Flask app on http://127.0.0.1:7860")
    app.run(host="127.0.0.1", port=7860, debug=True)