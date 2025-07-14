#!/usr/bin/env python3
"""
Liyana NEXUS v1 - Test Script
Testet alle Komponenten des Systems
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Testet alle Imports"""
    print("🔍 Teste Imports...")
    
    try:
        import config
        print("✅ config.py - OK")
    except Exception as e:
        print(f"❌ config.py - Fehler: {e}")
        return False
    
    try:
        from nexus_core import get_nexus_core
        print("✅ nexus_core.py - OK")
    except Exception as e:
        print(f"❌ nexus_core.py - Fehler: {e}")
        return False
    
    try:
        from memory_vault import MemoryVault
        print("✅ memory_vault.py - OK")
    except Exception as e:
        print(f"❌ memory_vault.py - Fehler: {e}")
        return False
    
    try:
        from email_unit import EmailUnit
        print("✅ email_unit.py - OK")
    except Exception as e:
        print(f"❌ email_unit.py - Fehler: {e}")
        return False
    
    try:
        from responder_unit import ResponderUnit
        print("✅ responder_unit.py - OK")
    except Exception as e:
        print(f"❌ responder_unit.py - Fehler: {e}")
        return False
    
    try:
        from telegram_unit import TelegramUnit
        print("✅ telegram_unit.py - OK")
    except Exception as e:
        print(f"❌ telegram_unit.py - Fehler: {e}")
        return False
    
    try:
        from call_center_unit import CallCenterUnit
        print("✅ call_center_unit.py - OK")
    except Exception as e:
        print(f"❌ call_center_unit.py - Fehler: {e}")
        return False
    
    try:
        from voice_clone_unit import VoiceCloneUnit
        print("✅ voice_clone_unit.py - OK")
    except Exception as e:
        print(f"❌ voice_clone_unit.py - Fehler: {e}")
        return False
    
    try:
        from drop_unit import DropUnit
        print("✅ drop_unit.py - OK")
    except Exception as e:
        print(f"❌ drop_unit.py - Fehler: {e}")
        return False
    
    try:
        from search_agent import SearchAgent
        print("✅ search_agent.py - OK")
    except Exception as e:
        print(f"❌ search_agent.py - Fehler: {e}")
        return False
    
    try:
        from learning_core import LearningCore
        print("✅ learning_core.py - OK")
    except Exception as e:
        print(f"❌ learning_core.py - Fehler: {e}")
        return False
    
    try:
        from automation_init import AutomationGUI
        print("✅ automation_init.py - OK")
    except Exception as e:
        print(f"❌ automation_init.py - Fehler: {e}")
        return False
    
    return True

def test_config():
    """Testet die Konfiguration"""
    print("\n🔧 Teste Konfiguration...")
    
    try:
        import config
        
        # Teste wichtige Konfigurationswerte
        assert hasattr(config, 'NEXUS_CONFIG'), "NEXUS_CONFIG fehlt"
        assert hasattr(config, 'EMAIL_CONFIG'), "EMAIL_CONFIG fehlt"
        assert hasattr(config, 'AI_CONFIG'), "AI_CONFIG fehlt"
        assert hasattr(config, 'VOICE_CONFIG'), "VOICE_CONFIG fehlt"
        assert hasattr(config, 'ECOMMERCE_CONFIG'), "ECOMMERCE_CONFIG fehlt"
        assert hasattr(config, 'GUI_CONFIG'), "GUI_CONFIG fehlt"
        
        print("✅ Konfiguration - OK")
        return True
        
    except Exception as e:
        print(f"❌ Konfiguration - Fehler: {e}")
        return False

def test_memory_vault():
    """Testet Memory Vault"""
    print("\n💾 Teste Memory Vault...")
    
    try:
        from memory_vault import MemoryVault
        
        # Memory Vault initialisieren
        memory = MemoryVault()
        
        # Teste Datenbankverbindung
        memory.init_database()
        
        # Teste einfache Operationen
        test_data = {
            "customer_id": "test_001",
            "email": "test@example.com",
            "name": "Test Customer"
        }
        
        # Speichern
        memory.store_customer(test_data)
        
        # Abrufen
        customer = memory.get_customer("test_001")
        assert customer is not None, "Kunde konnte nicht abgerufen werden"
        
        # Aufräumen
        memory.delete_customer("test_001")
        
        print("✅ Memory Vault - OK")
        return True
        
    except Exception as e:
        print(f"❌ Memory Vault - Fehler: {e}")
        return False

