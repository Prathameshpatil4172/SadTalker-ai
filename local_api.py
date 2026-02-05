"""
Local API Server for SadTalker AI

This Flask API server runs on your local laptop with GPU,
exposed to the internet via ngrok for the Vercel frontend to access.

Features:
- Job queue management via Supabase
- File upload/download handling
- Real-time progress updates via SSE
- GPU-accelerated video generation
"""

import os
import sys
import json
import uuid
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for SadTalker
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Initialize Flask app
app = Flask(__name__)

# Configure CORS - allow requests from Vercel frontend
frontend_url = os.getenv('FRONTEND_URL', '*')
CORS(app, resources={
    r"/api/*": {
        "origins": frontend_url if frontend_url != '*' else "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Secret"]
    }
})

# Configuration
UPLOAD_DIR = os.getenv('UPLOAD_DIR', 'uploads')
RESULT_DIR = os.getenv('RESULT_DIR', 'static/results')
CHECKPOINT_PATH = os.getenv('CHECKPOINT_PATH', 'checkpoints')
CONFIG_PATH = os.getenv('CONFIG_PATH', 'src/config')
API_SECRET = os.getenv('API_SECRET', 'default-secret-change-this')

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Global state
processing_status = {}  # job_id -> {progress, message, status}
active_jobs = {}  # job_id -> thread
sadtalker = None  # Will be initialized on first use

# Import Supabase client
try:
    from supabase import create_client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if supabase_url and supabase_key:
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Supabase client initialized")
    else:
        supabase = None
        print("⚠️ Supabase not configured - running in standalone mode")
except ImportError:
    supabase = None
    print("⚠️ Supabase package not installed - running in standalone mode")


