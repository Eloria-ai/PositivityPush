# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Positivity Push** is a WhatsApp-based AI coaching subscription service powered by **OpenAI GPT-4o mini**. Users get a **personalized AI coach** that learns their unique goals, challenges, and communication style to deliver tailored daily affirmations, gratitude prompts, accountability check-ins, weekly reflections, and 24/7 conversational support - all through WhatsApp.

## Current Project Status

### ✅ Complete & Production-Ready

**Frontend (95% Complete)**
- **Next.js 15 Landing Page**: Complete with hero, pricing, testimonials, FAQ sections
- **Policy Pages**: Privacy, Terms, and Refund Policy (GDPR-compliant)
- **Success Page**: WhatsApp activation with QR codes and session handling
- **UI Components**: 25+ shadcn/ui components with responsive design
- **Stripe Framework**: Payment integration ready (needs payment links configured)

**Backend API (100% Production-Ready)**
- **FastAPI Application**: Enterprise-grade with middleware, security, rate limiting
- **Stripe Webhook**: Complete payment processing and subscription lifecycle
- **Twilio WhatsApp Webhook**: Message handling, activation, AI conversations
- **Service Layer**: AI coach, WhatsApp, database, email, onboarding services
- **Health Checks**: Monitoring endpoints and diagnostics

**AI & Conversation Engine (100% Complete)**
- **OpenAI GPT-4o mini**: Advanced integration with psychological frameworks
- **Natural Conversational Onboarding**: AI learns preferences through chat
- **Context-Aware Responses**: Sophisticated prompt engineering
- **mem0 Memory Service**: Complete user context and conversation storage
- **Stripe Payment Framework**: Complete integration with plan management

**Database & Architecture (100% Production-Ready)**
- **Supabase Integration**: Complete with advanced schema and RLS
- **Sophisticated Schema**: Subscribers, conversations, scheduled messages
- **Timezone Management**: Automatic detection with manual override
- **User Preferences**: JSON-based flexible preference storage

**Celery Worker System (100% Advanced Implementation)**
- **Driver+Dispatcher Pattern**: Sophisticated scheduled message architecture
- **Personalized Scheduling**: User-specific timing (not timezone broadcast)
- **Background Tasks**: Onboarding, daily messages, weekly reports, emails
- **Production Logging**: Structured JSON logs with correlation IDs

**Infrastructure & Deployment (100% Ready)**
- **Railway Configuration**: Multi-service deployment ready
- **Docker Setup**: Production-optimized containers
- **Environment Management**: Comprehensive config with validation
- **Monitoring**: Health checks, structured logging, error tracking

### 🏗️ To Complete (Optional Enhancements)
- **Email Templates**: Design branded HTML templates (SendGrid service ready)
- **Advanced Analytics**: User engagement tracking and optimization

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
- **Twilio WhatsApp API** posts activation message to FastAPI `/whatsapp/webhook`
- Backend parses session ID from message text using regex pattern matching
- Matches session ID with Supabase subscription record
- **Updates record**: Links `wa_id` to subscription, status → "active"
- **Sets fixed affirmation times**: 
  - `morning_positivity`: "08:00" (8:00 AM)
  - `midday_positivity`: "12:00" (12:00 PM)  
  - `afternoon_positivity`: "16:00" (4:00 PM)
- **Triggers natural onboarding conversation** via Celery task

### 5. Natural Conversational Onboarding (Advanced AI)
- **ChatGPT-Style Natural Conversation**: AI coach learns preferences through organic chat
- **Collected Preferences** (stored in JSON `preferences` field):
  - `day_planning`: User's preferred morning planning time (AM/PM format)
  - `accountability_checkin`: Daily progress check-in time (AM/PM format)
  - `evening_gratitude`: Bedtime reflection time (AM/PM format)  
  - `weekly_reflection`: Day and time for weekly review (e.g., {"day": "sunday", "time": "10:00 AM"})
  - `current_timezone`: Auto-detected or manually provided (IANA format)
  - `onboarding_completed`: Boolean tracking completion status
- **Smart Time Extraction**: Handles casual expressions like "around 9", "maybe 7pm"
- **Context-Aware Questions**: AI asks one question at a time, builds on previous answers
- **Completion Logic**: Automatically detects when all 5 preferences are collected

### 6. Personalized Daily Coaching System
- **Fixed Affirmation Schedule** (hardcoded in database):
  - 8:00 AM: Morning motivation and positivity
  - 12:00 PM: Midday energy boost and encouragement  
  - 4:00 PM: Afternoon motivation and focus
- **User-Customized Messages** (based on onboarding preferences):
  - **Day Planning**: Sent at user's preferred morning time
  - **Accountability Check-ins**: Progress tracking at user's chosen time
  - **Evening Gratitude**: Bedtime reflection at user's specified time
  - **Weekly Reflections**: Progress review on user's chosen day/time
- **Driver+Dispatcher Architecture**: Sophisticated Celery system processes scheduled messages
- **24/7 Conversational AI**: Instant responses to any WhatsApp message

