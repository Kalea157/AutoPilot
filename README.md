# 🤖 Super AI Email Agent

Ein hochleistungsfähiger, autonomer E-Mail-Assistent mit GPT-4o-Intelligenz, der E-Mails automatisch analysiert, Antworten generiert und über Telegram zur Freigabe koordiniert.

## 🚀 Features

### 🔍 Intelligente E-Mail-Analyse
- **Automatische Kategorisierung**: Fragen, Beschwerden, Bestellungen, Support, etc.
- **Sentiment-Analyse**: Positive, neutrale, negative Stimmung
- **Dringlichkeits-Bewertung**: 1-10 Skala mit Prioritäten
- **Spracherkennung**: Deutsch, Englisch, Französisch, Spanisch
- **Schlüsselinformationen**: Extrahiert Fragen, Aufgaben, wichtige Details

### 🤖 GPT-4o Antwort-Generierung
- **Kontextuelle Antworten**: Berücksichtigt Ton, Stimmung, Kategorie
- **Mehrsprachige Unterstützung**: Antwortet in der Sprache der Original-E-Mail
- **Strategie-basiert**: Formal, casual, apologetisch, informativ
- **Vertrauens-Bewertung**: Confidence-Score für jede Antwort

### 📱 Telegram-Integration
- **Freigabe-System**: Manuelle Genehmigung für unsichere Antworten
- **Inline-Buttons**: Schnelle Aktionen (Genehmigen, Ablehnen, Bearbeiten, Ignorieren)
- **Timeout-Handling**: Automatische Timeout nach konfigurierbarer Zeit
- **Live-Statistiken**: Echtzeit-Übersicht über Verarbeitung

### ⚡ Automatische Freigabe
- **Confidence-basiert**: E-Mails mit >95% Vertrauen werden automatisch gesendet
- **Benachrichtigungen**: Telegram-Updates über automatische Aktionen
- **Sicherheit**: Manuelle Freigabe für alle unsicheren Antworten

### 🛠 Technische Features
- **Modulare Architektur**: Jede Komponente ist unabhängig und erweiterbar
- **Asynchrone Verarbeitung**: Maximale Performance und Skalierbarkeit
- **Umfassendes Logging**: JSON-basiertes Logging mit Strukturlog
- **Konfigurierbar**: YAML + Umgebungsvariablen
- **Gmail-kompatibel**: Optimiert für Gmail-Konten
- **Offline-fähig**: Läuft lokal ohne Cloud-Abhängigkeiten (außer Telegram)

## 📋 Voraussetzungen

- **Python 3.8+**
- **Gmail-Konto** mit App-Passwort
- **OpenAI API Key** für GPT-4o
- **Telegram Bot Token** und Chat ID

## 🚀 Installation

### 1. Repository klonen
```bash
git clone <repository-url>
cd super-ai-email-agent
```

### 2. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 3. Konfiguration einrichten
```bash
# Kopiere Beispiel-Konfiguration
cp .env.example .env

# Bearbeite .env mit deinen Werten
nano .env
```

