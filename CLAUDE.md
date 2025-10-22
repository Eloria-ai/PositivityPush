# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Positivity Push** is a WhatsApp-based AI coaching subscription service powered by **OpenAI GPT-4o mini**. Users get a **personalized AI coach** that learns their unique goals, challenges, and communication style to deliver tailored daily affirmations, gratitude prompts, accountability check-ins, weekly reflections, and 24/7 conversational support - all through WhatsApp.

## Current Project Status

### ✅ Complete & Production-Ready

**Frontend (95% Complete - Front-End/ Directory)**
- **Next.js 15 Landing Page**: Complete with hero, pricing, testimonials, FAQ sections
- **Policy Pages**: Privacy, Terms, and Refund Policy (GDPR-compliant)
- **Success Page**: WhatsApp activation with QR codes and session handling
- **UI Components**: 25+ shadcn/ui components with responsive design
- **Stripe Framework**: Payment integration ready (needs payment links configured)

**Backend API (100% Production-Ready - Back-End/ Directory)**
- **FastAPI Application**: Production-grade with security middleware, request logging, rate limiting
- **Stripe Webhook**: Complete payment processing and subscription lifecycle management
- **Twilio WhatsApp Webhook**: Message handling, activation, and AI conversation processing
- **Advanced Service Layer**: AICoachService with psychological framework, OnboardingService, specialized coaches
- **Production Monitoring**: Health checks, structured logging with correlation IDs

**AI & Conversation Engine (100% Complete)**
- **OpenAI GPT-4o mini**: Advanced integration with psychological frameworks and core personality
- **Interactive Onboarding**: OnboardingService manages step-by-step preference collection
- **Enhanced Prompts**: Token-optimized prompts with psychological framework integration
- **mem0 MemoryClient**: User context and conversation memory storage
- **Specialized Coaches**: Multiple coach types for different interaction contexts

**Database & Architecture (100% Production-Ready)**
- **Supabase PostgreSQL**: Complete with advanced UUID-based schema and RLS policies
- **Comprehensive Schema**: subscribers, conversations, user_progress, daily_plans, weekly_goals, scheduled_messages
- **Dynamic Timezone Management**: current_timezone tracking with automatic updates
- **Advanced Features**: Validation triggers, performance indexes, helper functions

**Celery Worker System (100% Production Implementation)**
- **Driver+Dispatcher Pattern**: process_personalized_messages runs every 5 minutes
- **Personalized Scheduling**: User-specific timing based on onboarding preferences
- **Background Tasks**: Daily messages, weekly reports, email notifications, onboarding automation
- **Production Logging**: Structured JSON logs with structlog for observability

**Infrastructure & Deployment (100% Deployed)**
- **Railway Production**: Single-service deployment with Procfile configuration
- **Environment Management**: Comprehensive config validation and error handling
- **Production Middleware**: Security headers, request logging, rate limiting
- **Monitoring & Health**: Health endpoints, structured logging, error tracking

### 🏗️ Integration & Enhancement Opportunities
- **Stripe Payment Links**: Configure payment products in Stripe dashboard
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
- Matches session ID with Supabase subscription record via SupabaseService
- **Updates record**: Links `wa_id` to subscription, status → "active"
- **Sets fixed affirmation times** (database columns):
  - `morning_positivity`: "08:00" (8:00 AM)
  - `midday_positivity`: "12:00" (12:00 PM)  
  - `afternoon_positivity`: "16:00" (4:00 PM)
- **Triggers onboarding conversation** via OnboardingService

### 5. Interactive Conversational Onboarding (Advanced AI)
- **OnboardingService**: Manages step-by-step preference collection through natural chat
- **Collected Preferences** (stored in JSON `preferences` field):
  - `day_planning`: User's preferred morning planning time (12-hour format)
  - `accountability_checkin`: Daily progress check-in time (12-hour format)
  - `evening_gratitude`: Bedtime reflection time (12-hour format)  
  - `weekly_reflection`: Day and time for weekly review (e.g., {"day": "sunday", "time": "10:00 AM"})
  - `onboarding_completed`: Boolean tracking completion status
