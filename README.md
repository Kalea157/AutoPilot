# E-Mail Agent System

Ein autonomer KI-E-Mail-Agent, der neue E-Mails liest, analysiert, passende Antworten generiert und diese per Telegram zur Genehmigung sendet. Erst nach Bestätigung wird die Antwort-E-Mail versendet.

## 🎯 Ziele

- **Autonome E-Mail-Verarbeitung** mit KI-gestützter Antwortgenerierung
- **Telegram-Integration** für menschliche Kontrolle über alle Ausgänge
- **Skalierbares System** für Kundenkontakt, Support-Antworten und mehr
- **Vollständige Kontrolle** durch Telegram-Zustimmung vor dem Versenden

## 🏗️ Systemarchitektur

Das System besteht aus 8 Hauptmodulen:

1. **`email_fetcher.py`** - Holt ungelesene E-Mails über IMAP
2. **`email_parser.py`** - Analysiert und strukturiert E-Mail-Inhalte
3. **`email_responder.py`** - Generiert Antworten mit GPT-4o
4. **`telegram_sender.py`** - Sendet Genehmigungsanfragen an Telegram
5. **`response_checker.py`** - Überwacht Telegram-Antworten
6. **`message_dispatcher.py`** - Versendet E-Mails über SMTP
7. **`config.yaml`** - Zentrale Konfiguration
8. **`main.py`** - Koordiniert alle Module

## 🚀 Installation

### 1. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2. Konfiguration einrichten

Bearbeiten Sie die `config.yaml` Datei:

```yaml
# E-Mail IMAP Einstellungen
email:
  imap:
    server: "imap.gmail.com"  # Ihr IMAP-Server
    port: 993
    username: "your-email@gmail.com"
    password: "your-app-password"  # App-Passwort für Gmail
    folder: "INBOX"
  
  smtp:
    server: "smtp.gmail.com"  # Ihr SMTP-Server
    port: 587
    username: "your-email@gmail.com"
    password: "your-app-password"
    use_tls: true

# Telegram Bot Einstellungen
telegram:
  bot_token: "YOUR_BOT_TOKEN_HERE"  # Von @BotFather
  user_id: "YOUR_TELEGRAM_USER_ID"  # Ihre Telegram-ID
  timeout: 1800  # 30 Minuten Timeout

# OpenAI API Einstellungen
openai:
  api_key: "YOUR_OPENAI_API_KEY"
  model: "gpt-4o"
  max_tokens: 1000
  temperature: 0.7
```

### 3. Telegram Bot erstellen