### 4. Gmail App-Passwort erstellen
1. Gehe zu [Google Account Settings](https://myaccount.google.com/)
2. Sicherheit → 2-Schritt-Verifizierung aktivieren
3. App-Passwörter → Neues App-Passwort für "Mail"
4. Verwende dieses Passwort in der `.env` Datei

### 5. Telegram Bot erstellen
1. Chatte mit [@BotFather](https://t.me/botfather) auf Telegram
2. `/newbot` → Folge den Anweisungen
3. Kopiere den Bot Token in `.env`
4. Starte den Bot und sende `/start`
5. Hole deine Chat ID von [@userinfobot](https://t.me/userinfobot)

## ⚙️ Konfiguration

### Umgebungsvariablen (.env)
```env
# Email Configuration
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Security
ENCRYPTION_KEY=your_32_character_encryption_key
```

### YAML-Konfiguration (config.yaml)
Die `config.yaml` enthält alle erweiterbaren Einstellungen:
- Agent-Verhalten (Confidence-Thresholds, Timeouts)
- E-Mail-Einstellungen (IMAP/SMTP, Check-Interval)
- AI-Parameter (Model, Temperature, Prompts)
- Telegram-Templates und Formatierung
- Logging und Performance-Optimierung

## 🎯 Verwendung

### Standard-Modus
```bash
python main.py
```

### Dashboard-Modus (Live-Übersicht)
```bash
python main.py dashboard
```

### Tests ausführen
```bash
# Alle Tests
python test_system.py all

# Nur Unit-Tests
python test_system.py unit

# Nur Integration-Tests
python test_system.py integration

# Nur Agent-Tests
python test_system.py agent
```

### Weitere Befehle
```bash
# Hilfe anzeigen
python main.py help

# Konfiguration anzeigen
python main.py config
```

## 📱 Telegram-Befehle

Sobald der Agent läuft, stehen folgende Telegram-Befehle zur Verfügung:

- `/start` - Willkommensnachricht und Übersicht
- `/status` - Aktuelle Statistiken und Performance
- `/help` - Detaillierte Hilfe und Anleitung

### Freigabe-Aktionen
Für jede E-Mail zur Freigabe stehen folgende Aktionen zur Verfügung:

- **✅ Genehmigen** - Antwort wird sofort gesendet
- **❌ Ablehnen** - E-Mail wird als gelesen markiert, keine Antwort
- **✏️ Bearbeiten** - E-Mail wird zur manuellen Bearbeitung markiert
- **🚫 Ignorieren** - E-Mail wird ignoriert, keine Aktion

## 🏗 Architektur

```
Super AI Agent
├── 📧 Email Module
│   ├── Fetcher (IMAP) - E-Mails abrufen
│   └── Sender (SMTP) - Antworten versenden
├── 🤖 AI Module
│   ├── Analyzer - E-Mail-Analyse mit GPT-4o
│   └── ResponseGenerator - Antwort-Generierung
├── 📱 Telegram Module
│   └── Coordinator - Freigabe und Kommunikation
├── ⚙️ Core Module
│   └── ConfigManager - Konfigurationsverwaltung
└── 🎯 Super Agent - Haupt-Orchestrator
```

### Datenfluss
1. **E-Mail-Abruf**: IMAP-Fetcher holt neue E-Mails
2. **AI-Analyse**: GPT-4o analysiert Inhalt, Ton, Kategorie
3. **Antwort-Generierung**: GPT-4o erstellt kontextuelle Antwort
4. **Freigabe-Entscheidung**: 
   - >95% Confidence → Automatische Freigabe
   - 85-95% Confidence → Telegram-Freigabe
   - <85% Confidence → Ignorieren
5. **Versand**: SMTP-Sender versendet genehmigte Antworten

## 🔧 Erweiterungen

### Neue E-Mail-Kategorien
Füge neue Kategorien in `src/ai/analyzer.py` hinzu:
```python
self.categories = [
    'question', 'complaint', 'order', 'support', 'feedback',
    'appointment', 'invoice', 'general', 'spam', 'urgent',
    'your_new_category'  # Neue Kategorie
]
```

### Custom Response-Strategien
Erweitere Antwort-Templates in `src/ai/response_generator.py`:
```python
self.response_templates = {
    'formal': {...},
    'casual': {...},
    'your_strategy': {  # Neue Strategie
        'greeting': 'Custom greeting',
        'closing': 'Custom closing',
        'tone': 'Custom tone'
    }
}
```

### Telegram-Integration erweitern
Füge neue Commands in `src/telegram/coordinator.py` hinzu:
```python
self.application.add_handler(CommandHandler("your_command", self._your_command_handler))
```

## 📊 Monitoring & Logging

### Logs
- **JSON-Format**: Strukturierte Logs für einfache Verarbeitung
- **Log-Rotation**: Automatische Rotation nach Größe/Zeit
- **Performance-Tracking**: Response-Zeiten und Confidence-Scores

### Statistiken
- **Verarbeitete E-Mails**: Gesamtanzahl und Erfolgsrate
- **Freigabe-Statistiken**: Genehmigt, abgelehnt, timeout
- **Performance-Metriken**: Durchschnittliche Verarbeitungszeit
- **Komponenten-Status**: Verbindungsstatus aller Module

## 🛡️ Sicherheit

- **Verschlüsselung**: Sensible Daten werden verschlüsselt gespeichert
- **App-Passwörter**: Gmail-App-Passwörter statt normaler Passwörter
- **Lokale Verarbeitung**: Alle Daten bleiben lokal (außer Telegram)
- **Timeout-Schutz**: Automatische Timeouts verhindern hängende Anfragen
- **Fehlerbehandlung**: Robuste Fehlerbehandlung mit Fallbacks

## 🚨 Troubleshooting

### Häufige Probleme

**IMAP-Verbindung fehlgeschlagen**
- Prüfe Gmail-App-Passwort
- Aktiviere 2-Schritt-Verifizierung
- Prüfe IMAP-Einstellungen in Gmail

**SMTP-Verbindung fehlgeschlagen**
- Prüfe SMTP-Einstellungen
- Stelle sicher, dass TLS aktiviert ist
- Prüfe Firewall-Einstellungen

**Telegram-Bot funktioniert nicht**
- Prüfe Bot Token
- Stelle sicher, dass Bot gestartet wurde
- Prüfe Chat ID

**OpenAI API Fehler**
- Prüfe API Key
- Prüfe Guthaben/Quotas
- Prüfe Internet-Verbindung

### Debug-Modus
```bash
# Aktiviere Debug-Logging in config.yaml
agent:
  debug: true
```

## 🤝 Beitragen

1. Fork das Repository
2. Erstelle einen Feature-Branch
3. Implementiere deine Änderungen
4. Führe Tests aus: `python test_system.py all`
5. Erstelle einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **OpenAI** für GPT-4o API
- **Telegram** für Bot API
- **Python Community** für die großartigen Libraries

---

**Entwickelt mit ❤️ für maximale E-Mail-Effizienz**