def test_nexus_core():
    """Testet NEXUS Core"""
    print("\n🤖 Teste NEXUS Core...")
    
    try:
        from nexus_core import get_nexus_core
        
        # NEXUS Core initialisieren
        nexus = get_nexus_core()
        
        # Teste System-Status
        status = nexus.get_system_status()
        assert isinstance(status, dict), "System-Status ist kein Dictionary"
        assert 'uptime' in status, "Uptime fehlt im Status"
        assert 'active_agents' in status, "Active Agents fehlt im Status"
        
        print("✅ NEXUS Core - OK")
        return True
        
    except Exception as e:
        print(f"❌ NEXUS Core - Fehler: {e}")
        return False

async def test_async_components():
    """Testet asynchrone Komponenten"""
    print("\n⚡ Teste asynchrone Komponenten...")
    
    try:
        from nexus_core import get_nexus_core
        
        # NEXUS Core initialisieren
        nexus = get_nexus_core()
        
        # Kurzer Test-Start
        await nexus.start('email_support')
        
        # Kurz warten
        await asyncio.sleep(2)
        
        # Status prüfen
        status = nexus.get_system_status()
        print(f"📊 Status nach Start: {status['active_agents']} aktive Agenten")
        
        # Stoppen
        await nexus.stop()
        
        print("✅ Asynchrone Komponenten - OK")
        return True
        
    except Exception as e:
        print(f"❌ Asynchrone Komponenten - Fehler: {e}")
        return False

def test_directories():
    """Testet erforderliche Verzeichnisse"""
    print("\n📁 Teste Verzeichnisse...")
    
    required_dirs = ["data", "logs", "models", "voice"]
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/ - OK")
        else:
            print(f"⚠️  {dir_name}/ - Nicht gefunden (wird erstellt)")
            dir_path.mkdir(exist_ok=True)
    
    return True

def test_dependencies():
    """Testet wichtige Dependencies"""
    print("\n📦 Teste Dependencies...")
    
    dependencies = [
        ("asyncio", "Async I/O"),
        ("sqlite3", "SQLite Database"),
        ("json", "JSON Processing"),
        ("logging", "Logging"),
        ("threading", "Threading"),
        ("time", "Time Functions"),
        ("pathlib", "Path Operations")
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✅ {module_name} ({description}) - OK")
        except ImportError:
            print(f"❌ {module_name} ({description}) - Fehler")
            return False
    
    # Optionale Dependencies
    optional_deps = [
        ("PySide6", "GUI Framework"),
        ("openai", "OpenAI API"),
        ("google.generativeai", "Google Gemini API"),
        ("numpy", "Numerical Computing"),
        ("pandas", "Data Analysis")
    ]
    
    for module_name, description in optional_deps:
        try:
            __import__(module_name)
            print(f"✅ {module_name} ({description}) - OK")
        except ImportError:
            print(f"⚠️  {module_name} ({description}) - Nicht verfügbar")
    
    return True

def main():
    """Hauptfunktion für Tests"""
    print("🧪 Liyana NEXUS v1 - System Test")
    print("=" * 50)
    
    # Teste Imports
    if not test_imports():
        print("\n❌ Import-Tests fehlgeschlagen")
        return False
    
    # Teste Konfiguration
    if not test_config():
        print("\n❌ Konfigurations-Tests fehlgeschlagen")
        return False
    
    # Teste Verzeichnisse
    if not test_directories():
        print("\n❌ Verzeichnis-Tests fehlgeschlagen")
        return False
    
    # Teste Dependencies
    if not test_dependencies():
        print("\n❌ Dependency-Tests fehlgeschlagen")
        return False
    
    # Teste Memory Vault
    if not test_memory_vault():
        print("\n❌ Memory Vault Tests fehlgeschlagen")
        return False
    
    # Teste NEXUS Core
    if not test_nexus_core():
        print("\n❌ NEXUS Core Tests fehlgeschlagen")
        return False
    
    # Teste asynchrone Komponenten
    try:
        asyncio.run(test_async_components())
    except Exception as e:
        print(f"\n❌ Async-Tests fehlgeschlagen: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Alle Tests erfolgreich!")
    print("✅ Liyana NEXUS v1 ist bereit für den Einsatz")
    print("\n🚀 Starte das System mit:")
    print("   python main.py --gui")
    print("   oder")
    print("   python main.py --type email_support")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)