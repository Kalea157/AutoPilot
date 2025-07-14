"""
Configuration management for Super-KI-Agent
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmailConfig(BaseSettings):
    """Email configuration settings"""
    username: str = Field(..., env="EMAIL_USERNAME")
    password: str = Field(..., env="EMAIL_PASSWORD")
    imap_server: str = Field("imap.gmail.com", env="EMAIL_IMAP_SERVER")
    smtp_server: str = Field("smtp.gmail.com", env="EMAIL_SMTP_SERVER")
    imap_port: int = 993
    smtp_port: int = 587
    use_ssl: bool = True
    use_tls: bool = True


class OpenAIConfig(BaseSettings):
    """OpenAI configuration settings"""
    api_key: str = Field(..., env="OPENAI_API_KEY")
    model: str = "gpt-4o"
    max_tokens: int = 2000
    temperature: float = 0.7


class TelegramConfig(BaseSettings):
    """Telegram configuration settings"""
    bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    chat_id: str = Field(..., env="TELEGRAM_CHAT_ID")
    approval_timeout: int = 300


class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self._config_data = self._load_config()
        self.email = EmailConfig()
        self.openai = OpenAIConfig()
        self.telegram = TelegramConfig()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self._config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return self._config_data.get('agent', {})
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email configuration"""
        return self._config_data.get('email', {})
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration"""
        return self._config_data.get('ai', {})
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration"""
        return self._config_data.get('telegram', {})
    
    def get_decision_config(self) -> Dict[str, Any]:
        """Get decision engine configuration"""
        return self._config_data.get('decision_engine', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self._config_data.get('logging', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config_data.get('monitoring', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self._config_data.get('security', {})


# Global configuration instance
config = Config()