# Positivity Push Background Workers Guide

## 🔄 Overview

The background worker system handles automated personalized messaging, weekly progress reports, and email notifications. Built with Celery and Redis for reliable, scalable task processing.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Celery Worker  │    │  Celery Beat    │
│                 │    │                 │    │  (Scheduler)    │
│  - Webhooks     │    │  - Daily msgs   │    │                 │
│  - AI coaching  │    │  - Weekly reports│    │  - Cron jobs    │
│  - User API     │    │  - Email tasks  │    │  - Periodic     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │      Redis Queue       │
                    │                        │
                    │  - Task broker         │
                    │  - Result backend      │
                    │  - Message persistence │
                    └────────────────────────┘
```

## 📋 Background Tasks

### Daily Messaging Tasks

**Morning Affirmations** (8 AM local time)
- Generates personalized affirmations using AI coach
- Based on user's goals, recent conversations, and progress
- Sent via WhatsApp to active subscribers
- Timezone-aware scheduling

**Evening Gratitude Prompts** (8 PM local time)
- Creates contextual gratitude reflection questions
- Encourages end-of-day mindfulness
- Personalized to user's experiences and challenges

**Weekly Check-ins** (Wednesdays)
- Proactive engagement for users who haven't messaged recently
- Celebrates progress and offers support
- Variety of check-in styles based on user preferences

### Weekly Progress Reports

**Sunday Evening Reports** (6 PM UTC)
- Analyzes week's conversation patterns
- Identifies growth, challenges, and themes
- AI-generated personalized insights
- Stores progress data for long-term tracking

**Monthly Insights** (1st of month)
- Broader pattern analysis across 30 days
- Goal progress evaluation
- Coaching approach adjustments

### Email Notifications

**Welcome Emails** (Immediate after payment)
- Thank you message with payment confirmation
- WhatsApp activation instructions
- Sets expectations for coaching journey

**Activation Reminders** (24-72 hours after payment)
- For users who haven't activated WhatsApp
- Includes direct activation link
- Prevents user drop-off

**Lifecycle Notifications**
- Payment failure alerts
- Subscription cancellation confirmations
- Monthly newsletters (optional)

## ⚙️ Configuration

### Celery Configuration

```python
# Timezone-aware scheduling
celery_app.conf.beat_schedule = {
    'send-morning-affirmations-utc': {
        'task': 'worker.tasks.daily_messages.send_morning_affirmations',
        'schedule': crontab(hour=8, minute=0),
        'kwargs': {'timezone': 'UTC'}
    },
    # ... multiple timezone configurations
}
```

### Task Queues

- `daily_messages` - High-priority daily content
- `weekly_reports` - Weekly analysis tasks
- `email_notifications` - Email sending
- `default` - General tasks

### Retry Logic

- **Max retries**: 3 attempts
- **Exponential backoff**: 60s, 120s, 240s
- **Error handling**: Graceful degradation
- **Dead letter queue**: Failed tasks logged for review

## 🚀 Setup and Deployment

### Local Development

1. **Install Redis**:
   ```bash
   # macOS
   brew install redis
   redis-server
   
   # Ubuntu
   sudo apt install redis-server
   sudo systemctl start redis
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start System**:
   ```bash
   # Option 1: Use startup script
   python start_system.py --mode dev
   
   # Option 2: Manual startup
   # Terminal 1: FastAPI
   python -m app.main
   
   # Terminal 2: Celery Worker
   celery -A worker.celery_app worker --loglevel=info
   
   # Terminal 3: Celery Beat
   celery -A worker.celery_app beat --loglevel=info
   ```

4. **Monitor Tasks** (Optional):
   ```bash
   # Start Flower monitoring
   celery -A worker.celery_app flower
   # Visit http://localhost:5555
   ```

### Production Deployment

**1. Redis Setup**:
- Use Redis Cloud or managed Redis service
- Configure persistence and high availability
- Set up authentication and encryption

