# 📚 SadTalker AI - API Documentation

Base URL: `https://your-api-domain.com/api/v1`

## Authentication

All API endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Create Job

Create a new video generation job.

**Endpoint:** `POST /jobs`

**Request Body:**
```json
{
  "image_url": "https://storage.supabase.co/uploads/image.jpg",
  "audio_url": "https://storage.supabase.co/uploads/audio.wav",
  "config": {
    "preprocess": "crop",
    "still_mode": false,
    "use_enhancer": false,
    "batch_size": 2,
    "size": 256,
    "pose_style": 0,
    "exp_scale": 1.0,
    "use_ref_video": false,
    "ref_video_url": null,
    "ref_info": "pose",
    "use_idle_mode": false,
    "length_of_audio": 0,
    "use_blink": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z",
    "estimated_time": 120
  }
}
```

### 2. Get Job Status

Retrieve the current status of a job.

**Endpoint:** `GET /jobs/{job_id}`

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "progress": 45,
    "message": "Generating face animation...",
    "config": {
      "preprocess": "crop",
      "still_mode": false,
      "use_enhancer": false
    },
    "input_files": {
      "image": "https://storage.supabase.co/uploads/image.jpg",
      "audio": "https://storage.supabase.co/uploads/audio.wav"
    },
    "result_url": null,
    "created_at": "2024-01-15T10:30:00Z",
    "started_at": "2024-01-15T10:30:05Z",
    "completed_at": null,
    "error_message": null
  }
}
```

**Status Values:**
- `pending` - Job queued, waiting for GPU
- `processing` - GPU is actively processing
- `completed` - Video generated successfully
- `failed` - Error occurred during processing
- `cancelled` - Job was cancelled

### 3. Get Job Result

Download the generated video.

**Endpoint:** `GET /jobs/{job_id}/result`

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "download_url": "https://storage.supabase.co/results/video_123.mp4?token=...",
    "expires_at": "2024-01-15T11:30:00Z",
    "video_info": {
      "duration": 10.5,
      "resolution": "256x256",
      "file_size": 2048576
    }
  }
}
```

### 4. Upload File

Get a presigned URL for direct file upload to storage.

**Endpoint:** `POST /upload`

**Request Body:**
```json
{
  "filename": "image.jpg",
  "content_type": "image/jpeg",
  "file_size": 1024000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "upload_url": "https://storage.supabase.co/uploads/image.jpg?X-Amz-Algorithm=...",
    "file_url": "https://storage.supabase.co/uploads/image.jpg",
    "expires_in": 300,
    "max_file_size": 10485760
  }
}
```

**Upload Instructions:**
1. Call this endpoint to get presigned URL
2. Upload file directly to `upload_url` via PUT request
3. Use `file_url` when creating a job

### 5. List Jobs

Get a list of user's jobs with pagination.

**Endpoint:** `GET /jobs?page=1&limit=20&status=completed`

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "preview_url": "https://storage.supabase.co/results/video_123_preview.gif",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "total_pages": 3
    }
  }
}
```

### 6. Cancel Job

Cancel a pending or processing job.

**Endpoint:** `POST /jobs/{job_id}/cancel`

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "cancelled",
    "message": "Job cancelled successfully"
  }
}
```

### 7. Health Check

Check API health status.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-15T10:30:00Z",
    "services": {
      "database": "connected",
      "storage": "connected",
      "gpu_runner": "available"
    }
  }
}
```

### 8. Webhook - Job Update (GPU Runner → API)

Internal endpoint for GPU runner to update job status.

**Endpoint:** `POST /webhooks/job-update`

**Headers:**
```
X-Webhook-Secret: <webhook_secret_key>
```

**Request Body:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 75,
  "message": "Rendering video frames...",
  "result_url": null,
  "error_message": null
}
```

**Response:**
```json
{
  "success": true,
  "message": "Job status updated"
}
```

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  }
}
```

**Common Error Codes:**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Job Not Found
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - GPU Runner Unavailable

## Real-time Updates

Subscribe to job status updates using Supabase Realtime:

```javascript
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

const subscription = supabase
  .from('jobs:job_id=eq.550e8400-e29b-41d4-a716-446655440000')
  .on('UPDATE', (payload) => {
    console.log('Job updated:', payload.new);
  })
  .subscribe();
```

## Rate Limits

- **Free Tier**: 5 jobs per hour, 20 jobs per day
- **Pro Tier**: 60 jobs per hour, 500 jobs per day
- **Upload**: 50 MB per file, 10 uploads per hour

## SDK Examples

### Python
```python
import requests

API_URL = "https://your-api-domain.com/api/v1"
API_KEY = "your_api_key"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Create job
response = requests.post(
    f"{API_URL}/jobs",
    headers=headers,
    json={
        "image_url": "https://...",
        "audio_url": "https://...",
        "config": {"preprocess": "crop"}
    }
)
job = response.json()["data"]

# Poll for completion
import time
while True:
    status = requests.get(
        f"{API_URL}/jobs/{job['job_id']}",
        headers=headers
    ).json()["data"]
    
    if status["status"] == "completed":
        print(f"Done! Download from: {status['result_url']}")
        break
    elif status["status"] == "failed":
        print(f"Error: {status['error_message']}")
        break
    
    time.sleep(5)
```

### JavaScript
```javascript
const createJob = async (imageUrl, audioUrl) => {
  const response = await fetch(`${API_URL}/jobs`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      image_url: imageUrl,
      audio_url: audioUrl,
      config: { preprocess: 'crop' }
    })
  });
  
  return response.json();
};

// Using Supabase realtime
supabase
  .channel('jobs')
  .on('postgres_changes', 
    { event: 'UPDATE', schema: 'public', table: 'jobs' },
    (payload) => {
      console.log('Progress:', payload.new.progress);
    }
  )
  .subscribe();