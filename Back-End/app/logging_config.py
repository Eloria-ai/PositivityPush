"""
Advanced Logging Configuration for Positivity Push
Production-ready logging with structured output and monitoring integration.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any
import os

from app.config import settings

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_data["correlation_id"] = record.correlation_id
        
        # Add extra fields from log record
        for key, value in record.__dict__.items():
            if key not in {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'exc_info', 'exc_text', 
                          'stack_info', 'getMessage'}:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add stack trace if present
        if record.stack_info:
            log_data["stack_trace"] = record.stack_info
        
        return json.dumps(log_data, default=str)

class ColorFormatter(logging.Formatter):
    """Colored formatter for development logging"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        if settings.ENVIRONMENT == "development":
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # Format with colors
            formatted = super().format(record)
            return f"{color}{formatted}{reset}"
        else:
            return super().format(record)

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Determine log level
    log_level = "DEBUG" if settings.ENVIRONMENT == "development" else "INFO"
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "colored": {
                "()": ColorFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "colored" if settings.ENVIRONMENT == "development" else "structured",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filename": os.path.join(logs_dir, "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "structured",
                "filename": os.path.join(logs_dir, "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "celery_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "structured",
                "filename": os.path.join(logs_dir, "celery.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "worker": {
                "level": log_level,
                "handlers": ["console", "celery_file"],
                "propagate": False
            },
            # External libraries
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "celery_file"],
                "propagate": False
            },
            # Suppress noisy libraries
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "urllib3": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger("app.logging")
    logger.info(
        "Logging configured",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": log_level,
            "logs_directory": logs_dir
        }
    )

class ContextLogger:
    """Logger with automatic context injection"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context that will be added to all log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear the current context"""
        self.context.clear()
    
    def _log_with_context(self, level: str, message: str, **kwargs):
        """Log message with context"""
        extra = {**self.context, **kwargs}
        getattr(self.logger, level)(message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context("critical", message, **kwargs)

def get_logger(name: str) -> ContextLogger:
    """Get a context-aware logger"""
    return ContextLogger(name)

# Performance monitoring decorator
def log_performance(logger_name: str = "app.performance"):
    """Decorator to log function performance"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Function completed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "success"
                    }
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Function failed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Function completed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "success"
                    }
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Function failed: {func.__name__}",
                    extra={
                        "function": func.__name__,
                        "duration_ms": round(duration * 1000, 2),
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator