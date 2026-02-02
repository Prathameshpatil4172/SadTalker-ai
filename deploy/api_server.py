"""
SadTalker AI - Flask API Server for Render/Railway Deployment
This is the lightweight API layer that handles job management and delegates GPU work to external runners.
"""

import os
import uuid
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from supabase import create_client, Client
import boto3
from botocore.exceptions import ClientError

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SUPABASE_URL'] = os.environ.get('SUPABASE_URL')
app.config['SUPABASE_KEY'] = os.environ.get('SUPABASE_SERVICE_KEY')
app.config['AWS_ACCESS_KEY'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
app.config['S3_BUCKET'] = os.environ.get('S3_BUCKET_NAME')
app.config['S3_REGION'] = os.environ.get('AWS_REGION', 'us-east-1')
app.config['WEBHOOK_SECRET'] = os.environ.get('WEBHOOK_SECRET')
app.config['MAX_FILE_SIZE'] = 50 * 1024 * 1024  # 50MB

# Enable CORS for Vercel frontend
CORS(app, origins=[
    "https://sadtalker-ai.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173"
])

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize Supabase client
supabase: Client = create_client(
    app.config['SUPABASE_URL'],
    app.config['SUPABASE_KEY']
)

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY'],
    aws_secret_access_key=app.config['AWS_SECRET_KEY'],
    region_name=app.config['S3_REGION']
)

# ============================================
# AUTHENTICATION HELPERS
# ============================================

def get_auth_user():
    """Extract and verify JWT token from Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        return user.user if user else None
    except Exception:
        return None

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_auth_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication required'}
            }), 401
        return f(user, *args, **kwargs)
    return decorated_function

def verify_webhook_signature(payload: str, signature: str) -> bool:
    """Verify webhook signature from GPU runner."""
    expected = hmac.new(
        app.config['WEBHOOK_SECRET'].encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'success': False,
        'error': {'code': 'RATE_LIMITED', 'message': 'Too many requests. Please try again later.'}
    }), 429

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}
    }), 500

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        supabase.table('jobs').select('count').limit(1).execute()
        
        return jsonify({
            'success': True,
            'data': {
                'status': 'healthy',
                'version': '1.0.0',
                'timestamp': datetime.utcnow().isoformat(),
                'services': {
                    'database': 'connected',
                    'storage': 'connected'
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'UNHEALTHY', 'message': str(e)}
        }), 503

# ============================================
# FILE UPLOAD
# ============================================

@app.route('/api/v1/upload', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")
def get_upload_url(user):
    """Generate presigned URL for direct S3 upload."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 'BAD_REQUEST', 'message': 'Request body required'}
        }), 400
    
    filename = data.get('filename')
    content_type = data.get('content_type')
    file_size = data.get('file_size', 0)
    
    # Validate inputs
    if not filename or not content_type:
        return jsonify({
            'success': False,
            'error': {'code': 'BAD_REQUEST', 'message': 'filename and content_type required'}
        }), 400
    
    if file_size > app.config['MAX_FILE_SIZE']:
        return jsonify({
            'success': False,
            'error': {'code': 'FILE_TOO_LARGE', 'message': f'File size exceeds {app.config["MAX_FILE_SIZE"] // (1024*1024)}MB limit'}
        }), 400
    
    # Validate content type
    allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'audio/wav', 'audio/mpeg', 'audio/mp3']
    if content_type not in allowed_types:
        return jsonify({
            'success': False,
            'error': {'code': 'INVALID_TYPE', 'message': f'Content type {content_type} not allowed'}
        }), 400
    
    # Generate unique filename
    file_ext = filename.split('.')[-1]
    unique_filename = f"{user.id}/{uuid.uuid4()}.{file_ext}"
    
    try:
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': app.config['S3_BUCKET'],
                'Key': f"uploads/{unique_filename}",
                'ContentType': content_type
            },
            ExpiresIn=300  # 5 minutes
        )
        
        # Store file record in database
        file_record = {
            'user_id': str(user.id),
            'filename': unique_filename,
            'original_name': filename,
            'file_type': 'image' if content_type.startswith('image') else 'audio',
            'mime_type': content_type,
            'size_bytes': file_size,
            'storage_path': f"uploads/{unique_filename}",
            'public_url': f"https://{app.config['S3_BUCKET']}.s3.{app.config['S3_REGION']}.amazonaws.com/uploads/{unique_filename}",
            'expires_at': (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        
        supabase.table('files').insert(file_record).execute()
        
        return jsonify({
            'success': True,
            'data': {
                'upload_url': presigned_url,
                'file_url': file_record['public_url'],
                'expires_in': 300,
                'max_file_size': app.config['MAX_FILE_SIZE']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'UPLOAD_ERROR', 'message': str(e)}
        }), 500

# ============================================
# JOB MANAGEMENT
# ============================================

@app.route('/api/v1/jobs', methods=['POST'])
@require_auth
@limiter.limit("5 per hour")  # Free tier limit
def create_job(user):
    """Create a new video generation job."""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 'BAD_REQUEST', 'message': 'Request body required'}
        }), 400
    
    image_url = data.get('image_url')
    audio_url = data.get('audio_url')
    config = data.get('config', {})
    
    if not image_url or not audio_url:
        return jsonify({
            'success': False,
            'error': {'code': 'BAD_REQUEST', 'message': 'image_url and audio_url required'}
        }), 400
    
    # Validate config
    valid_config = {
        'preprocess': config.get('preprocess', 'crop'),
        'still_mode': config.get('still_mode', False),
        'use_enhancer': config.get('use_enhancer', False),
        'batch_size': min(config.get('batch_size', 2), 10),
        'size': config.get('size', 256),
        'pose_style': config.get('pose_style', 0),
        'exp_scale': config.get('exp_scale', 1.0),
        'use_ref_video': config.get('use_ref_video', False),
        'ref_video_url': config.get('ref_video_url'),
        'ref_info': config.get('ref_info', 'pose'),
        'use_idle_mode': config.get('use_idle_mode', False),
        'length_of_audio': config.get('length_of_audio', 0),
        'use_blink': config.get('use_blink', True)
    }
    
    try:
        # Check user credits
        profile = supabase.table('profiles').select('credits').eq('id', str(user.id)).single().execute()
        
        if not profile.data or profile.data['credits'] < 1:
            return jsonify({
                'success': False,
                'error': {'code': 'INSUFFICIENT_CREDITS', 'message': 'Not enough credits. Please purchase more.'}
            }), 403
        
        # Create job
        job_data = {
            'user_id': str(user.id),
            'status': 'pending',
            'progress': 0,
            'message': 'Waiting in queue...',
            'config': valid_config,
            'image_url': image_url,
            'audio_url': audio_url,
            'credits_used': 1
        }
        
        result = supabase.table('jobs').insert(job_data).execute()
        job = result.data[0]
        
        # Deduct credits
        supabase.rpc('deduct_credits', {
            'p_user_id': str(user.id),
            'p_amount': 1,
            'p_job_id': job['id'],
            'p_description': 'Video generation job'
        }).execute()
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job['id'],
                'status': job['status'],
                'created_at': job['created_at'],
                'estimated_time': 120  # seconds
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'JOB_CREATE_ERROR', 'message': str(e)}
        }), 500

