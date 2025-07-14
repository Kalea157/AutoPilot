"""
Liyana NEXUS v1 - Zentrale Konfiguration
Super-KI-Agent Stufe 8 - Produktionskonfiguration
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Basis-Verzeichnisse
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"
VOICE_DIR = BASE_DIR / "voice"

# Erstelle Verzeichnisse falls nicht vorhanden
for dir_path in [DATA_DIR, LOGS_DIR, MODELS_DIR, CACHE_DIR, VOICE_DIR]:
    dir_path.mkdir(exist_ok=True)

class AgentState(Enum):
    """Zustände des NEXUS-Core"""
    WAITING = "waiting"
    THINKING = "thinking"
    EXECUTING = "executing"
    LEARNING = "learning"
    ERROR = "error"
    PAUSED = "paused"

class AutomationType(Enum):
    """Verfügbare Automatisierungstypen"""
    EMAIL_SUPPORT = "email_support"
    CALL_CENTER = "call_center"
    DROPSHIPPING = "dropshipping"
    TELEGRAM_BOT = "telegram_bot"
    VOICE_ASSISTANT = "voice_assistant"
    SEARCH_AGENT = "search_agent"

@dataclass
class APIConfig:
    """API-Konfiguration für kostenlose Dienste"""
    
    # OpenAI (Free Tier)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-3.5-turbo"
    
    # Google Gemini (Free)
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Telegram Bot
    telegram_token: str = os.getenv("TELEGRAM_TOKEN", "")
    
    # Email Configuration
    email_provider: str = "gmail"  # gmail, yahoo, outlook
    email_address: str = os.getenv("EMAIL_ADDRESS", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")
    imap_server: str = "imap.gmail.com"
    smtp_server: str = "smtp.gmail.com"
    imap_port: int = 993
    smtp_port: int = 587
    
    # Free APIs
    openmeteo_url: str = "https://api.open-meteo.com/v1"
    coingecko_url: str = "https://api.coingecko.com/api/v3"
    yahoo_finance_url: str = "https://query1.finance.yahoo.com/v8/finance"
    
    # E-commerce APIs
    aliexpress_api_key: str = os.getenv("ALIEXPRESS_API_KEY", "")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "")
    shopify_password: str = os.getenv("SHOPIFY_PASSWORD", "")
    shopify_shop_url: str = os.getenv("SHOPIFY_SHOP_URL", "")

@dataclass
class UIConfig:
    """Cyberpunk-Interface Konfiguration"""
    
    # Farben
    primary_color: str = "#00ff41"  # Neon-Grün
    secondary_color: str = "#ff0080"  # Neon-Pink
    accent_color: str = "#0080ff"  # Neon-Blau
    background_color: str = "#0a0a0a"  # Dunkel
    text_color: str = "#ffffff"  # Weiß
    
    # Animationen
    animation_speed: int = 1000  # ms
    glow_effect: bool = True
    particle_effects: bool = True
    
    # Fenster
    window_width: int = 1400
    window_height: int = 900
    window_title: str = "Liyana NEXUS v1 - Super-KI-Agent Stufe 8"

@dataclass
class SystemConfig:
    """System-Konfiguration"""
    
    # Performance
    max_concurrent_tasks: int = 10
    task_timeout: int = 300  # Sekunden
    memory_limit: int = 2048  # MB
    
    # Logging
    log_level: str = "INFO"
    log_file: str = str(LOGS_DIR / "nexus.log")
    max_log_size: int = 10  # MB
    
    # Database
    db_path: str = str(DATA_DIR / "nexus.db")
    cache_ttl: int = 3600  # Sekunden
    
    # Voice Processing
    sample_rate: int = 16000
    chunk_size: int = 1024
    voice_model: str = "piper"  # piper, silero, coqui
    
    # Learning
    learning_enabled: bool = True
    model_update_interval: int = 86400  # 24 Stunden

class Config:
    """Hauptkonfigurationsklasse"""
    
    def __init__(self):
        self.api = APIConfig()
        self.ui = UIConfig()
        self.system = SystemConfig()
        
        # Lade Umgebungsvariablen
        self._load_env_vars()
    
    def _load_env_vars(self):
        """Lade Konfiguration aus .env Datei"""
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
    
    def get_database_url(self) -> str:
        """Gibt die Datenbank-URL zurück"""
        return f"sqlite:///{self.system.db_path}"
    
    def get_voice_model_path(self) -> str:
        """Gibt den Pfad zum Voice-Model zurück"""
        return str(MODELS_DIR / f"{self.system.voice_model}_model")
    
    def validate_config(self) -> List[str]:
        """Validiert die Konfiguration und gibt Fehler zurück"""
        errors = []
        
        # Prüfe notwendige API Keys
        if not self.api.openai_api_key and not self.api.gemini_api_key:
            errors.append("Mindestens ein AI-API-Key (OpenAI oder Gemini) ist erforderlich")
        
        if not self.api.telegram_token:
            errors.append("Telegram Bot Token ist erforderlich für Bot-Funktionalität")
        
        if not self.api.email_address or not self.api.email_password:
            errors.append("Email-Konfiguration ist erforderlich für Email-Support")
        
        return errors

# Globale Konfigurationsinstanz
config = Config()

# Exportiere wichtige Konstanten
__all__ = [
    'config', 'AgentState', 'AutomationType', 'BASE_DIR', 'DATA_DIR', 
    'LOGS_DIR', 'MODELS_DIR', 'CACHE_DIR', 'VOICE_DIR'
]