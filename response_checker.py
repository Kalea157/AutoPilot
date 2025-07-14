import telegram
import asyncio
import logging
import yaml
from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta
import threading
import time

class ResponseChecker:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialisiert den Response-Checker für Telegram-Antworten."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.user_id = self.config['telegram']['user_id']
        self.timeout_minutes = self.config['telegram']['timeout_minutes']
        self.pending_responses = {}  # email_id -> {timestamp, callback}
        self._setup_bot()
        self._running = False
        self._check_thread = None
        
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
            self.logger.info("Response-Checker Bot erfolgreich konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei Bot-Konfiguration: {e}")
            raise
    
    def start_monitoring(self):
        """Startet die Überwachung von Telegram-Antworten."""
        if self._running:
            self.logger.warning("Response-Checker läuft bereits")
            return
        
        self._running = True
        self._check_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._check_thread.start()
        self.logger.info("Response-Checker Überwachung gestartet")
    
    def stop_monitoring(self):
        """Stoppt die Überwachung von Telegram-Antworten."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
        self.logger.info("Response-Checker Überwachung gestoppt")
    
    def _monitor_loop(self):
        """Hauptschleife für die Überwachung von Telegram-Antworten."""
        last_update_id = 0
        
        while self._running:
            try:
                # Hole Updates vom Bot
                updates = asyncio.run(self._get_updates(last_update_id))
                
                for update in updates:
                    if update.update_id > last_update_id:
                        last_update_id = update.update_id
                        
                        # Verarbeite Nachrichten
                        if update.message and update.message.from_user:
                            await asyncio.create_task(self._process_message(update.message))
                
                # Prüfe Timeouts
                self._check_timeouts()
                
                # Kurze Pause zwischen den Abfragen
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Fehler in der Überwachungsschleife: {e}")
                time.sleep(5)  # Längere Pause bei Fehlern
    
    async def _get_updates(self, offset: int) -> List:
        """Holt Updates vom Telegram-Bot."""
        try:
            updates = await self.bot.get_updates(offset=offset, timeout=1)
            return updates
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von Updates: {e}")
            return []
    
    async def _process_message(self, message):
        """Verarbeitet eine eingehende Telegram-Nachricht."""
        try:
            # Prüfe, ob die Nachricht von der autorisierten User-ID kommt
            if str(message.from_user.id) != self.user_id:
                self.logger.warning(f"Nachricht von nicht autorisierter User-ID: {message.from_user.id}")
                return
            
            # Verarbeite den Text der Nachricht
            if message.text:
                await self._process_text_response(message.text)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Nachricht: {e}")
    
    async def _process_text_response(self, text: str):
        """Verarbeitet eine Textantwort."""
        try:
            text_lower = text.strip().lower()
            
            # Prüfe auf JA/NEIN Antworten
            if text_lower in ['ja', 'yes', 'j', 'y', 'ok', 'okay']:
                await self._handle_positive_response()
            elif text_lower in ['nein', 'no', 'n', 'abbrechen', 'cancel']:
                await self._handle_negative_response()
            else:
                await self._handle_unknown_response(text)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Textantwort: {e}")
    
    async def _handle_positive_response(self):
        """Behandelt eine positive Antwort (JA)."""
        try:
            if not self.pending_responses:
                await self._send_message("Keine ausstehende E-Mail-Antwort zur Bestätigung.")
                return
            
            # Nimm die älteste ausstehende Antwort
            email_id = min(self.pending_responses.keys(), key=lambda k: self.pending_responses[k]['timestamp'])
            response_data = self.pending_responses[email_id]
            
            # Führe den Callback aus
            if response_data['callback']:
                try:
                    result = response_data['callback'](email_id, 'approved')
                    if result:
                        await self._send_message(f"✅ E-Mail-Antwort für {email_id} wurde genehmigt und gesendet.")
                    else:
                        await self._send_message(f"❌ Fehler beim Senden der E-Mail-Antwort für {email_id}.")
                except Exception as e:
                    self.logger.error(f"Fehler im Callback für {email_id}: {e}")
                    await self._send_message(f"❌ Fehler beim Verarbeiten der E-Mail-Antwort für {email_id}.")
            
            # Entferne aus der Warteschlange
            del self.pending_responses[email_id]
            
        except Exception as e:
            self.logger.error(f"Fehler bei positiver Antwort: {e}")
    
    async def _handle_negative_response(self):
        """Behandelt eine negative Antwort (NEIN)."""
        try:
            if not self.pending_responses:
                await self._send_message("Keine ausstehende E-Mail-Antwort zum Abbrechen.")
                return
            
            # Nimm die älteste ausstehende Antwort
            email_id = min(self.pending_responses.keys(), key=lambda k: self.pending_responses[k]['timestamp'])
            response_data = self.pending_responses[email_id]
            
            # Führe den Callback aus
            if response_data['callback']:
                try:
                    result = response_data['callback'](email_id, 'cancelled')
                    if result:
                        await self._send_message(f"❌ E-Mail-Antwort für {email_id} wurde abgebrochen.")
                    else:
                        await self._send_message(f"⚠️ Fehler beim Abbrechen der E-Mail-Antwort für {email_id}.")
                except Exception as e:
                    self.logger.error(f"Fehler im Callback für {email_id}: {e}")
                    await self._send_message(f"❌ Fehler beim Verarbeiten der E-Mail-Antwort für {email_id}.")
            
            # Entferne aus der Warteschlange
            del self.pending_responses[email_id]
            
        except Exception as e:
            self.logger.error(f"Fehler bei negativer Antwort: {e}")
    
    async def _handle_unknown_response(self, text: str):
        """Behandelt eine unbekannte Antwort."""
        await self._send_message(f"""Unbekannte Antwort: "{text}"

