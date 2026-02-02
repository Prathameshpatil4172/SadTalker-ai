# 🚀 SadTalker AI - Deployment Architecture

This document describes the distributed deployment architecture for SadTalker AI, separating the GPU-intensive inference workload from the web UI and API.

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                               │
│  ┌──────────┐                                                   │
│  │ Browser  │──→ https://sadtalker-ai.vercel.app                │
│  └──────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND LAYER                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Vercel (Next.js / Static Site)                 │    │
│  │  • React UI Components                                  │    │
│  │  • File Upload Interface                               │    │
│  │  • Real-time Progress Display                          │    │
│  │  • Results Gallery                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ API Calls
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (Render)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Flask API Server (Python)                   │    │
│  │                                                          │    │
│  │  Routes:                                                 │    │
│  │  • POST /api/v1/jobs          → Create new job          │    │
│  │  • GET  /api/v1/jobs/:id      → Get job status          │    │
│  │  • GET  /api/v1/jobs/:id/result → Download result       │    │
│  │  • POST /api/v1/upload        → Upload files (→ S3)     │    │
│  │  • GET  /api/v1/health        → Health check            │    │
│  │                                                          │    │
│  │  Environment Variables:                                  │    │
│  │  • SUPABASE_URL, SUPABASE_KEY                           │    │
│  │  • AWS_S3_BUCKET, AWS_ACCESS_KEY                        │    │
│  │  • COLAB_WEBHOOK_URL, API_SECRET                        │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ WebSocket / HTTP
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER (Supabase)                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              PostgreSQL + Realtime Subscriptions         │    │
│  │                                                          │    │
│  │  Tables:                                                 │    │
│  │  • jobs (id, status, progress, config, urls, timestamps)│    │
│  │  • users (id, email, credits, created_at)               │    │
│  │  • files (id, job_id, type, s3_url, size)               │    │
│  │                                                          │    │
│  │  Storage Buckets:                                       │    │
│  │  • uploads (input images/audio)                         │    │
│  │  • results (generated videos)                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ WebSocket Events
┌─────────────────────────────────────────────────────────────────┐
│                    GPU RUNNER LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │         Google Colab / Lightning AI / RunPod             │    │
│  │                                                          │    │
│  │  Workflow:                                               │    │
│  │  1. Poll Supabase for pending jobs                      │    │
│  │  2. Download files from S3/Supabase Storage             │    │
│  │  3. Run SadTalker inference (GPU-intensive)             │    │
│  │  4. Upload result video to S3/Supabase Storage          │    │
│  │  5. Update job status via API callback                  │    │
│  │                                                          │    │
│  │  Components:                                            │    │
│  │  • Colab Notebook (for free tier)                       │    │
│  │  • Lightning AI Studio (for persistent GPU)             │    │
│  │  • RunPod Serverless GPU (for production)               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. Job Creation Flow
```
User Uploads Files (Browser)
    ↓
Frontend validates files → Uploads to S3/Supabase Storage
    ↓
Frontend calls API: POST /api/v1/jobs
    ↓
API creates job record in Supabase (status: "pending")
    ↓
Real-time subscription notifies GPU Runner
    ↓
GPU Runner picks up job → Updates status to "processing"
```

### 2. Processing Flow
```
GPU Runner downloads input files
    ↓
SadTalker inference starts (GPU-intensive)
    ↓
Progress updates sent via WebSocket/HTTP callback to API
    ↓
API updates Supabase (real-time updates to Frontend)
    ↓
Inference complete → Upload result to S3/Supabase
    ↓
GPU Runner updates job status: "completed"
```

### 3. Result Retrieval Flow
```
Frontend receives real-time status update
    ↓
Job status: "completed"
    ↓
Frontend fetches result URL from API
    ↓
User downloads/views generated video
```

## 📦 Component Breakdown

### Frontend (Vercel)
- **Framework**: Next.js 14+ with App Router
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: React Query for server state management
- **Real-time**: Supabase Realtime subscriptions
- **Upload**: Direct browser-to-S3 upload with presigned URLs

### API (Render / Railway / Fly.io)
- **Framework**: Flask with Gunicorn
- **Database**: Supabase (PostgreSQL)
- **Storage**: AWS S3 or Supabase Storage
- **Auth**: Supabase Auth or custom JWT
- **Rate Limiting**: Flask-Limiter
- **CORS**: Flask-CORS for Vercel domain

### Database (Supabase)
- **Type**: PostgreSQL 15
- **Realtime**: Enabled for job status updates
- **Storage**: Built-in S3-compatible storage
- **Auth**: Row Level Security (RLS) policies

### GPU Runner (Google Colab / Lightning AI)
- **Inference**: SadTalker with PyTorch
- **Communication**: Polling or WebSocket to API
- **Storage**: Temporary local + S3 upload
- **Monitoring**: Health checks and auto-restart

## 🔐 Security Considerations

1. **API Authentication**: JWT tokens for user identification
2. **Webhook Security**: HMAC signatures for GPU runner callbacks
3. **CORS**: Restrict to Vercel deployment domain
4. **Rate Limiting**: Prevent abuse (max 5 jobs/hour for free tier)
5. **File Validation**: Check file types and sizes before upload
6. **Presigned URLs**: Time-limited S3 URLs for secure file access

## 💰 Cost Estimation (Monthly)

| Service | Free Tier | Paid (Low Traffic) |
|---------|-----------|-------------------|
| Vercel (Frontend) | $0 | $0 (generous free tier) |
| Render (API) | $0 | $7 |
| Supabase (DB + Storage) | $0 (500MB) | $25 |
| Google Colab | $0 (limited) | $10 (Colab Pro) |
| AWS S3 Storage | $0 (5GB) | $5 |
| **Total** | **$0** | **~$47/month** |

## 🚀 Deployment Steps

See individual deployment guides:
- [Frontend Deployment](./deploy/frontend.md) - Vercel setup
- [API Deployment](./deploy/api.md) - Render/Railway setup
- [Database Setup](./deploy/database.md) - Supabase configuration
- [GPU Runner Setup](./deploy/gpu-runner.md) - Colab/Lightning setup

## 📚 API Documentation

See [API.md](./API.md) for complete API endpoint documentation.