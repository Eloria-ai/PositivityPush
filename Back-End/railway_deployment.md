# Railway Deployment Guide for Positivity Push

## 🚂 Railway Deployment Setup

Railway provides an excellent platform for deploying the Positivity Push backend with automatic scaling and managed services.

## 📋 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Railway Project                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   FastAPI App   │  │  Celery Worker  │  │   Celery Beat   │  │
│  │                 │  │                 │  │                 │  │
│  │  - API Server   │  │  - Daily msgs   │  │  - Scheduler    │  │
│  │  - Webhooks     │  │  - Weekly rpts  │  │  - Periodic     │  │
│  │  - Health check │  │  - Email tasks  │  │  - Cron jobs    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│           │                     │                     │         │
│           └─────────────────────┼─────────────────────┘         │
│                                 │                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    Redis Service                            │ │
│  │                                                             │ │
│  │  - Task queue                                               │ │
│  │  - Result backend                                           │ │
│  │  - Session storage                                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Step-by-Step Deployment

### 1. Prepare Your Repository

```bash
# Ensure you're in the Back-End directory
cd Back-End

# Create .railway-ignore (optional)
echo "*.md
.env
.env.local
__pycache__/
*.pyc
.pytest_cache/
logs/
test_*.py" > .railway-ignore

# Commit all changes
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your Positivity Push repository
6. Select the `Back-End` folder as the root directory

### 3. Set Up Services

**Service 1: API Server**
- **Name**: `positivity-push-api`
- **Root Directory**: `Back-End`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python -m app.main`
- **Port**: `8000`

**Service 2: Celery Worker**
- **Name**: `positivity-push-worker`
- **Root Directory**: `Back-End`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A worker.celery_app worker --loglevel=info --concurrency=2`

**Service 3: Celery Beat**
- **Name**: `positivity-push-beat`
- **Root Directory**: `Back-End`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `celery -A worker.celery_app beat --loglevel=info`

**Service 4: Redis**
- **Name**: `redis`
- **Template**: Use Railway's Redis template
- **Or**: Use external Redis service (Redis Cloud, AWS ElastiCache)

### 4. Environment Variables

Set these in Railway dashboard for **ALL services**:

#### Required Variables
```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-production-key

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Redis (Railway will provide if using their Redis service)
REDIS_URL=redis://red-xxxxxx:6379
CELERY_BROKER_URL=redis://red-xxxxxx:6379
CELERY_RESULT_BACKEND=redis://red-xxxxxx:6379

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Stripe
STRIPE_SECRET_KEY=sk_live_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# WhatsApp
WA_TOKEN=your-whatsapp-token
WA_PHONE_ID=your-phone-id
WA_BUSINESS_NUMBER=your-business-number
WA_WEBHOOK_VERIFY_TOKEN=your-verify-token

# Email
SENDGRID_API_KEY=SG.your-sendgrid-key
FROM_EMAIL=hello@positivitypush.com

# Frontend
FRONTEND_URL=https://positivity-push.vercel.app
```

#### Optional Variables
```bash
# Memory service
MEM0_API_KEY=your-mem0-key
MEM0_URL=https://api.mem0.ai

# Monitoring
SENTRY_DSN=your-sentry-dsn (if using Sentry)
```

### 5. Service Dependencies

Configure service startup order:
1. **Redis** (starts first)
2. **API Server** (depends on Redis)
3. **Celery Worker** (depends on Redis and API)
4. **Celery Beat** (depends on Redis and API)

### 6. Domain and SSL

1. **Get your Railway domain**: `your-app-name.up.railway.app`
2. **Custom domain** (optional): Add your domain in Railway settings
3. **SSL**: Automatic with Railway

### 7. Update Frontend URLs

Update your Vercel frontend environment variables:
```bash
# In Vercel dashboard
NEXT_PUBLIC_API_URL=https://your-app-name.up.railway.app
```

### 8. Update External Webhooks

Update webhook URLs in external services:

**Stripe Webhooks:**
- URL: `https://your-app-name.up.railway.app/stripe/webhook`
- Events: `checkout.session.completed`, `invoice.payment_succeeded`, etc.

