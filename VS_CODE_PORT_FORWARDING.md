# 🚀 VS Code Port Forwarding Setup (Easiest Method)

If you're already using VS Code with Port Forwarding enabled, you **don't need ngrok**! VS Code provides a built-in secure tunnel to expose your local server to the internet.

## ✅ What You Already Have

Looking at your screenshot, you have:
- **Port**: 7860 forwarded
- **Visibility**: Public
- **Forwarded Address**: `https://0pk41rhv-7860....app`

This means VS Code is already acting as your secure tunnel!

## 📐 Architecture with VS Code Port Forwarding

```
User Browser
    ↓
Vercel Frontend (sad-talker-ai.vercel.app)
    ↓ API Calls
VS Code Forwarded URL (https://0pk41rhv-7860....app)
    ↓
Your Laptop (localhost:7860)
    ↓
SadTalker GPU Processing
    ↓
Supabase Database
```

## 🎯 Quick Setup Steps

### Step 1: Start Your Local API Server

Instead of using `local_gpu_server.py` (which uses ngrok), create a simpler version:

**`start_local_api.py`**:
```python
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
```

### Step 2: Enable Port Forwarding in VS Code

1. **Open Ports Panel**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - Type: `Ports: Focus on Ports View`
   - Press Enter

2. **Forward Port 7860**:
   - Click `Forward a Port` button
   - Enter: `7860`
   - Press Enter

3. **Make it Public**:
   - Right-click on port 7860 in the list
   - Select `Port Visibility` → `Public`
   - Copy the URL (looks like: `https://0pk41rhv-7860.app.github.dev`)

### Step 3: Update Vercel Frontend

In your Vercel project settings, update the environment variable:

```
VITE_API_BASE_URL=https://0pk41rhv-7860.app.github.dev/api/v1
```

(Replace with your actual VS Code forwarded URL)

### Step 4: Deploy Frontend

Redeploy your Vercel frontend to pick up the new API URL.

## 🔧 Alternative: Using app_flask.py directly

If you already have `app_flask.py` working on port 7860, just:

1. Run it:
   ```bash
   python app_flask.py
   ```

2. Forward port 7860 in VS Code (as shown above)

3. Copy the forwarded URL and use it in Vercel

## ✅ Advantages of VS Code Port Forwarding

| Feature | VS Code | ngrok |
|---------|---------|-------|
| Setup | ✅ Built-in | Requires signup |
| Cost | ✅ Free | Free tier limited |
| URL Persistence | Changes on restart | Can reserve domains |
| Security | ✅ Microsoft/GitHub auth | Token-based |
| Speed | ✅ Fast | Depends on region |

## 📝 Summary

**You already have everything you need!**

1. ✅ VS Code Port Forwarding = Your public URL
2. ✅ Local API Server = Your laptop GPU
3. ✅ Vercel Frontend = Public website
4. ✅ Supabase = Database

Just forward port 7860 in VS Code, copy the URL, and update your Vercel environment variable!

## 🆘 Troubleshooting

**Port not showing in VS Code?**
- Make sure you're using VS Code (not VS Code Insiders)
- Check that you're signed into GitHub/Microsoft account
- Try reloading VS Code window

**URL not working?**
- Make sure your local server is running on port 7860
- Check that the port visibility is set to "Public"
- Try copying the URL again (it may have changed)

**CORS errors?**
- Update `CORS_ORIGINS` in your `.env` file to include your Vercel domain
