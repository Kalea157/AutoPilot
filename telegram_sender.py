import telegram
import asyncio
import logging
import yaml
from typing import Dict, Optional
import json

class TelegramSender:
    """Sendet E-Mail-Antworten an Telegram für Genehmigung"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self._setup_bot()
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_bot(self):
        """Konfiguriert den Telegram Bot"""
        try:
            bot_token = self.config['telegram']['bot_token']
            if bot_token == "YOUR_BOT_TOKEN_HERE":
                self.logger.warning("Telegram Bot Token nicht konfiguriert")
                return
            
            self.bot = telegram.Bot(token=bot_token)
            self.logger.info("Telegram Bot konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei Telegram Bot-Konfiguration: {e}")
    
    async def send_email_for_approval(self, email_data: Dict, generated_response: Dict) -> Optional[int]:
        """Sendet E-Mail-Details und generierte Antwort an Telegram für Genehmigung"""
        if not self.bot:
            self.logger.error("Telegram Bot nicht konfiguriert")
            return None
        
        try:
            user_id = self.config['telegram']['user_id']
            if user_id == "YOUR_TELEGRAM_USER_ID":
                self.logger.error("Telegram User ID nicht konfiguriert")
                return None
            
            # Erstelle die Nachricht
            message = self._create_approval_message(email_data, generated_response)
            
            # Sende Nachricht
            sent_message = await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            self.logger.info(f"Genehmigungsanfrage an Telegram gesendet: Message ID {sent_message.message_id}")
            return sent_message.message_id
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Genehmigungsanfrage: {e}")
            return None
    
    def _create_approval_message(self, email_data: Dict, generated_response: Dict) -> str:
        """Erstellt die Telegram-Nachricht für Genehmigung"""
        template = self.config['templates']['telegram_message']
        
        # Kürze den Inhalt für Telegram
        content_preview = email_data.get('content', '')[:300]
        if len(email_data.get('content', '')) > 300:
            content_preview += "..."
        
        # Kürze die generierte Antwort
        response_preview = generated_response.get('body', '')[:500]
        if len(generated_response.get('body', '')) > 500:
            response_preview += "..."
        
        # Erstelle eindeutige ID für diese E-Mail
        email_id = email_data.get('id', 'unknown')
        
        message = template.format(
            sender=email_data.get('sender_name', 'Unbekannt'),
            subject=email_data.get('subject', 'Kein Betreff'),
            content_preview=content_preview,
            generated_response=response_preview
        )
        
        # Füge zusätzliche Informationen hinzu
        message += f"\n\n📊 <b>Details:</b>\n"
        message += f"• Kategorie: {email_data.get('category', 'Unbekannt')}\n"
        message += f"• Priorität: {email_data.get('priority', 'Normal')}\n"
        message += f"• Sprache: {email_data.get('language', 'Unbekannt')}\n"
        message += f"• Vertrauen: {generated_response.get('confidence', 0.0):.1%}\n"
        message += f"• E-Mail-ID: {email_id}\n\n"
        
        message += "💬 <b>Antwort mit:</b>\n"
        message += "• <code>JA</code> - E-Mail senden\n"
        message += "• <code>NEIN</code> - E-Mail verwerfen\n"
        message += "• <code>BEARBEITEN</code> - Antwort anpassen"
        
        return message
    
    async def send_approval_status(self, approved: bool, email_subject: str, reason: str = "") -> bool:
        """Sendet Bestätigung über Genehmigungsstatus"""
        if not self.bot:
            return False
        
        try:
            user_id = self.config['telegram']['user_id']
            
            if approved:
                message = f"✅ <b>E-Mail genehmigt und gesendet</b>\n\n"
                message += f"Betreff: {email_subject}\n"
                message += f"Status: Erfolgreich versendet"
            else:
                message = f"❌ <b>E-Mail verworfen</b>\n\n"
                message += f"Betreff: {email_subject}\n"
                if reason:
                    message += f"Grund: {reason}"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            self.logger.info(f"Genehmigungsstatus gesendet: {'Genehmigt' if approved else 'Verworfen'}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Genehmigungsstatus: {e}")
            return False
    
    async def send_error_notification(self, error_message: str, email_subject: str = "") -> bool:
        """Sendet Fehlermeldung an Telegram"""
        if not self.bot:
            return False
        
        try:
            user_id = self.config['telegram']['user_id']
            
            message = f"⚠️ <b>Fehler im E-Mail-Agent</b>\n\n"
            if email_subject:
                message += f"E-Mail: {email_subject}\n"
            message += f"Fehler: {error_message}"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            self.logger.info("Fehlermeldung an Telegram gesendet")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Fehlermeldung: {e}")
            return False
    
    async def send_system_status(self, status: str) -> bool:
        """Sendet Systemstatus an Telegram"""
        if not self.bot:
            return False
        
        try:
            user_id = self.config['telegram']['user_id']
            
            message = f"🔄 <b>Systemstatus</b>\n\n{status}"
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Systemstatus: {e}")
            return False
    
    def is_authorized_user(self, user_id: str) -> bool:
        """Prüft, ob ein Benutzer berechtigt ist"""
        authorized_id = self.config['telegram']['user_id']
        return str(user_id) == str(authorized_id)


# Wrapper-Funktionen für synchrone Verwendung
def send_email_for_approval_sync(email_data: Dict, generated_response: Dict) -> Optional[int]:
    """Synchrone Version von send_email_for_approval"""
    sender = TelegramSender()
    return asyncio.run(sender.send_email_for_approval(email_data, generated_response))

def send_approval_status_sync(approved: bool, email_subject: str, reason: str = "") -> bool:
    """Synchrone Version von send_approval_status"""
    sender = TelegramSender()
    return asyncio.run(sender.send_approval_status(approved, email_subject, reason))

def send_error_notification_sync(error_message: str, email_subject: str = "") -> bool:
    """Synchrone Version von send_error_notification"""
    sender = TelegramSender()
    return asyncio.run(sender.send_error_notification(error_message, email_subject))


if __name__ == "__main__":
    # Test des Telegram-Senders
    logging.basicConfig(level=logging.INFO)
    
    # Test-Daten
    test_email_data = {
        'id': '123',
        'sender_name': 'Max Mustermann',
        'sender_email': 'max@example.com',
        'subject': 'Test E-Mail',
        'content': 'Dies ist eine Test-E-Mail mit einem längeren Inhalt, um zu sehen, wie die Nachricht in Telegram formatiert wird.',
        'category': 'inquiry',
        'priority': 'normal',
        'language': 'german'
    }
    
    test_response = {
        'body': 'Sehr geehrter Herr Mustermann, vielen Dank für Ihre E-Mail. Ich werde Ihnen gerne weiterhelfen.',
        'confidence': 0.85
    }
    
    # Test der synchrone Funktion
    message_id = send_email_for_approval_sync(test_email_data, test_response)
    if message_id:
        print(f"Test-Nachricht gesendet mit ID: {message_id}")
    else:
        print("Fehler beim Senden der Test-Nachricht")