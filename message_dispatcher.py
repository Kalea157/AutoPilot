import smtplib
import logging
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, Optional
import ssl

class MessageDispatcher:
    """Sendet E-Mails über SMTP"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.smtp_server = None
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def connect(self) -> bool:
        """Verbindet sich mit dem SMTP-Server"""
        try:
            smtp_config = self.config['email']['smtp']
            
            if smtp_config['use_tls']:
                self.smtp_server = smtplib.SMTP(smtp_config['server'], smtp_config['port'])
                self.smtp_server.starttls(context=ssl.create_default_context())
            else:
                self.smtp_server = smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'])
            
            # Login
            self.smtp_server.login(smtp_config['username'], smtp_config['password'])
            
            self.logger.info("Erfolgreich mit SMTP-Server verbunden")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei SMTP-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Trennt die SMTP-Verbindung"""
        if self.smtp_server:
            try:
                self.smtp_server.quit()
                self.logger.info("SMTP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der SMTP-Verbindung: {e}")
    
    def send_email(self, email_data: Dict, response_data: Dict) -> bool:
        """Sendet eine E-Mail"""
        if not self.smtp_server:
            if not self.connect():
                return False
        
        try:
            # Erstelle E-Mail-Nachricht
            msg = self._create_email_message(email_data, response_data)
            
            # Sende E-Mail
            self.smtp_server.send_message(msg)
            
            self.logger.info(f"E-Mail erfolgreich gesendet an {email_data.get('sender_email', 'Unbekannt')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der E-Mail: {e}")
            return False
    
    def _create_email_message(self, email_data: Dict, response_data: Dict) -> MIMEMultipart:
        """Erstellt eine E-Mail-Nachricht"""
        smtp_config = self.config['email']['smtp']
        
        # Erstelle MIME-Nachricht
        msg = MIMEMultipart('alternative')
        
        # Setze Header
        msg['From'] = formataddr(("E-Mail Agent", smtp_config['username']))
        msg['To'] = email_data.get('sender_email', '')
        msg['Subject'] = response_data.get('subject', 'Antwort')
        
        # Füge Message-ID hinzu (für Threading)
        original_message_id = email_data.get('message_id', '')
        if original_message_id:
            msg['In-Reply-To'] = original_message_id
            msg['References'] = original_message_id
        
        # Erstelle Text-Version
        text_content = response_data.get('body', '')
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Erstelle HTML-Version (optional)
        html_content = self._convert_to_html(text_content)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        return msg
    
    def _convert_to_html(self, text_content: str) -> str:
        """Konvertiert Text zu HTML"""
        # Einfache HTML-Konvertierung
        html_content = text_content.replace('\n', '<br>')
        
        # Füge HTML-Struktur hinzu
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .email-content {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="email-content">
                {html_content}
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def send_test_email(self, recipient_email: str) -> bool:
        """Sendet eine Test-E-Mail"""
        test_email_data = {
            'sender_email': recipient_email,
            'message_id': '<test@email-agent.com>'
        }
        
        test_response_data = {
            'subject': 'Test E-Mail vom E-Mail-Agent',
            'body': """Sehr geehrte Damen und Herren,

dies ist eine Test-E-Mail vom E-Mail-Agent-System.

Das System funktioniert ordnungsgemäß und ist bereit für den produktiven Einsatz.

Mit freundlichen Grüßen
Ihr E-Mail-Agent"""
        }
        
        return self.send_email(test_email_data, test_response_data)
    
    def validate_email_address(self, email_address: str) -> bool:
        """Validiert eine E-Mail-Adresse"""
        import re
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email_address) is not None
    
    def get_smtp_status(self) -> Dict:
        """Gibt den SMTP-Status zurück"""
        return {
            'connected': self.smtp_server is not None,
            'server': self.config['email']['smtp']['server'],
            'port': self.config['email']['smtp']['port'],
            'use_tls': self.config['email']['smtp']['use_tls'],
            'username': self.config['email']['smtp']['username']
        }


if __name__ == "__main__":
    # Test des Message-Dispatchers
    logging.basicConfig(level=logging.INFO)
    
    dispatcher = MessageDispatcher()
    
    # Test SMTP-Verbindung
    if dispatcher.connect():
        print("SMTP-Verbindung erfolgreich")
        
        # Test-E-Mail senden
        test_email_data = {
            'sender_email': 'test@example.com',
            'message_id': '<test@email-agent.com>'
        }
        
        test_response_data = {
            'subject': 'Test E-Mail',
            'body': 'Dies ist eine Test-E-Mail vom E-Mail-Agent-System.'
        }
        
        success = dispatcher.send_email(test_email_data, test_response_data)
        if success:
            print("Test-E-Mail erfolgreich gesendet")
        else:
            print("Fehler beim Senden der Test-E-Mail")
        
        dispatcher.disconnect()
    else:
        print("Fehler bei SMTP-Verbindung")
    
    # Test E-Mail-Validierung
    test_emails = ['test@example.com', 'invalid-email', 'test@', '@example.com']
    for email in test_emails:
        is_valid = dispatcher.validate_email_address(email)
        print(f"E-Mail {email}: {'Gültig' if is_valid else 'Ungültig'}")
    
    # Zeige SMTP-Status
    status = dispatcher.get_smtp_status()
    print(f"SMTP-Status: {status}")