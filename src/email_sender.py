"""
E-Mail Sender für den Super-KI-Agenten
"""
import smtplib
import logging
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from email_fetcher import EmailData
from response_generator import GeneratedResponse

class EmailSender:
    """SMTP E-Mail Sender mit erweiterten Funktionen"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_email_config()
        self.logger = logging.getLogger(__name__)
        self.email_address = None
        self.password = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Lädt E-Mail-Credentials aus Umgebungsvariablen"""
        import os
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')
        
        if not self.email_address or not self.password:
            raise ValueError("E-Mail-Credentials nicht in Umgebungsvariablen gefunden")
    
    def send_email(self, original_email: EmailData, response: GeneratedResponse, 
                  attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Sendet E-Mail-Antwort"""
        try:
            self.logger.info(f"Sende Antwort an: {original_email.sender}")
            
            # Erstelle E-Mail-Nachricht
            msg = self._create_email_message(original_email, response, attachments)
            
            # Sende E-Mail
            success = self._send_via_smtp(msg)
            
            if success:
                self.logger.info(f"E-Mail erfolgreich gesendet an {original_email.sender}")
                return True
            else:
                self.logger.error(f"Fehler beim Senden der E-Mail an {original_email.sender}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim E-Mail-Versand: {e}")
            return False
    
    def _create_email_message(self, original_email: EmailData, response: GeneratedResponse, 
                            attachments: Optional[List[Dict[str, Any]]] = None) -> MIMEMultipart:
        """Erstellt E-Mail-Nachricht"""
        # Erstelle Multipart-Nachricht
        msg = MIMEMultipart('alternative')
        
        # Setze Header
        msg['From'] = self.email_address
        msg['To'] = original_email.sender
        msg['Subject'] = response.subject
        msg['In-Reply-To'] = f"<{original_email.uid}@email.com>"
        msg['References'] = f"<{original_email.uid}@email.com>"
        
        # Erstelle Text-Version
        text_content = self._create_text_content(original_email, response)
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Erstelle HTML-Version
        html_content = self._create_html_content(original_email, response)
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Füge Attachments hinzu
        if attachments:
            self._add_attachments(msg, attachments)
        
        return msg
    
    def _create_text_content(self, original_email: EmailData, response: GeneratedResponse) -> str:
        """Erstellt Text-Inhalt der Antwort"""
        content = f"""
{response.body}

---
Diese E-Mail wurde automatisch generiert vom Super-KI-Agenten.
Original E-Mail vom {original_email.date.strftime('%d.%m.%Y %H:%M')}
"""
        return content
    
    def _create_html_content(self, original_email: EmailData, response: GeneratedResponse) -> str:
        """Erstellt HTML-Inhalt der Antwort"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; 
                  font-size: 12px; color: #666; }}
        .original-email {{ background-color: #f9f9f9; padding: 15px; margin: 20px 0; 
                          border-left: 4px solid #007cba; }}
    </style>
</head>
<body>
    <div>
        {response.body.replace(chr(10), '<br>')}
    </div>
    
    <div class="footer">
        <p>Diese E-Mail wurde automatisch generiert vom Super-KI-Agenten.</p>
        <p>Original E-Mail vom {original_email.date.strftime('%d.%m.%Y %H:%M')}</p>
    </div>
</body>
</html>
"""
        return html_content
    
    def _add_attachments(self, msg: MIMEMultipart, attachments: List[Dict[str, Any]]):
        """Fügt Attachments zur E-Mail hinzu"""
        for attachment in attachments:
            try:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['data'])
                encoders.encode_base64(part)
                
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                
                msg.attach(part)
                self.logger.info(f"Attachment hinzugefügt: {attachment['filename']}")
                
            except Exception as e:
                self.logger.error(f"Fehler beim Hinzufügen von Attachment {attachment.get('filename', 'unknown')}: {e}")
    
    def _send_via_smtp(self, msg: MIMEMultipart) -> bool:
        """Sendet E-Mail über SMTP"""
        try:
            # Verbinde zum SMTP-Server
            if self.config.smtp['use_tls']:
                server = smtplib.SMTP(self.config.smtp['server'], self.config.smtp['port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.config.smtp['server'], self.config.smtp['port'])
            
            # Login
            server.login(self.email_address, self.password)
            
            # Sende E-Mail
            text = msg.as_string()
            server.sendmail(self.email_address, msg['To'], text)
            
            # Schließe Verbindung
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP-Fehler: {e}")
            return False
    
    def send_notification_email(self, recipient: str, subject: str, body: str) -> bool:
        """Sendet Benachrichtigungs-E-Mail"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = recipient
            msg['Subject'] = subject
            
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            return self._send_via_smtp(msg)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Benachrichtigung: {e}")
            return False
    
    def send_error_notification(self, error_message: str, context: str = "") -> bool:
        """Sendet Fehler-Benachrichtigung"""
        try:
            subject = f"Super-KI-Agent Fehler: {context}"
            body = f"""
Ein Fehler ist im Super-KI-Agenten aufgetreten:

Kontext: {context}
Fehler: {error_message}
Zeitstempel: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}

Bitte überprüfen Sie die Logs für weitere Details.
"""
            
            # Sende an Admin-E-Mail (falls konfiguriert)
            import os
            admin_email = os.getenv('ADMIN_EMAIL')
            if admin_email:
                return self.send_notification_email(admin_email, subject, body)
            else:
                self.logger.warning("Keine Admin-E-Mail konfiguriert für Fehler-Benachrichtigungen")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Fehler-Benachrichtigung: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Testet SMTP-Verbindung"""
        try:
            if self.config.smtp['use_tls']:
                server = smtplib.SMTP(self.config.smtp['server'], self.config.smtp['port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.config.smtp['server'], self.config.smtp['port'])
            
            server.login(self.email_address, self.password)
            server.quit()
            
            self.logger.info("SMTP-Verbindung erfolgreich getestet")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP-Verbindungstest fehlgeschlagen: {e}")
            return False
    
    def get_smtp_info(self) -> Dict[str, Any]:
        """Gibt SMTP-Informationen zurück"""
        return {
            'server': self.config.smtp['server'],
            'port': self.config.smtp['port'],
            'use_tls': self.config.smtp['use_tls'],
            'email_address': self.email_address
        }