@app.route('/api/v1/jobs/<job_id>', methods=['GET'])
@require_auth
def get_job(user, job_id):
    """Get job status and details."""
    try:
        result = supabase.table('jobs').select('*').eq('id', job_id).eq('user_id', str(user.id)).single().execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'Job not found'}
            }), 404
        
        job = result.data
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job['id'],
                'status': job['status'],
                'progress': job['progress'],
                'message': job['message'],
                'config': job['config'],
                'input_files': {
                    'image': job['image_url'],
                    'audio': job['audio_url']
                },
                'result_url': job['result_url'],
                'created_at': job['created_at'],
                'started_at': job['started_at'],
                'completed_at': job['completed_at'],
                'error_message': job['error_message']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'JOB_FETCH_ERROR', 'message': str(e)}
        }), 500

@app.route('/api/v1/jobs', methods=['GET'])
@require_auth
def list_jobs(user):
    """List user's jobs with pagination."""
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)
    status_filter = request.args.get('status')
    
    offset = (page - 1) * limit
    
    try:
        query = supabase.table('jobs').select('*', count='exact').eq('user_id', str(user.id))
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        total = result.count if hasattr(result, 'count') else len(result.data)
        total_pages = (total + limit - 1) // limit
        
        jobs = [{
            'job_id': job['id'],
            'status': job['status'],
            'preview_url': job.get('result_url'),  # Could be a thumbnail
            'created_at': job['created_at']
        } for job in result.data]
        
        return jsonify({
            'success': True,
            'data': {
                'jobs': jobs,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': total_pages
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'LIST_ERROR', 'message': str(e)}
        }), 500

