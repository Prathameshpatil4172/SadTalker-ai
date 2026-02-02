"""
SadTalker AI - GPU Runner for Google Colab / Lightning AI
This script runs on GPU instances and processes video generation jobs.
"""

import os
import sys
import time
import json
import hmac
import hashlib
import requests
import tempfile
import threading
from datetime import datetime
from pathlib import Path

# Configuration (set these as environment variables or modify below)
API_BASE_URL = os.environ.get("API_BASE_URL", "https://your-api.onrender.com/api/v1")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "your-webhook-secret")
RUNNER_ID = os.environ.get("RUNNER_ID", "colab-runner-1")
RUNNER_TYPE = os.environ.get("RUNNER_TYPE", "colab")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))

# SadTalker paths
CHECKPOINT_PATH = "/content/checkpoints"
CONFIG_PATH = "/content/src/config"


class APIClient:
    """Client for communicating with the API server."""
    
    def __init__(self, base_url, webhook_secret):
        self.base_url = base_url
        self.webhook_secret = webhook_secret
    
    def _sign_payload(self, payload):
        """Sign payload with webhook secret."""
        return hmac.new(
            self.webhook_secret.encode(),
            json.dumps(payload, sort_keys=True).encode(),
            hashlib.sha256
        ).hexdigest()
    
    def get_pending_jobs(self):
        """Fetch pending jobs from API."""
        try:
            response = requests.get(
                f"{self.base_url}/jobs/pending",
                headers={"X-Runner-ID": RUNNER_ID},
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception as e:
            print(f"❌ Error fetching jobs: {e}")
            return []
    
    def update_job_status(self, job_id, status, progress=None, message=None, 
                         result_url=None, error_message=None):
        """Update job status via webhook."""
        payload = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            "result_url": result_url,
            "error_message": error_message
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Secret": self._sign_payload(payload)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhooks/job-update",
                json=payload,
                headers=headers,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error updating job: {e}")
            return False
    
    def send_heartbeat(self, status, current_job_id=None):
        """Send heartbeat to API."""
        payload = {
            "runner_id": RUNNER_ID,
            "runner_type": RUNNER_TYPE,
            "status": status,
            "current_job_id": current_job_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Secret": self._sign_payload(payload)
        }
        
        try:
            requests.post(
                f"{self.base_url}/webhooks/runner-heartbeat",
                json=payload,
                headers=headers,
                timeout=10
            )
        except:
            pass


class JobProcessor:
    """Processes video generation jobs using SadTalker."""
    
    def __init__(self, api_client):
        self.api = api_client
        self.sadtalker = None
        self.current_job = None
        self.stop_event = threading.Event()
    
    def initialize_sadtalker(self):
        """Initialize SadTalker model."""
        try:
            sys.path.append('/content/SadTalker-ai')
            from src.gradio_demo import SadTalker
            import torch
            
            print("🔄 Initializing SadTalker...")
            self.sadtalker = SadTalker(CHECKPOINT_PATH, CONFIG_PATH, lazy_load=True)
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"✅ SadTalker initialized on {device}")
            if device == "cuda":
                print(f"   GPU: {torch.cuda.get_device_name(0)}")
            
            return True
        except Exception as e:
            print(f"❌ Failed to initialize SadTalker: {e}")
            return False
    
    def download_file(self, url, dest_path):
        """Download file from URL to destination."""
        try:
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def upload_file(self, file_path, job_id):
        """Upload result file to storage and return URL."""
        # In production, upload to S3/Supabase storage
        # For now, return a placeholder
        return f"{API_BASE_URL}/results/{job_id}/video.mp4"
    
    def process_job(self, job):
        """Process a single job."""
        job_id = job['job_id']
        self.current_job = job_id
        
        print(f"\n🎬 Processing job {job_id}")
        
        # Update status to processing
        self.api.update_job_status(job_id, "processing", 0, "Downloading input files...")
        
        try:
            # Create temp directory for this job
            with tempfile.TemporaryDirectory() as tmpdir:
                # Download input files
                img_path = os.path.join(tmpdir, "input_image.png")
                aud_path = os.path.join(tmpdir, "input_audio.wav")
                
                print("📥 Downloading input files...")
                if not self.download_file(job['image_url'], img_path):
                    raise Exception("Failed to download image")
                if not self.download_file(job['audio_url'], aud_path):
                    raise Exception("Failed to download audio")
                
                self.api.update_job_status(job_id, "processing", 10, "Initializing inference...")
                
                # Get configuration
                config = job.get('config', {})
                preprocess = config.get('preprocess', 'crop')
                still_mode = config.get('still_mode', False)
                use_enhancer = config.get('use_enhancer', False)
                batch_size = config.get('batch_size', 2)
                size = config.get('size', 256)
                pose_style = config.get('pose_style', 0)
                exp_scale = config.get('exp_scale', 1.0)
                use_ref_video = config.get('use_ref_video', False)
                ref_video_url = config.get('ref_video_url')
                ref_info = config.get('ref_info', 'pose')
                use_idle_mode = config.get('use_idle_mode', False)
                length_of_audio = config.get('length_of_audio', 0)
                use_blink = config.get('use_blink', True)
                
                # Progress simulation thread
                def progress_simulator():
                    progress = 20
                    while not self.stop_event.is_set() and progress < 90:
                        if progress < 50:
                            progress += 2
                            msg = "Generating face animation..."
                        elif progress < 80:
                            progress += 1
                            msg = "Rendering video frames..."
                        else:
                            progress += 0.5
                            msg = "Finalizing video..."
                        
                        self.api.update_job_status(job_id, "processing", int(progress), msg)
                        time.sleep(5)
                
                # Start progress simulator
                self.stop_event.clear()
                progress_thread = threading.Thread(target=progress_simulator)
                progress_thread.start()
                
                # Run SadTalker inference
                print("🚀 Running inference...")
                result_path = os.path.join(tmpdir, "result.mp4")
                
                try:
                    # Call SadTalker
                    self.sadtalker.test(
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
                        ref_video=ref_video_url if use_ref_video else None,
                        ref_info=ref_info,
                        use_idle_mode=use_idle_mode,
                        length_of_audio=length_of_audio,
                        use_blink=use_blink,
                        result_dir=tmpdir,
                        filename="result"
                    )
                    
                    # Stop progress simulator
                    self.stop_event.set()
                    progress_thread.join()
                    
                    # Upload result
                    self.api.update_job_status(job_id, "processing", 95, "Uploading result...")
                    print("📤 Uploading result...")
                    
                    result_url = self.upload_file(result_path, job_id)
                    
                    # Mark as completed
                    self.api.update_job_status(
                        job_id, 
                        "completed", 
                        100, 
                        "Video generated successfully!",
                        result_url=result_url
                    )
                    
                    print(f"✅ Job {job_id} completed!")
                    
                except Exception as e:
                    self.stop_event.set()
                    progress_thread.join()
                    raise e
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Job {job_id} failed: {error_msg}")
            self.api.update_job_status(
                job_id, 
                "failed", 
                error_message=error_msg
            )
        
        finally:
            self.current_job = None
    
    def run(self):
        """Main runner loop."""
        print("🏃 GPU Runner started")
        print(f"   Runner ID: {RUNNER_ID}")
        print(f"   API URL: {API_BASE_URL}")
        print(f"   Poll interval: {POLL_INTERVAL}s")
        
        # Initialize SadTalker
        if not self.initialize_sadtalker():
            print("❌ Cannot start without SadTalker")
            return
        
        # Send initial heartbeat
        self.api.send_heartbeat("idle")
        
        heartbeat_count = 0
        
        try:
            while True:
                # Send heartbeat every 30 seconds
                heartbeat_count += 1
                if heartbeat_count >= 3:
                    status = "busy" if self.current_job else "idle"
                    self.api.send_heartbeat(status, self.current_job)
                    heartbeat_count = 0
                
                # Check for pending jobs
                if not self.current_job:
                    jobs = self.api.get_pending_jobs()
                    
                    if jobs:
                        job = jobs[0]
                        self.process_job(job)
                    else:
                        print("⏳ No pending jobs, waiting...")
                
                time.sleep(POLL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n🛑 Runner stopped by user")
        except Exception as e:
            print(f"\n❌ Runner error: {e}")
        finally:
            self.api.send_heartbeat("offline")


def main():
    """Entry point."""
    # Check configuration
    if "your-api" in API_BASE_URL:
        print("⚠️  Please set API_BASE_URL environment variable!")
        print("   export API_BASE_URL=https://your-api.onrender.com/api/v1")
        return
    
    if "your-webhook" in WEBHOOK_SECRET:
        print("⚠️  Please set WEBHOOK_SECRET environment variable!")
        return
    
    # Create API client
    api_client = APIClient(API_BASE_URL, WEBHOOK_SECRET)
    
    # Create and run processor
    processor = JobProcessor(api_client)
    processor.run()


if __name__ == "__main__":
    main()