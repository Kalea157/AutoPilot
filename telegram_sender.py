import telegram
import asyncio
import logging
import yaml
from typing import Dict, Optional, List
from datetime import datetime, timedelta

class TelegramSender:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialisiert den Telegram-Sender mit Bot-Integration."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self._setup_bot()
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus der YAML-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_bot(self):
        """Konfiguriert den Telegram-Bot."""
        try:
            bot_token = self.config['telegram']['bot_token']
            self.bot = telegram.Bot(token=bot_token)
            self.logger.info("Telegram-Bot erfolgreich konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei Telegram-Bot-Konfiguration: {e}")
            raise
    
    async def send_email_notification(self, parsed_email: Dict, generated_response: Dict) -> bool:
        """Sendet eine Benachrichtigung über eine neue E-Mail an Telegram."""
        try:
            user_id = self.config['telegram']['user_id']
            template = self.config['templates']['telegram_notification']
            
            # Erstelle die Nachricht
            message = self._format_notification_message(parsed_email, generated_response, template)
            
            # Sende die Nachricht
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            self.logger.info(f"E-Mail-Benachrichtigung erfolgreich an Telegram gesendet")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Telegram-Benachrichtigung: {e}")
            return False
    
    def _format_notification_message(self, parsed_email: Dict, generated_response: Dict, template: str) -> str:
        """Formatiert die Benachrichtigungsnachricht."""
        try:
            # Bereite die Daten für das Template vor
            sender = parsed_email['sender']['name']
            subject = parsed_email['subject']
            content_preview = parsed_email['content_preview']
            generated_response_text = generated_response['content']
            
            # Kürze die generierte Antwort für die Vorschau
            if len(generated_response_text) > 500:
                generated_response_text = generated_response_text[:500] + "..."
            
            # Formatiere die Nachricht
            message = template.format(
                sender=sender,
                subject=subject,
                content_preview=content_preview,
                generated_response=generated_response_text
            )
            
            return message
            
        except Exception as e:
            self.logger.error(f"Fehler beim Formatieren der Nachricht: {e}")
            return self._create_fallback_message(parsed_email, generated_response)
    
    def _create_fallback_message(self, parsed_email: Dict, generated_response: Dict) -> str:
        """Erstellt eine Fallback-Nachricht bei Formatierungsfehlern."""
        return f"""📧 Neue E-Mail erhalten

Von: {parsed_email['sender']['name']}
Betreff: {parsed_email['subject']}

Generierte Antwort:
{generated_response['content'][:300]}...

Antworten Sie mit "JA" um die E-Mail zu senden oder "NEIN" um abzubrechen."""
    
    async def send_status_message(self, message: str) -> bool:
        """Sendet eine Status-Nachricht an Telegram."""
        try:
            user_id = self.config['telegram']['user_id']
            
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🤖 E-Mail-Agent Status:\n{message}",
                parse_mode='HTML'
            )
            
            self.logger.info("Status-Nachricht erfolgreich gesendet")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Status-Nachricht: {e}")
            return False
    
    async def send_error_message(self, error: str) -> bool:
        """Sendet eine Fehlermeldung an Telegram."""
        try:
            user_id = self.config['telegram']['user_id']
            
            await self.bot.send_message(
                chat_id=user_id,
                text=f"❌ E-Mail-Agent Fehler:\n{error}",
                parse_mode='HTML'
            )
            
            self.logger.info("Fehlermeldung erfolgreich gesendet")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Fehlermeldung: {e}")
            return False
    
    async def send_confirmation_request(self, email_id: str, response_preview: str) -> bool:
        """Sendet eine Bestätigungsanfrage für eine E-Mail-Antwort."""
        try:
            user_id = self.config['telegram']['user_id']
            
            message = f"""📧 E-Mail-Antwort zur Bestätigung

E-Mail-ID: {email_id}

Antwort-Vorschau:
{response_preview[:300]}...

Antworten Sie mit "JA" um die E-Mail zu senden oder "NEIN" um abzubrechen."""
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            self.logger.info("Bestätigungsanfrage erfolgreich gesendet")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Bestätigungsanfrage: {e}")
            return False
    
    async def send_confirmation_status(self, email_id: str, status: str, details: str = "") -> bool:
        """Sendet eine Bestätigung über den Status einer E-Mail-Antwort."""
        try:
            user_id = self.config['telegram']['user_id']
            
            if status == "sent":
                message = f"✅ E-Mail erfolgreich gesendet\nE-Mail-ID: {email_id}"
            elif status == "cancelled":
                message = f"❌ E-Mail-Antwort abgebrochen\nE-Mail-ID: {email_id}"
            elif status == "timeout":
                message = f"⏰ E-Mail-Antwort abgelaufen (Timeout)\nE-Mail-ID: {email_id}"
            else:
                message = f"ℹ️ E-Mail-Status: {status}\nE-Mail-ID: {email_id}"
            
            if details:
                message += f"\nDetails: {details}"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            self.logger.info(f"Status-Bestätigung erfolgreich gesendet: {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Status-Bestätigung: {e}")
            return False
    
    def get_user_id(self) -> str:
        """Gibt die konfigurierte Telegram-User-ID zurück."""
        return self.config['telegram']['user_id']
    
    def get_timeout_minutes(self) -> int:
        """Gibt das konfigurierte Timeout in Minuten zurück."""
        return self.config['telegram']['timeout_minutes']
    
    async def test_connection(self) -> bool:
        """Testet die Telegram-Verbindung."""
        try:
            user_id = self.config['telegram']['user_id']
            
            await self.bot.send_message(
                chat_id=user_id,
                text="🤖 E-Mail-Agent Test-Nachricht\nVerbindung erfolgreich!"
            )
            
            self.logger.info("Telegram-Verbindung erfolgreich getestet")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Testen der Telegram-Verbindung: {e}")
            return False

# Hilfsfunktionen für synchrone Aufrufe
def send_email_notification_sync(parsed_email: Dict, generated_response: Dict, config_path: str = "config.yaml") -> bool:
    """Synchrone Version von send_email_notification."""
    sender = TelegramSender(config_path)
    return asyncio.run(sender.send_email_notification(parsed_email, generated_response))

def send_status_message_sync(message: str, config_path: str = "config.yaml") -> bool:
    """Synchrone Version von send_status_message."""
    sender = TelegramSender(config_path)
    return asyncio.run(sender.send_status_message(message))

def send_error_message_sync(error: str, config_path: str = "config.yaml") -> bool:
    """Synchrone Version von send_error_message."""
    sender = TelegramSender(config_path)
    return asyncio.run(sender.send_error_message(error))

if __name__ == "__main__":
    # Test des Telegram-Senders
    logging.basicConfig(level=logging.INFO)
    
    async def test_telegram():
        sender = TelegramSender()
        
        # Test-Verbindung
        success = await sender.test_connection()
        print(f"Verbindungstest: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
        
        # Test-Status-Nachricht
        success = await sender.send_status_message("Test-Nachricht vom E-Mail-Agent")
        print(f"Status-Nachricht: {'Erfolgreich' if success else 'Fehlgeschlagen'}")
    
    asyncio.run(test_telegram())