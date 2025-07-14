# 🤖 Super-KI-Agent

Ein extrem leistungsfähiger, autonomer KI-E-Mail-Agent mit vollständiger Modulstruktur und umfassendem Testsystem.

## 🚀 Features

### 🔍 Intelligente E-Mail-Analyse
- **Automatische Kategorisierung** (Support, Sales, Inquiry, Complaint, etc.)
- **Sentiment-Analyse** (positiv, neutral, negativ)
- **Spracherkennung** (DE, EN, FR, ES)
- **Dringlichkeitserkennung** (hoch, mittel, niedrig)
- **Spam-Erkennung** mit erweiterten Filtern
- **Schlüsselinformationen-Extraktion** (Fragen, Anliegen, Kontaktdaten)

### 🧠 KI-gestützte Antwortgenerierung
- **GPT-4o Integration** für intelligente Antworten
- **Mehrsprachige Antworten** in der Originalsprache
- **Ton-Anpassung** (formal, freundlich, aggressiv)
- **Kontextbewusste Antworten** basierend auf E-Mail-Inhalt
- **Automatische Verbesserung** basierend auf Feedback

### 📱 Telegram-Integration
- **Echtzeit-Benachrichtigungen** über neue E-Mails
- **Genehmigungsworkflow** mit Inline-Buttons
- **Auto-Approval Kommandos** (ja/nein für alle)
- **Bearbeitungsfunktion** mit Feedback
- **Timeout-Behandlung** für ausstehende Genehmigungen
- **Status-Updates** und Statistiken

### ⚡ Intelligente Entscheidungsfindung
- **Confidence-basierte Entscheidungen** (0.0-1.0)
- **Automatische Genehmigung** bei hoher Confidence (≥95%)
- **Manuelle Überprüfung** bei mittlerer Confidence (≥70%)
- **Automatische Ablehnung** bei niedriger Confidence (≤30%)
- **Eskalation** für hochprioritäre E-Mails

### 🔒 Sicherheit & Robustheit
- **Verschlüsselte Verbindungen** (IMAP/SMTP SSL/TLS)
- **Rate Limiting** und Retry-Mechanismen
- **Verdächtige Inhalte-Erkennung**
- **Umfassendes Logging** und Fehlerbehandlung
- **Graceful Shutdown** mit Signal-Behandlung

## 🏗️ Architektur

```
Super-KI-Agent/
├── src/
│   ├── config_manager.py      # Konfigurationsverwaltung
│   ├── email_fetcher.py       # IMAP E-Mail Abruf
│   ├── email_analyzer.py      # KI-basierte E-Mail-Analyse
│   ├── response_generator.py  # GPT-4o Antwortgenerierung
│   ├── telegram_coordinator.py # Telegram Bot Integration
│   ├── email_sender.py        # SMTP E-Mail Versand
│   ├── decision_engine.py     # Intelligente Entscheidungsfindung
│   └── super_agent.py         # Hauptkoordinator
├── config.yaml               # Konfigurationsdatei
├── .env.example              # Umgebungsvariablen Template
├── requirements.txt          # Python-Abhängigkeiten
├── test_system.py           # Umfassendes Testsystem
└── README.md                # Diese Dokumentation
```

## 📋 Voraussetzungen

- **Python 3.8+**
- **Gmail-Konto** mit App-Passwort
- **OpenAI API Key** (GPT-4o)
- **Telegram Bot Token**
- **Linux/Windows/macOS**

## 🛠️ Installation

### 1. Repository klonen
```bash
git clone <repository-url>
cd super-ki-agent
```

### 2. Python-Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. Konfiguration einrichten
```bash
# Kopiere .env.example zu .env
cp .env.example .env

# Bearbeite .env mit deinen Credentials
nano .env
```

### 4. Umgebungsvariablen konfigurieren
```env
# E-Mail Konfiguration
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_ADMIN_CHAT_ID=your-admin-chat-id
TELEGRAM_NOTIFICATION_CHAT_ID=your-notification-chat-id
```

