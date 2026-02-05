# 🖥️ Local GPU Setup Guide - SadTalker AI

This guide explains how to set up SadTalker AI with your **local laptop as the GPU runner and API server**, while using **Vercel for frontend** and **Supabase for database**.

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                      │
│  ┌──────────┐                                                               │
│  │ Browser  │──→ https://sadtalker-ai.vercel.app (Vercel Frontend)         │
│  └──────────┘                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ API Calls
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LOCAL GPU LAPTOP                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  🌐 ngrok (Public URL)                                              │     │
│  │     https://abc123.ngrok.io ──→ http://localhost:5000               │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  🚀 Flask API Server (Python)                                       │     │
│  │     • Receives API requests from Vercel frontend                    │     │
│  │     • Manages job queue                                             │     │
│  │     • Serves results                                                │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  🎮 SadTalker GPU Inference                                         │     │
│  │     • Processes video generation using local GPU                    │     │
│  │     • NVIDIA GPU with CUDA required                                 │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
│                                    │                                         │
│                                    ▼ Database Calls                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER (Supabase)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐     │
│  │  📊 PostgreSQL + Storage                                            │     │
│  │     • Jobs queue and status tracking                                │
│  │     • File storage (uploads/results)                                │     │
│  │     • User management                                               │     │
│  └─────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## ✅ Prerequisites

### Hardware Requirements
- **NVIDIA GPU** with at least 4GB VRAM (8GB+ recommended)
- **CUDA-capable GPU** (GTX 1060, RTX 2060, RTX 3060, etc.)
- **Stable internet connection** (for ngrok tunnel)

### Software Requirements
- Windows 10/11 or Linux
- Python 3.8 - 3.10
- NVIDIA GPU drivers installed
- CUDA Toolkit 11.8 or 12.1
- Git

## 🚀 Step-by-Step Setup

### Step 1: Install Prerequisites

#### 1.1 Install NVIDIA GPU Drivers
```bash
# Check if GPU is detected
nvidia-smi

# If not installed, download from:
# https://www.nvidia.com/Download/index.aspx
```

#### 1.2 Install CUDA Toolkit
```bash
# Download CUDA 11.8 from:
# https://developer.nvidia.com/cuda-11-8-0-download-archive

# Verify installation
nvcc --version
```

#### 1.3 Install Python Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install PyTorch with CUDA support
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -r requirements.txt

# Install additional packages for API
pip install flask flask-cors pyngrok supabase python-dotenv requests
```

### Step 2: Set Up Supabase

#### 2.1 Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and sign up
2. Create a new project
3. Save your project credentials

#### 2.2 Get Supabase Credentials
In Supabase Dashboard → Settings → API:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 2.3 Run Database Migrations
1. Go to SQL Editor in Supabase Dashboard
2. Copy and run the SQL from [`deploy/database.sql`](deploy/database.sql)
3. This creates tables: `profiles`, `jobs`, `files`, `credit_transactions`

#### 2.4 Configure Storage Buckets
1. Go to Storage → Buckets
2. Create bucket: `uploads` (Private)
3. Create bucket: `results` (Private)
4. Set up storage policies (see COMPLETE_DEPLOYMENT_GUIDE.md)

### Step 3: Configure Environment Variables

Create a `.env` file in your project root:

```env
# ============================================
# Supabase Configuration
# ============================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ============================================
# ngrok Configuration
# ============================================
# Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
NGROK_REGION=in  # Options: us, eu, au, ap, sa, jp, in

# ============================================
# API Configuration
# ============================================
API_SECRET=your-secret-key-here-change-this
FLASK_PORT=5000
FLASK_DEBUG=false

# ============================================
# Frontend Configuration (for CORS)
# ============================================
FRONTEND_URL=https://your-frontend.vercel.app

# ============================================
# Local Paths (auto-configured)
# ============================================
CHECKPOINT_PATH=checkpoints
CONFIG_PATH=src/config
RESULT_DIR=static/results
UPLOAD_DIR=uploads
```

### Step 4: Set Up ngrok

#### 4.1 Sign Up for ngrok
1. Go to [ngrok.com](https://ngrok.com)
2. Sign up for a free account
3. Get your authtoken from the dashboard

#### 4.2 Install ngrok
```bash
# Windows (using Chocolatey)
choco install ngrok

# Or download from: https://ngrok.com/download
```

#### 4.3 Configure ngrok
```bash
# Add authtoken
ngrok config add-authtoken your_authtoken_here
```

### Step 5: Start the Local API Server

#### 5.1 Start the Flask API with ngrok

We provide a launcher script that handles everything:

```bash
# Run the local GPU server with ngrok
python local_gpu_server.py
```

This will:
1. Start the Flask API server on `localhost:5000`
2. Create an ngrok tunnel to expose it publicly
3. Print the public URL for your frontend

#### 5.2 Manual Start (Alternative)

If you prefer to run components separately:

```bash
# Terminal 1: Start ngrok
ngrok http 5000 --region in

