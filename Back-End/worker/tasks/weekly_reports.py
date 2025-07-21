"""
Weekly Progress Report Tasks for Positivity Push
Generates and sends personalized weekly reflection reports.
"""

from celery import shared_task
from datetime import datetime, timedelta
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from services.ai_coach import AICoachService
from services.whatsapp_service import WhatsAppService
from services.supabase_client import SupabaseService
from services.email_service import EmailService
from deps import get_supabase_client
from config import settings

# Use structured logging
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_weekly_progress_reports(self):
    """
    Generate and send personalized weekly progress reports to all active users
    """
    logger.info("weekly_reports_start",
               task_name="send_weekly_progress_reports")
    
    try:
        return asyncio.run(_send_weekly_progress_reports_async())
    except Exception as e:
        logger.error("weekly_reports_task_error",
                    error=str(e),
                    retry_count=self.request.retries,
                    exc_info=True)
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes

async def _send_weekly_progress_reports_async():
    """Async implementation of weekly progress reports"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    ai_coach = AICoachService()
    whatsapp_service = WhatsAppService()
    
    # Get all active subscribers
    subscribers = await supabase_service.get_active_subscribers()
    
    sent_count = 0
    error_count = 0
    
    for subscriber in subscribers:
        try:
            # Generate weekly progress report
            progress_report = await _generate_weekly_progress_report(
                subscriber, supabase_service, ai_coach
            )
            
            if progress_report:
                # Send via WhatsApp
                if subscriber.get('wa_id'):
                    success = await whatsapp_service.send_message(
                        to=subscriber['wa_id'],
                        message=progress_report
                    )
                    
                    if success:
                        # Log the sent report
                        await supabase_service.log_conversation(
                            subscriber_id=subscriber['id'],
                            content=progress_report,
                            message_type='assistant'
                        )
                        
                        # Store progress data
                        await _store_weekly_progress_data(
                            subscriber, supabase_service
                        )
                        
                        sent_count += 1
                        logger.info("weekly_report_sent",
                                   user_id=subscriber['id'])
                    else:
                        error_count += 1
                        logger.error("weekly_report_send_failed",
                                    user_id=subscriber['id'])
            else:
                logger.warning("weekly_report_generation_failed",
                              user_id=subscriber['id'])
            
        except Exception as e:
            error_count += 1
            logger.error("weekly_report_user_error",
                        user_id=subscriber.get('id', 'unknown'),
                        error=str(e),
                        exc_info=True)
    
    logger.info("weekly_reports_complete",
               sent_count=sent_count,
               error_count=error_count)
    return {"sent": sent_count, "errors": error_count}

async def _generate_weekly_progress_report(
    subscriber: dict, 
    supabase_service: SupabaseService, 
    ai_coach: AICoachService
) -> str:
    """Generate personalized weekly progress report for a user"""
    
    try:
        # Get conversation history for the past week
        week_conversations = await _get_week_conversations(subscriber['id'], supabase_service)
        
        if not week_conversations:
            # If no conversations this week, send encouraging check-in
            return await _generate_gentle_check_in(subscriber, ai_coach)
        
        # Analyze the week's conversations
        week_analysis = await _analyze_week_conversations(week_conversations)
        
        # Generate personalized progress report
        report_prompt = f"""
        Create a warm, personalized weekly progress report for this user. Based on their conversations this week, include:
        
        USER CONTEXT:
        - Name: {subscriber.get('email', '').split('@')[0] if subscriber.get('email') else 'friend'}
        - Plan: {subscriber.get('plan_type', '3_month')}
        - Goals: {subscriber.get('personal_goals', {})}
        
        WEEK'S CONVERSATIONS SUMMARY:
        {week_analysis}
        
        REPORT STRUCTURE:
        1. Warm greeting acknowledging their week
        2. Celebrate specific progress or insights mentioned
        3. Acknowledge any challenges with empathy
        4. Highlight growth patterns you noticed
        5. Gentle encouragement for the coming week
        6. Optional: One meaningful question for reflection
        
        STYLE:
        - Personal and warm (use their name/preferred address)
        - 100-150 words total
        - Specific to their actual conversations
        - Encouraging but authentic
        - End with forward-looking positivity
        
        Generate a progress report that makes them feel seen, appreciated, and motivated.
        """
        
        # Get weekly memories from mem0
        weekly_memories = await ai_coach.mem0_service.get_memories(subscriber['id'], limit=20)
        
        # Generate the report using AI coach
        response = ai_coach.openai_client.chat.completions.create(
            model=ai_coach.model,
            messages=[
                {"role": "system", "content": report_prompt},
                {"role": "user", "content": f"Weekly memories: {weekly_memories}"}
            ],
            max_tokens=250,
            temperature=0.8
        )
        
        report = response.choices[0].message.content.strip()
        
        # Store this report generation in mem0
        await ai_coach.mem0_service.add_memory(
            user_id=subscriber['id'],
            message=f"Generated weekly progress report: {report}",
            metadata={"interaction_type": "weekly_report", "date": datetime.now().isoformat()}
        )
        
        return report
        
    except Exception as e:
        logger.error("weekly_report_generation_error",
                    user_id=subscriber['id'],
                    error=str(e),
                    exc_info=True)
        return None

async def _get_week_conversations(subscriber_id: str, supabase_service: SupabaseService) -> list:
    """Get all conversations for the past week"""
    
    try:
        # Get conversations from the past 7 days
        week_start = datetime.utcnow() - timedelta(days=7)
        
        # Get recent conversation history
        all_conversations = await supabase_service.get_conversation_history(subscriber_id, limit=100)
        
        # Filter to this week only
        week_conversations = []
        for conv in all_conversations:
            conv_date = datetime.fromisoformat(conv['timestamp'])
            if conv_date >= week_start:
                week_conversations.append(conv)
        
        return week_conversations
        
    except Exception as e:
        logger.error("week_conversations_error",
                    error=str(e),
                    exc_info=True)
        return []

async def _analyze_week_conversations(conversations: list) -> str:
    """Analyze the week's conversations to identify patterns and themes"""
    
    if not conversations:
        return "No conversations this week."
    
    # Separate user messages and assistant messages
    user_messages = [c['content'] for c in conversations if c['message_type'] == 'user']
    assistant_messages = [c['content'] for c in conversations if c['message_type'] == 'assistant']
    
    # Basic analysis
    analysis = {
        'total_messages': len(conversations),
        'user_messages': len(user_messages),
        'assistant_messages': len(assistant_messages),
        'first_message_date': conversations[-1]['timestamp'] if conversations else None,
        'last_message_date': conversations[0]['timestamp'] if conversations else None,
    }
    
    # Identify common themes in user messages
    themes = []
    if user_messages:
        user_text = ' '.join(user_messages).lower()
        
        # Look for common themes
        theme_keywords = {
            'stress': ['stress', 'stressed', 'overwhelmed', 'pressure', 'anxious', 'worry'],
            'work': ['work', 'job', 'boss', 'meeting', 'project', 'deadline'],
            'goals': ['goal', 'want to', 'trying to', 'working on', 'improve'],
            'gratitude': ['grateful', 'thankful', 'appreciate', 'blessed', 'happy'],
            'challenges': ['difficult', 'hard', 'struggle', 'problem', 'issue'],
            'progress': ['better', 'improvement', 'progress', 'achievement', 'success']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in user_text for keyword in keywords):
                themes.append(theme)
    
    # Create summary
    summary = f"""
    Week Summary:
    - Total interactions: {analysis['total_messages']}
    - User engaged {len(user_messages)} times
    - Main themes discussed: {', '.join(themes) if themes else 'General conversation'}
    - Week span: {analysis['first_message_date']} to {analysis['last_message_date']}
    """
    
    return summary.strip()

