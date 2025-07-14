import smtplib
import logging
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, Optional, List
from datetime import datetime

class MessageDispatcher:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialisiert den Message-Dispatcher für E-Mail-Versand."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.smtp_connection = None
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus der YAML-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def connect(self) -> bool:
        """Stellt Verbindung zum SMTP-Server her."""
        try:
            smtp_config = self.config['email']['smtp']
            
            if smtp_config['use_tls']:
                self.smtp_connection = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
                self.smtp_connection.starttls()
            else:
                self.smtp_connection = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            
            # Login
            self.smtp_connection.login(smtp_config['username'], smtp_config['password'])
            
            self.logger.info("SMTP-Verbindung erfolgreich hergestellt")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei SMTP-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Trennt die SMTP-Verbindung."""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
                self.logger.info("SMTP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der SMTP-Verbindung: {e}")
    
    def send_email(self, response_data: Dict) -> bool:
        """Sendet eine E-Mail-Antwort."""
        try:
            # Stelle Verbindung her, falls nicht vorhanden
            if not self.smtp_connection:
                if not self.connect():
                    return False
            
            # Erstelle E-Mail-Nachricht
            message = self._create_email_message(response_data)
            
            # Sende E-Mail
            smtp_config = self.config['email']['smtp']
            self.smtp_connection.send_message(message)
            
            self.logger.info(f"E-Mail erfolgreich gesendet an {response_data['to_email']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der E-Mail: {e}")
            return False
    
    def _create_email_message(self, response_data: Dict) -> MIMEMultipart:
        """Erstellt eine E-Mail-Nachricht aus den Antwortdaten."""
        try:
            # Erstelle MIME-Nachricht
            message = MIMEMultipart()
            
            # Setze Header
            message['From'] = formataddr(("E-Mail-Agent", self.config['email']['smtp']['username']))
            message['To'] = formataddr((response_data['to_name'], response_data['to_email']))
            message['Subject'] = response_data['subject']
            message['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Füge Message-ID hinzu
            message_id = f"<{datetime.now().strftime('%Y%m%d%H%M%S')}.{response_data['original_email_id']}@email-agent>"
            message['Message-ID'] = message_id
            
            # Füge In-Reply-To und References für Threading hinzu
            message['In-Reply-To'] = f"<{response_data['original_email_id']}@email-agent>"
            message['References'] = f"<{response_data['original_email_id']}@email-agent>"
            
            # Füge Text-Inhalt hinzu
            text_part = MIMEText(response_data['content'], 'plain', 'utf-8')
            message.attach(text_part)
            
            # Füge Footer hinzu
            footer = self._create_footer(response_data)
            if footer:
                footer_part = MIMEText(footer, 'plain', 'utf-8')
                message.attach(footer_part)
            
            return message
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der E-Mail-Nachricht: {e}")
            raise
    
    def _create_footer(self, response_data: Dict) -> str:
        """Erstellt einen Footer für die E-Mail."""
        footer = f"""