**2. Process Management**:
```yaml
# systemd service example
[Unit]
Description=Positivity Push Celery Worker
After=network.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/app/Back-End
ExecStart=celery -A worker.celery_app worker --detach
ExecStop=celery -A worker.celery_app control shutdown
ExecReload=celery -A worker.celery_app control pool_restart

[Install]
WantedBy=multi-user.target
```

**3. Environment Variables**:
```bash
# Production Redis
REDIS_URL=redis://username:password@redis-host:6379/0

# Task configuration
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Scaling
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

## 🧪 Testing

### Test Background Workers

```bash
# Test Redis connection and task imports
python test_workers.py

# Test specific task execution
python -c "
from worker.tasks.daily_messages import send_morning_affirmations
result = send_morning_affirmations.delay('UTC')
print(f'Task ID: {result.id}')
"
```

### Monitor Task Execution

```bash
# View active tasks
celery -A worker.celery_app inspect active

# View scheduled tasks
celery -A worker.celery_app inspect scheduled

# View worker stats
celery -A worker.celery_app inspect stats
```

### Debug Failed Tasks

```bash
# Purge all tasks
celery -A worker.celery_app purge

# View reserved tasks
celery -A worker.celery_app inspect reserved

# Restart workers
celery -A worker.celery_app control pool_restart
```

## 📊 Monitoring and Analytics

### Key Metrics

- **Message Delivery Rate**: % of scheduled messages sent successfully
- **Task Execution Time**: Average time per task type
- **Error Rate**: Failed tasks per hour/day
- **User Engagement**: Response rates to daily messages
- **Queue Length**: Pending tasks in each queue

### Logging

```python
# Structured logging for tasks
logger.info("Morning affirmations complete", extra={
    "sent_count": sent_count,
    "error_count": error_count,
    "timezone": timezone,
    "execution_time": execution_time
})
```

### Alerting

Set up monitoring for:
- Worker downtime
- High error rates (>5%)
- Queue backlog (>100 pending tasks)
- Redis connection failures
- Task execution time spikes

## 🔧 Maintenance

### Daily Operations

- Monitor Flower dashboard for task health
- Check error logs for failed tasks
- Verify message delivery rates

### Weekly Operations

- Review user engagement metrics
- Analyze task performance trends
- Update AI prompts based on user feedback

### Monthly Operations

- Scale workers based on user growth
- Optimize task scheduling for efficiency
- Review and update automated content

## 🎯 Performance Optimization

### Scaling Workers

```bash
# Scale up workers
celery -A worker.celery_app control pool_grow 2

# Scale down workers
celery -A worker.celery_app control pool_shrink 1

# Auto-scaling based on queue length
celery -A worker.celery_app worker --autoscale=10,3
```

### Task Optimization

- **Batch Processing**: Group similar tasks
- **Task Chunking**: Split large tasks into smaller ones
- **Result Caching**: Cache expensive computations
- **Rate Limiting**: Respect API limits for external services

### Redis Optimization

```python
# Connection pooling
CELERY_BROKER_POOL_LIMIT = 10
CELERY_BROKER_CONNECTION_MAX_RETRIES = 5

# Task compression
CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
```

## 🚨 Troubleshooting

### Common Issues

**1. Tasks Not Executing**
- Check if workers are running
- Verify Redis connection
- Check task imports

**2. High Memory Usage**
- Monitor task result retention
- Implement result expiration
- Use task result backends efficiently

**3. Slow Task Execution**
- Profile task functions
- Optimize database queries
- Use async operations where possible

**4. Failed API Calls**
- Implement retry logic with exponential backoff
- Use circuit breakers for external services
- Cache API responses when appropriate

### Emergency Procedures

**Stop All Tasks**:
```bash
celery -A worker.celery_app control shutdown
```

**Purge All Queues**:
```bash
celery -A worker.celery_app purge
```

**Restart System**:
```bash
python start_system.py --mode dev
```

## 📈 Future Enhancements

- **Machine Learning**: Optimize send times based on user engagement
- **A/B Testing**: Test different message formats and timing
- **Advanced Analytics**: Detailed user journey analysis
- **Multi-language**: Support for different languages and cultures
- **Smart Frequency**: Adjust message frequency based on user preferences