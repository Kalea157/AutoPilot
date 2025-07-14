#!/usr/bin/env python3
"""
E-Mail-Agent Hauptsystem
Autonomer KI-E-Mail-Agent mit Telegram-Integration
"""

import asyncio
import logging
import schedule
import time
import signal
import sys
from datetime import datetime
from typing import Dict, Optional

# Import der eigenen Module
from email_fetcher import EmailFetcher
from email_parser import EmailParser
from email_responder import EmailResponder
from telegram_sender import TelegramSender
from response_checker import ResponseChecker, start_response_monitoring, stop_response_monitoring
from message_dispatcher import MessageDispatcher

class EmailAgent:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialisiert den E-Mail-Agent."""
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # Initialisiere Module
        self.email_fetcher = EmailFetcher(config_path)
        self.email_parser = EmailParser()
        self.email_responder = EmailResponder(config_path)
        self.telegram_sender = TelegramSender(config_path)
        self.message_dispatcher = MessageDispatcher(config_path)
        self.response_checker = ResponseChecker(config_path)
        
        # Status-Variablen
        self.running = False
        self.current_email_id = None
        self.pending_responses = {}
        
        self.logger.info("E-Mail-Agent erfolgreich initialisiert")
    
    def _load_config(self) -> dict:
        """Lädt die Konfiguration."""
        import yaml
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Konfiguriert das Logging."""
        log_config = self.config['agent']
        
        # Erstelle Logger
        logger = logging.getLogger('EmailAgent')
        logger.setLevel(getattr(logging, log_config['log_level']))
        
        # Erstelle Handler für Datei
        file_handler = logging.FileHandler(log_config['log_file'])
        file_handler.setLevel(logging.INFO)
        
        # Erstelle Handler für Konsole
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Erstelle Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Füge Handler hinzu
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def start(self):
        """Startet den E-Mail-Agent."""
        try:
            self.logger.info("Starte E-Mail-Agent...")
            
            # Teste Verbindungen
            await self._test_connections()
            
            # Starte Response-Checker
            start_response_monitoring(self.config_path)
            
            # Setze Status
            self.running = True
            
            # Sende Start-Benachrichtigung
            await self.telegram_sender.send_status_message("E-Mail-Agent gestartet und bereit")
            
            # Starte Hauptschleife
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des E-Mail-Agents: {e}")
            await self.telegram_sender.send_error_message(f"Startfehler: {e}")
            raise
    
    async def stop(self):
        """Stoppt den E-Mail-Agent."""
        try:
            self.logger.info("Stoppe E-Mail-Agent...")
            
            # Setze Status
            self.running = False
            
            # Stoppe Response-Checker
            stop_response_monitoring()
            
            # Trenne Verbindungen
            self.email_fetcher.disconnect()
            self.message_dispatcher.disconnect()
            
            # Sende Stop-Benachrichtigung
            await self.telegram_sender.send_status_message("E-Mail-Agent gestoppt")
            
            self.logger.info("E-Mail-Agent erfolgreich gestoppt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen des E-Mail-Agents: {e}")
    
    async def _test_connections(self):
        """Testet alle Verbindungen."""
        self.logger.info("Teste Verbindungen...")
        
        # Teste IMAP
        if not self.email_fetcher.connect():
            raise Exception("IMAP-Verbindung fehlgeschlagen")
        
        # Teste SMTP
        if not self.message_dispatcher.connect():
            raise Exception("SMTP-Verbindung fehlgeschlagen")
        
        # Teste Telegram
        if not await self.telegram_sender.test_connection():
            raise Exception("Telegram-Verbindung fehlgeschlagen")
        
        self.logger.info("Alle Verbindungen erfolgreich getestet")
    
    async def _main_loop(self):
        """Hauptschleife des E-Mail-Agents."""
        check_interval = self.config['agent']['check_interval_minutes']
        max_emails = self.config['agent']['max_emails_per_cycle']
        
        self.logger.info(f"Hauptschleife gestartet - Prüfe alle {check_interval} Minuten")
        
        while self.running:
            try:
                # Prüfe auf neue E-Mails
                await self._process_emails(max_emails)
                
                # Warte bis zur nächsten Prüfung
                await asyncio.sleep(check_interval * 60)
                
            except Exception as e:
                self.logger.error(f"Fehler in der Hauptschleife: {e}")
                await self.telegram_sender.send_error_message(f"Hauptschleife Fehler: {e}")
                await asyncio.sleep(60)  # Kurze Pause bei Fehlern
    
    async def _process_emails(self, max_emails: int):
        """Verarbeitet neue E-Mails."""
        try:
            # Hole ungelesene E-Mails
            emails = self.email_fetcher.fetch_unread_emails(max_emails)
            
            if not emails:
                self.logger.debug("Keine neuen E-Mails gefunden")
                return
            
            self.logger.info(f"{len(emails)} neue E-Mail(s) gefunden")
            
            # Verarbeite jede E-Mail
            for email_data in emails:
                if not self.running:
                    break
                
                await self._process_single_email(email_data)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten von E-Mails: {e}")
            await self.telegram_sender.send_error_message(f"E-Mail-Verarbeitung Fehler: {e}")
    
    async def _process_single_email(self, email_data: Dict):
        """Verarbeitet eine einzelne E-Mail."""
        email_id = email_data['id']
        
        try:
            self.logger.info(f"Verarbeite E-Mail {email_id}")
            
            # Parse E-Mail
            parsed_email = self.email_parser.parse_email(email_data)
            
            # Prüfe, ob Antwort benötigt wird
            if not parsed_email['requires_response']:
                self.logger.info(f"E-Mail {email_id} benötigt keine Antwort")
                self.email_fetcher.mark_as_read(email_id)
                return
            
            # Generiere Antwort
            generated_response = self.email_responder.generate_response(parsed_email)
            
            # Validiere Antwort
            if not self.email_responder.validate_response(generated_response):
                self.logger.warning(f"Generierte Antwort für {email_id} ist ungültig")
                await self.telegram_sender.send_error_message(f"Ungültige Antwort für E-Mail {email_id}")
                return
            
            # Sende Benachrichtigung an Telegram
            await self.telegram_sender.send_email_notification(parsed_email, generated_response)
            
            # Füge zur Überwachung hinzu
            self._add_to_pending_responses(email_id, generated_response)
            
            # Markiere als gelesen
            self.email_fetcher.mark_as_read(email_id)
            
            self.logger.info(f"E-Mail {email_id} erfolgreich verarbeitet")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten von E-Mail {email_id}: {e}")
            await self.telegram_sender.send_error_message(f"Fehler bei E-Mail {email_id}: {e}")
    
    def _add_to_pending_responses(self, email_id: str, response_data: Dict):
        """Fügt eine Antwort zur Überwachung hinzu."""
        try:
            # Callback für Response-Checker
            def response_callback(email_id: str, status: str) -> bool:
                return asyncio.run(self._handle_response_callback(email_id, status))
            
            # Füge zur Überwachung hinzu
            success = self.response_checker.add_pending_response(email_id, response_callback)
            
            if success:
                self.pending_responses[email_id] = response_data
                self.logger.info(f"E-Mail {email_id} zur Überwachung hinzugefügt")
            else:
                self.logger.error(f"Fehler beim Hinzufügen von E-Mail {email_id} zur Überwachung")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur Überwachung: {e}")
    
    async def _handle_response_callback(self, email_id: str, status: str) -> bool:
        """Behandelt Callbacks vom Response-Checker."""
        try:
            if email_id not in self.pending_responses:
                self.logger.warning(f"E-Mail {email_id} nicht in pending_responses gefunden")
                return False
            
            response_data = self.pending_responses[email_id]
            
            if status == 'approved':
                # Sende E-Mail
                success = self.message_dispatcher.send_email(response_data)
                
                if success:
                    await self.telegram_sender.send_confirmation_status(email_id, "sent")
                    self.logger.info(f"E-Mail {email_id} erfolgreich gesendet")
                else:
                    await self.telegram_sender.send_confirmation_status(email_id, "error", "Senden fehlgeschlagen")
                    self.logger.error(f"Fehler beim Senden von E-Mail {email_id}")
                
                # Entferne aus pending_responses
                del self.pending_responses[email_id]
                return success
                
            elif status == 'cancelled':
                # E-Mail wurde abgebrochen
                await self.telegram_sender.send_confirmation_status(email_id, "cancelled")
                self.logger.info(f"E-Mail {email_id} wurde abgebrochen")
                
                # Entferne aus pending_responses
                del self.pending_responses[email_id]
                return True
                
            elif status == 'timeout':
                # E-Mail ist abgelaufen
                await self.telegram_sender.send_confirmation_status(email_id, "timeout")
                self.logger.info(f"E-Mail {email_id} ist abgelaufen (Timeout)")
                
                # Entferne aus pending_responses
                del self.pending_responses[email_id]
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Fehler im Response-Callback für {email_id}: {e}")
            return False
    
    async def get_status(self) -> Dict:
        """Gibt den aktuellen Status des E-Mail-Agents zurück."""
        return {
            'running': self.running,
            'pending_responses': len(self.pending_responses),
            'current_email_id': self.current_email_id,
            'smtp_status': self.message_dispatcher.get_smtp_status(),
            'response_checker_count': self.response_checker.get_response_count(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def send_status_update(self):
        """Sendet einen Status-Update an Telegram."""
        try:
            status = await self.get_status()
            
            message = f"""🤖 E-Mail-Agent Status

Status: {'🟢 Läuft' if status['running'] else '🔴 Gestoppt'}
Ausstehende Antworten: {status['pending_responses']}
SMTP-Verbindung: {'✅ OK' if status['smtp_status']['connection_ok'] else '❌ Fehler'}
Response-Checker: {status['response_checker_count']} aktiv

Zeitstempel: {status['timestamp']}"""
            
            await self.telegram_sender.send_status_message(message)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Status-Updates: {e}")

# Globale Agent-Instanz
_agent = None

def get_agent(config_path: str = "config.yaml") -> EmailAgent:
    """Gibt eine globale Agent-Instanz zurück."""
    global _agent
    if _agent is None:
        _agent = EmailAgent(config_path)
    return _agent

async def main():
    """Hauptfunktion."""
    # Signal-Handler für sauberes Beenden
    def signal_handler(signum, frame):
        print("\nBeende E-Mail-Agent...")
        asyncio.create_task(stop_agent())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Starte Agent
        agent = get_agent()
        await agent.start()
        
    except KeyboardInterrupt:
        print("\nBeende E-Mail-Agent...")
        await stop_agent()
    except Exception as e:
        print(f"Fehler: {e}")
        await stop_agent()
        sys.exit(1)

async def stop_agent():
    """Stoppt den Agent."""
    global _agent
    if _agent:
        await _agent.stop()
        _agent = None

if __name__ == "__main__":
    # Starte Hauptschleife
    asyncio.run(main())