def require_api_secret(f):
    """Decorator to require API secret for protected endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        secret = request.headers.get('X-API-Secret') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if secret != API_SECRET:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


def init_sadtalker():
    """Initialize SadTalker model (lazy loading)."""
    global sadtalker
    if sadtalker is None:
        print("🔄 Initializing SadTalker model...")
        try:
            from gradio_demo import SadTalker
            sadtalker = SadTalker(CHECKPOINT_PATH, CONFIG_PATH, lazy_load=True)
            print("✅ SadTalker model initialized")
        except Exception as e:
            print(f"❌ Failed to initialize SadTalker: {e}")
            raise
    return sadtalker


def generate_video_task(job_id, img_path, aud_path, config):
    """Background task for video generation."""
    try:
        # Update status to processing
        processing_status[job_id] = {
            "progress": 0,
            "message": "Initializing...",
            "status": "processing"
        }
        
        # Update Supabase if available
        if supabase:
            supabase.table('jobs').update({
                'status': 'processing',
                'started_at': datetime.utcnow().isoformat()
            }).eq('id', job_id).execute()
        
        # Progress callback
        def progress_callback(progress, message):
            processing_status[job_id] = {
                "progress": progress,
                "message": message,
                "status": "processing"
            }
        
        # Simulate progress updates
        def progress_simulator():
            stages = [
                (0, 20, "Initializing and Preprocessing...", 2),
                (20, 50, "Generating Face Animation...", 1),
                (50, 80, "Rendering Video Frames...", 0.5),
                (80, 95, "Finalizing Video...", 0.2),
            ]
            
            for start, end, msg, increment in stages:
                current = start
                while current < end and processing_status.get(job_id, {}).get('status') == 'processing':
                    current = min(current + increment, end)
                    progress_callback(round(current, 1), msg)
                    time.sleep(0.5)
        
        # Start progress simulator
        sim_thread = threading.Thread(target=progress_simulator)
        sim_thread.start()
        
        # Initialize SadTalker and generate video
        model = init_sadtalker()
        
        video_path = model.test(
            source_image=img_path,
            driven_audio=aud_path,
            preprocess=config.get('preprocess', 'crop'),
            still_mode=config.get('still_mode', False),
            use_enhancer=config.get('use_enhancer', False),
            batch_size=config.get('batch_size', 2),
            size=config.get('size', 256),
            pose_style=config.get('pose_style', 0),
            exp_scale=config.get('exp_scale', 1.0),
            use_ref_video=config.get('use_ref_video', False),
            ref_video=config.get('ref_video'),
            ref_info=config.get('ref_info', 'pose'),
            use_idle_mode=config.get('use_idle_mode', False),
            length_of_audio=config.get('length_of_audio', 0),
            use_blink=config.get('use_blink', True)
        )
        
        # Stop progress simulator
        sim_thread.join()
        
        # Copy result to results directory
        result_filename = f"{job_id}.mp4"
        result_path = os.path.join(RESULT_DIR, result_filename)
        shutil.copy(video_path, result_path)
        
        # Update status to completed
        processing_status[job_id] = {
            "progress": 100,
            "message": "Complete",
            "status": "completed",
            "result_url": f"/api/v1/jobs/{job_id}/download"
        }
        
        # Update Supabase if available
        if supabase:
            # Upload to Supabase storage
            with open(result_path, 'rb') as f:
                supabase.storage.from_('results').upload(
                    f"{job_id}.mp4",
                    f,
                    file_options={'content-type': 'video/mp4'}
                )
            
            # Get public URL
            result_url = supabase.storage.from_('results').get_public_url(f"{job_id}.mp4")
            
            supabase.table('jobs').update({
                'status': 'completed',
                'result_url': result_url,
                'completed_at': datetime.utcnow().isoformat(),
                'progress': 100
            }).eq('id', job_id).execute()
        
        print(f"✅ Job {job_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Job {job_id} failed: {error_msg}")
        
        processing_status[job_id] = {
            "progress": 0,
            "message": f"Error: {error_msg}",
            "status": "failed",
            "error": error_msg
        }
        
        # Update Supabase if available
        if supabase:
            supabase.table('jobs').update({
                'status': 'failed',
                'error_message': error_msg,
                'completed_at': datetime.utcnow().isoformat()
            }).eq('id', job_id).execute()
    
    finally:
        # Cleanup upload files
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
            if aud_path and os.path.exists(aud_path):
                os.remove(aud_path)
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


# ============================================
# API Routes
# ============================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "gpu_available": torch.cuda.is_available() if 'torch' in sys.modules else False,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/api/v1/jobs', methods=['POST'])
def create_job():
    """Create a new video generation job."""
    try:
        # Check if files are provided
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No image file provided"}), 400
        
        image_file = request.files['image']
        audio_file = request.files.get('audio')
        
        if image_file.filename == '':
            return jsonify({"success": False, "error": "No image selected"}), 400
        
        # Get configuration
        config = {
            'preprocess': request.form.get('preprocess', 'crop'),
            'still_mode': request.form.get('still_mode', 'false').lower() == 'true',
            'use_enhancer': request.form.get('use_enhancer', 'false').lower() == 'true',
            'batch_size': int(request.form.get('batch_size', 2)),
            'size': int(request.form.get('size', 256)),
            'pose_style': int(request.form.get('pose_style', 0)),
            'exp_scale': float(request.form.get('exp_scale', 1.0)),
            'use_ref_video': request.form.get('use_ref_video', 'false').lower() == 'true',
            'ref_video': request.form.get('ref_video'),
            'ref_info': request.form.get('ref_info', 'pose'),
            'use_idle_mode': request.form.get('use_idle_mode', 'false').lower() == 'true',
            'length_of_audio': int(request.form.get('length_of_audio', 0)),
            'use_blink': request.form.get('use_blink', 'true').lower() == 'true'
        }
        
        # Validate idle mode or audio
        if not audio_file and not config['use_idle_mode'] and not config['use_ref_video']:
            return jsonify({
                "success": False,
                "error": "Please provide audio, enable idle mode, or use reference video"
            }), 400
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Save uploaded files
        img_ext = os.path.splitext(image_file.filename)[1]
        img_path = os.path.join(UPLOAD_DIR, f"{job_id}_image{img_ext}")
        image_file.save(img_path)
        
        aud_path = None
        if audio_file and audio_file.filename:
            aud_ext = os.path.splitext(audio_file.filename)[1]
            aud_path = os.path.join(UPLOAD_DIR, f"{job_id}_audio{aud_ext}")
            audio_file.save(aud_path)
        
        # Create job in Supabase if available
        if supabase:
            job_data = {
                'id': job_id,
                'status': 'pending',
                'config': config,
                'input_image': img_path,
                'input_audio': aud_path,
                'created_at': datetime.utcnow().isoformat(),
                'progress': 0
            }
            supabase.table('jobs').insert(job_data).execute()
        
        # Initialize status
        processing_status[job_id] = {
            "progress": 0,
            "message": "Queued",
            "status": "pending"
        }
        
        # Start background processing
        thread = threading.Thread(
            target=generate_video_task,
            args=(job_id, img_path, aud_path, config)
        )
        thread.start()
        active_jobs[job_id] = thread
        
        return jsonify({
            "success": True,
            "data": {
                "job_id": job_id,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "estimated_time": 120
            }
        }), 201
        
    except Exception as e:
        print(f"Error creating job: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the status of a job."""
    try:
        # First check local status
        if job_id in processing_status:
            status = processing_status[job_id]
            return jsonify({
                "success": True,
                "data": {
                    "job_id": job_id,
                    **status
                }
            })
        
        # Check Supabase if available
        if supabase:
            result = supabase.table('jobs').select('*').eq('id', job_id).execute()
            if result.data:
                job = result.data[0]
                return jsonify({
                    "success": True,
                    "data": {
                        "job_id": job_id,
                        "status": job.get('status'),
                        "progress": job.get('progress', 0),
                        "result_url": job.get('result_url'),
                        "error": job.get('error_message')
                    }
                })
        
        return jsonify({"success": False, "error": "Job not found"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/jobs/<job_id>/download', methods=['GET'])
def download_result(job_id):
    """Download the generated video."""
    try:
        result_path = os.path.join(RESULT_DIR, f"{job_id}.mp4")
        
        if os.path.exists(result_path):
            return send_from_directory(
                RESULT_DIR,
                f"{job_id}.mp4",
                as_attachment=True,
                download_name=f"sadtalker_{job_id}.mp4"
            )
        
        # If not found locally, try Supabase
        if supabase:
            result = supabase.table('jobs').select('result_url').eq('id', job_id).execute()
            if result.data and result.data[0].get('result_url'):
                return jsonify({
                    "success": True,
                    "data": {
                        "download_url": result.data[0]['result_url']
                    }
                })
        
        return jsonify({"success": False, "error": "Result not found"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/jobs/<job_id>/stream', methods=['GET'])
def stream_progress(job_id):
    """Stream progress updates via Server-Sent Events."""
    def event_stream():
        while True:
            status = processing_status.get(job_id, {})
            
            # Check if file exists as fallback
            if not status:
                result_path = os.path.join(RESULT_DIR, f"{job_id}.mp4")
                if os.path.exists(result_path):
                    status = {"progress": 100, "message": "Complete", "status": "completed"}
                else:
                    status = {"progress": 0, "message": "Waiting...", "status": "pending"}
            
            yield f"data: {json.dumps(status)}\n\n"
            
            # Stop if completed or failed
            if status.get('status') in ['completed', 'failed']:
                break
            
            time.sleep(1)
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/v1/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (admin endpoint)."""
    try:
        if supabase:
            result = supabase.table('jobs').select('*').order('created_at', desc=True).limit(50).execute()
            return jsonify({
                "success": True,
                "data": result.data
            })
        else:
            # Return local jobs
            jobs = [
                {"job_id": k, **v}
                for k, v in processing_status.items()
            ]
            return jsonify({
                "success": True,
                "data": jobs
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/v1/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id):
    """Cancel a pending or processing job."""
    try:
        if job_id in active_jobs:
            # Note: Thread cancellation is complex in Python
            # This is a simplified version
            processing_status[job_id] = {
                "progress": 0,
                "message": "Cancelled",
                "status": "cancelled"
            }
        
        if supabase:
            supabase.table('jobs').update({
                'status': 'cancelled',
                'completed_at': datetime.utcnow().isoformat()
            }).eq('id', job_id).execute()
        
        return jsonify({
            "success": True,
            "message": "Job cancelled"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# Main Entry Point
# ============================================

if __name__ == '__main__':
    import torch
    
    # Check GPU availability
    if torch.cuda.is_available():
        print(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("⚠️ No GPU detected - processing will be slow!")
    
    # Print configuration
    print(f"\n🚀 Starting Local API Server")
    print(f"   Port: {os.getenv('FLASK_PORT', 5000)}")
    print(f"   Upload Dir: {UPLOAD_DIR}")
    print(f"   Result Dir: {RESULT_DIR}")
    print(f"   Supabase: {'Connected' if supabase else 'Not configured'}")
    print(f"   Frontend: {frontend_url}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        threaded=True
    )
