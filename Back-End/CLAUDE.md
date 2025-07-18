# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Positivity Push** is a WhatsApp-based AI coaching subscription service powered by **OpenAI GPT-4o mini**. Users get a **personalized AI coach** that learns their unique goals, challenges, and communication style to deliver tailored daily affirmations, gratitude prompts, accountability check-ins, weekly reflections, and 24/7 conversational support - all through WhatsApp.

## Current Project Status

### ✅ Complete
- **Next.js 15 Landing Page**: Main page (`app/page.tsx`) with pricing, testimonials, FAQ sections
- **Policy Pages**: Privacy, Terms, and Refund Policy pages complete
- **Frontend Components**: All UI components built with shadcn/ui and Tailwind CSS

### 🏗️ To Build
- **Success Page**: Post-payment WhatsApp activation page with QR code/link
- **Stripe Integration**: Payment processing, webhooks, subscription management, payment links in pricing components
- **Python FastAPI Backend**: API endpoints, webhook handlers, business logic
- **WhatsApp Cloud API**: Message sending/receiving, conversation handling
- **OpenAI GPT-4o mini**: Personalized AI coaching conversations
- **mem0 Integration**: Individual user context and memory storage
- **Supabase Database**: User data, subscriptions, conversation logs
- **Celery Workers**: Scheduled personalized messaging
- **Email System**: Thank you emails and invoices
- **Railway Deployment**: Backend hosting and scaling

## Complete Subscription to Active Coaching Flow

### 1. Choose & Pay
- User lands on Next.js landing page
- Picks 3-month or 6-month plan
- Completes payment via **Stripe Checkout** (to be integrated)
- **Data Collected**: Phone number, email, plan selection, payment details

### 2. Record Subscription
- Stripe fires `checkout.session.completed` webhook to FastAPI `/stripe/webhook`
- Backend verifies webhook event signature
- Extracts phone number, email & session ID from Stripe event
- **Creates subscription record in Supabase** with status "paid_pending_optin"
- **Sends thank you email** (simple welcome, invoice attached)

### 3. WhatsApp Opt-In (Critical Step)
- **After payment**, Stripe redirects to `/success` page which shows:
  - **"Activate Your AI Coach"** section
  - **WhatsApp link/button**: `https://wa.me/<BUSINESS_NUMBER>?text=POSITIVITY-PUSH%20START%20<SESSION_ID>`
  - **QR Code**: Same WhatsApp link for mobile scanning
  - **Clear instructions**: "Click the button below or scan the QR code to start chatting with your AI coach"
- User clicks link/scans QR → Opens WhatsApp with "POSITIVITY-PUSH START <SESSION_ID>" pre-filled
- User taps **Send** to activate coaching

### 4. Activate in WhatsApp
- Twilio WhatsApp API posts activation message to FastAPI `/whatsapp/webhook`
- Backend parses session ID from message text
- Matches session ID with Supabase subscription record
- **Updates record**: Links `wa_id` to subscription, status → "active"
- **Immediately sends personalized welcome message** via WhatsApp

### 5. Welcome & Personalized Daily Coaching
- AI coach sends welcome message: "Welcome to Positivity Push! I'm your personal AI coach..."
- **Onboarding conversation**: AI learns user's goals, challenges, preferences
- **Daily personalized content**: Celery workers generate and send individual affirmations, gratitude prompts, check-ins
- **Continuous learning**: Every interaction stored in mem0 for personalization

### 6. On-Demand Chat & Lifecycle Management
- **24/7 AI Conversations**: Any WhatsApp message → `/whatsapp/webhook` → GPT-4o mini + mem0 context → personalized response
- **Subscription Lifecycle** via `/stripe/webhook`:
  - Renewals → Continue coaching + confirmation email
  - Payment failures → Pause messages + recovery email
  - Cancellations → Stop coaching + farewell email

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AI Engine** | **OpenAI GPT-4o mini** | **Personalized conversational AI coach** |
| **Memory** | **mem0** | **Individual user context & learning** |
| Frontend | Next.js 15 + Vercel | Landing page, success page with WhatsApp activation |
| API | FastAPI + Railway | AI conversations, Stripe/WhatsApp webhooks |
| Queue/Jobs | Redis + Celery | Personalized scheduled messages |
| Database | Supabase | User subscriptions, personal profiles, conversations |
| Messaging | Twilio WhatsApp API | AI message delivery |
| Payments | Stripe | Subscription management, webhooks |
| Email | SendGrid/Mailgun | Thank you emails, invoices, notifications |
| Monitoring | Sentry + PostHog | Errors, usage analytics |

## Critical Pages & Endpoints

### Frontend Pages (Next.js)
- `/` - Landing page with pricing (✅ Complete)
- `/privacy`, `/terms`, `/refund-policy` - Policy pages (✅ Complete) 
- `/success` - **Post-payment WhatsApp activation page** (🏗️ To Build)
  - Shows WhatsApp link: `https://wa.me/<BUSINESS_NUMBER>?text=POSITIVITY-PUSH%20START%20<SESSION_ID>`
  - QR code for mobile users
  - Clear activation instructions

### Backend Endpoints (FastAPI)
- `POST /stripe/webhook` - Handle payment completion, subscription lifecycle
- `POST /whatsapp/webhook` - Process AI conversations and activation messages
- `GET /success?session_id=<ID>` - Generate success page with session-specific WhatsApp link

## Personalized AI Coach Features

### Individual User Learning
- **Onboarding**: AI asks about goals, challenges, communication preferences
- **Continuous Learning**: mem0 stores conversation patterns, motivators, obstacles
- **Adaptive Responses**: AI adjusts tone, content, timing based on user behavior
- **Progress Tracking**: Personal wins, setbacks, growth patterns

