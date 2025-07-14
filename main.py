#!/usr/bin/env python3
"""
E-Mail Agent System - Hauptmodul
Autonomer KI-E-Mail-Agent mit Telegram-Integration
"""

import asyncio
import logging
import yaml
import time
import signal
import sys
from datetime import datetime
from typing import Dict, Optional
import threading

# Import der eigenen Module
from email_fetcher import EmailFetcher
from email_parser import EmailParser
from email_responder import EmailResponder
from telegram_sender import TelegramSender
from response_checker import ResponseChecker
from message_dispatcher import MessageDispatcher

class EmailAgent:
    """Hauptklasse des E-Mail-Agent-Systems"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.running = False
        
        # Initialisiere Module
        self.email_fetcher = EmailFetcher(config_path)
        self.email_parser = EmailParser()
        self.email_responder = EmailResponder(config_path)
        self.telegram_sender = TelegramSender(config_path)
        self.response_checker = ResponseChecker(config_path)
        self.message_dispatcher = MessageDispatcher(config_path)
        
        # Status-Tracking
        self.current_email = None
        self.pending_approvals = {}
        
        self.logger.info("E-Mail-Agent-System initialisiert")
    
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Konfiguriert das Logging-System"""
        log_config = self.config['system']
        
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
    
    async def process_single_email(self, email_data: Dict) -> bool:
        """Verarbeitet eine einzelne E-Mail"""
        try:
            self.logger.info(f"Verarbeite E-Mail: {email_data.get('subject', 'Unbekannt')}")
            
            # 1. Parse E-Mail
            parsed_email = self.email_parser.parse_email(email_data)
            
            # Prüfe, ob Antwort benötigt wird
            if not parsed_email.get('requires_response', True):
                self.logger.info("E-Mail benötigt keine Antwort - überspringe")
                return True
            
            # 2. Generiere Antwort
            key_info = self.email_parser.extract_key_information(parsed_email)
            generated_response = self.email_responder.generate_response(key_info)
            
            # 3. Sende an Telegram für Genehmigung
            message_id = await self.telegram_sender.send_email_for_approval(
                key_info, generated_response
            )
            
            if message_id:
                # Speichere ausstehende Genehmigung
                self.pending_approvals[message_id] = {
                    'email_data': email_data,
                    'parsed_email': parsed_email,
                    'generated_response': generated_response,
                    'timestamp': datetime.now()
                }
                
                # Füge zur Response-Checker hinzu
                self.response_checker.add_pending_approval(message_id, {
                    'email_id': email_data.get('id'),
                    'subject': parsed_email.get('subject'),
                    'sender_name': key_info.get('sender_name'),
                    'response': generated_response
                })
                
                self.logger.info(f"Genehmigungsanfrage gesendet: Message ID {message_id}")
                return True
            else:
                self.logger.error("Fehler beim Senden der Genehmigungsanfrage")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler bei der E-Mail-Verarbeitung: {e}")
            await self.telegram_sender.send_error_notification(
                str(e), email_data.get('subject', 'Unbekannt')
            )
            return False
    
    async def handle_telegram_response(self, response_data: Dict):
        """Behandelt Telegram-Antworten"""
        try:
            message_id = response_data['message_id']
            approved = response_data.get('approved', False)
            needs_edit = response_data.get('needs_edit', False)
            
            # Hole die entsprechenden Daten
            if message_id not in self.pending_approvals:
                self.logger.warning(f"Keine ausstehende Genehmigung für Message ID {message_id}")
                return
            
            approval_data = self.pending_approvals[message_id]
            email_data = approval_data['email_data']
            parsed_email = approval_data['parsed_email']
            generated_response = approval_data['generated_response']
            
            if approved:
                # Sende E-Mail
                success = self.message_dispatcher.send_email(
                    email_data, generated_response
                )
                
                if success:
                    # Markiere E-Mail als gelesen
                    self.email_fetcher.mark_as_read(email_data['id'])
                    
                    # Sende Bestätigung
                    await self.telegram_sender.send_approval_status(
                        True, parsed_email.get('subject', 'Unbekannt')
                    )
                    
                    self.logger.info(f"E-Mail erfolgreich gesendet: {parsed_email.get('subject')}")
                else:
                    # Sende Fehlermeldung
                    await self.telegram_sender.send_approval_status(
                        False, parsed_email.get('subject', 'Unbekannt'), "SMTP-Fehler"
                    )
                    self.logger.error("Fehler beim Senden der E-Mail")
            
            elif needs_edit:
                # Hier könnte man eine Bearbeitungsfunktion implementieren
                await self.telegram_sender.send_approval_status(
                    False, parsed_email.get('subject', 'Unbekannt'), "Bearbeitung nicht implementiert"
                )
                self.logger.info("Bearbeitungsanfrage erhalten (nicht implementiert)")
            
            else:
                # E-Mail verworfen
                await self.telegram_sender.send_approval_status(
                    False, parsed_email.get('subject', 'Unbekannt'), "Verworfen"
                )
                self.logger.info(f"E-Mail verworfen: {parsed_email.get('subject')}")
            
            # Entferne aus ausstehenden Genehmigungen
            del self.pending_approvals[message_id]
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Behandlung der Telegram-Antwort: {e}")
    
    async def check_timeouts(self):
        """Prüft auf abgelaufene Genehmigungen"""
        expired_approvals = self.response_checker.check_timeout_approvals()
        
        for expired in expired_approvals:
            message_id = expired['message_id']
            data = expired['data']
            
            if message_id in self.pending_approvals:
                email_subject = self.pending_approvals[message_id]['parsed_email'].get('subject', 'Unbekannt')
                
                # Sende Timeout-Benachrichtigung
                await self.telegram_sender.send_approval_status(
                    False, email_subject, "Timeout - keine Antwort erhalten"
                )
                
                # Entferne aus ausstehenden Genehmigungen
                del self.pending_approvals[message_id]
                
                self.logger.warning(f"Timeout für E-Mail: {email_subject}")
    
    async def process_email_batch(self):
        """Verarbeitet eine Batch von E-Mails"""
        try:
            # Hole ungelesene E-Mails (maximal 1 gleichzeitig)
            unread_emails = self.email_fetcher.fetch_unread_emails(limit=1)
            
            if not unread_emails:
                self.logger.debug("Keine neuen E-Mails gefunden")
                return
            
            # Verarbeite nur die erste E-Mail
            email_data = unread_emails[0]
            await self.process_single_email(email_data)
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Batch-Verarbeitung: {e}")
    
    async def main_loop(self):
        """Hauptschleife des E-Mail-Agents"""
        self.logger.info("E-Mail-Agent gestartet")
        
        # Starte Telegram-Polling
        await self.response_checker.start_polling(self.handle_telegram_response)
        
        # Sende Start-Benachrichtigung
        await self.telegram_sender.send_system_status("E-Mail-Agent gestartet und bereit")
        
        check_interval = self.config['system']['check_interval']
        
        while self.running:
            try:
                # Verarbeite E-Mails
                await self.process_email_batch()
                
                # Prüfe Timeouts
                await self.check_timeouts()
                
                # Warte bis zum nächsten Check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Fehler in der Hauptschleife: {e}")
                await asyncio.sleep(60)  # Warte 1 Minute bei Fehlern
    
    def start(self):
        """Startet den E-Mail-Agent"""
        self.running = True
        
        # Signal-Handler für sauberes Beenden
        def signal_handler(signum, frame):
            self.logger.info("Beende-Signal erhalten")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Starte asynchrone Hauptschleife
            asyncio.run(self.main_loop())
        except KeyboardInterrupt:
            self.logger.info("E-Mail-Agent durch Benutzer gestoppt")
        finally:
            self.stop()
    
    async def stop_async(self):
        """Stoppt den E-Mail-Agent (asynchron)"""
        self.running = False
        
        # Stoppe Telegram-Polling
        await self.response_checker.stop_polling()
        
        # Trenne Verbindungen
        self.email_fetcher.disconnect()
        self.message_dispatcher.disconnect()
        
        # Sende Stop-Benachrichtigung
        await self.telegram_sender.send_system_status("E-Mail-Agent gestoppt")
        
        self.logger.info("E-Mail-Agent gestoppt")
    
    def stop(self):
        """Stoppt den E-Mail-Agent (synchron)"""
        asyncio.run(self.stop_async())
    
    def get_status(self) -> Dict:
        """Gibt den aktuellen Status zurück"""
        return {
            'running': self.running,
            'pending_approvals': len(self.pending_approvals),
            'current_email': self.current_email,
            'last_check': datetime.now().isoformat()
        }


def main():
    """Hauptfunktion"""
    try:
        # Erstelle und starte E-Mail-Agent
        agent = EmailAgent()
        agent.start()
    except Exception as e:
        print(f"Fehler beim Starten des E-Mail-Agents: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()