### 5. Gmail App-Passwort erstellen
1. Gehe zu [Google Account Settings](https://myaccount.google.com/)
2. Sicherheit → 2-Schritt-Verifizierung aktivieren
3. App-Passwörter → Neues App-Passwort erstellen
4. Verwende dieses Passwort in der `.env` Datei

### 6. Telegram Bot erstellen
1. Chatte mit [@BotFather](https://t.me/botfather) auf Telegram
2. `/newbot` → Name und Username eingeben
3. Bot-Token kopieren und in `.env` eintragen
4. Chat-ID ermitteln (mit [@userinfobot](https://t.me/userinfobot))

## 🚀 Verwendung

### Super-KI-Agent starten
```bash
python src/super_agent.py
```

### Tests ausführen
```bash
python test_system.py
```

### Konfiguration anpassen
```bash
# Bearbeite config.yaml für erweiterte Einstellungen
nano config.yaml
```

## 📱 Telegram-Befehle

### Grundlegende Befehle
- `/start` - Bot starten
- `/help` - Hilfe anzeigen
- `/status` - Aktuellen Status anzeigen

### E-Mail-Genehmigung
- `/approve [id]` - Spezifische E-Mail genehmigen
- `/reject [id]` - Spezifische E-Mail ablehnen
- `/edit [id] [feedback]` - E-Mail bearbeiten

### Auto-Approval
- `ja`, `yes`, `ok`, `approve` - Alle ausstehenden E-Mails genehmigen
- `nein`, `no`, `reject` - Alle ausstehenden E-Mails ablehnen

## ⚙️ Konfiguration

### E-Mail-Einstellungen
```yaml
email:
  imap:
    server: "imap.gmail.com"
    port: 993
    use_ssl: true
  smtp:
    server: "smtp.gmail.com"
    port: 587
    use_tls: true
  fetch_interval: 30  # Sekunden
  max_emails_per_fetch: 10
```

### AI-Einstellungen
```yaml
ai:
  model: "gpt-4o"
  max_tokens: 2000
  temperature: 0.7
  confidence_thresholds:
    auto_approve: 0.95
    auto_reject: 0.3
    require_human: 0.7
```

### Telegram-Einstellungen
```yaml
telegram:
  timeout_seconds: 300
  auto_approve_commands: ["ja", "yes", "ok", "approve"]
  reject_commands: ["nein", "no", "reject"]
  edit_commands: ["bearbeiten", "edit", "change"]
```

## 🔧 Erweiterte Features

### Automatische Kategorisierung
- **Support**: Hilfe-Anfragen, technische Probleme
- **Sales**: Kaufanfragen, Preisinformationen
- **Inquiry**: Allgemeine Anfragen, Informationen
- **Complaint**: Beschwerden, negative Feedback
- **Feedback**: Bewertungen, Meinungen
- **Appointment**: Termine, Meetings
- **Order**: Bestellungen, Rechnungen
- **Spam**: Automatisch erkannte Spam-E-Mails

### Prioritätserkennung
- **Hoch**: Dringende Angelegenheiten, Eskalation erforderlich
- **Mittel**: Normale Geschäftsanfragen
- **Niedrig**: Informationsanfragen, Newsletter

### Mehrsprachige Unterstützung
- **Deutsch**: Vollständige Unterstützung
- **Englisch**: Vollständige Unterstützung
- **Französisch**: Grundlegende Unterstützung
- **Spanisch**: Grundlegende Unterstützung

## 📊 Monitoring & Logging

### Log-Dateien
- `logs/super_agent.log` - Hauptlog-Datei
- Automatische Rotation bei 10MB
- 5 Backup-Dateien

### Telegram-Status-Updates
- Echtzeit-Benachrichtigungen
- Statistiken und Performance-Metriken
- Fehler-Benachrichtigungen

### Statistiken
- Verarbeitete E-Mails
- Genehmigte/Abgelehnte E-Mails
- Durchschnittliche Verarbeitungszeit
- Confidence-Level-Verteilung

## 🧪 Testing

### Test-Suite ausführen
```bash
python test_system.py
```

### Test-Kategorien
- **Unit Tests**: Einzelne Module
- **Integration Tests**: Modul-Interaktionen
- **Performance Tests**: Skalierbarkeit
- **Spam-Erkennung**: Sicherheitstests
- **Spracherkennung**: Mehrsprachigkeit

## 🔒 Sicherheit

### Implementierte Sicherheitsmaßnahmen
- **Verschlüsselte Verbindungen** (SSL/TLS)
- **App-Passwörter** statt normaler Passwörter
- **Rate Limiting** gegen API-Missbrauch
- **Spam-Erkennung** mit mehreren Filtern
- **Verdächtige Inhalte-Erkennung**
- **Timeout-Mechanismen** für Genehmigungen

### Best Practices
- Regelmäßige Passwort-Updates
- Monitoring der API-Nutzung
- Backup der Konfigurationsdateien
- Regelmäßige Log-Analyse

## 🚀 Performance-Optimierung

### Empfohlene Einstellungen
- **Fetch-Interval**: 30-60 Sekunden
- **Max E-Mails per Fetch**: 10-20
- **Confidence-Thresholds**: Anpassung basierend auf Erfahrung
- **Timeout**: 300-600 Sekunden

### Skalierung
- **Mehrere Instanzen** für hohe E-Mail-Volumen
- **Load Balancing** über mehrere E-Mail-Konten
- **Datenbank-Integration** für Persistenz
- **Redis-Caching** für Performance

## 🐛 Troubleshooting

### Häufige Probleme

#### E-Mail-Verbindung fehlgeschlagen
```bash
# Prüfe Gmail-Einstellungen
# - 2-Schritt-Verifizierung aktiviert?
# - App-Passwort korrekt?
# - IMAP aktiviert?
```

#### OpenAI API Fehler
```bash
# Prüfe API Key
# - Korrekt in .env eingetragen?
# - Guthaben verfügbar?
# - Rate Limits erreicht?
```

#### Telegram Bot funktioniert nicht
```bash
# Prüfe Bot-Konfiguration
# - Bot-Token korrekt?
# - Chat-ID richtig?
# - Bot gestartet?
```

### Debug-Modus aktivieren
```yaml
# In config.yaml
logging:
  level: "DEBUG"
```

## 📈 Roadmap

### Geplante Features
- [ ] **Datenbank-Integration** (PostgreSQL/MongoDB)
- [ ] **Web-Interface** für Konfiguration
- [ ] **Erweiterte Analytics** und Reporting
- [ ] **Multi-Account Support**
- [ ] **Kalender-Integration**
- [ ] **CRM-Integration**
- [ ] **Machine Learning** für bessere Erkennung
- [ ] **API-Endpoints** für externe Integration

### Performance-Verbesserungen
- [ ] **Async Processing** für höhere Durchsatz
- [ ] **Caching-System** für wiederholte Anfragen
- [ ] **Queue-Management** für große Volumen
- [ ] **Distributed Processing** für Skalierung

## 🤝 Beitragen

### Entwicklungsumgebung einrichten
```bash
# Fork Repository
# Clone dein Fork
git clone https://github.com/your-username/super-ki-agent.git

# Branch erstellen
git checkout -b feature/neue-funktion

# Änderungen committen
git commit -m "Neue Funktion hinzugefügt"

# Pull Request erstellen
```

### Coding Standards
- **PEP 8** für Python-Code
- **Type Hints** für alle Funktionen
- **Docstrings** für alle Klassen/Methoden
- **Unit Tests** für neue Features
- **Logging** für Debugging

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🙏 Danksagungen

- **OpenAI** für GPT-4o API
- **Telegram** für Bot API
- **Python Community** für hervorragende Libraries
- **Open Source Community** für Inspiration und Support

## 📞 Support

Bei Fragen oder Problemen:
- **Issues**: GitHub Issues erstellen
- **Discussions**: GitHub Discussions nutzen
- **Email**: support@super-ki-agent.com

---

**Super-KI-Agent** - Intelligentes E-Mail-Management der nächsten Generation! 🚀
