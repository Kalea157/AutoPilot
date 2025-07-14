#!/usr/bin/env python3
"""
Liyana NEXUS v1 - Main Entry Point
Super-KI-Agent Stage 8 - Hauptstartskript
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import NEXUS_CONFIG, LOGGING_CONFIG
    from nexus_core import get_nexus_core
    from automation_init import AutomationGUI
except ImportError as e:
    print(f"❌ Import-Fehler: {e}")
    print("💡 Stelle sicher, dass alle Dependencies installiert sind:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

def setup_logging():
    """Konfiguriert das Logging-System"""
    try:
        import logging.config
        logging.config.dictConfig(LOGGING_CONFIG)
        logger = logging.getLogger("nexus.main")
        logger.info("🚀 Liyana NEXUS v1 - Logging initialisiert")
        return logger
    except Exception as e:
        print(f"❌ Logging-Fehler: {e}")
        # Fallback logging
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        return logging.getLogger("nexus.main")

def check_environment():
    """Überprüft die Umgebung und Dependencies"""
    logger = logging.getLogger("nexus.main")
    
    # Python Version check
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 oder höher erforderlich")
        return False
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning("⚠️ .env Datei nicht gefunden")
        logger.info("💡 Kopiere .env.example zu .env und konfiguriere deine API-Keys")
    
    # Check for required directories
    required_dirs = ["data", "logs", "models", "voice"]
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            logger.info(f"📁 Verzeichnis erstellt: {dir_name}")
    
    logger.info("✅ Umgebungsprüfung abgeschlossen")
    return True

def print_banner():
    """Zeigt das NEXUS Banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    ██╗     ██╗██╗   ██╗ █████╗ ███╗   ██╗ █████╗         ║
    ║    ██║     ██║╚██╗ ██╔╝██╔══██╗████╗  ██║██╔══██╗        ║
    ║    ██║     ██║ ╚████╔╝ ███████║██╔██╗ ██║███████║        ║
    ║    ██║     ██║  ╚██╔╝  ██╔══██║██║╚██╗██║██╔══██║        ║
    ║    ███████╗██║   ██║   ██║  ██║██║ ╚████║██║  ██║        ║
    ║    ╚══════╝╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝        ║
    ║                                                              ║
    ║                    Super-KI-Agent Stage 8                   ║
    ║                        Version 1.0.0                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🚀 Initialisiere Liyana NEXUS v1...
    """
    print(banner)

def print_automation_types():
    """Zeigt verfügbare Automatisierungstypen"""
    types = {
        "email_support": {
            "name": "📧 E-Mail Support",
            "description": "Automatische E-Mail-Verarbeitung und KI-basierte Antworten"
        },
        "call_center": {
            "name": "🎙️ Call Center",
            "description": "Sprachverarbeitung und automatische Anrufbehandlung"
        },
        "dropshipping": {
            "name": "🛒 Dropshipping",
            "description": "Automatische Produktsuche und Bestellungen"
        },
        "research": {
            "name": "🔍 Marktforschung",
            "description": "Trendanalysen und Konkurrenzvergleich"
        }
    }
    
    print("\n📋 Verfügbare Automatisierungstypen:")
    print("=" * 60)
    for key, info in types.items():
        print(f"  {info['name']}")
        print(f"    └─ {info['description']}")
        print(f"    └─ Verwendung: --type {key}")
        print()

async def run_console_mode(automation_type: str, duration: Optional[int] = None):
    """Führt NEXUS im Konsolenmodus aus"""
    logger = logging.getLogger("nexus.main")
    
    try:
        # NEXUS Core initialisieren
        nexus = get_nexus_core()
        
        # System starten
        logger.info(f"🎯 Starte Automatisierung: {automation_type}")
        await nexus.start(automation_type)
        
        # Status anzeigen
        status = nexus.get_system_status()
        logger.info(f"✅ System gestartet - Uptime: {status['uptime']}")
        logger.info(f"📊 Aktive Agenten: {status['active_agents']}")
        
        # Laufzeit
        if duration:
            logger.info(f"⏱️  Laufzeit: {duration} Sekunden")
            await asyncio.sleep(duration)
        else:
            logger.info("⏱️  System läuft unbegrenzt (Strg+C zum Beenden)")
            try:
                # Unendliche Schleife mit Status-Updates
                while True:
                    await asyncio.sleep(60)  # Status alle 60 Sekunden
                    status = nexus.get_system_status()
                    logger.info(f"📊 Status: {status['active_agents']} aktive Agenten")
            except KeyboardInterrupt:
                logger.info("🛑 Beenden durch Benutzer...")
        
        # System stoppen
        await nexus.stop()
        logger.info("✅ NEXUS erfolgreich beendet")
        
    except Exception as e:
        logger.error(f"❌ Fehler im Konsolenmodus: {e}")
        raise

def run_gui_mode():
    """Startet die GUI-Version von NEXUS"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # Qt Application erstellen
        app = QApplication(sys.argv)
        app.setApplicationName("Liyana NEXUS v1")
        app.setApplicationVersion("1.0.0")
        
        # GUI erstellen und anzeigen
        gui = AutomationGUI()
        gui.show()
        
        # Event-Loop starten
        sys.exit(app.exec())
        
    except ImportError:
        print("❌ PySide6 nicht verfügbar - Fallback zu Konsolenmodus")
        print("💡 Installiere PySide6 für die GUI: pip install PySide6")
        return False
    except Exception as e:
        print(f"❌ GUI-Fehler: {e}")
        return False

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(
        description="Liyana NEXUS v1 - Super-KI-Agent Stage 8",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py --gui                    # Startet GUI
  python main.py --type email_support     # E-Mail Support
  python main.py --type call_center       # Call Center
  python main.py --type dropshipping      # Dropshipping
  python main.py --type research          # Marktforschung
  python main.py --type email_support --duration 3600  # 1 Stunde
        """
    )
    
    parser.add_argument(
        "--gui", 
        action="store_true",
        help="Startet die GUI-Version"
    )
    
    parser.add_argument(
        "--type",
        choices=["email_support", "call_center", "dropshipping", "research"],
        default="email_support",
        help="Automatisierungstyp (Standard: email_support)"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        help="Laufzeit in Sekunden (Standard: unbegrenzt)"
    )
    
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="Zeigt verfügbare Automatisierungstypen"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"Liyana NEXUS v1 {NEXUS_CONFIG['version']} (Stage {NEXUS_CONFIG['stage']})"
    )
    
    args = parser.parse_args()
    
    # Banner anzeigen
    print_banner()
    
    # Automatisierungstypen auflisten
    if args.list_types:
        print_automation_types()
        return
    
    # Logging initialisieren
    logger = setup_logging()
    
    # Debug-Modus
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🐛 Debug-Modus aktiviert")
    
    # Umgebungsprüfung
    if not check_environment():
        sys.exit(1)
    
    # GUI-Modus
    if args.gui:
        logger.info("🖥️  Starte GUI-Modus")
        if not run_gui_mode():
            logger.info("🔄 Fallback zu Konsolenmodus")
            asyncio.run(run_console_mode(args.type, args.duration))
        return
    
    # Konsolenmodus
    logger.info("💻 Starte Konsolenmodus")
    try:
        asyncio.run(run_console_mode(args.type, args.duration))
    except KeyboardInterrupt:
        logger.info("🛑 Programm durch Benutzer beendet")
    except Exception as e:
        logger.error(f"❌ Unbehandelter Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()