"""
Local GPU Server Launcher with ngrok Integration

This script:
1. Starts the Flask API server locally
2. Creates an ngrok tunnel to expose it to the internet
3. Displays the public URL for connecting your Vercel frontend

Usage:
    python local_gpu_server.py

Requirements:
    - ngrok installed and authenticated
    - All dependencies installed
    - .env file configured
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
NGROK_AUTHTOKEN = os.getenv('NGROK_AUTHTOKEN')
NGROK_REGION = os.getenv('NGROK_REGION', 'in')

# Global variables
ngrok_process = None
flask_process = None
public_url = None


def print_banner():
    """Print startup banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           🎬 SadTalker AI - Local GPU Server                    ║
║                                                                  ║
║   Local laptop as GPU runner + API server + ngrok tunnel        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def check_prerequisites():
    """Check if all prerequisites are installed."""
    print("🔍 Checking prerequisites...\n")
    
    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    
    # Check ngrok
    try:
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok installed: {result.stdout.strip()}")
        else:
            print("❌ ngrok not found. Install from: https://ngrok.com/download")
            return False
    except FileNotFoundError:
        print("❌ ngrok not found. Install from: https://ngrok.com/download")
        print("   Or run: pip install pyngrok")
        return False
    
    # Check ngrok authtoken
    if not NGROK_AUTHTOKEN:
        print("⚠️  NGROK_AUTHTOKEN not set in .env file")
        print("   Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken")
        return False
    print("✅ ngrok authtoken configured")
    
    # Check Supabase credentials
    if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_SERVICE_KEY'):
        print("✅ Supabase credentials configured")
    else:
        print("⚠️  Supabase not configured - running in standalone mode")
    
    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"✅ GPU detected: {gpu_name} ({vram:.2f} GB VRAM)")
        else:
            print("⚠️  No GPU detected - processing will be slow!")
    except ImportError:
        print("⚠️  PyTorch not installed - GPU check skipped")
    
    print()
    return True


def setup_ngrok():
    """Configure ngrok with authtoken."""
    if NGROK_AUTHTOKEN:
        try:
            subprocess.run(['ngrok', 'config', 'add-authtoken', NGROK_AUTHTOKEN], 
                          capture_output=True, check=True)
            print("✅ ngrok authenticated\n")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  ngrok authentication warning: {e}")


def start_ngrok():
    """Start ngrok tunnel and return public URL."""
    global ngrok_process, public_url
    
    print(f"🌐 Starting ngrok tunnel on port {FLASK_PORT}...")
    
    # Start ngrok process
    cmd = ['ngrok', 'http', str(FLASK_PORT), '--region', NGROK_REGION, '--log=stdout']
    ngrok_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for tunnel to be established and extract URL
    print("⏳ Waiting for ngrok tunnel...")
    time.sleep(3)
    
    # Try to get public URL using ngrok API
    import urllib.request
    import json
    
    for _ in range(10):
        try:
            with urllib.request.urlopen('http://localhost:4040/api/tunnels') as response:
                data = json.loads(response.read().decode())
                if data['tunnels']:
                    public_url = data['tunnels'][0]['public_url']
                    break
        except Exception:
            time.sleep(1)
    
    if public_url:
        print(f"✅ ngrok tunnel established!")
        print(f"\n{'='*60}")
        print(f"🌐 PUBLIC URL: {public_url}")
        print(f"{'='*60}\n")
        print("📋 Use this URL in your Vercel frontend configuration\n")
        return True
    else:
        print("❌ Failed to get ngrok URL")
        return False


def start_flask():
    """Start the Flask API server."""
    global flask_process
    
    print(f"🚀 Starting Flask API server on port {FLASK_PORT}...\n")
    
    env = os.environ.copy()
    env['FLASK_PORT'] = str(FLASK_PORT)
    
    flask_process = subprocess.Popen(
        [sys.executable, 'local_api.py'],
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True
    )
    
    # Wait a moment to ensure it starts
    time.sleep(2)
    
    if flask_process.poll() is None:
        print(f"✅ Flask API server running\n")
        return True
    else:
        print("❌ Flask API server failed to start")
        return False


def monitor_processes():
    """Monitor processes and handle shutdown."""
    try:
        while True:
            # Check if Flask is still running
            if flask_process and flask_process.poll() is not None:
                print("\n❌ Flask server stopped unexpectedly")
                break
            
            # Check if ngrok is still running
            if ngrok_process and ngrok_process.poll() is not None:
                print("\n❌ ngrok tunnel stopped unexpectedly")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")


def cleanup():
    """Clean up processes on exit."""
    global ngrok_process, flask_process
    
    if flask_process:
        print("🛑 Stopping Flask server...")
        flask_process.terminate()
        try:
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            flask_process.kill()
    
    if ngrok_process:
        print("🛑 Stopping ngrok tunnel...")
        ngrok_process.terminate()
        try:
            ngrok_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ngrok_process.kill()
    
    print("✅ Cleanup complete")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n🛑 Ctrl+C pressed, shutting down...")
    cleanup()
    sys.exit(0)


def main():
    """Main entry point."""
    global ngrok_process, flask_process
    
    # Print banner
    print_banner()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Setup ngrok
    setup_ngrok()
    
    try:
        # Start ngrok first
        if not start_ngrok():
            print("❌ Failed to start ngrok tunnel")
            sys.exit(1)
        
        # Start Flask
        if not start_flask():
            print("❌ Failed to start Flask server")
            cleanup()
            sys.exit(1)
        
        # Print usage info
        print("📝 Usage Instructions:")
        print("   1. Copy the PUBLIC URL above")
        print("   2. Update your Vercel frontend environment variables")
        print("   3. Deploy or redeploy your frontend")
        print("   4. Access your app through the Vercel URL")
        print("\n💡 API Endpoints:")
        print(f"   Health Check: {public_url}/api/v1/health")
        print(f"   Create Job:   {public_url}/api/v1/jobs (POST)")
        print(f"   Job Status:   {public_url}/api/v1/jobs/<job_id> (GET)")
        print("\n⚠️  Keep this terminal open to maintain the tunnel!")
        print("   Press Ctrl+C to stop\n")
        print("="*60 + "\n")
        
        # Monitor processes
        monitor_processes()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        cleanup()


if __name__ == '__main__':
    main()
