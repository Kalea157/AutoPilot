# 🤖 Autonomer KI-E-Mail-Agent

Ein vollständig funktionsfähiger, autonomer E-Mail-Agent mit KI-gestützter Antwortgenerierung und Telegram-Integration für vollständige Kontrolle über ausgehende E-Mails.

## 🎯 Funktionen

- **Automatische E-Mail-Verarbeitung**: Liest ungelesene E-Mails über IMAP
- **KI-gestützte Antwortgenerierung**: Nutzt OpenAI GPT-4o für intelligente Antworten
- **Telegram-Integration**: Benachrichtigungen und Bestätigungen über Telegram
- **Vollständige Kontrolle**: Nur nach Ihrer Bestätigung (JA/NEIN) werden E-Mails gesendet
- **Sichere Authentifizierung**: Reagiert nur auf Ihre Telegram-User-ID
- **Timeout-Handling**: Automatisches Verwerfen nach 30 Minuten ohne Antwort
- **Umfassendes Logging**: Detaillierte Protokollierung aller Aktivitäten
- **Skalierbar**: Erweiterbar für Kundenkontakt, Support-Antworten etc.

## 📋 Voraussetzungen

- Python 3.8 oder höher
- Gmail-Account (oder anderer E-Mail-Anbieter mit IMAP/SMTP)
- Telegram-Bot-Token
- OpenAI API-Key
- App-Passwort für Gmail (falls 2FA aktiviert)

## 🚀 Installation

### 1. Repository klonen
```bash
git clone <repository-url>
cd email-agent
```

### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 3. Konfiguration einrichten

