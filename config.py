"""
Liyana NEXUS v1 - Super-KI-Agent Stufe 8
Konfigurationsdatei für alle Module und APIs
"""

import os
from pathlib import Path
from typing import Dict, Any

# System-Pfade
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
VOICE_DIR = BASE_DIR / "voice"

# Erstelle Verzeichnisse falls nicht vorhanden
for dir_path in [DATA_DIR, LOGS_DIR, MODELS_DIR, VOICE_DIR]:
    dir_path.mkdir(exist_ok=True)

# NEXUS Core Konfiguration
NEXUS_CONFIG = {
    "system_name": "Liyana NEXUS v1",
    "version": "1.0.0",
    "stage": 8,
    "max_concurrent_agents": 10,
    "auto_restart": True,
    "debug_mode": False,
    "log_level": "INFO"
}

# Agent-Zustände
AGENT_STATES = {
    "WAITING": "Wartend",
    "THINKING": "Analysierend", 
    "EXECUTING": "Ausführend",
    "LEARNING": "Lernend",
    "ERROR": "Fehler",
    "PAUSED": "Pausiert"
}

# Email-Konfiguration (kostenlose APIs)
EMAIL_CONFIG = {
    "gmail": {
        "imap_server": "imap.gmail.com",
        "smtp_server": "smtp.gmail.com",
        "imap_port": 993,
        "smtp_port": 587,
        "use_ssl": True
    },
    "yahoo": {
        "imap_server": "imap.mail.yahoo.com", 
        "smtp_server": "smtp.mail.yahoo.com",
        "imap_port": 993,
        "smtp_port": 587,
        "use_ssl": True
    },
    "outlook": {
        "imap_server": "outlook.office365.com",
        "smtp_server": "smtp-mail.outlook.com", 
        "imap_port": 993,
        "smtp_port": 587,
        "use_ssl": True
    }
}

# AI APIs (kostenlos)
AI_CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "model": "gpt-3.5-turbo",
        "max_tokens": 1000,
        "temperature": 0.7
    },
    "gemini": {
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "model": "gemini-pro",
        "max_tokens": 1000,
        "temperature": 0.7
    },
    "local_llm": {
        "model_path": str(MODELS_DIR / "local_model"),
        "device": "cpu",
        "max_tokens": 500
    }
}

# Telegram Bot (kostenlos)
TELEGRAM_CONFIG = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    "webhook_url": "",
    "polling_interval": 1
}

# Voice & Speech (lokal/kostenlos)
VOICE_CONFIG = {
    "whisper": {
        "model": "base",  # base, small, medium, large
        "language": "de",
        "device": "cpu"
    },
    "tts": {
        "engine": "piper",  # piper, silero, coqui
        "voice": "de_DE-ramona-medium",
        "speed": 1.0
    },
    "voice_clone": {
        "enabled": True,
        "sample_rate": 22050,
        "chunk_size": 1024
    }
}

# E-commerce APIs (kostenlos)
ECOMMERCE_CONFIG = {
    "aliexpress": {
        "api_key": os.getenv("ALIEXPRESS_API_KEY", ""),
        "tracking_id": os.getenv("ALIEXPRESS_TRACKING_ID", ""),
        "base_url": "https://api.aliexpress.com/v2/"
    },
    "temu": {
        "scraper_enabled": True,
        "base_url": "https://www.temu.com",
        "delay": 2.0
    },
    "shopify": {
        "api_key": os.getenv("SHOPIFY_API_KEY", ""),
        "api_secret": os.getenv("SHOPIFY_API_SECRET", ""),
        "store_url": os.getenv("SHOPIFY_STORE_URL", "")
    }
}

# Kostenlose APIs
FREE_APIS = {
    "weather": {
        "open_meteo": "https://api.open-meteo.com/v1/",
        "geocoding": "https://geocoding-api.open-meteo.com/v1/"
    },
    "finance": {
        "alpha_vantage": "https://www.alphavantage.co/query",
        "api_key": os.getenv("ALPHA_VANTAGE_API_KEY", "")
    },
    "geolocation": {
        "free_geoip": "https://freegeoip.app/json/",
        "ipapi": "https://ipapi.co/json/"
    },
    "crypto": {
        "coingecko": "https://api.coingecko.com/api/v3/",
        "binance": "https://api.binance.com/api/v3/"
    }
}

# Datenbank-Konfiguration
DATABASE_CONFIG = {
    "sqlite": {
        "path": str(DATA_DIR / "nexus.db"),
        "backup_interval": 3600,  # 1 Stunde
        "max_backups": 10
    },
    "memory": {
        "max_entries": 10000,
        "cleanup_interval": 300  # 5 Minuten
    }
}

# GUI Cyberpunk-Design
GUI_CONFIG = {
    "theme": "cyberpunk",
    "colors": {
        "primary": "#00ff41",      # Neon-Grün
        "secondary": "#ff0080",    # Neon-Pink  
        "accent": "#0080ff",       # Neon-Blau
        "background": "#0a0a0a",   # Dunkel
        "surface": "#1a1a1a",      # Dunkelgrau
        "text": "#ffffff",         # Weiß
        "error": "#ff0000",        # Rot
        "warning": "#ffff00",      # Gelb
        "success": "#00ff00"       # Grün
    },
    "animations": {
        "enabled": True,
        "duration": 300,
        "easing": "ease-in-out"
    },
    "window": {
        "width": 1400,
        "height": 900,
        "min_width": 800,
        "min_height": 600
    }
}

# Automatisierungs-Module
AUTOMATION_MODULES = {
    "email_support": {
        "name": "E-Mail Support",
        "description": "Automatische E-Mail-Bearbeitung und Antworten",
        "enabled": True,
        "providers": ["gmail", "yahoo", "outlook"]
    },
    "call_center": {
        "name": "Call Center", 
        "description": "Sprachverarbeitung und Anrufbehandlung",
        "enabled": True,
        "voice_enabled": True
    },
    "dropshipping": {
        "name": "Dropshipping",
        "description": "Automatische Produktsuche und Bestellungen",
        "enabled": True,
        "platforms": ["aliexpress", "temu", "shopify"]
    },
    "research": {
        "name": "Marktforschung",
        "description": "Trendanalysen und Konkurrenzvergleich",
        "enabled": True,
        "apis": ["weather", "finance", "crypto"]
    }
}

# Logging-Konfiguration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "cyberpunk": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            "datefmt": "%H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "cyberpunk",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.FileHandler", 
            "level": "DEBUG",
            "formatter": "cyberpunk",
            "filename": str(LOGS_DIR / "nexus.log"),
            "mode": "a"
        }
    },
    "loggers": {
        "nexus": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False
        }
    }
}

# Sicherheits-Konfiguration
SECURITY_CONFIG = {
    "encryption": {
        "enabled": True,
        "algorithm": "AES-256",
        "key_file": str(DATA_DIR / ".key")
    },
    "authentication": {
        "required": False,
        "session_timeout": 3600
    },
    "rate_limiting": {
        "enabled": True,
        "max_requests": 100,
        "time_window": 60
    }
}

# Performance-Konfiguration
PERFORMANCE_CONFIG = {
    "threading": {
        "max_workers": 8,
        "timeout": 30
    },
    "caching": {
        "enabled": True,
        "ttl": 300,
        "max_size": 1000
    },
    "memory": {
        "max_usage": 0.8,  # 80% RAM
        "cleanup_threshold": 0.7
    }
}