async def _generate_gentle_check_in(subscriber: dict, ai_coach: AICoachService) -> str:
    """Generate a gentle check-in for users who haven't been active"""
    
    check_ins = [
        f"Hi {subscriber.get('email', '').split('@')[0] if subscriber.get('email') else 'there'}! 👋 I haven't heard from you this week and wanted to check in. How are you doing? Sometimes life gets busy, and that's completely okay. I'm here whenever you need support or just want to chat. What's been on your mind lately?",
        
        f"Thinking of you this week! 💭 I know everyone's journey has different rhythms, and sometimes we need quiet space to process and grow. How has your week been treating you? Whether it's been smooth sailing or full of challenges, I'm here to listen and support you.",
        
        f"Just wanted to reach out and see how you're doing! 🌟 No pressure to respond - sometimes we all need a little breathing room. But if you're up for it, I'd love to hear what's been happening in your world this week. How are you taking care of yourself?",
        
        f"Hope you're having a good week! 🌸 I've been thinking about our journey together and wanted you to know that progress isn't always about daily check-ins. Sometimes growth happens in the quiet moments too. How are you feeling about things lately?",
    ]
    
    # Choose based on user ID for consistency
    message_index = hash(subscriber['id']) % len(check_ins)
    return check_ins[message_index]

async def _store_weekly_progress_data(subscriber: dict, supabase_service: SupabaseService):
    """Store weekly progress data for analytics and tracking"""
    
    try:
        # Calculate week start (Monday)
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday())
        
        # Get conversation data for this week
        week_conversations = await _get_week_conversations(subscriber['id'], supabase_service)
        
        # Basic progress metrics
        progress_data = {
            'subscriber_id': subscriber['id'],
            'week_start': week_start.isoformat(),
            'wins': [],  # Could be enhanced to extract wins from conversations
            'challenges': [],  # Could be enhanced to extract challenges
            'goal_progress': {},  # Could track specific goal mentions
            'mood_patterns': [],  # Could analyze sentiment over time
            'engagement_score': min(len(week_conversations), 10),  # 0-10 based on activity
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Store in user_progress table
        await supabase_service.log_user_progress(subscriber['id'], progress_data)
        
        logger.info("weekly_progress_stored",
                   user_id=subscriber['id'])
        
    except Exception as e:
        logger.error("weekly_progress_storage_error",
                    error=str(e),
                    exc_info=True)

@shared_task(bind=True, max_retries=2)
def generate_monthly_insights(self):
    """
    Generate monthly insights and send summary reports
    """
    logger.info("monthly_insights_start",
               task_name="generate_monthly_insights")
    
    try:
        return asyncio.run(_generate_monthly_insights_async())
    except Exception as e:
        logger.error("monthly_insights_task_error",
                    error=str(e),
                    retry_count=self.request.retries,
                    exc_info=True)
        raise self.retry(exc=e, countdown=600)  # Retry after 10 minutes

async def _generate_monthly_insights_async():
    """Generate monthly insights for active users"""
    
    # Initialize services
    db = get_supabase_client()
    supabase_service = SupabaseService(db)
    
    # Get users who have been active in the past month
    month_start = datetime.utcnow() - timedelta(days=30)
    subscribers = await supabase_service.get_active_subscribers()
    
    insights_generated = 0
    
    for subscriber in subscribers:
        try:
            # Get monthly conversation data
            all_conversations = await supabase_service.get_conversation_history(subscriber['id'], limit=500)
            
            # Filter to past month
            monthly_conversations = [
                c for c in all_conversations 
                if datetime.fromisoformat(c['timestamp']) >= month_start
            ]
            
            if len(monthly_conversations) >= 5:  # Only generate insights for engaged users
                # Could implement detailed monthly analysis here
                insights_generated += 1
                logger.info("monthly_insights_generated",
                           user_id=subscriber['id'])
        
        except Exception as e:
            logger.error("monthly_insights_user_error",
                        user_id=subscriber.get('id', 'unknown'),
                        error=str(e),
                        exc_info=True)
    
    logger.info("monthly_insights_complete",
               insights_generated=insights_generated)
    return {"insights_generated": insights_generated}