# 🚀 SadTalker AI - Simple Setup Guide (VS Code Port Forwarding)

Use your laptop's GPU to process videos, with a public website anyone can access.

## 📐 What You'll Build

```
User visits: https://sad-talker-ai.vercel.app
                ↓
    Vercel (Free Frontend Hosting)
                ↓
    VS Code Port Forwarding URL
                ↓
    Your Laptop (GPU Processing)
                ↓
    Supabase (Free Database)
```

## ✅ Prerequisites

1. **NVIDIA GPU** with CUDA support
2. **Python 3.10** installed
3. **VS Code** with your project open
4. **GitHub account** (for Vercel)

---

## Step 1: Install Dependencies

Open terminal in VS Code and run:

```bash
pip install flask flask-cors python-dotenv supabase requests
```

---

## Step 2: Configure Environment

1. Copy the example file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` file with your details:
   ```env
   # Supabase (from your Supabase project)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   
   # API Settings
   API_PORT=7860
   API_SECRET=make-up-a-random-secret-key
   
   # CORS (your Vercel URL - we'll get this in Step 4)
   FRONTEND_URL=https://sad-talker-ai.vercel.app
   ```

---

## Step 3: Start Local API Server

1. Run the server:
   ```bash
   python start_local_api.py
   ```

2. You should see:
   ```
   🚀 SadTalker Local API Server
   Server starting on http://localhost:7860
   ```

---

## Step 4: Enable VS Code Port Forwarding

1. **Open Ports Panel**:
   - Press `Ctrl+Shift+P`
   - Type: `Ports: Focus on Ports View`
   - Press Enter

2. **Forward Port 7860**:
   - Click `Forward a Port` button
   - Enter: `7860`
   - Press Enter

3. **Make it Public**:
   - Right-click on port 7860
   - Select `Port Visibility` → `Public`
   - **Copy the URL** (looks like: `https://0pk41rhv-7860.app.github.dev`)

---

## Step 5: Deploy Frontend to Vercel

1. **Push code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin dev
   ```

2. **Go to Vercel**:
   - Visit [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Use these settings:
     - **Framework**: Other (static site)
     - **Root Directory**: `.` (root)
     - **Build Command**: (leave empty)

3. **Add Environment Variable**:
   - Key: `VITE_API_BASE_URL`
   - Value: Your VS Code forwarded URL + `/api/v1`
   - Example: `https://0pk41rhv-7860.app.github.dev/api/v1`

4. **Deploy**

5. **Copy your Vercel URL** (e.g., `https://sad-talker-ai.vercel.app`)

---

## Step 6: Update CORS Settings

1. Stop your local server (Ctrl+C)

2. Edit `.env` file:
   ```env
   FRONTEND_URL=https://sad-talker-ai.vercel.app
   ```
   (Use your actual Vercel URL)

3. Restart the server:
   ```bash
   python start_local_api.py
   ```

---

## ✅ Done! Test Your Setup

1. Visit your Vercel URL: `https://sad-talker-ai.vercel.app`
2. Upload an image and audio
3. Click Generate
4. Check your laptop - it should start processing!

---

## 🔄 Daily Usage

Every time you want to use the service:

1. Open VS Code
2. Run: `python start_local_api.py`
3. Make sure port 7860 is forwarded (check Ports panel)
4. Share your Vercel URL with anyone!

**Note**: The VS Code forwarded URL changes each session. If it changes, update the `VITE_API_BASE_URL` in Vercel and redeploy.

---

## 🆘 Troubleshooting

**"Port already in use"**:
```bash
# Find and kill the process
netstat -ano | findstr :7860
taskkill /PID <number> /F
```

**"CORS error" in browser**:
- Make sure `FRONTEND_URL` in `.env` matches your Vercel URL exactly
- Restart the local server

**"Cannot connect to API"**:
- Check that port 7860 is forwarded in VS Code
- Verify the URL in Vercel environment variables
- Make sure your local server is running

**GPU not detected**:
- Install CUDA: https://developer.nvidia.com/cuda-downloads
- Verify: `python -c "import torch; print(torch.cuda.is_available())"`

---

## 📁 Files You Need

These are the only files you need to care about:

- `start_local_api.py` - Starts your local server
- `.env` - Your configuration
- `VS_CODE_PORT_FORWARDING.md` - Detailed guide
- `unified.html` - Your frontend (deployed to Vercel)

Everything else is documentation or alternative setups you can ignore.
