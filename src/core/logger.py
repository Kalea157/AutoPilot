"""
Logging system for Super-KI-Agent
"""

import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
from structlog.stdlib import LoggerFactory

from .config import config


class SuperAgentLogger:
    """Advanced logging system for Super-KI-Agent"""
    
    def __init__(self, name: str = "super_agent"):
        self.name = name
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> structlog.BoundLogger:
        """Setup structured logging"""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Create logs directory
        log_config = config.get_logging_config()
        log_file = log_config.get('file', 'logs/super_agent.log')
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Get logger
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return structlog.get_logger(self.name)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def log_email_processing(self, email_id: str, action: str, **kwargs):
        """Log email processing events"""
        self.info(
            f"Email processing: {action}",
            email_id=email_id,
            action=action,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
    
    def log_ai_analysis(self, email_id: str, analysis_type: str, confidence: float, **kwargs):
        """Log AI analysis results"""
        self.info(
            f"AI analysis completed: {analysis_type}",
            email_id=email_id,
            analysis_type=analysis_type,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
    
    def log_telegram_interaction(self, email_id: str, action: str, response: str, **kwargs):
        """Log Telegram interactions"""
        self.info(
            f"Telegram interaction: {action}",
            email_id=email_id,
            action=action,
            response=response,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
    
    def log_decision(self, email_id: str, decision: str, confidence: float, **kwargs):
        """Log decision engine results"""
        self.info(
            f"Decision made: {decision}",
            email_id=email_id,
            decision=decision,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
    
    def log_error(self, error_type: str, error_message: str, **kwargs):
        """Log errors with context"""
        self.error(
            f"Error occurred: {error_type}",
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )


# Global logger instance
logger = SuperAgentLogger()