### Personalized Daily Content
- **Morning Affirmations**: Targeted to user's specific goals/insecurities
- **Evening Gratitude**: Contextual to user's day and experiences
- **Accountability Check-ins**: Based on user's actual commitments
- **Weekly Reflections**: AI-analyzed individual progress reports

### 24/7 Conversational Support
- **On-demand coaching**: User messages anytime for guidance
- **"BOOST" keyword**: Instant personalized motivation
- **Goal support**: AI helps break down objectives into steps
- **Challenge coaching**: Contextual advice for specific obstacles

## Database Schema (Supabase)

```sql
-- User subscriptions and profiles
subscribers (
  id, phone_number, email, wa_id, stripe_customer_id, stripe_session_id,
  plan_type, status, created_at, activated_at, timezone,
  current_timezone, timezone_updated_at, client_ip,
  personal_goals, communication_style, active_challenges
)

-- Conversation tracking
conversations (
  id, subscriber_id, message_type, content, ai_response, 
  context_used, timestamp, effectiveness_score
)

-- Progress tracking
user_progress (
  id, subscriber_id, week_start, wins, challenges,
  goal_progress, mood_patterns, coaching_adjustments
)
```

### Database Setup

Run the complete schema setup:
```bash
# In Supabase SQL Editor, run:
psql -f database/schema.sql

# Or copy/paste the contents of schema.sql
```

### Timezone Detection System

The system uses a multi-layered approach to detect user timezones:

1. **Phone-based detection (preferred)**: Extracts timezone from WhatsApp message metadata
2. **IP-based detection (fallback)**: Uses external APIs to detect timezone from IP address
3. **Manual commands**: Users can update timezone with "update timezone" command

**Limitations & Detection Priority:**

**Phone-based detection (primary method):**
- ⚠️ **Limited success rate**: WhatsApp typically provides Unix timestamps without timezone offsets
- ⚠️ **Minimal metadata**: Phone metadata rarely includes explicit timezone information  
- ⚠️ **API version dependent**: Success rate depends on WhatsApp API version and message format
- ⚠️ **Frequent failures**: Phone-based detection often returns None, requiring fallback

**IP-based detection (primary fallback):**
- ✅ **Higher reliability**: More consistent results than phone detection
- ⚠️ **External API dependency**: Requires external API calls (ip-api.com, ipapi.co)
- ⚠️ **VPN/Proxy issues**: Less accurate for users behind VPNs or proxies
- ⚠️ **Rate limits**: May hit API rate limits with high user volume

**Recommendation**: Treat IP-based detection as the primary method with phone detection as supplementary, contrary to initial assumptions.

## Environment Variables

```bash
# Core AI Integration
OPENAI_API_KEY=sk-proj-...
MEM0_URL=https://mem0.api.url
MEM0_API_KEY=mem0-key

# Twilio WhatsApp API (to be set up)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=whatsapp:+14155238886

# Stripe Integration (to be set up)
STRIPE_SECRET=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email Service
SENDGRID_API_KEY=...
FROM_EMAIL=hello@positivitypush.com

# Infrastructure
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=service-role-key
REDIS_URL=redis://...
```

## Development Commands

### Frontend Development
- `npm run dev` - Start Next.js development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Backend Development (To Be Implemented)
- `python -m app.main` - Start FastAPI server
- `celery -A worker.celery_app worker` - Start background worker
- `python -m pytest` - Run tests
- `alembic upgrade head` - Run database migrations

## Development Priority

1. **Success Page**: Create `/success` page with WhatsApp activation link/QR code
2. **Stripe Integration**: Set up products, payment links in pricing components, webhook handling
3. **Basic FastAPI**: Stripe webhook → Supabase integration
4. **WhatsApp Setup**: Business account, webhook for activation messages
5. **AI Coach Core**: GPT-4o mini + mem0 for personalized coaching
6. **Celery Workers**: Personalized daily messaging system
7. **Email System**: Thank you emails with invoices
8. **Railway Deployment**: Full backend deployment

## File Structure (Planned)

```
positivity-push/
├── Front-End/          # Current Next.js app
│   ├── app/
│   │   ├── page.tsx              # ✅ Landing page
│   │   ├── privacy/page.tsx      # ✅ Privacy policy
│   │   ├── terms/page.tsx        # ✅ Terms of service
│   │   ├── refund-policy/page.tsx # ✅ Refund policy
│   │   └── success/
│   │       └── page.tsx          # 🏗️ WhatsApp activation page
├── app/                # 🏗️ FastAPI backend
│   ├── main.py
│   ├── routers/
│   │   ├── stripe_webhook.py     # Payment processing
│   │   └── whatsapp_webhook.py   # AI conversations + activation
│   └── services/
│       ├── personalized_coach.py # GPT-4o mini integration
│       ├── mem0_client.py        # User memory/context
│       ├── whatsapp_service.py   # Message sending
│       └── email_service.py      # Thank you emails
├── worker/             # 🏗️ Celery background tasks
│   ├── celery_app.py
│   └── tasks/
│       ├── daily_messages.py     # Personalized daily content
│       └── weekly_reports.py     # Progress summaries
└── prompts/            # 🏗️ AI coaching templates
    ├── onboarding.py             # Initial user profiling
    ├── daily_content.py          # Affirmations, gratitude
    └── conversational.py         # Chat responses
```

## Key Success Metrics

- **Activation Rate**: % of paid users who complete WhatsApp opt-in
- **Engagement**: Daily/weekly message response rates
- **Personalization**: User satisfaction with AI coaching relevance
- **Retention**: Monthly subscription renewal rates
- **Support Load**: Reduction in manual customer service needs