1. Chatten Sie mit [@BotFather](https://t.me/botfather) auf Telegram
2. Erstellen Sie einen neuen Bot: `/newbot`
3. Kopieren Sie den Bot-Token in die `config.yaml`
4. Starten Sie den Bot: `/start`

### 4. Telegram User ID finden

1. Chatten Sie mit [@userinfobot](https://t.me/userinfobot)
2. Kopieren Sie Ihre User ID in die `config.yaml`

### 5. Gmail App-Passwort erstellen (für Gmail)

1. Gehen Sie zu [Google Account Settings](https://myaccount.google.com/)
2. Sicherheit → 2-Schritt-Verifizierung aktivieren
3. App-Passwörter → Neues App-Passwort erstellen
4. Passwort in `config.yaml` eintragen

## 🎮 Verwendung

### System starten

```bash
python main.py
```

### Telegram-Befehle

Nach dem Start erhalten Sie Telegram-Nachrichten für jede neue E-Mail:

- **`JA`** - E-Mail genehmigen und senden
- **`NEIN`** - E-Mail verwerfen
- **`BEARBEITEN`** - Antwort anpassen (in Entwicklung)

## 🔧 Konfiguration

### E-Mail-Anbieter

Das System unterstützt alle IMAP/SMTP-Anbieter:

- **Gmail**: `imap.gmail.com` / `smtp.gmail.com`
- **Outlook**: `outlook.office365.com` / `smtp.office365.com`
- **Web.de**: `imap.web.de` / `smtp.web.de`
- **GMX**: `imap.gmx.net` / `mail.gmx.net`

### System-Einstellungen

```yaml
system:
  check_interval: 300  # 5 Minuten zwischen Checks
  max_processing_time: 1800  # 30 Minuten max Verarbeitungszeit
  log_level: "INFO"
  log_file: "email_agent.log"
```

## 📊 Funktionsweise

### 1. E-Mail-Abruf
- Alle 5 Minuten werden ungelesene E-Mails abgerufen
- Nur eine E-Mail wird gleichzeitig verarbeitet

### 2. E-Mail-Analyse
- Automatische Kategorisierung (Support, Verkauf, Anfrage, etc.)
- Spracherkennung (Deutsch/Englisch)
- Stimmungsanalyse
- Prioritätsbestimmung

### 3. Antwortgenerierung
- GPT-4o generiert kontextuelle Antworten
- Berücksichtigt Kategorie, Sprache und Stimmung
- Professionelle Anrede und Grußformel

### 4. Telegram-Genehmigung
- Vollständige E-Mail-Details werden gesendet
- Generierte Antwort wird zur Überprüfung angezeigt
- 30-Minuten-Timeout für Antworten

### 5. E-Mail-Versand
- Nur nach "JA"-Bestätigung wird gesendet
- Automatisches Threading mit Original-E-Mail
- HTML- und Text-Version

## 🛡️ Sicherheit

- **Nur autorisierte Telegram-User** können antworten
- **App-Passwörter** statt normaler Passwörter
- **TLS-Verschlüsselung** für alle Verbindungen
- **Timeout-Schutz** gegen hängende Genehmigungen
- **Umfassendes Logging** aller Aktivitäten

## 📝 Logging

Alle Aktivitäten werden in `email_agent.log` protokolliert:

```
2024-01-15 10:30:00 - EmailAgent - INFO - E-Mail-Agent gestartet
2024-01-15 10:30:05 - EmailFetcher - INFO - E-Mail gefunden: Test-Anfrage von max@example.com
2024-01-15 10:30:10 - EmailResponder - INFO - Antwort generiert für E-Mail: Test-Anfrage
2024-01-15 10:30:15 - TelegramSender - INFO - Genehmigungsanfrage gesendet: Message ID 12345
```

## 🔄 Erweiterungen

### Neue E-Mail-Kategorien

Fügen Sie in `email_parser.py` neue Kategorien hinzu:

```python
categories = {
    'support': ['support', 'hilfe', 'help', 'problem'],
    'sales': ['sales', 'verkauf', 'preis', 'price'],
    'new_category': ['keyword1', 'keyword2', 'keyword3']
}
```

### Anpassbare Antwort-Templates

Bearbeiten Sie die Templates in `config.yaml`:

```yaml
templates:
  telegram_message: |
    📧 Neue E-Mail erhalten:
    Von: {sender}
    Betreff: {subject}
    Inhalt: {content_preview}
    Generierte Antwort: {generated_response}
```

## 🐛 Fehlerbehebung

### Häufige Probleme

1. **IMAP-Verbindungsfehler**
   - Prüfen Sie Server/Port-Einstellungen
   - Stellen Sie sicher, dass App-Passwort korrekt ist

2. **Telegram-Bot funktioniert nicht**
   - Prüfen Sie Bot-Token und User-ID
   - Starten Sie den Bot mit `/start`

3. **OpenAI-Fehler**
   - Prüfen Sie API-Key und Guthaben
   - Stellen Sie sicher, dass GPT-4o verfügbar ist

### Debug-Modus

Setzen Sie in `config.yaml`:

```yaml
system:
  log_level: "DEBUG"
```

## 📈 Monitoring

### Status-Abfrage

```python
from main import EmailAgent

agent = EmailAgent()
status = agent.get_status()
print(f"Läuft: {status['running']}")
print(f"Ausstehende Genehmigungen: {status['pending_approvals']}")
```

### Telegram-Status

Der Bot sendet automatisch Status-Updates:
- System-Start/Stop
- Fehlermeldungen
- Genehmigungsstatus

## 🤝 Beitragen

1. Fork das Repository
2. Erstellen Sie einen Feature-Branch
3. Committen Sie Ihre Änderungen
4. Erstellen Sie einen Pull Request

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## 🆘 Support

Bei Fragen oder Problemen:

1. Prüfen Sie die Logs in `email_agent.log`
2. Stellen Sie sicher, dass alle Konfigurationen korrekt sind
3. Testen Sie einzelne Module mit den Test-Funktionen

---

**Hinweis**: Dieses System ist für produktive Nutzung konzipiert. Testen Sie es zunächst in einer sicheren Umgebung.