**WhatsApp Webhooks:**
- URL: `https://your-app-name.up.railway.app/whatsapp/webhook`
- Verify Token: Your `WA_WEBHOOK_VERIFY_TOKEN`

## 🔧 Production Configuration

### Health Checks

Railway automatically monitors:
- **API Health**: `GET /health`
- **Service Uptime**: Process health
- **Resource Usage**: CPU, Memory, Network

### Scaling Configuration

```bash
# In Railway dashboard, set:
# - CPU: 1-2 vCPU per service
# - Memory: 512MB - 1GB per service
# - Auto-scaling: Enable for API service
```

### Monitoring Setup

1. **Railway Metrics**: Built-in monitoring
2. **Application Logs**: `railway logs --service=positivity-push-api`
3. **Error Tracking**: Configure Sentry (optional)

### Backup Strategy

1. **Database**: Supabase handles backups
2. **Redis**: Railway Redis includes persistence
3. **Application**: Code is in Git
4. **Environment Variables**: Export from Railway dashboard

## 🧪 Testing Deployment

### 1. Health Check
```bash
curl https://your-app-name.up.railway.app/health
```

### 2. API Documentation
Visit: `https://your-app-name.up.railway.app/docs` (dev only)

### 3. Test Stripe Webhook
```bash
# Send test webhook from Stripe dashboard
# Check Railway logs for processing
```

### 4. Test WhatsApp Webhook
```bash
# Send message to your WhatsApp Business number
# Check worker logs for AI responses
```

### 5. Test Scheduled Tasks
```bash
# Check Celery Beat logs for scheduled task execution
railway logs --service=positivity-push-beat
```

## 📊 Monitoring and Logs

### View Logs
```bash
# API Server logs
railway logs --service=positivity-push-api

# Worker logs
railway logs --service=positivity-push-worker

# Beat scheduler logs
railway logs --service=positivity-push-beat

# Follow live logs
railway logs --service=positivity-push-api --follow
```

### Performance Monitoring
```bash
# View metrics in Railway dashboard:
# - CPU usage
# - Memory usage
# - Request count
# - Response times
# - Error rates
```

## 🚨 Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
railway logs --service=positivity-push-api

# Common fixes:
# - Verify environment variables
# - Check Redis connection
# - Validate Python dependencies
```

**2. Webhooks Not Working**
```bash
# Verify webhook URLs are updated
# Check CORS settings
# Validate webhook signatures
```

**3. Tasks Not Executing**
```bash
# Check worker logs
railway logs --service=positivity-push-worker

# Verify Redis connection
# Check Celery beat scheduler
```

**4. High Memory Usage**
```bash
# Scale up memory in Railway dashboard
# Optimize task concurrency
# Implement result expiration
```

### Emergency Procedures

**Restart All Services:**
```bash
railway redeploy --service=positivity-push-api
railway redeploy --service=positivity-push-worker
railway redeploy --service=positivity-push-beat
```

**Rollback Deployment:**
```bash
# Use Railway dashboard to rollback to previous deployment
# Or revert Git commit and redeploy
```

## 💰 Cost Optimization

### Railway Pricing
- **Starter Plan**: $5/month per service
- **Pro Plan**: Usage-based pricing
- **Redis**: Separate addon pricing

### Optimization Tips
1. **Combine services** where possible
2. **Use external Redis** if cheaper
3. **Optimize worker concurrency**
4. **Implement task result expiration**
5. **Monitor resource usage**

## 🔄 CI/CD Pipeline

Railway automatically deploys on Git push to main branch:

```yaml
# .github/workflows/deploy.yml (optional)
name: Deploy to Railway

on:
  push:
    branches: [main]
    paths: ['Back-End/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          # Railway handles deployment automatically
          echo "Deployment triggered by push to main"
```

## 📈 Production Checklist

- [ ] All environment variables configured
- [ ] Health checks responding
- [ ] Webhook URLs updated in external services
- [ ] SSL certificates active
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Error tracking enabled
- [ ] Documentation updated
- [ ] Load testing completed
- [ ] Security review completed

Your Positivity Push backend is now production-ready on Railway! 🚂✨