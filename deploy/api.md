# API Server Deployment Guide (Render/Railway)

This guide explains how to deploy the SadTalker AI API server.

## Prerequisites

1. **Render or Railway Account**
2. **Supabase Project** - Database configured
3. **AWS Account** - For S3 storage (or use Supabase Storage)
4. **GitHub Repository** - Code pushed to GitHub

## Environment Variables

Configure these in your deployment platform:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# AWS S3 (optional, can use Supabase Storage)
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1

# Webhook Security
WEBHOOK_SECRET=your-webhook-secret-key

# CORS
FRONTEND_URL=https://sadtalker-ai.vercel.app
```

## Deployment on Render

### 1. Create Web Service

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect your GitHub repository
3. Configure:
   - **Name**: sadtalker-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r deploy/requirements-api.txt`
   - **Start Command**: `gunicorn deploy.api_server:app`
   - **Plan**: Starter ($7/month) or Free

### 2. Add Environment Variables

In Render Dashboard → Environment:
- Add all variables from the list above

### 3. Deploy

Click "Create Web Service" → Automatic deployment starts

## Deployment on Railway

### 1. Create Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 2. Add Environment Variables

```bash
railway variables set SECRET_KEY=your-secret
railway variables set SUPABASE_URL=your-url
# ... add all variables
```

### 3. Configure Domain

```bash
railway domain
```

## Database Setup

### 1. Run Migrations

Execute the SQL in [`database.sql`](database.sql) in Supabase SQL Editor:

1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `database.sql`
3. Run the script

### 2. Configure Storage Buckets

Create two buckets in Supabase Storage:

**uploads bucket:**
- Public: No
- Allowed MIME types: image/*, audio/*
- Max file size: 50MB

**results bucket:**
- Public: No
- Allowed MIME types: video/*
- Max file size: 500MB

### 3. Set Storage Policies

```sql
-- uploads bucket policy
CREATE POLICY "Users can upload own files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
  bucket_id = 'uploads' AND
  (storage.foldername(name))[1] = auth.uid()::text
);

-- results bucket policy
CREATE POLICY "Users can read own results"
ON storage.objects FOR SELECT
TO authenticated
USING (
  bucket_id = 'results' AND
  (storage.foldername(name))[1] = auth.uid()::text
);
```

## API Endpoints

### Health Check
```bash
curl https://your-api.onrender.com/api/v1/health
```

### Upload File (Get Presigned URL)
```bash
curl -X POST https://your-api.onrender.com/api/v1/upload \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "image.jpg",
    "content_type": "image/jpeg",
    "file_size": 1024000
  }'
```

### Create Job
```bash
curl -X POST https://your-api.onrender.com/api/v1/jobs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://...",
    "audio_url": "https://...",
    "config": {
      "preprocess": "crop",
      "still_mode": false
    }
  }'
```

### Get Job Status
```bash
curl https://your-api.onrender.com/api/v1/jobs/<job_id> \
  -H "Authorization: Bearer <token>"
```

## Webhook Endpoints (GPU Runner)

These endpoints are called by the GPU runner:

### Job Update
```bash
POST /api/v1/webhooks/job-update
Headers:
  X-Webhook-Secret: <signature>

Body:
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 50,
  "message": "Generating...",
  "result_url": null,
  "error_message": null
}
```

### Runner Heartbeat
```bash
POST /api/v1/webhooks/runner-heartbeat
Headers:
  X-Webhook-Secret: <signature>

Body:
{
  "runner_id": "colab-runner-1",
  "runner_type": "colab",
  "status": "busy",
  "current_job_id": "uuid"
}
```

## Testing

### Local Testing

```bash
# Install dependencies
pip install -r deploy/requirements-api.txt

# Set environment variables
export SUPABASE_URL=...
export SUPABASE_SERVICE_KEY=...
# ... etc

# Run locally
python deploy/api_server.py
```

### API Tests

```bash
# Test health
curl http://localhost:5000/api/v1/health

# Test with auth (get token from Supabase)
curl http://localhost:5000/api/v1/jobs \
  -H "Authorization: Bearer <token>"
```

## Monitoring

### Render
- Built-in logs in Dashboard
- Metrics available on paid plans

### Railway
- Real-time logs
- Metrics dashboard
- Alerting available

### Custom Monitoring

Add health check endpoint monitoring:
- UptimeRobot (free)
- Pingdom
- Better Uptime

## Troubleshooting

### Database Connection Errors

1. Verify `SUPABASE_SERVICE_KEY` is correct (use service role key, not anon key)
2. Check Supabase project is active
3. Verify IP allowlist (if using IPv4 add-on)

### CORS Errors

1. Add your Vercel domain to CORS origins in `api_server.py`:
```python
CORS(app, origins=[
    "https://your-domain.vercel.app",
    "http://localhost:3000"
])
```

### File Upload Failures

1. Verify AWS credentials
2. Check S3 bucket CORS policy
3. Ensure bucket exists and is accessible

### Webhook Verification Fails

1. Ensure `WEBHOOK_SECRET` matches between API and GPU runner
2. Check payload is JSON-serialized consistently

## Scaling

### Render
- Upgrade to Starter ($7/month) for always-on
- Use Auto-Scaling on higher tiers

### Railway
- Auto-scaling based on usage
- Configure min/max instances

## Security Checklist

- [ ] Use strong `SECRET_KEY`
- [ ] Enable Row Level Security in Supabase
- [ ] Use service role key only server-side
- [ ] Validate all file uploads
- [ ] Rate limiting enabled
- [ ] CORS restricted to known domains
- [ ] Webhook signatures verified
- [ ] Environment variables not in code

## Cost Estimation

| Service | Free Tier | Starter |
|---------|-----------|---------|
| Render | 750 hrs/month | $7/month |
| Railway | $5 credit/month | Pay per usage |
| Supabase | 500MB + 2M requests | $25/month |
| AWS S3 | 5GB | ~$5/month |

**Total estimated cost:**
- Free tier: $0 (with limitations)
- Production: ~$40-50/month

## Next Steps

1. Deploy API server
2. Configure environment variables
3. Run database migrations
4. Test endpoints
5. Deploy GPU runner (Colab/Lightning)
6. Deploy frontend (Vercel)
7. Test end-to-end flow

See [DEPLOYMENT.md](../DEPLOYMENT.md) for full architecture overview.