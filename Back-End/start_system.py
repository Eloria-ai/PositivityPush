#!/usr/bin/env python3
"""
Positivity Push System Startup Script
Starts FastAPI server and Celery workers for complete system operation.
"""

import subprocess
import sys
import os
import signal
import time
from multiprocessing import Process
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessManager:
    """Manages multiple processes for the Positivity Push system"""
    
    def __init__(self):
        self.processes = []
        self.running = True
    
    def start_fastapi_server(self):
        """Start the FastAPI server"""
        logger.info("🚀 Starting FastAPI server...")
        
        try:
            process = subprocess.Popen([
                sys.executable, "-m", "app.main"
            ], cwd=os.getcwd())
            
            self.processes.append(("FastAPI Server", process))
            logger.info("✅ FastAPI server started")
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start FastAPI server: {e}")
            return None
    
    def start_celery_worker(self):
        """Start Celery worker"""
        logger.info("👷 Starting Celery worker...")
        
        try:
            process = subprocess.Popen([
                "celery", "-A", "worker.celery_app", 
                "worker", "--loglevel=info",
                "--concurrency=2"
            ], cwd=os.getcwd())
            
            self.processes.append(("Celery Worker", process))
            logger.info("✅ Celery worker started")
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start Celery worker: {e}")
            return None
    
    def start_celery_beat(self):
        """Start Celery beat scheduler"""
        logger.info("⏰ Starting Celery beat scheduler...")
        
        try:
            process = subprocess.Popen([
                "celery", "-A", "worker.celery_app",
                "beat", "--loglevel=info"
            ], cwd=os.getcwd())
            
            self.processes.append(("Celery Beat", process))
            logger.info("✅ Celery beat scheduler started")
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start Celery beat: {e}")
            return None
    
    def start_flower_monitor(self):
        """Start Flower monitoring (optional)"""
        logger.info("🌸 Starting Flower monitoring...")
        
        try:
            process = subprocess.Popen([
                "celery", "-A", "worker.celery_app",
                "flower", "--port=5555"
            ], cwd=os.getcwd())
            
            self.processes.append(("Flower Monitor", process))
            logger.info("✅ Flower monitoring started on http://localhost:5555")
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start Flower: {e}")
            return None
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("🛑 Received shutdown signal, stopping all processes...")
        self.running = False
        self.stop_all_processes()
        sys.exit(0)
    
    def stop_all_processes(self):
        """Stop all managed processes"""
        for name, process in self.processes:
            try:
                logger.info(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ Force killing {name}...")
                process.kill()
            except Exception as e:
                logger.error(f"❌ Error stopping {name}: {e}")
        
        self.processes.clear()
    
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            logger.error("❌ .env file not found. Copy .env.example to .env and configure it.")
            return False
        
        # Check required environment variables
        required_vars = ['OPENAI_API_KEY', 'REDIS_URL']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {missing_vars}")
            return False
        
        # Check if Redis is accessible
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            r.ping()
            logger.info("✅ Redis connection successful")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            logger.error("   Make sure Redis is running: redis-server")
            return False
        
        # Check if required packages are installed
        try:
            import fastapi
            import celery
            import openai
            logger.info("✅ Required packages available")
        except ImportError as e:
            logger.error(f"❌ Missing package: {e}")
            logger.error("   Run: pip install -r requirements.txt")
            return False
        
        return True
    
    def start_development_mode(self):
        """Start system in development mode"""
        logger.info("🏃 Starting Positivity Push in DEVELOPMENT mode")
        logger.info("=" * 60)
        
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met. Cannot start system.")
            return
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start services
        services_started = 0
        
        # Start FastAPI server
        if self.start_fastapi_server():
            services_started += 1
            time.sleep(2)  # Give server time to start
        
        # Start Celery worker
        if self.start_celery_worker():
            services_started += 1
            time.sleep(2)
        
        # Start Celery beat
        if self.start_celery_beat():
            services_started += 1
            time.sleep(2)
        
        if services_started > 0:
            logger.info("🎉 System startup complete!")
            logger.info("=" * 60)
            logger.info("📊 Service URLs:")
            logger.info("   • API Server: http://localhost:8000")
            logger.info("   • API Docs: http://localhost:8000/docs")
            logger.info("   • Health Check: http://localhost:8000/health")
            logger.info("")
            logger.info("🔧 Management Commands:")
            logger.info("   • View logs: Check terminal output")
            logger.info("   • Stop system: Ctrl+C")
            logger.info("   • Test workers: python test_workers.py")
            logger.info("")
            
            # Keep main process alive
            try:
                while self.running:
                    time.sleep(1)
                    
                    # Check if any process died
                    for name, process in self.processes[:]:
                        if process.poll() is not None:
                            logger.warning(f"⚠️ {name} stopped unexpectedly")
                            self.processes.remove((name, process))
            
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
            
            finally:
                self.stop_all_processes()
        
        else:
            logger.error("❌ Failed to start any services")
    
    def start_production_mode(self):
        """Start system in production mode"""
        logger.info("🏭 Starting Positivity Push in PRODUCTION mode")
        
        # In production, typically use process managers like supervisor, systemd, or Docker
        logger.info("For production deployment, use:")
        logger.info("1. gunicorn for FastAPI: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker")
        logger.info("2. systemd/supervisor for Celery worker and beat")
        logger.info("3. nginx for reverse proxy")
        logger.info("4. Redis cluster for high availability")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Positivity Push System Startup")
    parser.add_argument("--mode", choices=["dev", "prod"], default="dev",
                      help="Startup mode (default: dev)")
    parser.add_argument("--flower", action="store_true",
                      help="Also start Flower monitoring")
    
    args = parser.parse_args()
    
    manager = ProcessManager()
    
    if args.mode == "dev":
        if args.flower:
            # Start Flower in development mode
            manager.start_flower_monitor()
        manager.start_development_mode()
    else:
        manager.start_production_mode()

if __name__ == "__main__":
    main()