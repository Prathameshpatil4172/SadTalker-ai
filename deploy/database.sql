-- SadTalker AI - Supabase Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    credits INTEGER DEFAULT 0,
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'pro', 'enterprise')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Profile policies
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id);

-- Trigger to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url, credits, tier)
    VALUES (
        NEW.id, 
        NEW.email, 
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url',
        10, -- Free tier starts with 10 credits
        'free'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.jobs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    
    -- Status tracking
    status TEXT DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    message TEXT DEFAULT 'Waiting in queue...',
    
    -- Configuration
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Input files
    image_url TEXT NOT NULL,
    audio_url TEXT NOT NULL,
    
    -- Result
    result_url TEXT,
    result_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Error tracking
    error_message TEXT,
    error_code TEXT,
    
    -- GPU runner tracking
    runner_id TEXT,
    runner_type TEXT CHECK (runner_type IN ('colab', 'lightning', 'runpod')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Cost tracking
    credits_used INTEGER DEFAULT 1,
    processing_time_seconds INTEGER
);

-- Enable RLS on jobs
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- Job policies
CREATE POLICY "Users can view own jobs" 
    ON public.jobs FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own jobs" 
    ON public.jobs FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs" 
    ON public.jobs FOR UPDATE 
    USING (auth.uid() = user_id);

-- Index for faster queries
CREATE INDEX idx_jobs_user_id ON public.jobs(user_id);
CREATE INDEX idx_jobs_status ON public.jobs(status);
CREATE INDEX idx_jobs_created_at ON public.jobs(created_at DESC);

-- ============================================
-- FILES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.files (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    
    -- File info
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('image', 'audio', 'video')),
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    
    -- Storage
    storage_path TEXT NOT NULL,
    public_url TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Enable RLS on files
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;

-- File policies
CREATE POLICY "Users can view own files" 
    ON public.files FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own files" 
    ON public.files FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own files" 
    ON public.files FOR DELETE 
    USING (auth.uid() = user_id);

-- Index for file queries
CREATE INDEX idx_files_user_id ON public.files(user_id);
CREATE INDEX idx_files_job_id ON public.files(job_id);

-- ============================================
-- CREDIT TRANSACTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.credit_transactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    
    -- Transaction details
    amount INTEGER NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('purchase', 'usage', 'refund', 'bonus')),
    description TEXT,
    
    -- Related entities
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    payment_id TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on credit transactions
ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;

-- Credit transaction policies
CREATE POLICY "Users can view own transactions" 
    ON public.credit_transactions FOR SELECT 
    USING (auth.uid() = user_id);

-- Index for transactions
CREATE INDEX idx_credit_transactions_user_id ON public.credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_created_at ON public.credit_transactions(created_at DESC);

-- ============================================
-- GPU RUNNERS TABLE (for tracking active runners)
-- ============================================
CREATE TABLE IF NOT EXISTS public.gpu_runners (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('colab', 'lightning', 'runpod')),
    status TEXT DEFAULT 'idle' CHECK (status IN ('idle', 'busy', 'offline')),
    
    -- Capabilities
    gpu_type TEXT,
    gpu_memory_gb INTEGER,
    
    -- Current job
    current_job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    
    -- Health tracking
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    total_jobs_processed INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on gpu_runners (admin only)
ALTER TABLE public.gpu_runners ENABLE ROW LEVEL SECURITY;

-- Only service role can manage runners
CREATE POLICY "Service role can manage runners" 
    ON public.gpu_runners FOR ALL 
    USING (auth.role() = 'service_role');

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to update job status with validation
CREATE OR REPLACE FUNCTION public.update_job_status(
    p_job_id UUID,
    p_status TEXT,
    p_progress INTEGER DEFAULT NULL,
    p_message TEXT DEFAULT NULL,
    p_result_url TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE public.jobs
    SET 
        status = p_status,
        progress = COALESCE(p_progress, progress),
        message = COALESCE(p_message, message),
        result_url = COALESCE(p_result_url, result_url),
        error_message = COALESCE(p_error_message, error_message),
        completed_at = CASE WHEN p_status IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE completed_at END,
        started_at = CASE WHEN p_status = 'processing' AND started_at IS NULL THEN NOW() ELSE started_at END
    WHERE id = p_job_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to deduct credits
CREATE OR REPLACE FUNCTION public.deduct_credits(
    p_user_id UUID,
    p_amount INTEGER,
    p_job_id UUID,
    p_description TEXT DEFAULT 'Job processing'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_current_credits INTEGER;
BEGIN
    -- Get current credits
    SELECT credits INTO v_current_credits 
    FROM public.profiles 
    WHERE id = p_user_id;
    
    -- Check if enough credits
    IF v_current_credits < p_amount THEN
        RETURN FALSE;
    END IF;
    
    -- Deduct credits
    UPDATE public.profiles 
    SET credits = credits - p_amount 
    WHERE id = p_user_id;
    
    -- Record transaction
    INSERT INTO public.credit_transactions (user_id, amount, type, description, job_id)
    VALUES (p_user_id, -p_amount, 'usage', p_description, p_job_id);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get pending jobs for GPU runner
CREATE OR REPLACE FUNCTION public.get_pending_jobs(limit_count INTEGER DEFAULT 1)
RETURNS TABLE (
    job_id UUID,
    user_id UUID,
    image_url TEXT,
    audio_url TEXT,
    config JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        j.id as job_id,
        j.user_id,
        j.image_url,
        j.audio_url,
        j.config
    FROM public.jobs j
    WHERE j.status = 'pending'
    ORDER BY j.created_at ASC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- REALTIME SUBSCRIPTIONS
-- ============================================

-- Enable realtime for jobs table
ALTER PUBLICATION supabase_realtime ADD TABLE public.jobs;

-- ============================================
-- STORAGE BUCKETS
-- ============================================

-- Create storage buckets (run these in Supabase Storage UI or use supabase CLI)
-- Bucket: uploads - for user uploaded files
-- Bucket: results - for generated videos

-- Storage policies (to be configured in Supabase UI)
-- uploads bucket:
--   - Users can upload to their own folder: uploads/{user_id}/*
--   - Users can read their own files
--   - Files auto-delete after 24 hours

-- results bucket:
--   - Service role can upload
--   - Users can read their own results
--   - Results kept for 30 days

-- ============================================
-- SAMPLE DATA (for testing)
-- ============================================

-- Uncomment to insert test data
/*
INSERT INTO public.profiles (id, email, full_name, credits, tier)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'Test User', 100, 'pro');
*/