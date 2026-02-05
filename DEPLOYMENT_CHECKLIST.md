# ✅ SadTalker AI - Local GPU Setup Checklist

Use this checklist to ensure you've completed all steps for setting up SadTalker AI with your local laptop as the GPU runner.

---

## Phase 1: Prerequisites Setup

### Hardware Check
- [ ] NVIDIA GPU with 4GB+ VRAM (check with `nvidia-smi`)
- [ ] Stable internet connection
- [ ] Sufficient disk space (10GB+ for models)

### Software Installation
- [ ] Python 3.8 - 3.10 installed
- [ ] NVIDIA GPU drivers installed
- [ ] CUDA Toolkit 11.8 or 12.1 installed
- [ ] Git installed
- [ ] ngrok installed (`ngrok --version` to verify)

---

## Phase 2: Supabase Setup

### Project Creation
- [ ] Created Supabase account at [supabase.com](https://supabase.com)
- [ ] Created new project
- [ ] Saved project password securely

### Credentials
- [ ] Copied `SUPABASE_URL` from Settings → API
- [ ] Copied `SUPABASE_SERVICE_KEY` (service_role key)
- [ ] Copied `SUPABASE_ANON_KEY` (anon public key)

### Database Setup
- [ ] Opened SQL Editor in Supabase Dashboard
- [ ] Ran SQL from `deploy/database.sql`
- [ ] Verified tables created: `profiles`, `jobs`, `files`, `credit_transactions`

### Storage Setup
- [ ] Created `uploads` bucket (Private)
- [ ] Created `results` bucket (Private)
- [ ] Set up storage policies for both buckets

---

## Phase 3: ngrok Setup

### Account
- [ ] Signed up at [ngrok.com](https://ngrok.com)
- [ ] Copied authtoken from dashboard

### Installation
- [ ] Installed ngrok CLI
- [ ] Added authtoken: `ngrok config add-authtoken <token>`
- [ ] Verified installation: `ngrok --version`

---

## Phase 4: Local Environment Setup

### Python Environment
```bash
# Run these commands and verify each step
```
- [ ] Created virtual environment: `python -m venv venv`
- [ ] Activated virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
- [ ] Installed PyTorch with CUDA: `pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118`
- [ ] Installed requirements: `pip install -r requirements.txt`
- [ ] Installed API dependencies: `pip install flask flask-cors pyngrok supabase python-dotenv requests`

### Configuration File
- [ ] Copied `.env.example` to `.env`
- [ ] Filled in `SUPABASE_URL`
- [ ] Filled in `SUPABASE_SERVICE_KEY`
- [ ] Filled in `SUPABASE_ANON_KEY`
- [ ] Filled in `NGROK_AUTHTOKEN`
- [ ] Changed `API_SECRET` to a secure random string
- [ ] Set `FRONTEND_URL` to your Vercel URL (or `*` for development)

### Model Checkpoints
- [ ] Downloaded model checkpoints to `checkpoints/` folder
- [ ] Verified checkpoint files exist

---

## Phase 5: Test Local Server

### Start Server
```bash
python local_gpu_server.py
```

- [ ] Server starts without errors
- [ ] ngrok tunnel established
- [ ] Public URL displayed (copy this!)
- [ ] Flask API server running

### Test API Endpoints
Open browser or use curl to test:

- [ ] Health check: `https://your-ngrok-url.ngrok.io/api/v1/health`
  - Should return: `{"success": true, "status": "healthy"}`

- [ ] Test job creation (use Postman or curl):
  ```bash
  curl -X POST https://your-ngrok-url.ngrok.io/api/v1/jobs \
    -F "image=@test_image.jpg" \
    -F "audio=@test_audio.wav"
  ```

---

## Phase 6: Frontend Setup

### Environment Variables
- [ ] Copied `frontend/.env.local.example` to `frontend/.env.local`
- [ ] Set `NEXT_PUBLIC_API_URL` to your ngrok URL + `/api/v1`
- [ ] Set `NEXT_PUBLIC_SUPABASE_URL`
- [ ] Set `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Configuration
- [ ] Updated `frontend/config.js` if needed
- [ ] Verified API endpoints match your setup

### Deploy to Vercel
```bash
cd frontend
npm install
vercel --prod
```

- [ ] Frontend deployed successfully
- [ ] Vercel URL obtained

---

## Phase 7: End-to-End Testing

### Upload Test
- [ ] Open Vercel frontend URL in browser
- [ ] Upload an image file (JPG/PNG)
- [ ] Upload an audio file (WAV/MP3)
- [ ] Submit the form

### Processing Test
- [ ] Job created successfully
- [ ] Progress updates showing
- [ ] Local GPU being utilized (check `nvidia-smi`)

### Result Test
- [ ] Video generated successfully
- [ ] Can download/play the video
- [ ] Video stored in Supabase storage

---

## Phase 8: Monitoring & Maintenance

### Logs
- [ ] Checked local server logs for errors
- [ ] Checked ngrok dashboard for tunnel status
- [ ] Checked Supabase logs for database operations

### Performance
- [ ] Monitored GPU usage during processing
- [ ] Checked memory usage
- [ ] Verified reasonable processing times

### Security
- [ ] Changed default `API_SECRET`
- [ ] Verified CORS is configured correctly
- [ ] Checked Supabase RLS policies are active

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| ngrok tunnel not working | Check authtoken, firewall settings |
| GPU not detected | Reinstall PyTorch with correct CUDA version |
| Supabase connection failed | Verify credentials in `.env` |
| CORS errors | Check `FRONTEND_URL` matches Vercel URL |
| Slow processing | Close other GPU-intensive applications |
| Out of memory | Reduce batch size or image resolution |

---

## Next Steps After Setup

- [ ] Set up monitoring (optional)
- [ ] Configure backup for generated videos
- [ ] Consider ngrok paid plan for static URL
- [ ] Document any custom configuration
- [ ] Share your setup with team members

---

## Support Resources

- **Local GPU Setup Guide**: [`LOCAL_GPU_SETUP.md`](LOCAL_GPU_SETUP.md)
- **Complete Deployment Guide**: [`COMPLETE_DEPLOYMENT_GUIDE.md`](COMPLETE_DEPLOYMENT_GUIDE.md)
- **API Documentation**: [`API.md`](API.md)
- **ngrok Dashboard**: https://dashboard.ngrok.com
- **Supabase Dashboard**: https://app.supabase.com

---

**Congratulations!** Once all items are checked, your SadTalker AI local GPU setup is complete! 🎉