#### E-Mail-Konfiguration (Gmail)
1. **App-Passwort erstellen**:
   - Gehen Sie zu [Google-Kontoeinstellungen](https://myaccount.google.com/)
   - Sicherheit → 2-Schritt-Verifizierung → App-Passwörter
   - Erstellen Sie ein neues App-Passwort für "E-Mail-Agent"

#### Telegram-Bot erstellen
1. **Bot erstellen**:
   - Senden Sie `/newbot` an [@BotFather](https://t.me/botfather) auf Telegram
   - Folgen Sie den Anweisungen und erhalten Sie den Bot-Token

2. **User-ID ermitteln**:
   - Senden Sie eine Nachricht an Ihren Bot
   - Rufen Sie `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` auf
   - Notieren Sie Ihre `id` aus der Antwort

#### OpenAI API-Key
1. **API-Key erstellen**:
   - Gehen Sie zu [OpenAI Platform](https://platform.openai.com/)
   - API Keys → Create new secret key
   - Notieren Sie den API-Key

### 4. Konfigurationsdatei anpassen

Bearbeiten Sie `config.yaml`:

```yaml
# E-Mail-Konfiguration
email:
  imap:
    server: "imap.gmail.com"
    port: 993
    username: "ihre-email@gmail.com"
    password: "ihr-app-passwort"
  
  smtp:
    server: "smtp.gmail.com"
    port: 587
    username: "ihre-email@gmail.com"
    password: "ihr-app-passwort"
    use_tls: true

# Telegram-Konfiguration
telegram:
  bot_token: "ihr-telegram-bot-token"
  user_id: "ihre-telegram-user-id"
  timeout_minutes: 30

# OpenAI-Konfiguration
openai:
  api_key: "ihr-openai-api-key"
  model: "gpt-4o-mini"
  max_tokens: 1000
  temperature: 0.7

# Agent-Einstellungen
agent:
  check_interval_minutes: 5
  max_emails_per_cycle: 1
  log_level: "INFO"
  log_file: "email_agent.log"
```

## 🏃‍♂️ Verwendung

### Agent starten
```bash
python main.py
```

### Als Service starten (Linux)
```bash
# Systemd Service erstellen
sudo nano /etc/systemd/system/email-agent.service
```

Service-Datei:
```ini
[Unit]
Description=Email Agent Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/email-agent
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Service aktivieren:
```bash
sudo systemctl enable email-agent
sudo systemctl start email-agent
sudo systemctl status email-agent
```

## 📱 Telegram-Interaktion

### Benachrichtigungen erhalten
Der Agent sendet automatisch Benachrichtigungen über neue E-Mails:

```
📧 Neue E-Mail erhalten

Von: Max Mustermann
Betreff: Anfrage zu Produkt

Inhalt:
Hallo, ich interessiere mich für Ihr Produkt...

Generierte Antwort:
Sehr geehrte/r Max Mustermann,
vielen Dank für Ihre Anfrage...

Antworten Sie mit "JA" um die E-Mail zu senden oder "NEIN" um abzubrechen.
```

### Antworten senden
- **"JA"** oder **"YES"**: E-Mail wird gesendet
- **"NEIN"** oder **"NO"**: E-Mail wird abgebrochen
- **Andere Antworten**: Sie erhalten eine Hilfemeldung

### Status-Updates
Der Agent sendet automatisch Status-Updates bei:
- Start/Stop des Agents
- Fehlern in der Verarbeitung
- Timeout von Antworten
- Erfolgreichem/fehlgeschlagenem E-Mail-Versand

## 🔧 Konfiguration

### E-Mail-Anbieter

#### Gmail
```yaml
email:
  imap:
    server: "imap.gmail.com"
    port: 993
  smtp:
    server: "smtp.gmail.com"
    port: 587
    use_tls: true
```

#### Outlook/Hotmail
```yaml
email:
  imap:
    server: "outlook.office365.com"
    port: 993
  smtp:
    server: "smtp-mail.outlook.com"
    port: 587
    use_tls: true
```

#### Web.de
```yaml
email:
  imap:
    server: "imap.web.de"
    port: 993
  smtp:
    server: "smtp.web.de"
    port: 587
    use_tls: true
```

### Agent-Einstellungen

- `check_interval_minutes`: Wie oft nach neuen E-Mails gesucht wird (Standard: 5)
- `max_emails_per_cycle`: Maximale E-Mails pro Durchlauf (Standard: 1)
- `timeout_minutes`: Timeout für Telegram-Antworten (Standard: 30)
- `log_level`: Logging-Level (DEBUG, INFO, WARNING, ERROR)

## 📊 Logging

Logs werden in `email_agent.log` gespeichert und enthalten:
- E-Mail-Verarbeitung
- Telegram-Interaktionen
- Fehler und Warnungen
- System-Status

Beispiel-Log:
```
2024-01-15 10:30:15 - EmailAgent - INFO - E-Mail-Agent erfolgreich initialisiert
2024-01-15 10:30:16 - EmailAgent - INFO - Alle Verbindungen erfolgreich getestet
2024-01-15 10:30:17 - EmailAgent - INFO - E-Mail-Agent gestartet und bereit
2024-01-15 10:35:20 - EmailAgent - INFO - 1 neue E-Mail(s) gefunden
2024-01-15 10:35:21 - EmailAgent - INFO - Verarbeite E-Mail 12345
```

## 🛠️ Troubleshooting

### Häufige Probleme

#### IMAP-Verbindung fehlgeschlagen
- Prüfen Sie App-Passwort (nicht normales Passwort)
- 2-Schritt-Verifizierung muss aktiviert sein
- Prüfen Sie IMAP-Einstellungen in Gmail

#### Telegram-Bot funktioniert nicht
- Bot-Token korrekt?
- User-ID korrekt?
- Bot gestartet? (`/start` an Bot senden)

#### OpenAI API-Fehler
- API-Key korrekt?
- Guthaben vorhanden?
- Rate-Limits erreicht?

#### E-Mails werden nicht gesendet
- SMTP-Einstellungen korrekt?
- App-Passwort für SMTP?
- Firewall blockiert Port 587?

### Debug-Modus
```yaml
agent:
  log_level: "DEBUG"
```

### Test-Verbindungen
```bash
# Teste E-Mail-Verbindung
python -c "from email_fetcher import EmailFetcher; f = EmailFetcher(); print('IMAP OK' if f.connect() else 'IMAP FAIL')"

# Teste Telegram-Verbindung
python -c "import asyncio; from telegram_sender import TelegramSender; asyncio.run(TelegramSender().test_connection())"

# Teste OpenAI-Verbindung
python -c "from email_responder import EmailResponder; r = EmailResponder(); print('OpenAI OK')"
```

## 🔒 Sicherheit

- **Telegram-User-ID**: Nur Ihre ID kann Antworten senden
- **App-Passwörter**: Sichere Authentifizierung ohne 2FA-Bypass
- **Timeout**: Automatisches Verwerfen nach 30 Minuten
- **Logging**: Keine sensiblen Daten in Logs
- **Validierung**: Alle E-Mails werden vor Versand validiert

## 📈 Erweiterungen

### Eigene Antwort-Templates
Bearbeiten Sie `config.yaml`:
```yaml
templates:
  telegram_notification: |
    📧 Neue E-Mail erhalten
    
    Von: {sender}
    Betreff: {subject}
    
    Inhalt:
    {content_preview}
    
    Generierte Antwort:
    {generated_response}
    
    Antworten Sie mit "JA" um die E-Mail zu senden oder "NEIN" um abzubrechen.
```

### Zusätzliche E-Mail-Kategorien
Erweitern Sie `email_parser.py`:
```python
def _categorize_email(self, subject: str, content: str) -> str:
    # Fügen Sie eigene Kategorien hinzu
    categories = {
        'support': ['support', 'hilfe', 'help'],
        'sales': ['verkauf', 'sale', 'preis'],
        'custom_category': ['your_keywords']
    }
```

### Webhook-Integration
Fügen Sie Webhook-Support hinzu für externe Systeme.

## 📞 Support

Bei Problemen:
1. Prüfen Sie die Logs in `email_agent.log`
2. Testen Sie die Verbindungen einzeln
3. Prüfen Sie die Konfiguration
4. Erstellen Sie ein Issue mit Logs und Konfiguration

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## 🤝 Beitragen

Beiträge sind willkommen! Bitte:
1. Fork erstellen
2. Feature-Branch erstellen
3. Änderungen committen
4. Pull Request erstellen

---

**Viel Erfolg mit Ihrem autonomen E-Mail-Agent! 🚀**