---
Diese E-Mail wurde automatisch generiert und gesendet.
Generiert am: {response_data.get('generated_at', datetime.now().isoformat())}
Konfidenz-Score: {response_data.get('confidence_score', 'N/A')}
"""
        
        # Füge Disclaimer hinzu, falls es sich um eine Fallback-Antwort handelt
        if response_data.get('is_fallback', False):
            footer += "\nHinweis: Dies ist eine automatische Antwort. Ein Mitarbeiter wird sich bald bei Ihnen melden."
        
        return footer
    
    def send_bulk_emails(self, response_list: List[Dict]) -> Dict[str, bool]:
        """Sendet mehrere E-Mails und gibt Ergebnisse zurück."""
        results = {}
        
        for response_data in response_list:
            email_id = response_data.get('original_email_id', 'unknown')
            success = self.send_email(response_data)
            results[email_id] = success
            
            # Kurze Pause zwischen E-Mails
            import time
            time.sleep(1)
        
        return results
    
    def validate_email_address(self, email: str) -> bool:
        """Validiert eine E-Mail-Adresse."""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_response_data(self, response_data: Dict) -> bool:
        """Validiert die Antwortdaten vor dem Senden."""
        required_fields = ['to_email', 'to_name', 'subject', 'content']
        
        for field in required_fields:
            if field not in response_data or not response_data[field]:
                self.logger.warning(f"Fehlendes oder leeres Feld: {field}")
                return False
        
        # Validiere E-Mail-Adresse
        if not self.validate_email_address(response_data['to_email']):
            self.logger.warning(f"Ungültige E-Mail-Adresse: {response_data['to_email']}")
            return False
        
        # Prüfe Mindestlänge der Antwort
        if len(response_data['content']) < 10:
            self.logger.warning("E-Mail-Inhalt ist zu kurz")
            return False
        
        return True
    
    def create_draft_email(self, response_data: Dict) -> str:
        """Erstellt einen E-Mail-Entwurf ohne zu senden."""
        try:
            message = self._create_email_message(response_data)
            return message.as_string()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen des E-Mail-Entwurfs: {e}")
            return ""
    
    def send_test_email(self, to_email: str, to_name: str = "Test") -> bool:
        """Sendet eine Test-E-Mail."""
        test_response = {
            'to_email': to_email,
            'to_name': to_name,
            'subject': 'Test-E-Mail vom E-Mail-Agent',
            'content': f"""Sehr geehrte/r {to_name},

dies ist eine Test-E-Mail vom E-Mail-Agent-System.

Zeitstempel: {datetime.now().isoformat()}

Mit freundlichen Grüßen
E-Mail-Agent""",
            'original_email_id': 'test',
            'generated_at': datetime.now().isoformat(),
            'confidence_score': 1.0
        }
        
        return self.send_email(test_response)
    
    def get_smtp_status(self) -> Dict:
        """Gibt den aktuellen SMTP-Status zurück."""
        status = {
            'connected': self.smtp_connection is not None,
            'server': self.config['email']['smtp']['server'],
            'port': self.config['email']['smtp']['port'],
            'use_tls': self.config['email']['smtp']['use_tls'],
            'username': self.config['email']['smtp']['username']
        }
        
        if self.smtp_connection:
            try:
                # Teste Verbindung
                self.smtp_connection.noop()
                status['connection_ok'] = True
            except Exception as e:
                status['connection_ok'] = False
                status['error'] = str(e)
        else:
            status['connection_ok'] = False
        
        return status

# Hilfsfunktionen für einfache Verwendung
def send_email_sync(response_data: Dict, config_path: str = "config.yaml") -> bool:
    """Synchrone Version von send_email."""
    dispatcher = MessageDispatcher(config_path)
    try:
        return dispatcher.send_email(response_data)
    finally:
        dispatcher.disconnect()

def send_test_email_sync(to_email: str, to_name: str = "Test", config_path: str = "config.yaml") -> bool:
    """Synchrone Version von send_test_email."""
    dispatcher = MessageDispatcher(config_path)
    try:
        return dispatcher.send_test_email(to_email, to_name)
    finally:
        dispatcher.disconnect()

if __name__ == "__main__":
    # Test des Message-Dispatchers
    logging.basicConfig(level=logging.INFO)
    
    test_response = {
        'to_email': 'test@example.com',
        'to_name': 'Test Empfänger',
        'subject': 'Test-E-Mail',
        'content': 'Dies ist eine Test-E-Mail vom E-Mail-Agent.',
        'original_email_id': 'test_1',
        'generated_at': datetime.now().isoformat(),
        'confidence_score': 0.8
    }
    
    dispatcher = MessageDispatcher()
    
    # Teste SMTP-Status
    status = dispatcher.get_smtp_status()
    print(f"SMTP-Status: {status}")
    
    # Validiere Testdaten
    is_valid = dispatcher.validate_response_data(test_response)
    print(f"Daten valid: {is_valid}")
    
    # Erstelle E-Mail-Entwurf
    draft = dispatcher.create_draft_email(test_response)
    print(f"E-Mail-Entwurf erstellt: {len(draft)} Zeichen")
    
    # Teste E-Mail-Versand (nur wenn Konfiguration vorhanden)
    if status['connected']:
        success = dispatcher.send_test_email('test@example.com')
        print(f"Test-E-Mail gesendet: {success}")
    
    dispatcher.disconnect()