"""
Simple local API server for VS Code Port Forwarding
No ngrok needed - VS Code handles the tunnel!
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and start the local API
from local_api import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 SadTalker Local API Server")
    print("=" * 60)
    print("\n📍 Server starting on http://localhost:7860")
    print("\n⚠️  IMPORTANT: Make sure VS Code Port Forwarding is enabled!")
    print("   1. Open VS Code Command Palette (Ctrl+Shift+P)")
    print("   2. Type 'Ports: Focus on Ports View'")
    print("   3. Click 'Forward a Port' → Enter 7860")
    print("   4. Right-click the port → 'Port Visibility' → 'Public'")
    print("\n🌐 Your public URL will appear in the Ports panel")
    print("=" * 60)
    
    # Start Flask server
    app.run(host='0.0.0.0', port=7860, debug=False, threaded=True)
