"""
Configuration Manager für den Super AI Agent
Handhabt YAML-Konfiguration und Umgebungsvariablen
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import structlog

logger = structlog.get_logger(__name__)


class ConfigManager:
    """Zentrale Konfigurationsverwaltung für den Super AI Agent"""
    
    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Lädt Konfiguration aus YAML und Umgebungsvariablen"""
        try:
            # Lade .env Datei
            if self.env_path.exists():
                load_dotenv(self.env_path)
                logger.info("Environment variables loaded", path=str(self.env_path))
            
            # Lade YAML Konfiguration
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                logger.info("Configuration loaded", path=str(self.config_path))
            else:
                logger.warning("Configuration file not found", path=str(self.config_path))
                self._config = {}
            
            # Ersetze Umgebungsvariablen in der Konfiguration
            self._substitute_env_vars()
            
        except Exception as e:
            logger.error("Failed to load configuration", error=str(e))
            raise
    
    def _substitute_env_vars(self) -> None:
        """Ersetzt ${VAR} Platzhalter mit Umgebungsvariablen"""
        def replace_vars(obj):
            if isinstance(obj, str):
                if obj.startswith('${') and obj.endswith('}'):
                    var_name = obj[2:-1]
                    return os.getenv(var_name, obj)
                return obj
            elif isinstance(obj, dict):
                return {k: replace_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_vars(item) for item in obj]
            return obj
        
        self._config = replace_vars(self._config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Holt einen Konfigurationswert mit Punkt-Notation"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_email_config(self) -> Dict[str, Any]:
        """Gibt E-Mail-Konfiguration zurück"""
        return {
            'username': os.getenv('EMAIL_USERNAME'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('EMAIL_FROM'),
            'imap': self.get('email.imap', {}),
            'smtp': self.get('email.smtp', {})
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Gibt AI-Konfiguration zurück"""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': self.get('ai.model'),
            'max_tokens': self.get('ai.max_tokens'),
            'temperature': self.get('ai.temperature'),
            'system_prompt': self.get('ai.system_prompt'),
            'analysis_prompt': self.get('ai.analysis_prompt')
        }
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Gibt Telegram-Konfiguration zurück"""
        return {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
            'approval_timeout': self.get('telegram.approval_timeout'),
            'message_format': self.get('telegram.message_format'),
            'templates': self.get('telegram.templates', {})
        }
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Gibt Agent-Konfiguration zurück"""
        return {
            'name': self.get('agent.name'),
            'version': self.get('agent.version'),
            'debug': self.get('agent.debug', False),
            'max_concurrent_emails': self.get('agent.max_concurrent_emails'),
            'processing_timeout': self.get('agent.processing_timeout'),
            'confidence_threshold': self.get('agent.confidence_threshold'),
            'auto_approve_threshold': self.get('agent.auto_approve_threshold')
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Gibt Logging-Konfiguration zurück"""
        return self.get('logging', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Gibt Sicherheits-Konfiguration zurück"""
        return self.get('security', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Gibt Performance-Konfiguration zurück"""
        return self.get('performance', {})
    
    def validate_config(self) -> bool:
        """Validiert die Konfiguration"""
        required_env_vars = [
            'EMAIL_USERNAME', 'EMAIL_PASSWORD', 'EMAIL_FROM',
            'OPENAI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error("Missing required environment variables", missing=missing_vars)
            return False
        
        logger.info("Configuration validation successful")
        return True
    
    def reload(self) -> None:
        """Lädt Konfiguration neu"""
        self._load_config()
        logger.info("Configuration reloaded")