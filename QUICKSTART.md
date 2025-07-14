# 🚀 Liyana NEXUS v1 - Quick Start Guide

## ⚡ Schnellstart in 5 Minuten

### 1. 📦 Dependencies installieren

```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv

# Umgebung aktivieren
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt
```

### 2. 🔑 API-Keys konfigurieren

```bash
# .env Datei erstellen
cp .env.example .env

# .env Datei bearbeiten
nano .env  # oder dein bevorzugter Editor
```

**Minimale Konfiguration (für Test):**
```env
# AI APIs (mindestens eine erforderlich)
OPENAI_API_KEY=your_openai_key_here
# oder
GEMINI_API_KEY=your_gemini_key_here

# Telegram (optional, für Benachrichtigungen)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Debug-Modus für Tests
DEBUG_MODE=true
MOCK_APIS=true
```

### 3. 🧪 System testen

```bash
# Demo anzeigen
python demo.py

# Systemtest durchführen
python test_nexus.py
```

### 4. 🚀 System starten

```bash
# GUI-Start (empfohlen)
python main.py --gui

# Konsolen-Start
python main.py --type email_support

# Mit Debug-Informationen
python main.py --type email_support --debug
```

## 🎯 Automatisierungstypen

| Typ | Befehl | Beschreibung |
|-----|--------|--------------|
| 📧 E-Mail Support | `--type email_support` | Automatische E-Mail-Verarbeitung |
| 🎙️ Call Center | `--type call_center` | Sprachverarbeitung |
| 🛒 Dropshipping | `--type dropshipping` | Produktsuche & Bestellungen |
| 🔍 Marktforschung | `--type research` | Trendanalyse |

## 🔧 Häufige Probleme

### Import-Fehler
```bash
# Dependencies neu installieren
pip install --upgrade -r requirements.txt
```

### API-Key-Fehler
- Überprüfe `.env` Datei
- Stelle sicher, dass API-Keys gültig sind
- Teste mit `MOCK_APIS=true` für Simulation

### GUI-Probleme
```bash
# PySide6 neu installieren
pip install PySide6 --upgrade

# Fallback zu Konsolenmodus
python main.py --type email_support
```

### Speicherprobleme
- Reduziere `MAX_CONCURRENT_AGENTS` in `config.py`
- Überprüfe verfügbaren RAM

## 📊 System-Monitoring

### Status abfragen
```python
from nexus_core import get_nexus_core

nexus = get_nexus_core()
status = nexus.get_system_status()
print(f"Uptime: {status['uptime']}")
print(f"Aktive Agenten: {status['active_agents']}")
```

### Logs überprüfen
```bash
# Live-Logs anzeigen
tail -f logs/nexus.log

# Letzte 100 Zeilen
tail -n 100 logs/nexus.log
```

## 🎮 Erste Schritte

### 1. E-Mail Support testen
```bash
python main.py --type email_support --duration 300
```

### 2. Call Center simulieren
```bash
python main.py --type call_center --debug
```

### 3. Dropshipping erkunden
```bash
python main.py --type dropshipping
```

### 4. Marktforschung starten
```bash
python main.py --type research
```

## 🔐 Sicherheit

### API-Keys schützen
- Bewahre `.env` sicher auf
- Teile API-Keys nicht
- Verwende App-Passwörter für E-Mail

### Rate Limiting
- Überprüfe API-Limits
- Verwende `RATE_LIMITING_ENABLED=true`
- Monitor API-Nutzung

## 📈 Performance-Optimierung

### Speicher
```env
MAX_MEMORY_USAGE=0.8
MAX_CACHE_SIZE=1000
```

### Threading
```env
MAX_CONCURRENT_AGENTS=5
MAX_WORKERS=8
```

### Caching
```env
CACHE_TTL=300
```

## 🆘 Support

### Logs analysieren
```bash
# Fehler suchen
grep "ERROR" logs/nexus.log

# Warnungen anzeigen
grep "WARNING" logs/nexus.log
```

### Debug-Modus
```bash
# Vollständiges Debug-Logging
python main.py --type email_support --debug

# Mock-APIs für Tests
MOCK_APIS=true python main.py --type email_support
```

### System-Status
```bash
# Verfügbare Automatisierungstypen
python main.py --list-types

# Version anzeigen
python main.py --version
```

## 🎉 Erfolgreich gestartet!

Nach dem Start siehst du:
- ✅ System-Status
- 📊 Aktive Agenten
- 🔄 Laufende Prozesse
- 📱 Telegram-Benachrichtigungen (falls konfiguriert)

## 📚 Nächste Schritte

1. **Konfiguration anpassen**: Bearbeite `config.py` für deine Bedürfnisse
2. **APIs erweitern**: Füge weitere API-Keys hinzu
3. **Automatisierung optimieren**: Passe Module an deine Workflows an
4. **Monitoring einrichten**: Überwache System-Performance
5. **Backup konfigurieren**: Richte automatische Backups ein

---

**🚀 Viel Erfolg mit Liyana NEXUS v1!**

Bei Fragen: Überprüfe die `README.md` oder erstelle ein Issue im Repository.