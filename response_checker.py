import telegram
import asyncio
import logging
import yaml
import time
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import json

class ResponseChecker:
    """Überwacht Telegram-Antworten und verarbeitet Genehmigungen"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.updater = None
        self.pending_approvals = {}  # {message_id: approval_data}
        self._setup_bot()
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_bot(self):
        """Konfiguriert den Telegram Bot für Updates"""
        try:
            bot_token = self.config['telegram']['bot_token']
            if bot_token == "YOUR_BOT_TOKEN_HERE":
                self.logger.warning("Telegram Bot Token nicht konfiguriert")
                return
            
            self.bot = telegram.Bot(token=bot_token)
            self.updater = telegram.ext.Updater(token=bot_token, use_context=True)
            self.logger.info("Telegram Bot für Response-Checking konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei Telegram Bot-Konfiguration: {e}")
    
    def add_pending_approval(self, message_id: int, approval_data: Dict):
        """Fügt eine ausstehende Genehmigung hinzu"""
        self.pending_approvals[message_id] = {
            'data': approval_data,
            'timestamp': datetime.now(),
            'timeout': self.config['telegram']['timeout']
        }
        self.logger.info(f"Ausstehende Genehmigung hinzugefügt: Message ID {message_id}")
    
    def remove_pending_approval(self, message_id: int):
        """Entfernt eine ausstehende Genehmigung"""
        if message_id in self.pending_approvals:
            del self.pending_approvals[message_id]
            self.logger.info(f"Ausstehende Genehmigung entfernt: Message ID {message_id}")
    
    def get_pending_approval(self, message_id: int) -> Optional[Dict]:
        """Holt eine ausstehende Genehmigung"""
        return self.pending_approvals.get(message_id)
    
    def check_timeout_approvals(self) -> list:
        """Prüft auf abgelaufene Genehmigungen"""
        current_time = datetime.now()
        expired_approvals = []
        
        for message_id, approval_info in list(self.pending_approvals.items()):
            if current_time - approval_info['timestamp'] > timedelta(seconds=approval_info['timeout']):
                expired_approvals.append({
                    'message_id': message_id,
                    'data': approval_info['data']
                })
                self.remove_pending_approval(message_id)
        
        if expired_approvals:
            self.logger.warning(f"{len(expired_approvals)} abgelaufene Genehmigungen gefunden")
        
        return expired_approvals
    
    def process_telegram_response(self, message_text: str, user_id: str) -> Optional[Dict]:
        """Verarbeitet eine Telegram-Antwort"""
        if not self.is_authorized_user(user_id):
            self.logger.warning(f"Unautorisierte Antwort von User ID: {user_id}")
            return None
        
        message_text = message_text.strip().upper()
        
        # Suche nach der entsprechenden ausstehenden Genehmigung
        for message_id, approval_info in self.pending_approvals.items():
            # Einfache Zuordnung: Prüfe, ob die Antwort zu einer ausstehenden Genehmigung gehört
            # In einer echten Implementierung würde man hier eine bessere Zuordnung verwenden
            
            if message_text in ['JA', 'YES', 'OK', 'SENDEN', 'SEND']:
                self.remove_pending_approval(message_id)
                self.logger.info(f"Genehmigung erhalten für Message ID {message_id}")
                return {
                    'message_id': message_id,
                    'approved': True,
                    'data': approval_info['data'],
                    'response': message_text
                }
            
            elif message_text in ['NEIN', 'NO', 'VERWERFEN', 'DISCARD', 'ABORT']:
                self.remove_pending_approval(message_id)
                self.logger.info(f"Ablehnung erhalten für Message ID {message_id}")
                return {
                    'message_id': message_id,
                    'approved': False,
                    'data': approval_info['data'],
                    'response': message_text
                }
            
            elif message_text in ['BEARBEITEN', 'EDIT', 'ÄNDERN', 'CHANGE']:
                self.logger.info(f"Bearbeitungsanfrage erhalten für Message ID {message_id}")
                return {
                    'message_id': message_id,
                    'approved': False,
                    'needs_edit': True,
                    'data': approval_info['data'],
                    'response': message_text
                }
        
        self.logger.warning(f"Keine passende ausstehende Genehmigung für Antwort: {message_text}")
        return None
    
    def is_authorized_user(self, user_id: str) -> bool:
        """Prüft, ob ein Benutzer berechtigt ist"""
        authorized_id = self.config['telegram']['user_id']
        return str(user_id) == str(authorized_id)
    
    async def start_polling(self, callback: Callable):
        """Startet das Polling für Telegram-Updates"""
        if not self.updater:
            self.logger.error("Telegram Updater nicht konfiguriert")
            return
        
        def message_handler(update, context):
            """Handler für eingehende Nachrichten"""
            try:
                message = update.message
                if not message or not message.text:
                    return
                
                user_id = str(message.from_user.id)
                message_text = message.text
                
                # Verarbeite die Antwort
                result = self.process_telegram_response(message_text, user_id)
                
                if result:
                    # Rufe den Callback auf
                    asyncio.create_task(callback(result))
                else:
                    # Sende Hilfemeldung
                    asyncio.create_task(self.send_help_message(user_id))
                    
            except Exception as e:
                self.logger.error(f"Fehler beim Verarbeiten der Telegram-Nachricht: {e}")
        
        # Registriere den Handler
        self.updater.dispatcher.add_handler(
            telegram.ext.MessageHandler(
                telegram.ext.Filters.text & ~telegram.ext.Filters.command,
                message_handler
            )
        )
        
        # Starte das Polling
        self.updater.start_polling()
        self.logger.info("Telegram Polling gestartet")
    
    async def stop_polling(self):
        """Stoppt das Polling"""
        if self.updater:
            self.updater.stop()
            self.logger.info("Telegram Polling gestoppt")
    
    async def send_help_message(self, user_id: str):
        """Sendet eine Hilfemeldung"""
        if not self.bot:
            return
        
        help_message = """🤖 <b>E-Mail-Agent Hilfe</b>