# Terminal 2: Start Flask API
python local_api.py
```

### Step 6: Deploy Frontend to Vercel

#### 6.1 Update Frontend API URL

In your frontend code (e.g., `config.js` or `.env.local`):

```javascript
// config.js
const API_BASE_URL = 'https://your-ngrok-url.ngrok.io/api/v1';
// Replace with the URL shown when you start ngrok

export default API_BASE_URL;
```

#### 6.2 Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod
```

Or use the Vercel dashboard:
1. Push your frontend code to GitHub
2. Import project in Vercel dashboard
3. Set environment variables
4. Deploy

## 📁 Project Structure

```
SadTalker/
├── 📄 local_gpu_server.py      # Main launcher with ngrok
├── 📄 local_api.py             # Flask API server
├── 📄 supabase_client.py       # Supabase integration
├── 📄 .env                     # Environment variables
├── 📄 LOCAL_GPU_SETUP.md       # This guide
│
├── 📁 src/                     # SadTalker source code
├── 📁 checkpoints/             # Model weights
├── 📁 static/results/          # Generated videos
├── 📁 uploads/                 # Temporary uploads
│
├── 📁 frontend/                # Vercel frontend (separate)
│   ├── 📄 config.js
│   └── 📄 ...
│
└── 📁 deploy/                  # Deployment configs
    └── 📄 database.sql
```

## 🔧 How It Works

### 1. User Uploads Files
```
User → Vercel Frontend → Supabase Storage (uploads bucket)
```

### 2. Job Creation
```
Frontend → ngrok URL → Local API → Supabase (jobs table)
```

### 3. Local Processing
```
Local API polls Supabase → Downloads files → GPU Inference → Uploads result
```

### 4. Result Delivery
```
Supabase (results bucket) → Frontend (via Supabase URL)
```

## 🔄 Workflow Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Browser   │────→│    Vercel    │────→│  Supabase       │
│   (User)    │←────│   Frontend   │←────│  (Files/DB)     │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                │
                                                │ Webhook/Realtime
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Browser   │←────│    Vercel    │←────│  Local Laptop   │
│   (Result)  │     │   Frontend   │     │  (API + GPU)    │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                ▲
                                                │ ngrok tunnel
                                         ┌──────┴──────┐
                                         │   ngrok.io  │
                                         │  (Public)   │
                                         └─────────────┘
```

## 🛠️ Troubleshooting

### Issue: ngrok tunnel not working
**Solution:**
```bash
# Check ngrok status
ngrok status

# Restart ngrok with verbose output
ngrok http 5000 --region in --log=stdout

# Check firewall settings
# Ensure port 5000 is not blocked
```

### Issue: GPU not detected
**Solution:**
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
```

### Issue: Supabase connection failed
**Solution:**
```bash
# Check environment variables
echo %SUPABASE_URL%  # Windows
echo $SUPABASE_URL   # Linux/Mac

# Test connection
python -c "from supabase import create_client; import os; sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY')); print(sb.table('jobs').select('*').limit(1).execute())"
```

### Issue: CORS errors in frontend
**Solution:**
- Ensure `FRONTEND_URL` in `.env` matches your Vercel URL
- Check that `flask-cors` is installed
- Verify CORS headers are set in `local_api.py`

## 🔒 Security Considerations

1. **API Secret**: Change the default `API_SECRET` in `.env`
2. **ngrok**: Free tier URLs change on restart. Consider paid plan for static URL
3. **Supabase**: Use Row Level Security (RLS) policies
4. **Firewall**: Only expose necessary ports through ngrok

## 💰 Cost Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | Vercel (Hobby) | Free |
| Database | Supabase (Free Tier) | Free |
| Tunnel | ngrok (Free) | Free |
| GPU | Your Laptop | Free |
| **Total** | | **Free** |

## 📝 Next Steps

1. ✅ Complete this setup guide
2. ✅ Test video generation locally
3. ✅ Configure frontend to use ngrok URL
4. ✅ Deploy frontend to Vercel
5. ✅ Test end-to-end workflow
6. 🔄 Set up monitoring and logging
7. 🔄 Consider ngrok paid plan for static URL

## 📞 Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review logs in the terminal running `local_gpu_server.py`
3. Check ngrok dashboard: https://dashboard.ngrok.com
4. Check Supabase logs in the dashboard

---

**Happy generating! 🎬🤖**
