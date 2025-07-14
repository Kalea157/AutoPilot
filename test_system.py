#!/usr/bin/env python3
"""
Test-System für das E-Mail-Agent-System
Testet alle Module einzeln und das Gesamtsystem
"""

import logging
import yaml
import asyncio
from datetime import datetime

# Import der Module
from email_fetcher import EmailFetcher
from email_parser import EmailParser
from email_responder import EmailResponder
from telegram_sender import TelegramSender
from response_checker import ResponseChecker
from message_dispatcher import MessageDispatcher

class SystemTester:
    """Testet alle Module des E-Mail-Agent-Systems"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Test-E-Mail-Daten
        self.test_email_data = {
            'id': 'test_123',
            'subject': 'Test-Anfrage zu Ihrem Produkt',
            'sender': 'Max Mustermann <max.mustermann@example.com>',
            'date': 'Mon, 15 Jan 2024 10:30:00 +0100',
            'content': """Hallo,

ich interessiere mich sehr für Ihr Produkt und hätte gerne mehr Informationen dazu.

Können Sie mir bitte:
1. Den aktuellen Preis nennen
2. Die Lieferzeit angeben
3. Ein Datenblatt zusenden

Vielen Dank für Ihre Hilfe!

Mit freundlichen Grüßen
Max Mustermann""",
            'message_id': '<test@example.com>'
        }
    
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_logging(self) -> logging.Logger:
        """Konfiguriert das Logging für Tests"""
        logger = logging.getLogger('SystemTester')
        logger.setLevel(logging.INFO)
        
        # Console Handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def test_email_parser(self) -> bool:
        """Testet das E-Mail-Parser-Modul"""
        self.logger.info("=== Teste E-Mail-Parser ===")
        
        try:
            parser = EmailParser()
            parsed_email = parser.parse_email(self.test_email_data)
            
            # Prüfe Ergebnisse
            assert parsed_email['subject'] == 'Test-Anfrage zu Ihrem Produkt'
            assert parsed_email['sender']['name'] == 'Max Mustermann'
            assert parsed_email['sender']['email'] == 'max.mustermann@example.com'
            assert parsed_email['category'] == 'inquiry'
            assert parsed_email['language'] == 'german'
            assert parsed_email['requires_response'] == True
            
            self.logger.info("✅ E-Mail-Parser: Alle Tests bestanden")
            self.logger.info(f"   Kategorie: {parsed_email['category']}")
            self.logger.info(f"   Sprache: {parsed_email['language']}")
            self.logger.info(f"   Priorität: {parsed_email['priority']}")
            self.logger.info(f"   Stimmung: {parsed_email['sentiment']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ E-Mail-Parser Test fehlgeschlagen: {e}")
            return False
    
    def test_email_responder(self) -> bool:
        """Testet das E-Mail-Responder-Modul"""
        self.logger.info("=== Teste E-Mail-Responder ===")
        
        try:
            # Parse E-Mail zuerst
            parser = EmailParser()
            parsed_email = parser.parse_email(self.test_email_data)
            key_info = parser.extract_key_information(parsed_email)
            
            # Teste Responder
            responder = EmailResponder()
            response = responder.generate_response(key_info)
            
            # Prüfe Ergebnisse
            assert 'body' in response
            assert 'subject' in response
            assert 'confidence' in response
            assert len(response['body']) > 0
            
            self.logger.info("✅ E-Mail-Responder: Alle Tests bestanden")
            self.logger.info(f"   Betreff: {response['subject']}")
            self.logger.info(f"   Vertrauen: {response['confidence']:.1%}")
            self.logger.info(f"   Sprache: {response['language']}")
            self.logger.info(f"   Antwort-Länge: {len(response['body'])} Zeichen")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ E-Mail-Responder Test fehlgeschlagen: {e}")
            return False
    
    def test_message_dispatcher(self) -> bool:
        """Testet das Message-Dispatcher-Modul"""
        self.logger.info("=== Teste Message-Dispatcher ===")
        
        try:
            dispatcher = MessageDispatcher()
            
            # Teste E-Mail-Validierung
            valid_emails = ['test@example.com', 'user@domain.org']
            invalid_emails = ['invalid-email', 'test@', '@example.com']
            
            for email in valid_emails:
                assert dispatcher.validate_email_address(email) == True
            
            for email in invalid_emails:
                assert dispatcher.validate_email_address(email) == False
            
            # Teste SMTP-Status
            status = dispatcher.get_smtp_status()
            assert 'connected' in status
            assert 'server' in status
            
            self.logger.info("✅ Message-Dispatcher: Alle Tests bestanden")
            self.logger.info(f"   SMTP-Server: {status['server']}")
            self.logger.info(f"   SMTP-Port: {status['port']}")
            self.logger.info(f"   TLS aktiviert: {status['use_tls']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Message-Dispatcher Test fehlgeschlagen: {e}")
            return False
    
    def test_response_checker(self) -> bool:
        """Testet das Response-Checker-Modul"""
        self.logger.info("=== Teste Response-Checker ===")
        
        try:
            checker = ResponseChecker()
            
            # Teste autorisierte Benutzer
            authorized_id = self.config['telegram']['user_id']
            assert checker.is_authorized_user(authorized_id) == True
            assert checker.is_authorized_user("wrong_id") == False
            
            # Teste Antwort-Verarbeitung
            test_approval_data = {
                'email_id': 'test_123',
                'subject': 'Test E-Mail',
                'sender_name': 'Max Mustermann',
                'response': {'body': 'Test-Antwort', 'confidence': 0.8}
            }
            
            # Füge Test-Genehmigung hinzu
            checker.add_pending_approval(12345, test_approval_data)
            assert checker.get_pending_count() == 1
            
            # Teste verschiedene Antworten
            result_ja = checker.process_telegram_response("JA", authorized_id)
            assert result_ja is not None
            assert result_ja['approved'] == True
            
            # Füge neue Test-Genehmigung hinzu
            checker.add_pending_approval(12346, test_approval_data)
            
            result_nein = checker.process_telegram_response("NEIN", authorized_id)
            assert result_nein is not None
            assert result_nein['approved'] == False
            
            # Teste Timeout-Check
            expired = checker.check_timeout_approvals()
            assert isinstance(expired, list)
            
            self.logger.info("✅ Response-Checker: Alle Tests bestanden")
            self.logger.info(f"   Ausstehende Genehmigungen: {checker.get_pending_count()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Response-Checker Test fehlgeschlagen: {e}")
            return False
    
    async def test_telegram_sender(self) -> bool:
        """Testet das Telegram-Sender-Modul"""
        self.logger.info("=== Teste Telegram-Sender ===")
        
        try:
            sender = TelegramSender()
            
            # Teste Bot-Konfiguration
            if sender.bot is None:
                self.logger.warning("⚠️ Telegram Bot nicht konfiguriert - überspringe Test")
                return True
            
            # Teste Nachrichten-Erstellung
            test_response = {
                'body': 'Sehr geehrter Herr Mustermann, vielen Dank für Ihre Anfrage.',
                'confidence': 0.85
            }
            
            message = sender._create_approval_message(
                self.test_email_data, test_response
            )
            
            assert len(message) > 0
            assert 'Test-Anfrage' in message
            assert 'Max Mustermann' in message
            
            self.logger.info("✅ Telegram-Sender: Alle Tests bestanden")
            self.logger.info(f"   Nachrichten-Länge: {len(message)} Zeichen")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Telegram-Sender Test fehlgeschlagen: {e}")
            return False
    
    def test_email_fetcher(self) -> bool:
        """Testet das E-Mail-Fetcher-Modul"""
        self.logger.info("=== Teste E-Mail-Fetcher ===")
        
        try:
            fetcher = EmailFetcher()
            
            # Teste Konfiguration
            assert fetcher.config is not None
            assert 'email' in fetcher.config
            assert 'imap' in fetcher.config['email']
            
            # Teste Verbindung (nur wenn Konfiguration vorhanden)
            if fetcher.config['email']['imap']['username'] != "your-email@gmail.com":
                if fetcher.connect():
                    self.logger.info("✅ IMAP-Verbindung erfolgreich")
                    fetcher.disconnect()
                else:
                    self.logger.warning("⚠️ IMAP-Verbindung fehlgeschlagen - Konfiguration prüfen")
            else:
                self.logger.info("ℹ️ E-Mail-Konfiguration nicht eingerichtet - überspringe Verbindungstest")
            
            self.logger.info("✅ E-Mail-Fetcher: Konfiguration-Tests bestanden")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ E-Mail-Fetcher Test fehlgeschlagen: {e}")
            return False
    
    async def test_integration(self) -> bool:
        """Testet die Integration aller Module"""
        self.logger.info("=== Teste System-Integration ===")
        
        try:
            # Parse E-Mail
            parser = EmailParser()
            parsed_email = parser.parse_email(self.test_email_data)
            key_info = parser.extract_key_information(parsed_email)
            
            # Generiere Antwort
            responder = EmailResponder()
            response = responder.generate_response(key_info)
            
            # Teste Message-Dispatcher
            dispatcher = MessageDispatcher()
            
            # Erstelle Test-E-Mail-Nachricht
            msg = dispatcher._create_email_message(self.test_email_data, response)
            
            assert msg['To'] == 'max.mustermann@example.com'
            assert msg['Subject'] == response['subject']
            
            self.logger.info("✅ System-Integration: Alle Tests bestanden")
            self.logger.info(f"   E-Mail-Adresse: {msg['To']}")
            self.logger.info(f"   Betreff: {msg['Subject']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ System-Integration Test fehlgeschlagen: {e}")
            return False
    
    async def run_all_tests(self) -> dict:
        """Führt alle Tests aus"""
        self.logger.info("🚀 Starte System-Tests")
        self.logger.info("=" * 50)
        
        results = {
            'email_parser': False,
            'email_responder': False,
            'message_dispatcher': False,
            'response_checker': False,
            'telegram_sender': False,
            'email_fetcher': False,
            'integration': False
        }
        
        # Führe Tests aus
        results['email_parser'] = self.test_email_parser()
        results['email_responder'] = self.test_email_responder()
        results['message_dispatcher'] = self.test_message_dispatcher()
        results['response_checker'] = self.test_response_checker()
        results['telegram_sender'] = await self.test_telegram_sender()
        results['email_fetcher'] = self.test_email_fetcher()
        results['integration'] = await self.test_integration()
        
        # Zeige Zusammenfassung
        self.logger.info("=" * 50)
        self.logger.info("📊 Test-Zusammenfassung")
        self.logger.info("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ BESTANDEN" if result else "❌ FEHLGESCHLAGEN"
            self.logger.info(f"{test_name:20} {status}")
        
        self.logger.info("=" * 50)
        self.logger.info(f"Gesamt: {passed}/{total} Tests bestanden ({passed/total*100:.1f}%)")
        
        if passed == total:
            self.logger.info("🎉 Alle Tests erfolgreich! Das System ist bereit.")
        else:
            self.logger.warning("⚠️ Einige Tests fehlgeschlagen. Bitte Konfiguration prüfen.")
        
        return results


async def main():
    """Hauptfunktion für Tests"""
    tester = SystemTester()
    results = await tester.run_all_tests()
    
    # Exit-Code basierend auf Testergebnissen
    if all(results.values()):
        return 0
    else:
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)