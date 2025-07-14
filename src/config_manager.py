"""
Konfigurations-Manager für den Super-KI-Agenten
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import logging
from pydantic import BaseModel, Field

class EmailConfig(BaseModel):
    imap: Dict[str, Any]
    smtp: Dict[str, Any]
    fetch_interval: int
    max_emails_per_fetch: int
    auto_delete_processed: bool

class AIConfig(BaseModel):
    model: str
    max_tokens: int
    temperature: float
    confidence_thresholds: Dict[str, float]
    analysis_prompts: Dict[str, str]

class TelegramConfig(BaseModel):
    bot_token: str
    admin_chat_id: str
    notification_chat_id: str
    auto_approve_commands: list
    reject_commands: list
    edit_commands: list
    timeout_seconds: int

class LoggingConfig(BaseModel):
    level: str
    file: str
    max_size_mb: int
    backup_count: int
    format: str

class FeaturesConfig(BaseModel):
    auto_categorization: bool
    priority_detection: bool
    multilingual_support: bool
    sentiment_analysis: bool
    auto_archiving: bool
    smart_filtering: bool
    response_templates: bool
    escalation_rules: bool

class SecurityConfig(BaseModel):
    encrypt_sensitive_data: bool
    max_retry_attempts: int
    rate_limiting: bool
    suspicious_content_detection: bool

class ConfigManager:
    """Zentrale Konfigurationsverwaltung für den Super-KI-Agenten"""
    
    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        self.config_path = Path(config_path)
        self.env_path = Path(env_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._setup_logging()
    
    def _load_config(self):
        """Lädt Konfiguration aus YAML und Umgebungsvariablen"""
        # Lade .env Datei
        if self.env_path.exists():
            load_dotenv(self.env_path)
        
        # Lade YAML Konfiguration
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        
        # Ersetze Umgebungsvariablen
        self._replace_env_vars()
        
        # Validiere Konfiguration
        self._validate_config()
    
    def _replace_env_vars(self):
        """Ersetzt ${VAR} Platzhalter mit Umgebungsvariablen"""
        def replace_in_dict(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                        env_var = value[2:-1]
                        data[key] = os.getenv(env_var, "")
                    elif isinstance(value, (dict, list)):
                        replace_in_dict(value)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                        env_var = item[2:-1]
                        data[i] = os.getenv(env_var, "")
                    elif isinstance(item, (dict, list)):
                        replace_in_dict(item)
        
        replace_in_dict(self.config)
    
    def _validate_config(self):
        """Validiert die Konfiguration"""
        required_env_vars = [
            'EMAIL_ADDRESS', 'EMAIL_PASSWORD', 'OPENAI_API_KEY',
            'TELEGRAM_BOT_TOKEN', 'TELEGRAM_ADMIN_CHAT_ID'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Fehlende Umgebungsvariablen: {', '.join(missing_vars)}")
    
    def _setup_logging(self):
        """Konfiguriert das Logging-System"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        
        # Erstelle Logs-Verzeichnis
        log_file = log_config.get('file', 'logs/super_agent.log')
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Konfiguriere Logging
        logging.basicConfig(
            level=log_level,
            format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get_email_config(self) -> EmailConfig:
        """Gibt E-Mail-Konfiguration zurück"""
        return EmailConfig(**self.config.get('email', {}))
    
    def get_ai_config(self) -> AIConfig:
        """Gibt AI-Konfiguration zurück"""
        return AIConfig(**self.config.get('ai', {}))
    
    def get_telegram_config(self) -> TelegramConfig:
        """Gibt Telegram-Konfiguration zurück"""
        return TelegramConfig(**self.config.get('telegram', {}))
    
    def get_logging_config(self) -> LoggingConfig:
        """Gibt Logging-Konfiguration zurück"""
        return LoggingConfig(**self.config.get('logging', {}))
    
    def get_features_config(self) -> FeaturesConfig:
        """Gibt Features-Konfiguration zurück"""
        return FeaturesConfig(**self.config.get('features', {}))
    
    def get_security_config(self) -> SecurityConfig:
        """Gibt Security-Konfiguration zurück"""
        return SecurityConfig(**self.config.get('security', {}))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Gibt Konfigurationswert zurück"""
        return self.config.get(key, default)
    
    def reload(self):
        """Lädt Konfiguration neu"""
        self._load_config()