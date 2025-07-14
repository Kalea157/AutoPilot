#!/usr/bin/env python3
"""
Start-Skript für den Super-KI-Agenten
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent / "src"))

from super_agent import SuperAgent

def setup_logging():
    """Konfiguriert Logging für den Start"""
    # Erstelle logs-Verzeichnis
    Path("logs").mkdir(exist_ok=True)
    
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/super_agent.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def check_environment():
    """Prüft Umgebungsvariablen"""
    required_vars = [
        'EMAIL_ADDRESS',
        'EMAIL_PASSWORD', 
        'OPENAI_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_ADMIN_CHAT_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Fehlende Umgebungsvariablen:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Bitte konfiguriere die .env Datei:")
        print("   cp .env.example .env")
        print("   nano .env")
        return False
    
    return True

def check_config_files():
    """Prüft Konfigurationsdateien"""
    required_files = ['config.yaml', '.env']
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Fehlende Konfigurationsdateien:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n📝 Bitte erstelle die fehlenden Dateien:")
        if 'config.yaml' in missing_files:
            print("   # config.yaml sollte bereits vorhanden sein")
        if '.env' in missing_files:
            print("   cp .env.example .env")
            print("   nano .env")
        return False
    
    return True

def print_banner():
    """Zeigt Start-Banner"""
    banner = """
🤖 Super-KI-Agent
================
Intelligentes E-Mail-Management der nächsten Generation!

🚀 Features:
• KI-gestützte E-Mail-Analyse
• Automatische Antwortgenerierung
• Telegram-Integration
• Confidence-basierte Entscheidungen
• Mehrsprachige Unterstützung

📊 Status: Initialisiere...
"""
    print(banner)

def print_status():
    """Zeigt aktuellen Status"""
    print("\n📋 Konfiguration:")
    print(f"   E-Mail: {os.getenv('EMAIL_ADDRESS', 'Nicht konfiguriert')}")
    print(f"   OpenAI: {'✅ Konfiguriert' if os.getenv('OPENAI_API_KEY') else '❌ Nicht konfiguriert'}")
    print(f"   Telegram: {'✅ Konfiguriert' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Nicht konfiguriert'}")
    
    print("\n📁 Verzeichnisse:")
    print(f"   Logs: {'✅' if Path('logs').exists() else '❌'} logs/")
    print(f"   Source: {'✅' if Path('src').exists() else '❌'} src/")
    print(f"   Config: {'✅' if Path('config.yaml').exists() else '❌'} config.yaml")

async def main():
    """Hauptfunktion"""
    print_banner()
    
    # Prüfe Umgebung
    if not check_environment():
        sys.exit(1)
    
    if not check_config_files():
        sys.exit(1)
    
    print_status()
    
    # Setup Logging
    setup_logging()
    
    print("\n🚀 Starte Super-KI-Agent...")
    
    try:
        # Erstelle und starte Agent
        agent = SuperAgent()
        await agent.run_with_signal_handling()
        
    except KeyboardInterrupt:
        print("\n🛑 Super-KI-Agent gestoppt (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        logging.error(f"Kritischer Fehler beim Starten: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Prüfe Python-Version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ erforderlich!")
        sys.exit(1)
    
    # Starte Agent
    asyncio.run(main())