- **Smart Time Extraction**: OpenAI-powered parsing of casual expressions like "around 9", "maybe 7pm"
- **Context-Aware Questions**: AI asks one question at a time using optimized prompts
- **Step Management**: OnboardingStep enum tracks progress through preference collection
- **Timezone Detection**: Automatic detection with TimezoneService and client IP fallback

### 6. Personalized Daily Coaching System
- **Fixed Affirmation Schedule** (database columns, never customizable):
  - 8:00 AM: Morning motivation (`daily_affirmation`)
  - 12:00 PM: Midday energy boost (`midday_boost`)
  - 4:00 PM: Afternoon motivation (`evening_wind_down`)
- **User-Customized Messages** (based on onboarding preferences):
  - **Day Planning**: Sent at user's preferred morning time
  - **Accountability Check-ins**: Progress tracking at user's chosen time
  - **Gratitude Prompt**: Evening reflection at user's specified time
  - **Weekly Reflections**: Progress review on user's chosen day/time
- **Driver+Dispatcher Architecture**: process_personalized_messages task runs every 5 minutes
- **24/7 Conversational AI**: AICoachService with psychological framework and specialized coaches

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
| **Memory** | **mem0 MemoryClient** | **Individual user context & learning** |
| Frontend | Next.js 15 + Vercel | Landing page, success page with WhatsApp activation |
| API | FastAPI + Railway | AI conversations, Stripe/WhatsApp webhooks |
| Queue/Jobs | Redis + Celery | Driver+Dispatcher personalized scheduling |
| Database | Supabase PostgreSQL | Subscribers, conversations, progress tracking |
| **Messaging** | **Twilio WhatsApp API** | **AI message delivery & webhook processing** |
| Payments | Stripe | Subscription management, webhooks |
| Email | SendGrid | Thank you emails, invoices, notifications |
| Logging | structlog | Structured JSON logging for production observability |

## Critical Pages & Endpoints

### Frontend Pages (Next.js - Front-End/ Directory)
- `/` - Landing page with pricing (✅ Complete)
- `/privacy`, `/terms`, `/refund-policy` - Policy pages (✅ Complete) 
- `/success` - **Post-payment WhatsApp activation page** (✅ Complete)
  - Shows WhatsApp link: `https://wa.me/<BUSINESS_NUMBER>?text=POSITIVITY-PUSH%20START%20<SESSION_ID>`
  - QR code for mobile users
  - Clear activation instructions

### Backend Endpoints (FastAPI - Back-End/ Directory)
- `POST /stripe/webhook` - Handle payment completion, subscription lifecycle management
- `POST /whatsapp/webhook` - Process AI conversations and activation messages
- `GET /whatsapp/webhook` - WhatsApp webhook verification for Meta Business API
- `GET /health` - Health check endpoint for monitoring
- `GET /` - Root endpoint with service information and API documentation

## Personalized AI Coach Features

### Individual User Learning
- **OnboardingService**: Interactive preference collection through natural conversation
- **mem0 MemoryClient**: Stores conversation patterns, motivators, obstacles, and user context
- **PsychologicalFramework**: Evidence-based coaching approaches and adaptive responses
- **PatternTracker**: Analyzes user engagement and progress over time
- **Core Personality**: Consistent AI personality across all interactions

### Personalized Daily Content
- **Fixed Affirmations**: Daily (8AM), midday (12PM), afternoon (4PM) motivation using fixed times
- **Custom Scheduling**: User-defined times for planning, check-ins, gratitude based on onboarding
- **AI-Generated Content**: Dynamic messages based on user context, goals, and progress
- **Enhanced Prompts**: Token-optimized prompts for cost-effective conversations
- **Specialized Coaches**: Different coach types for various interaction contexts

### 24/7 Conversational Support
- **AICoachService**: Handles any WhatsApp message instantly with context-aware responses
- **Goal Tracking**: daily_plans and weekly_goals tables track user progress and achievements
- **Adaptive Messaging**: AI adjusts based on user engagement patterns and preferences
- **Psychological Integration**: Evidence-based frameworks guide conversation strategies

## Database Schema (Supabase)

