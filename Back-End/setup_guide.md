# Positivity Push Backend Setup Guide

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
cd Back-End
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
cp .env.example .env
```

Then edit `.env` with your actual API keys:

#### Required for AI Coach Testing:
- `OPENAI_API_KEY` - Get from [OpenAI Platform](https://platform.openai.com)
- `MEM0_API_KEY` - Get from [mem0.ai](https://mem0.ai) (optional for basic testing)

#### Required for Full Functionality:
- `SUPABASE_URL` & `SUPABASE_SERVICE_KEY` - From [Supabase](https://supabase.com)
- `STRIPE_SECRET_KEY` & `STRIPE_WEBHOOK_SECRET` - From [Stripe](https://stripe.com)
- `WA_TOKEN` & `WA_PHONE_ID` - From [Meta for Developers](https://developers.facebook.com)
- `SENDGRID_API_KEY` - From [SendGrid](https://sendgrid.com)

### 3. Set Up Database (Supabase)
1. Create a new project at [supabase.com](https://supabase.com)
2. Go to SQL Editor
3. Run the schema from `database/schema.sql`
4. Copy your project URL and service role key to `.env`

### 4. Test AI Coach
```bash
python test_ai_coach.py
```

This will test:
- ✅ OpenAI GPT-4o mini connection
- ✅ mem0 memory system
- ✅ Welcome message generation
- ✅ Daily affirmations
- ✅ Gratitude prompts
- ✅ Conversation flow
- ✅ Memory persistence

### 5. Run the API Server
```bash
python -m app.main
```

Visit `http://localhost:8000/docs` to see the API documentation.

## 🔧 Service Setup Instructions

### OpenAI Setup
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account and add billing
3. Generate API key
4. Add to `.env` as `OPENAI_API_KEY`

### mem0 Setup (Optional but Recommended)
1. Go to [mem0.ai](https://mem0.ai)
2. Sign up for account
3. Get API key from dashboard
4. Add to `.env` as `MEM0_API_KEY`

### Supabase Database Setup
1. Create project at [supabase.com](https://supabase.com)
2. Go to Settings → API → Copy:
   - Project URL → `SUPABASE_URL`
   - Service role key → `SUPABASE_SERVICE_KEY`
3. Go to SQL Editor
4. Copy and run the entire `database/schema.sql` file

### Stripe Setup
1. Go to [stripe.com](https://stripe.com) dashboard
2. Get API keys from Developers → API keys:
   - Secret key → `STRIPE_SECRET_KEY` 
   - Publishable key → `STRIPE_PUBLISHABLE_KEY`
3. Set up webhook endpoint:
   - URL: `https://your-api.com/stripe/webhook`
   - Events: `checkout.session.completed`, `invoice.payment_succeeded`, etc.
   - Copy webhook secret → `STRIPE_WEBHOOK_SECRET`

### WhatsApp Business API Setup
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create WhatsApp Business app
3. Get Phone Number ID and Access Token
4. Set webhook URL: `https://your-api.com/whatsapp/webhook`
5. Add values to `.env`:
   - `WA_TOKEN`
   - `WA_PHONE_ID`
   - `WA_BUSINESS_NUMBER`
   - `WA_WEBHOOK_VERIFY_TOKEN`

### SendGrid Email Setup
1. Create account at [sendgrid.com](https://sendgrid.com)
2. Go to Settings → API Keys
3. Create API key with mail send permissions
4. Add to `.env` as `SENDGRID_API_KEY`
5. Set `FROM_EMAIL` to your verified sender email

## 🧪 Testing Strategy

### Phase 1: Core AI Testing
```bash
python test_ai_coach.py
```

### Phase 2: API Endpoint Testing
```bash
# Start the server
python -m app.main

# Test health check
curl http://localhost:8000/health

# Test Stripe webhook (with proper payload)
curl -X POST http://localhost:8000/stripe/webhook
```

### Phase 3: WhatsApp Integration Testing
1. Set up ngrok for local webhook testing:
   ```bash
   ngrok http 8000
   ```
2. Update WhatsApp webhook URL to ngrok URL
3. Send test message to your WhatsApp Business number

## 🚀 Deployment (Railway)
1. Connect Railway to your GitHub repo
2. Set environment variables in Railway dashboard
3. Deploy backend service
4. Update webhook URLs to Railway domain

## 📋 Troubleshooting

### Common Issues:
1. **OpenAI API errors**: Check API key and billing
2. **mem0 connection fails**: Verify API key or skip for basic testing
3. **Supabase connection fails**: Check URL and service role key
4. **Import errors**: Make sure you're in the Back-End directory

### Support:
- Check logs in `/logs/` directory
- Review error messages in test output
- Verify all environment variables are set correctly