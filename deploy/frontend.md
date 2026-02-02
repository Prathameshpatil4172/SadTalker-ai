# Frontend Deployment Guide (Vercel)

This guide explains how to deploy the SadTalker AI frontend to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **API Server**: Your Render/Railway API should be deployed and running
4. **Supabase Project**: Database and auth should be configured

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/       # React components
│   ├── hooks/           # Custom hooks
│   ├── lib/             # Utilities
│   ├── pages/           # Page components
│   ├── services/        # API services
│   ├── store/           # State management
│   └── App.tsx          # Main app
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Environment Variables

Create a `.env.local` file for local development:

```env
# API Configuration
VITE_API_BASE_URL=https://your-api.onrender.com/api/v1

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

For Vercel deployment, add these in the Vercel Dashboard:
1. Go to Project Settings → Environment Variables
2. Add each variable from above

## Deployment Steps

### Option 1: Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   cd frontend
   vercel --prod
   ```

### Option 2: GitHub Integration (Recommended)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Import Project in Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Select the `frontend` directory as root
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

3. **Configure Environment Variables**
   - Add all environment variables from above
   - Click Deploy

### Option 3: Vercel.json Config

The included [`vercel.json`](vercel.json) handles the configuration:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": { "distDir": "dist" }
    }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

## Frontend Architecture

### Key Components

1. **AuthContext** - Manages user authentication with Supabase
2. **JobContext** - Manages job state and real-time updates
3. **UploadService** - Handles file uploads to S3 via presigned URLs
4. **JobService** - API calls for job management
5. **RealtimeService** - Supabase realtime subscriptions

### File Upload Flow

```
User selects file
    ↓
Frontend validates (type, size)
    ↓
Request presigned URL from API
    ↓
Upload directly to S3
    ↓
Confirm upload, get public URL
    ↓
Create job with file URLs
```

### Real-time Updates

```typescript
// Subscribe to job updates
supabase
  .channel('jobs')
  .on('postgres_changes', 
    { event: 'UPDATE', schema: 'public', table: 'jobs' },
    (payload) => {
      updateJobInUI(payload.new);
    }
  )
  .subscribe();
```

## Custom Domain (Optional)

1. **Add Domain in Vercel**
   - Project Settings → Domains
   - Add your domain (e.g., `sadtalker-ai.com`)

2. **Configure DNS**
   - Add CNAME record pointing to `cname.vercel-dns.com`
   - Or use A record for apex domain

3. **Update CORS**
   - Add your custom domain to API server's CORS whitelist

## Troubleshooting

### Build Failures

```bash
# Check build locally
npm run build

# Check for TypeScript errors
npx tsc --noEmit
```

### API Connection Issues

1. Verify `VITE_API_BASE_URL` is correct
2. Check API CORS settings include Vercel domain
3. Test API health endpoint: `GET {API_URL}/health`

### Environment Variables Not Working

- Variables must be prefixed with `VITE_` for Vite
- Redeploy after adding variables
- Check Vercel deployment logs

## Performance Optimization

1. **Enable Vercel Edge Network**
   - Automatic with all deployments

2. **Optimize Images**
   ```bash
   npm install -D @vercel/image-optimization
   ```

3. **Enable Compression**
   - Vercel handles this automatically

4. **Code Splitting**
   ```typescript
   // Lazy load heavy components
   const VideoPlayer = lazy(() => import('./VideoPlayer'));
   ```

## Monitoring

1. **Vercel Analytics**
   - Enable in Project Settings
   - Tracks Core Web Vitals

2. **Error Tracking**
   - Integrate Sentry:
   ```bash
   npm install @sentry/react
   ```

## Cost Considerations

| Feature | Free Tier | Pro ($20/mo) |
|---------|-----------|--------------|
| Bandwidth | 100GB | 1TB |
| Build Executions | 6,000 min | 24,000 min |
| Team Members | 1 | Unlimited |
| Analytics | Basic | Advanced |

For most hobby projects, the free tier is sufficient.

## Next Steps

1. Deploy your API server (Render/Railway)
2. Set up Supabase database
3. Configure environment variables
4. Deploy frontend to Vercel
5. Test end-to-end flow
6. Set up custom domain (optional)

See [DEPLOYMENT.md](../DEPLOYMENT.md) for the full architecture overview.