<b>Verfügbare Befehle:</b>
• <code>JA</code> - E-Mail genehmigen und senden
• <code>NEIN</code> - E-Mail verwerfen
• <code>BEARBEITEN</code> - Antwort anpassen

<b>Status:</b>
• Aktive Genehmigungen: {pending_count}
• System läuft normal

Antworten Sie einfach mit einem der Befehle auf eine Genehmigungsanfrage.""".format(
            pending_count=len(self.pending_approvals)
        )
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=help_message,
                parse_mode='HTML'
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Hilfemeldung: {e}")
    
    def get_pending_count(self) -> int:
        """Gibt die Anzahl ausstehender Genehmigungen zurück"""
        return len(self.pending_approvals)
    
    def get_pending_approvals_info(self) -> list:
        """Gibt Informationen über alle ausstehenden Genehmigungen zurück"""
        info = []
        current_time = datetime.now()
        
        for message_id, approval_info in self.pending_approvals.items():
            time_remaining = approval_info['timeout'] - (current_time - approval_info['timestamp']).total_seconds()
            info.append({
                'message_id': message_id,
                'subject': approval_info['data'].get('subject', 'Unbekannt'),
                'sender': approval_info['data'].get('sender_name', 'Unbekannt'),
                'time_remaining': max(0, int(time_remaining)),
                'timestamp': approval_info['timestamp']
            })
        
        return info


# Wrapper-Funktionen für synchrone Verwendung
def process_telegram_response_sync(message_text: str, user_id: str) -> Optional[Dict]:
    """Synchrone Version von process_telegram_response"""
    checker = ResponseChecker()
    return checker.process_telegram_response(message_text, user_id)

def check_timeout_approvals_sync() -> list:
    """Synchrone Version von check_timeout_approvals"""
    checker = ResponseChecker()
    return checker.check_timeout_approvals()


if __name__ == "__main__":
    # Test des Response-Checkers
    logging.basicConfig(level=logging.INFO)
    
    checker = ResponseChecker()
    
    # Test-Daten
    test_approval_data = {
        'email_id': '123',
        'subject': 'Test E-Mail',
        'sender_name': 'Max Mustermann',
        'response': {
            'body': 'Test-Antwort',
            'confidence': 0.8
        }
    }
    
    # Füge eine Test-Genehmigung hinzu
    checker.add_pending_approval(12345, test_approval_data)
    
    # Teste verschiedene Antworten
    test_responses = ['JA', 'NEIN', 'BEARBEITEN', 'UNBEKANNT']
    
    for response in test_responses:
        result = checker.process_telegram_response(response, "YOUR_TELEGRAM_USER_ID")
        if result:
            print(f"Antwort '{response}': {result}")
        else:
            print(f"Antwort '{response}': Keine passende Genehmigung gefunden")
    
    # Prüfe Timeouts
    expired = checker.check_timeout_approvals()
    print(f"Abgelaufene Genehmigungen: {len(expired)}")
    
    # Zeige ausstehende Genehmigungen
    pending_info = checker.get_pending_approvals_info()
    print(f"Ausstehende Genehmigungen: {len(pending_info)}")