Bitte antworten Sie mit:
- "JA" oder "YES" um die E-Mail-Antwort zu genehmigen
- "NEIN" oder "NO" um die E-Mail-Antwort abzubrechen""")
    
    async def _send_message(self, text: str):
        """Sendet eine Nachricht an den autorisierten Benutzer."""
        try:
            await self.bot.send_message(
                chat_id=self.user_id,
                text=text,
                parse_mode='HTML'
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Nachricht: {e}")
    
    def _check_timeouts(self):
        """Prüft auf abgelaufene Antworten."""
        current_time = datetime.now()
        expired_responses = []
        
        for email_id, response_data in self.pending_responses.items():
            timeout_time = response_data['timestamp'] + timedelta(minutes=self.timeout_minutes)
            
            if current_time > timeout_time:
                expired_responses.append(email_id)
        
        # Behandle abgelaufene Antworten
        for email_id in expired_responses:
            response_data = self.pending_responses[email_id]
            
            # Führe den Callback aus
            if response_data['callback']:
                try:
                    response_data['callback'](email_id, 'timeout')
                except Exception as e:
                    self.logger.error(f"Fehler im Timeout-Callback für {email_id}: {e}")
            
            # Entferne aus der Warteschlange
            del self.pending_responses[email_id]
            
            self.logger.info(f"E-Mail-Antwort {email_id} ist abgelaufen (Timeout)")
    
    def add_pending_response(self, email_id: str, callback: Callable) -> bool:
        """Fügt eine ausstehende Antwort zur Überwachung hinzu."""
        try:
            if email_id in self.pending_responses:
                self.logger.warning(f"E-Mail-ID {email_id} ist bereits in der Warteschlange")
                return False
            
            self.pending_responses[email_id] = {
                'timestamp': datetime.now(),
                'callback': callback
            }
            
            self.logger.info(f"E-Mail-Antwort {email_id} zur Überwachung hinzugefügt")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen der ausstehenden Antwort: {e}")
            return False
    
    def remove_pending_response(self, email_id: str) -> bool:
        """Entfernt eine ausstehende Antwort aus der Überwachung."""
        try:
            if email_id in self.pending_responses:
                del self.pending_responses[email_id]
                self.logger.info(f"E-Mail-Antwort {email_id} aus der Überwachung entfernt")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler beim Entfernen der ausstehenden Antwort: {e}")
            return False
    
    def get_pending_responses(self) -> Dict:
        """Gibt alle ausstehenden Antworten zurück."""
        return self.pending_responses.copy()
    
    def is_response_pending(self, email_id: str) -> bool:
        """Prüft, ob eine Antwort für eine E-Mail-ID aussteht."""
        return email_id in self.pending_responses
    
    def get_response_count(self) -> int:
        """Gibt die Anzahl der ausstehenden Antworten zurück."""
        return len(self.pending_responses)
    
    async def send_status_update(self):
        """Sendet einen Status-Update über ausstehende Antworten."""
        try:
            count = self.get_response_count()
            
            if count == 0:
                message = "✅ Keine ausstehenden E-Mail-Antworten."
            else:
                message = f"⏳ {count} ausstehende E-Mail-Antworten zur Bestätigung."
                
                # Liste der E-Mail-IDs
                email_ids = list(self.pending_responses.keys())
                message += f"\nE-Mail-IDs: {', '.join(email_ids)}"
            
            await self._send_message(message)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Status-Updates: {e}")

# Globale Instanz für einfache Verwendung
_response_checker = None

def get_response_checker(config_path: str = "config.yaml") -> ResponseChecker:
    """Gibt eine globale Response-Checker-Instanz zurück."""
    global _response_checker
    if _response_checker is None:
        _response_checker = ResponseChecker(config_path)
    return _response_checker

def start_response_monitoring(config_path: str = "config.yaml"):
    """Startet die Response-Überwachung."""
    checker = get_response_checker(config_path)
    checker.start_monitoring()

def stop_response_monitoring():
    """Stoppt die Response-Überwachung."""
    global _response_checker
    if _response_checker:
        _response_checker.stop_monitoring()

if __name__ == "__main__":
    # Test des Response-Checkers
    logging.basicConfig(level=logging.INFO)
    
    async def test_response_checker():
        checker = ResponseChecker()
        
        # Test-Callback
        def test_callback(email_id: str, status: str):
            print(f"Callback aufgerufen: {email_id} - {status}")
            return True
        
        # Füge eine Test-Antwort hinzu
        success = checker.add_pending_response("test_email_1", test_callback)
        print(f"Test-Antwort hinzugefügt: {success}")
        
        # Starte Überwachung
        checker.start_monitoring()
        
        # Warte kurz
        await asyncio.sleep(5)
        
        # Stoppe Überwachung
        checker.stop_monitoring()
    
    asyncio.run(test_response_checker())