@app.route('/api/v1/jobs/<job_id>/cancel', methods=['POST'])
@require_auth
def cancel_job(user, job_id):
    """Cancel a pending or processing job."""
    try:
        result = supabase.table('jobs').select('status').eq('id', job_id).eq('user_id', str(user.id)).single().execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'Job not found'}
            }), 404
        
        if result.data['status'] not in ['pending', 'processing']:
            return jsonify({
                'success': False,
                'error': {'code': 'INVALID_STATE', 'message': f"Cannot cancel job in {result.data['status']} state"}
            }), 400
        
        # Update job status
        supabase.table('jobs').update({
            'status': 'cancelled',
            'message': 'Job cancelled by user',
            'completed_at': datetime.utcnow().isoformat()
        }).eq('id', job_id).execute()
        
        # Refund credits
        supabase.table('credit_transactions').insert({
            'user_id': str(user.id),
            'amount': 1,
            'type': 'refund',
            'description': 'Job cancellation refund',
            'job_id': job_id
        }).execute()
        
        supabase.table('profiles').update({
            'credits': supabase.rpc('increment', {'x': 1})
        }).eq('id', str(user.id)).execute()
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'status': 'cancelled',
                'message': 'Job cancelled successfully'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'CANCEL_ERROR', 'message': str(e)}
        }), 500

@app.route('/api/v1/jobs/<job_id>/result', methods=['GET'])
@require_auth
def get_result(user, job_id):
    """Get job result download URL."""
    try:
        result = supabase.table('jobs').select('*').eq('id', job_id).eq('user_id', str(user.id)).single().execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_FOUND', 'message': 'Job not found'}
            }), 404
        
        job = result.data
        
        if job['status'] != 'completed':
            return jsonify({
                'success': False,
                'error': {'code': 'NOT_READY', 'message': f"Job is {job['status']}. Result not available yet."}
            }), 400
        
        if not job.get('result_url'):
            return jsonify({
                'success': False,
                'error': {'code': 'NO_RESULT', 'message': 'Result URL not available'}
            }), 404
        
        # Generate presigned URL for download (if using S3)
        try:
            video_key = job['result_url'].split('.com/')[-1]
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': app.config['S3_BUCKET'],
                    'Key': video_key,
                    'ResponseContentDisposition': f'attachment; filename="result_{job_id}.mp4"'
                },
                ExpiresIn=3600  # 1 hour
            )
        except:
            download_url = job['result_url']
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'download_url': download_url,
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'video_info': job.get('result_metadata', {})
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'RESULT_ERROR', 'message': str(e)}
        }), 500

# ============================================
# WEBHOOKS (GPU Runner → API)
# ============================================

@app.route('/api/v1/webhooks/job-update', methods=['POST'])
def webhook_job_update():
    """Receive job updates from GPU runner."""
    signature = request.headers.get('X-Webhook-Secret')
    
    if not signature or not verify_webhook_signature(request.get_data(as_text=True), signature):
        return jsonify({
            'success': False,
            'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid webhook signature'}
        }), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': {'code': 'BAD_REQUEST', 'message': 'Request body required'}
        }), 400
    
    job_id = data.get('job_id')
    status = data.get('status')
    progress = data.get('progress')
    message = data.get('message')
    result_url = data.get('result_url')
    error_message = data.get('error_message')
    
    try:
        # Update job using RPC function
        supabase.rpc('update_job_status', {
            'p_job_id': job_id,
            'p_status': status,
            'p_progress': progress,
            'p_message': message,
            'p_result_url': result_url,
            'p_error_message': error_message
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Job status updated'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {'code': 'UPDATE_ERROR', 'message': str(e)}
        }), 500

@app.route('/api/v1/webhooks/runner-heartbeat', methods=['POST'])
def webhook_runner_heartbeat():
    """Receive heartbeat from GPU runner."""
    signature = request.headers.get('X-Webhook-Secret')
    
    if not signature or not verify_webhook_signature(request.get_data(as_text=True), signature):
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Invalid signature'}}), 401
    
    data = request.get_json()
    runner_id = data.get('runner_id')
    runner_type = data.get('runner_type')
    status = data.get('status')
    current_job_id = data.get('current_job_id')
    
    try:
        # Upsert runner record
        supabase.table('gpu_runners').upsert({
            'id': runner_id,
            'type': runner_type,
            'status': status,
            'current_job_id': current_job_id,
            'last_heartbeat': datetime.utcnow().isoformat()
        }).execute()
        
        return jsonify({'success': True, 'message': 'Heartbeat recorded'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'ERROR', 'message': str(e)}}), 500

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)