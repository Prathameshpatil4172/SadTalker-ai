/**
 * Frontend Configuration for SadTalker AI
 * 
 * This file contains the API configuration for your Vercel frontend.
 * Update the API_BASE_URL with your ngrok URL when running locally.
 */

// ============================================
// Configuration
// ============================================

// Get the API URL from environment variable or use default
// For local GPU setup, replace this with your ngrok URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
                     process.env.REACT_APP_API_URL || 
                     'https://your-ngrok-url.ngrok.io/api/v1';

// Supabase configuration
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 
                     process.env.REACT_APP_SUPABASE_URL || 
                     'https://your-project-id.supabase.co';

const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 
                          process.env.REACT_APP_SUPABASE_ANON_KEY || 
                          'your-anon-key';

// ============================================
// API Endpoints
// ============================================

const API_ENDPOINTS = {
    // Health check
    health: `${API_BASE_URL}/health`,
    
    // Jobs
    createJob: `${API_BASE_URL}/jobs`,
    getJob: (jobId) => `${API_BASE_URL}/jobs/${jobId}`,
    downloadResult: (jobId) => `${API_BASE_URL}/jobs/${jobId}/download`,
    streamProgress: (jobId) => `${API_BASE_URL}/jobs/${jobId}/stream`,
    cancelJob: (jobId) => `${API_BASE_URL}/jobs/${jobId}`,
    listJobs: `${API_BASE_URL}/jobs`,
};

// ============================================
// Helper Functions
// ============================================

/**
 * Get API headers with optional secret
 */
function getHeaders(includeSecret = false) {
    const headers = {
        'Content-Type': 'application/json',
    };
    
    if (includeSecret) {
        const apiSecret = process.env.NEXT_PUBLIC_API_SECRET || 
                         process.env.REACT_APP_API_SECRET;
        if (apiSecret) {
            headers['X-API-Secret'] = apiSecret;
        }
    }
    
    return headers;
}

/**
 * Create a new video generation job
 */
async function createJob(formData) {
    const response = await fetch(API_ENDPOINTS.createJob, {
        method: 'POST',
        body: formData,
        // Note: Don't set Content-Type header when using FormData
        // The browser will set it with the correct boundary
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create job');
    }
    
    return response.json();
}

/**
 * Get job status
 */
async function getJobStatus(jobId) {
    const response = await fetch(API_ENDPOINTS.getJob(jobId), {
        method: 'GET',
        headers: getHeaders(),
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get job status');
    }
    
    return response.json();
}

/**
 * Stream job progress using Server-Sent Events
 */
function streamJobProgress(jobId, onProgress) {
    const eventSource = new EventSource(API_ENDPOINTS.streamProgress(jobId));
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onProgress(data);
        
        // Close connection if job is complete or failed
        if (data.status === 'completed' || data.status === 'failed') {
            eventSource.close();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        eventSource.close();
    };
    
    // Return function to close connection
    return () => eventSource.close();
}

/**
 * Download job result
 */
async function downloadResult(jobId) {
    const response = await fetch(API_ENDPOINTS.downloadResult(jobId), {
        method: 'GET',
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to download result');
    }
    
    // If it's a direct file download
    if (response.headers.get('content-type')?.includes('video')) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sadtalker_${jobId}.mp4`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        return { success: true };
    }
    
    // If it's a JSON with download URL
    return response.json();
}

/**
 * Check API health
 */
async function checkHealth() {
    try {
        const response = await fetch(API_ENDPOINTS.health, {
            method: 'GET',
            headers: getHeaders(),
        });
        return response.ok;
    } catch (error) {
        return false;
    }
}

// ============================================
// Exports
// ============================================

// For ES modules
export {
    API_BASE_URL,
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    API_ENDPOINTS,
    getHeaders,
    createJob,
    getJobStatus,
    streamJobProgress,
    downloadResult,
    checkHealth,
};

// For CommonJS (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        API_BASE_URL,
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
        API_ENDPOINTS,
        getHeaders,
        createJob,
        getJobStatus,
        streamJobProgress,
        downloadResult,
        checkHealth,
    };
}