```sql
-- User subscriptions and profiles (Production UUID-based Schema)
subscribers (
  id UUID PRIMARY KEY,
  
  -- Stripe Integration
  stripe_session_id VARCHAR(255) UNIQUE,
  stripe_customer_id VARCHAR(255),
  stripe_subscription_id VARCHAR(255),
  
  -- User Information
  email VARCHAR(255),
  phone_number VARCHAR(20),
  wa_id VARCHAR(50) UNIQUE, -- WhatsApp ID
  
  -- Subscription Details
  plan_type VARCHAR(20) CHECK (plan_type IN ('3_month', '6_month')),
  status VARCHAR(20) DEFAULT 'paid_pending_optin',
  amount_total INTEGER, -- In cents
  currency VARCHAR(3) DEFAULT 'usd',
  
  -- Personal Coaching Data
  personal_goals JSONB DEFAULT '{}',
  communication_style JSONB DEFAULT '{}',
  active_challenges JSONB DEFAULT '[]',
  timezone VARCHAR(50) DEFAULT 'UTC', -- Original timezone
  
  -- Dynamic Timezone Tracking
  current_timezone VARCHAR(50) DEFAULT 'UTC',
  timezone_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  client_ip VARCHAR(45), -- IPv6 support
  
  -- Fixed Affirmation Times (database columns)
  morning_positivity VARCHAR(5) DEFAULT '08:00',
  midday_positivity VARCHAR(5) DEFAULT '12:00',
  afternoon_positivity VARCHAR(5) DEFAULT '16:00',
  
  -- User Scheduling Preferences (JSON)
  preferences JSONB DEFAULT '{
    "day_planning": "08:00",
    "accountability_checkin": "19:00", 
    "evening_gratitude": "21:00",
    "weekly_reflection": {"day": "sunday", "time": "10:00"},
    "onboarding_completed": false
  }',
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  activated_at TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations (UUID-based)
conversations (
  id UUID PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  message_type VARCHAR(20) CHECK (message_type IN ('user', 'assistant')),
  wa_message_id VARCHAR(255),
  context_used TEXT, -- mem0 context
  effectiveness_score INTEGER CHECK (effectiveness_score BETWEEN 1 AND 5),
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Progress (UUID-based weekly tracking)
user_progress (
  id UUID PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  wins JSONB DEFAULT '[]',
  challenges JSONB DEFAULT '[]',
  goal_progress JSONB DEFAULT '{}',
  mood_patterns JSONB DEFAULT '[]',
  coaching_adjustments JSONB DEFAULT '{}',
  progress_score INTEGER CHECK (progress_score BETWEEN 1 AND 10),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(subscriber_id, week_start)
);

-- Daily Plans (Goal tracking)
daily_plans (
  id UUID PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  plan_date DATE NOT NULL,
  items JSONB DEFAULT '[]',
  raw_text TEXT,
  extracted_goals JSONB DEFAULT NULL,
  completion_status JSONB DEFAULT NULL,
  completion_response TEXT,
  completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(subscriber_id, plan_date)
);

-- Weekly Goals
weekly_goals (
  id UUID PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  week_start DATE NOT NULL,
  items JSONB DEFAULT '[]',
  source VARCHAR(20) DEFAULT 'daily_aggregate',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(subscriber_id, week_start)
);

-- Scheduled Messages (UUID-based Driver+Dispatcher)
scheduled_messages (
  id UUID PRIMARY KEY,
  subscriber_id UUID REFERENCES subscribers(id) ON DELETE CASCADE,
  message_type VARCHAR(30) CHECK (message_type IN (
    'daily_affirmation', 'midday_boost', 'evening_wind_down',
    'day_planning', 'accountability_checkin', 'gratitude_prompt', 'weekly_reflection',
    'onboarding_welcome', 'onboarding_response', 'onboarding_question'
  )),
  scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
  content TEXT, -- Pre-generated or NULL for AI-generated
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'sent', 'failed', 'cancelled')),
  sent_at TIMESTAMP WITH TIME ZONE,
  last_error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX idx_subscribers_wa_id ON subscribers(wa_id);
CREATE INDEX idx_subscribers_status ON subscribers(status);
CREATE INDEX idx_scheduled_messages_pending ON scheduled_messages(status, scheduled_for) WHERE status = 'pending';
CREATE INDEX idx_conversations_subscriber_timestamp ON conversations(subscriber_id, timestamp DESC);
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

### Backend Development (Production-Ready)
- `uvicorn app.main:app --reload` - Start FastAPI development server  
- `celery -A worker.celery_app worker --loglevel=info` - Start Celery background worker
- `celery -A worker.celery_app beat --loglevel=info` - Start Celery scheduler
- `python test_setup.py` - Test database and service connections
- `python test_whatsapp.py` - Test WhatsApp service integration

### Testing & Monitoring  
- `python -m pytest tests/` - Run test suite
- `python start_system.py` - Start complete system (API + worker + beat)

### Railway Deployment
- Railway automatically deploys from git push using `Procfile`
- Environment variables configured in Railway dashboard
- Single service deployment with web process only

## File Structure (Current Implementation)

```
positivity-push/
├── Front-End/                    # ✅ Complete Next.js Frontend
│   ├── app/
│   │   ├── page.tsx              # ✅ Landing page
│   │   ├── privacy/page.tsx      # ✅ Privacy policy
│   │   ├── terms/page.tsx        # ✅ Terms of service
│   │   ├── refund-policy/page.tsx # ✅ Refund policy
│   │   └── success/
│   │       └── page.tsx          # ✅ WhatsApp activation page
└── Back-End/                     # ✅ Complete FastAPI Backend
    ├── app/
    │   ├── main.py               # ✅ FastAPI application with middleware
    │   ├── config.py             # ✅ Environment settings with validation
    │   ├── deps.py               # ✅ Dependency injection (Supabase, Stripe, OpenAI)
    │   ├── middleware.py         # ✅ Production middleware (logging, security, rate limiting)
    │   ├── logging_config.py     # ✅ Structured logging configuration
    │   ├── routers/
    │   │   ├── stripe_webhook.py      # ✅ Payment processing & subscription lifecycle
    │   │   └── whatsapp_webhook.py    # ✅ AI conversations & activation
    │   └── services/
    │       ├── ai_coach.py            # ✅ OpenAI GPT-4o mini integration
    │       ├── supabase_client.py     # ✅ Database operations
    │       ├── whatsapp_service.py    # ✅ Twilio WhatsApp API
    │       ├── onboarding_service.py  # ✅ Interactive onboarding flow
    │       ├── mem0_client.py         # ✅ User memory/context storage
    │       ├── psychological_framework.py # ✅ Evidence-based coaching
    │       ├── enhanced_prompts.py    # ✅ Token-optimized prompts
    │       ├── specialized_coaches.py # ✅ Different coach types
    │       ├── core_personality.py   # ✅ Consistent AI personality
    │       ├── pattern_tracker.py    # ✅ User engagement analysis
    │       ├── timezone_service.py   # ✅ Dynamic timezone management
    │       ├── stripe_service.py     # ✅ Payment processing
    │       └── email_service.py      # ✅ SendGrid integration
    ├── worker/                   # ✅ Celery background tasks
    │   ├── celery_app.py              # ✅ Celery configuration with structlog
    │   └── tasks/
    │       ├── daily_messages.py      # ✅ Driver+Dispatcher personalized scheduling
    │       ├── weekly_reports.py      # ✅ Progress summaries
    │       ├── email_notifications.py # ✅ Email workflows
    │       ├── onboarding_tasks.py    # ✅ Onboarding automation
    │       └── ai_coach_async.py      # ✅ Async AI operations
    ├── prompts/                  # ✅ AI coaching templates
    │   ├── onboarding.py              # ✅ Optimized onboarding prompts
    │   ├── daily_content.py           # ✅ Daily message templates
    │   └── coach_personality.py       # ✅ Core personality definitions
    ├── database/                 # ✅ Database management
    │   └── schema.sql                 # ✅ Complete Supabase schema
    ├── tests/                    # ✅ Test suite
    │   ├── test_onboarding.py         # ✅ Onboarding flow tests
    │   └── test_scheduled_task.py     # ✅ Celery task tests
    ├── Procfile                  # ✅ Railway deployment configuration
    ├── railway.json              # ✅ Railway service configuration
    ├── requirements.txt          # ✅ Production dependencies
    └── start_system.py           # ✅ Complete system startup script
```

## Key Success Metrics

- **Activation Rate**: % of paid users who complete WhatsApp opt-in
- **Engagement**: Daily/weekly message response rates
- **Personalization**: User satisfaction with AI coaching relevance
- **Retention**: Monthly subscription renewal rates
- **Support Load**: Reduction in manual customer service needs