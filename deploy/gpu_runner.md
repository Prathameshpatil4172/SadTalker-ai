# GPU Runner Deployment Guide (Google Colab / Lightning AI)

This guide explains how to set up the GPU runner that processes video generation jobs.

## Overview

The GPU runner:
1. Polls the API for pending jobs
2. Downloads input files (image + audio)
3. Runs SadTalker inference on GPU
4. Uploads results to storage
5. Updates job status via webhook

## Option 1: Google Colab (Free Tier)

### Setup Steps

1. **Open Colab Notebook**
   - Go to [colab.research.google.com](https://colab.research.google.com)
   - Create new notebook
   - Change runtime to GPU: Runtime → Change runtime type → GPU

2. **Install Dependencies**

```python
# Cell 1: Mount Drive (optional but recommended)
from google.colab import drive
drive.mount('/content/drive')

# Cell 2: Clone and setup
%cd /content
!git clone https://github.com/Prathameshpatil4172/SadTalker-ai.git
%cd SadTalker-ai

# Install dependencies
!pip install -q torch==2.0.1+cu118 torchvision==0.15.2+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
!pip install -q -r requirements.txt
!pip install -q supabase boto3 requests
```

3. **Download Checkpoints**

```python
# Cell 3: Download model checkpoints
import os

checkpoint_path = "/content/checkpoints"
os.makedirs(checkpoint_path, exist_ok=True)

checkpoints = {
    "SadTalker_V0.0.2_256.safetensors": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
    "mapping_00109-model.pth.tar": "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
    # Add more checkpoints as needed
}

for name, url in checkpoints.items():
    path = os.path.join(checkpoint_path, name)
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        !wget -q -O {path} {url}
    else:
        print(f"✅ {name} exists")
```

4. **Configure and Run**

```python
# Cell 4: Set environment variables
import os

os.environ['API_BASE_URL'] = 'https://your-api.onrender.com/api/v1'
os.environ['WEBHOOK_SECRET'] = 'your-webhook-secret'
os.environ['RUNNER_ID'] = 'colab-runner-1'
os.environ['RUNNER_TYPE'] = 'colab'

# Cell 5: Run the GPU runner
%cd /content/SadTalker-ai
!python deploy/colab_runner.py
```

### Keeping Colab Running

Colab free tier has limitations:
- **12-hour runtime limit**
- **May disconnect if idle**

**Tips to keep running:**
1. Use Colab Pro ($9.99/month) for longer runtimes
2. Add this to prevent idle timeout:
```python
# Cell: Keep alive
import time
while True:
    time.sleep(60)
    print("Keeping alive...")
```

3. Use browser extension to prevent auto-disconnect

## Option 2: Lightning AI (Recommended)

Lightning AI provides persistent GPU instances with better reliability.

### Setup Steps

1. **Create Account**
   - Sign up at [lightning.ai](https://lightning.ai)
   - New users get free credits

2. **Create Studio**
   - Click "New Studio"
   - Select GPU (T4 or A10G)
   - Choose PyTorch template

3. **Setup Environment**

```bash
# In Lightning terminal
git clone https://github.com/Prathameshpatil4172/SadTalker-ai.git
cd SadTalker-ai
pip install -r requirements.txt
pip install supabase boto3 requests
```

4. **Download Checkpoints**

```bash
mkdir -p /content/checkpoints
# Download checkpoints (same as Colab)
```

5. **Create .env file**

```bash
cat > .env << EOF
API_BASE_URL=https://your-api.onrender.com/api/v1
WEBHOOK_SECRET=your-webhook-secret
RUNNER_ID=lightning-runner-1
RUNNER_TYPE=lightning
EOF
```

6. **Run Runner**

```bash
python deploy/colab_runner.py
```

### Lightning AI Benefits

- Persistent storage
- No idle timeout
- Better GPU availability
- Can run 24/7
- Easy scaling

## Option 3: RunPod Serverless

For production workloads, RunPod offers serverless GPU.

### Setup

1. **Create Account** at [runpod.io](https://runpod.io)

2. **Create Serverless Endpoint**
   - Go to Serverless → New Endpoint
   - Select GPU type (RTX 3090 or A100)
   - Configure:
     - Max Workers: 3
     - Idle Timeout: 60 seconds
     - Container Image: Custom

3. **Create Dockerfile**

```dockerfile
FROM runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /workspace

# Clone repo
RUN git clone https://github.com/Prathameshpatil4172/SadTalker-ai.git

# Install dependencies
RUN pip install -r SadTalker-ai/requirements.txt
RUN pip install supabase boto3 requests

# Download checkpoints
COPY download_checkpoints.sh .
RUN bash download_checkpoints.sh

# Set working directory
WORKDIR /workspace/SadTalker-ai

# Run handler
CMD ["python", "deploy/runpod_handler.py"]
```

4. **Create Handler** (`deploy/runpod_handler.py`)

```python
import runpod
import os
from colab_runner import JobProcessor, APIClient

# Initialize
api_client = APIClient(
    os.environ['API_BASE_URL'],
    os.environ['WEBHOOK_SECRET']
)
processor = JobProcessor(api_client)

def handler(job):
    """RunPod serverless handler."""
    job_input = job['input']
    
    # Process job
    result = processor.process_job(job_input)
    
    return result

runpod.serverless.start({
    "handler": handler
})
```

## Monitoring

### Check Runner Status

API endpoint to check active runners:
```bash
curl https://your-api.onrender.com/api/v1/health
```

### Logs

**Colab:**
- View output in notebook cells
- Use `logger` module for persistent logs

**Lightning AI:**
- Built-in logging in Studio
- Download logs from UI

**RunPod:**
- CloudWatch integration
- RunPod dashboard logs

## Troubleshooting

### CUDA Out of Memory

1. Reduce batch size in job config
2. Use smaller image sizes (256 instead of 512)
3. Enable mixed precision:
```python
torch.set_default_tensor_type('torch.cuda.FloatTensor')
```

### API Connection Failed

1. Verify API_BASE_URL is correct
2. Check if API server is running
3. Test connection:
```python
import requests
response = requests.get(f"{API_BASE_URL}/health")
print(response.status_code)
```

### Checkpoints Not Found

1. Verify checkpoint_path is correct
2. Check files downloaded successfully
3. Re-download if corrupted:
```bash
rm -rf /content/checkpoints/*
# Re-run download script
```

### Job Processing Fails

Check logs for:
- Input file download errors
- CUDA errors
- Memory issues
- Webhook failures

## Performance Optimization

### Batch Processing

Process multiple jobs in sequence:
```python
while True:
    jobs = api.get_pending_jobs(limit=5)
    for job in jobs:
        processor.process_job(job)
```

### Model Warmup

Keep model loaded between jobs:
```python
# Initialize once
sadtalker = SadTalker(...)

# Process multiple jobs
for job in jobs:
    process_with_loaded_model(job)
```

### Caching

Cache downloaded files:
```python
import hashlib

def get_cache_path(url):
    filename = hashlib.md5(url.encode()).hexdigest()
    return f"/content/cache/{filename}"
```

## Cost Comparison

| Platform | GPU | Cost/Hour | Reliability |
|----------|-----|-----------|-------------|
| Colab Free | T4 | $0 | Low |
| Colab Pro | T4/V100 | $0.10 | Medium |
| Lightning | T4/A10G | $0.20-0.60 | High |
| RunPod | RTX 3090 | $0.44 | High |
| RunPod | A100 | $1.99 | High |

## Recommendation

**Development:**
- Use Colab Free for testing

**Production (Low Volume):**
- Use Colab Pro or Lightning AI

**Production (High Volume):**
- Use RunPod Serverless for auto-scaling

## Next Steps

1. Choose your GPU platform
2. Set up the runner
3. Configure environment variables
4. Test with a sample job
5. Monitor and scale as needed

See [DEPLOYMENT.md](../DEPLOYMENT.md) for full architecture overview.