### 7. Advanced Subscription & Lifecycle Management
- **24/7 AI Conversations**: 
  - Any WhatsApp message → Twilio webhook → `/whatsapp/webhook`
  - GPT-4o mini + psychological framework + conversation context
  - Personalized response with user memory and coaching history
- **Subscription Lifecycle** via `/stripe/webhook`:
  - `checkout.session.completed` → Create subscription + welcome email
  - `invoice.payment_succeeded` → Continue coaching + confirmation
  - `invoice.payment_failed` → Pause messages + recovery email  
  - `customer.subscription.deleted` → Stop coaching + farewell email
- **Advanced Error Handling**: Comprehensive webhook validation and retry logic
- **Structured Logging**: All events tracked with correlation IDs for debugging

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **AI Engine** | **OpenAI GPT-4o mini** | **Personalized conversational AI coach** |
| **Memory** | **mem0** | **Individual user context & learning** |
| Frontend | Next.js 15 + Vercel | Landing page, success page with WhatsApp activation |
| API | FastAPI + Railway | AI conversations, Stripe/WhatsApp webhooks |
| Queue/Jobs | Redis + Celery | Personalized scheduled messages |
| Database | Supabase | User subscriptions, personal profiles, conversations |
| **Messaging** | **Twilio WhatsApp API** | **AI message delivery & webhook processing** |
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
-- User subscriptions and profiles (Production Schema)
subscribers (
  id UUID PRIMARY KEY,
  phone_number VARCHAR(20) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  wa_id VARCHAR(50) UNIQUE,  -- Twilio WhatsApp ID
  
  -- Stripe integration
  stripe_customer_id VARCHAR(255) UNIQUE,
  stripe_session_id VARCHAR(255) UNIQUE,
  stripe_subscription_id VARCHAR(255) UNIQUE,
  
  -- Subscription management
  plan_type VARCHAR(20) NOT NULL,  -- '3_month' or '6_month'
  status VARCHAR(20) DEFAULT 'paid_pending_optin',  -- 'active', 'cancelled', 'past_due'
  amount DECIMAL(10,2),
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  activated_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Advanced timezone management
  original_timezone VARCHAR(50),     -- From IP detection
  current_timezone VARCHAR(50),      -- Current/updated timezone (IANA format)
  timezone_updated_at TIMESTAMPTZ,
  client_ip INET,                    -- For timezone detection
  
  -- Fixed affirmation times (hardcoded, never change)
  morning_positivity TIME DEFAULT '08:00',   -- 8:00 AM
  midday_positivity TIME DEFAULT '12:00',    -- 12:00 PM
  afternoon_positivity TIME DEFAULT '16:00', -- 4:00 PM
  
  -- User preferences (JSON field for flexibility)
  preferences JSONB DEFAULT '{}',
  /* preferences structure:
  {
    "day_planning": "9:00 AM",              -- User's morning planning time
    "accountability_checkin": "7:00 PM",    -- Daily progress check-in time
    "evening_gratitude": "10:00 PM",        -- Bedtime gratitude time
    "weekly_reflection": {                   -- Weekly reflection schedule
      "day": "sunday",
      "time": "11:00 AM"
    },
    "onboarding_completed": true,            -- Onboarding completion status
    "onboarding_step": null                  -- Current onboarding step (null when complete)
  }
  */
  
  -- Personal coaching data
  personal_goals JSONB,
  communication_style JSONB,
  active_challenges JSONB
);

-- Conversation tracking
conversations (
  id BIGSERIAL PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  message_type VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
  content TEXT NOT NULL,
  ai_response TEXT,
  wa_message_id VARCHAR(255),  -- Twilio message ID
  context_used JSONB,          -- AI context at time of response
  timestamp TIMESTAMPTZ DEFAULT NOW(),
  effectiveness_score INTEGER  -- 1-5 rating for response quality
);

-- Scheduled messages (Driver+Dispatcher Architecture)
scheduled_messages (
  id BIGSERIAL PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  message_type VARCHAR(50) NOT NULL,  -- 'daily_affirmation', 'accountability_checkin', etc.
  content TEXT,                       -- Pre-generated content (for onboarding) or NULL (generate on dispatch)
  scheduled_for TIMESTAMPTZ NOT NULL, -- When to send the message
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'queued', 'sent', 'failed'
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  last_error TEXT                     -- Error details if status = 'failed'
);

-- Progress tracking
user_progress (
  id BIGSERIAL PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  wins JSONB,
  challenges JSONB,
  goal_progress JSONB,
  mood_patterns JSONB,
  coaching_adjustments JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_scheduled_messages_pending ON scheduled_messages(status, scheduled_for) WHERE status = 'pending';
CREATE INDEX idx_conversations_subscriber ON conversations(subscriber_id, timestamp DESC);
CREATE INDEX idx_subscribers_status ON subscribers(status) WHERE status = 'active';
```

## Environment Variables

```bash
# Core AI Integration
OPENAI_API_KEY=sk-proj-...
MEM0_URL=https://mem0.api.url
MEM0_API_KEY=mem0-key

# WhatsApp Business (to be set up)
WA_TOKEN=WhatsApp_Business_Token
WA_PHONE_ID=WhatsApp_Phone_Number_ID  
WA_BUSINESS_NUMBER=1234567890

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