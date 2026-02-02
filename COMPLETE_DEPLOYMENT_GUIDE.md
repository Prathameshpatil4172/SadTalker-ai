# 🚀 SadTalker AI - Complete Deployment Guide

This guide provides step-by-step instructions for deploying the complete SadTalker AI architecture.

---

## Step 1: Set Up Supabase (Database + Storage + Auth)

### 1.1 Create Supabase Project

1. **Sign up at [supabase.com](https://supabase.com)**
   - Click "New Project"
   - Choose your organization
   - Enter project name: `sadtalker-ai`
   - Set database password (save this securely!)
   - Select region closest to your users (e.g., `us-east-1`)
   - Click "Create new project"

2. **Wait for project initialization** (2-3 minutes)

### 1.2 Get Connection Details

1. **Project Settings → API**
   - Copy `Project URL` - you'll need: `SUPABASE_URL`
   - Copy `Project API keys` → `service_role key` (NOT the anon key!) - you'll need: `SUPABASE_SERVICE_KEY`
   - Copy `anon public` key - you'll need: `SUPABASE_ANON_KEY` (for frontend)

2. **Save these securely** in a text file:
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 1.3 Run Database Migrations

1. **Go to SQL Editor**
   - In Supabase Dashboard, click "SQL Editor" in left sidebar
   - Click "New query"

2. **Copy and paste the entire SQL from** [`deploy/database.sql`](deploy/database.sql)

3. **Run the SQL**
   - Click "Run" button (or Ctrl+Enter)
   - You should see success messages for all tables created
   - Check Tables in left sidebar to verify: `profiles`, `jobs`, `files`, `credit_transactions`, `gpu_runners`

### 1.4 Configure Storage Buckets

1. **Go to Storage → Buckets**
   - Click "New Bucket"
   - Create bucket named: `uploads`
   - Toggle "Public bucket" OFF (keep private)
   - Click "Save"

2. **Create another bucket**
   - Name: `results`
   - Public: OFF
   - Click "Save"

### 1.5 Set Storage Policies

1. **For 'uploads' bucket:**
   - Click the bucket → Policies → "New Policy"
   - Select "For Select" (read)
   - Policy name: "Users can read own uploads"
   - Allowed operation: SELECT
   - Target roles: `authenticated`
   - Policy definition:
```sql
(storage.foldername(name))[1] = auth.uid()::text
```
   - Click "Review" → "Save policy"

2. **Create Insert policy for uploads:**
   - Click "New Policy" → "For Insert"
   - Policy name: "Users can upload files"
   - Target roles: `authenticated`
   - Policy definition:
```sql
(storage.foldername(name))[1] = auth.uid()::text AND (
  (storage.extension(name) = 'jpg' OR 
   storage.extension(name) = 'jpeg' OR 
   storage.extension(name) = 'png' OR 
   storage.extension(name) = 'wav' OR 
   storage.extension(name) = 'mp3')
)
```
   - Click "Save policy"

3. **For 'results' bucket:**
   - Create SELECT policy with same definition as uploads
   - Create INSERT policy for `service_role` only (API will use this)

### 1.6 Enable Realtime

1. **Go to Database → Replication**
   - Click "0 tables" under Realtime
   - Toggle ON for table `jobs`
   - Click "Save"

---

## Step 2: Deploy API Server (Render)

### 2.1 Create Render Account

1. **Sign up at [render.com](https://render.com)**
   - Use "GitHub" signup method (connects your repo automatically)
   - Authorize Render to access your repositories

### 2.2 Create Web Service

1. **New Web Service**
   - Dashboard → "New +" → "Web Service"
   - Select your GitHub repository: `SadTalker-ai`
   - Click "Connect"

2. **Configure Service**
   - **Name**: `sadtalker-api`
   - **Region**: Same as your Supabase (e.g., `Oregon (US West)`)
   - **Branch**: `dev` (or `main`)
   - **Runtime**: `Python 3`
   - **Build Command**:
```bash
pip install -r deploy/requirements-api.txt
```
   - **Start Command**:
```bash
gunicorn deploy.api_server:app
```
   - **Plan**: Select `Starter` ($7/month) or `Free` (spin down after inactivity)

3. **Click "Create Web Service"**
   - Wait for build to complete (2-3 minutes)

### 2.3 Configure Environment Variables

1. **Environment Tab**
   - Click "Environment" in your service dashboard
   - Add each variable one by one:

```
Key: SECRET_KEY
Value: (generate random string: openssl rand -hex 32 or use random.org)
```

```
Key: SUPABASE_URL
Value: (paste from Step 1.2)
```

```
Key: SUPABASE_SERVICE_KEY
Value: (paste from Step 1.2 - the service_role key!)
```

```
Key: WEBHOOK_SECRET
Value: (generate another random string, save it - needed for GPU runner)
```

```
Key: AWS_ACCESS_KEY_ID
Value: (optional - for S3, can skip if using Supabase Storage only)
```

```
Key: AWS_SECRET_ACCESS_KEY
Value: (optional - for S3)
```

```
Key: S3_BUCKET_NAME
Value: (optional - your S3 bucket name)
```

```
Key: AWS_REGION
Value: us-east-1
```

2. **Click "Save Changes"**
   - Render will redeploy with new environment

### 2.4 Verify Deployment

1. **Check Health Endpoint**
   ```bash
   curl https://sadtalker-api.onrender.com/api/v1/health
   ```
   
   Expected response:
   ```json
   {"success": true, "data": {"status": "healthy", "version": "1.0.0"}}
   ```

2. **Check Logs**
   - Render Dashboard → Your service → Logs
   - Look for "Running on http://0.0.0.0:10000" or similar

3. **Save API URL**
   ```
   API_BASE_URL=https://sadtalker-api.onrender.com/api/v1
   ```

---

## Step 3: Deploy Frontend (Vercel)

### 3.1 Prepare Frontend Code

1. **Create frontend directory structure** (if not exists):
```
frontend/
├── public/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   └── App.tsx
├── package.json
├── vite.config.ts
└── index.html
```

2. **Create environment file** `frontend/.env.production`:
```env
VITE_API_BASE_URL=https://sadtalker-api.onrender.com/api/v1
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-from-step-1.2
```

### 3.2 Create Vercel Project

1. **Sign up at [vercel.com](https://vercel.com)**
   - Use GitHub signup

2. **Import Repository**
   - Dashboard → "Add New..." → "Project"
   - Select your `SadTalker-ai` repository
   - Click "Import"

3. **Configure Project**
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend` (or where your package.json is)
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)

4. **Environment Variables**
   - Expand "Environment Variables" section
   - Add:
     - `VITE_API_BASE_URL` = `https://sadtalker-api.onrender.com/api/v1`
     - `VITE_SUPABASE_URL` = `your supabase url`
     - `VITE_SUPABASE_ANON_KEY` = `your anon key`

5. **Click "Deploy"**
   - Wait for build (2-3 minutes)

### 3.3 Configure Custom Domain (Optional)

1. **Domain Settings**
   - Project Settings → Domains
   - Enter your domain (e.g., `sadtalker-ai.com`)
   - Follow DNS instructions:
     - Add CNAME record: `cname.vercel-dns.com`
     - Or A record for apex domain

2. **Update CORS in API**
   - Edit `deploy/api_server.py` line ~50:
```python
CORS(app, origins=[
    "https://sadtalker-ai.vercel.app",
    "https://sadtalker-ai.com",  # your custom domain
    "http://localhost:3000",
    "http://localhost:5173"
])
```
   - Commit and push → auto-redeploy

### 3.4 Verify Frontend

1. **Open Vercel URL**
   - Should see your app loading
   - Check browser console for errors

2. **Test Authentication**
   - Try signing up/in with Supabase Auth

---

## Step 4: Start GPU Runner (Google Colab)

### 4.1 Create Colab Notebook

1. **Open [colab.research.google.com](https://colab.research.google.com)**

2. **Runtime → Change runtime type**
   - Hardware accelerator: `GPU`
   - GPU type: `T4` (free tier)
   - Click "Save"

3. **Create cells and add code:**

**Cell 1: Mount Drive (Optional)**
```python
from google.colab import drive
drive.mount('/content/drive')
```

**Cell 2: Clone Repository**
```python
%cd /content
!git clone https://github.com/Prathameshpatil4172/SadTalker-ai.git
%cd SadTalker-ai
```

**Cell 3: Install Dependencies**
```python
!pip install -q torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
!pip install -q -r requirements.txt
!pip install -q supabase boto3 requests
```

**Cell 4: Download Checkpoints**
```python
import os

checkpoint_path = "/content/checkpoints"
os.makedirs(checkpoint_path, exist_ok=True)

checkpoints = {
    "SadTalker_V0.0.2_256.safetensors": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
    "mapping_00109-model.pth.tar": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
    "facevid2vid_00189-model.pth.tar": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/facevid2vid_00189-model.pth.tar"
}

for name, url in checkpoints.items():
    path = os.path.join(checkpoint_path, name)
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        !wget -q -O {path} {url}
        print(f"✅ {name} downloaded")
    else:
        print(f"✅ {name} exists")
```

**Cell 5: Set Environment Variables**
```python
import os

# REPLACE THESE VALUES:
os.environ['API_BASE_URL'] = 'https://sadtalker-api.onrender.com/api/v1'  # From Step 2.4
os.environ['WEBHOOK_SECRET'] = 'your-webhook-secret-from-step-2.3'        # From Step 2.3
os.environ['RUNNER_ID'] = 'colab-runner-1'
os.environ['RUNNER_TYPE'] = 'colab'

print("✅ Environment configured")
```

**Cell 6: Run GPU Runner**
```python
%cd /content/SadTalker-ai
!python deploy/colab_runner.py
```

### 4.2 Run the Notebook

1. **Run all cells**
   - Runtime → Run all (or Ctrl+F9)
   - Wait for checkpoint downloads (5-10 minutes first time)

2. **Keep Colab Running**
   - Colab may disconnect after 90 minutes idle
   - To prevent: add this cell and run it in parallel:
```python
import time
while True:
    time.sleep(60)
    print("Keeping alive...")
```

3. **Verify Connection**
   - Check API logs in Render dashboard
   - Should see heartbeat messages from runner

### 4.3 Alternative: Use Python Script Directly

1. **Save as file** `start_runner.py`:
```python
import os

os.environ['API_BASE_URL'] = 'https://sadtalker-api.onrender.com/api/v1'
os.environ['WEBHOOK_SECRET'] = 'your-webhook-secret'
os.environ['RUNNER_ID'] = 'colab-runner-1'
os.environ['RUNNER_TYPE'] = 'colab'

exec(open('deploy/colab_runner.py').read())
```

2. **Run in terminal**:
```bash
python start_runner.py
```

---

## Step 5: Testing the Complete Flow

### 5.1 End-to-End Test

1. **Open Frontend** (Vercel URL)

2. **Sign Up / Log In**
   - Use Supabase Auth

3. **Upload Files**
   - Select image (PNG/JPG)
   - Select audio (WAV/MP3)

4. **Create Job**
   - Click "Generate"
   - Should see job created with status "pending"

5. **Check GPU Runner**
   - Colab should pick up job
   - See progress updates in Colab output

6. **Monitor Progress**
   - Frontend should show real-time progress
   - Check API logs for webhook calls

7. **View Result**
   - When complete, download video
   - Check Supabase Storage → results bucket

### 5.2 Troubleshooting

| Issue | Solution |
|-------|----------|
| API connection failed | Check CORS settings in api_server.py |
| Database connection error | Verify SUPABASE_SERVICE_KEY (not anon key) |
| File upload fails | Check storage policies in Supabase |
| GPU runner not picking jobs | Verify WEBHOOK_SECRET matches API |
| CUDA out of memory | Reduce batch_size in job config |

---

## Step 6: Production Considerations

### 6.1 Security

1. **Enable RLS on all tables** (already done in SQL)
2. **Use strong SECRET_KEY**
3. **Regenerate WEBHOOK_SECRET** periodically
4. **Enable API rate limiting** (configured in api_server.py)

### 6.2 Monitoring

1. **Render**: Built-in logs and metrics
2. **Supabase**: Database usage dashboard
3. **Vercel**: Analytics and Core Web Vitals

### 6.3 Scaling

1. **Upgrade Render** to paid tier for always-on API
2. **Use multiple GPU runners** with different RUNNER_IDs
3. **Consider RunPod** for auto-scaling GPU

### 6.4 Cost Optimization

| Service | Free Tier | Monthly Cost |
|---------|-----------|--------------|
| Vercel | 100GB bandwidth | $0 |
| Render | 750 hours | $7 (Starter) |
| Supabase | 500MB storage | $25 (Pro) |
| Colab | 12 hours/day | $10 (Pro) |
| **Total** | | **~$42/month** |

---

## 📚 Additional Resources

- [Supabase Docs](https://supabase.com/docs)
- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Colab FAQ](https://research.google.com/colaboratory/faq.html)

---

## ✅ Deployment Checklist

- [ ] Supabase project created
- [ ] Database schema deployed
- [ ] Storage buckets configured
- [ ] API deployed on Render
- [ ] Environment variables set
- [ ] Frontend deployed on Vercel
- [ ] GPU runner running on Colab
- [ ] End-to-end test passed
- [ ] Custom domain configured (optional)

**Your SadTalker AI is now fully deployed! 🎉**