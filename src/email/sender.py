"""
Email Sender - SMTP-basierte E-Mail-Versendung
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger(__name__)


@dataclass
class EmailResponse:
    """Datenklasse für E-Mail-Antworten"""
    to: str
    subject: str
    content: str
    content_type: str = "text/plain"
    attachments: List[Dict[str, Any]] = None
    reply_to_message_id: Optional[str] = None
    in_reply_to: Optional[str] = None


class EmailSender:
    """SMTP-basierter E-Mail-Sender mit asynchroner Verarbeitung"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.smtp_config = config['smtp']
        self.credentials = {
            'username': config['username'],
            'password': config['password'],
            'from_email': config['from_email']
        }
        self.connection: Optional[smtplib.SMTP] = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._sent_count = 0
        self._failed_count = 0
        
    async def connect(self) -> bool:
        """Stellt SMTP-Verbindung her"""
        try:
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                self.executor,
                self._connect_sync
            )
            logger.info("SMTP connection established", 
                       server=self.smtp_config['server'])
            return True
        except Exception as e:
            logger.error("Failed to connect to SMTP server", error=str(e))
            return False
    
    def _connect_sync(self) -> smtplib.SMTP:
        """Synchrone SMTP-Verbindung"""
        if self.smtp_config.get('use_tls', True):
            context = ssl.create_default_context()
            connection = smtplib.SMTP(
                self.smtp_config['server'],
                self.smtp_config['port'],
                timeout=self.smtp_config.get('timeout', 30)
            )
            connection.starttls(context=context)
        else:
            connection = smtplib.SMTP(
                self.smtp_config['server'],
                self.smtp_config['port'],
                timeout=self.smtp_config.get('timeout', 30)
            )
        
        connection.login(
            self.credentials['username'],
            self.credentials['password']
        )
        return connection
    
    async def disconnect(self) -> None:
        """Trennt SMTP-Verbindung"""
        if self.connection:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    self.connection.quit
                )
                logger.info("SMTP connection closed")
            except Exception as e:
                logger.error("Error closing SMTP connection", error=str(e))
            finally:
                self.connection = None
    
    async def send_email(self, email_response: EmailResponse) -> bool:
        """Sendet eine E-Mail"""
        if not self.connection:
            if not await self.connect():
                return False
        
        try:
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._send_email_sync,
                email_response
            )
            
            if success:
                self._sent_count += 1
                logger.info("Email sent successfully", 
                           to=email_response.to, 
                           subject=email_response.subject)
            else:
                self._failed_count += 1
                logger.error("Failed to send email", 
                            to=email_response.to, 
                            subject=email_response.subject)
            
            return success
            
        except Exception as e:
            self._failed_count += 1
            logger.error("Exception while sending email", 
                        to=email_response.to, 
                        error=str(e))
            return False
    
    def _send_email_sync(self, email_response: EmailResponse) -> bool:
        """Synchrone E-Mail-Versendung"""
        try:
            # Erstelle MIME-Nachricht
            if email_response.attachments:
                msg = MIMEMultipart()
                msg['From'] = self.credentials['from_email']
                msg['To'] = email_response.to
                msg['Subject'] = email_response.subject
                
                # Füge Inhalt hinzu
                text_part = MIMEText(email_response.content, 
                                   email_response.content_type, 'utf-8')
                msg.attach(text_part)
                
                # Füge Anhänge hinzu
                for attachment in email_response.attachments:
                    if 'filename' in attachment and 'content' in attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment['content'])
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)
            else:
                msg = MIMEText(email_response.content, 
                             email_response.content_type, 'utf-8')
                msg['From'] = self.credentials['from_email']
                msg['To'] = email_response.to
                msg['Subject'] = email_response.subject
            
            # Füge Reply-To Header hinzu
            if email_response.reply_to_message_id:
                msg['In-Reply-To'] = email_response.reply_to_message_id
                msg['References'] = email_response.reply_to_message_id
            
            # Sende E-Mail
            self.connection.send_message(msg)
            return True
            
        except Exception as e:
            logger.error("SMTP send error", error=str(e))
            return False
    
    async def send_bulk_emails(self, email_responses: List[EmailResponse]) -> Dict[str, int]:
        """Sendet mehrere E-Mails in Batch"""
        results = {'sent': 0, 'failed': 0}
        
        if not self.connection:
            if not await self.connect():
                return results
        
        tasks = []
        for email_response in email_responses:
            task = asyncio.create_task(self.send_email(email_response))
            tasks.append(task)
        
        # Warte auf alle Tasks
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_tasks:
            if isinstance(result, Exception):
                results['failed'] += 1
            elif result:
                results['sent'] += 1
            else:
                results['failed'] += 1
        
        logger.info("Bulk email sending completed", results=results)
        return results
    
    def create_reply_email(self, original_email, response_content: str, 
                          content_type: str = "text/plain") -> EmailResponse:
        """Erstellt eine Antwort-E-Mail basierend auf der ursprünglichen E-Mail"""
        # Extrahiere E-Mail-Adresse aus dem Sender
        sender_email = self._extract_email_address(original_email.sender)
        
        # Erstelle Betreff
        subject = original_email.subject
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
        
        # Erstelle Message-ID für Reply-To
        message_id = f"<{original_email.uid}@{self.credentials['from_email'].split('@')[1]}>"
        
        return EmailResponse(
            to=sender_email,
            subject=subject,
            content=response_content,
            content_type=content_type,
            reply_to_message_id=message_id,
            in_reply_to=message_id
        )
    
    def _extract_email_address(self, sender: str) -> str:
        """Extrahiert E-Mail-Adresse aus Sender-String"""
        import re
        email_pattern = r'<([^>]+)>'
        match = re.search(email_pattern, sender)
        if match:
            return match.group(1)
        else:
            # Fallback: Suche nach @ Symbol
            if '@' in sender:
                return sender.strip()
            return sender
    
    def create_forward_email(self, original_email, forward_to: str, 
                           additional_content: str = "") -> EmailResponse:
        """Erstellt eine Weiterleitungs-E-Mail"""
        subject = original_email.subject
        if not subject.lower().startswith('fw:'):
            subject = f"Fw: {subject}"
        
        content = f"""
{additional_content}

--- Weitergeleitete Nachricht ---
Von: {original_email.sender}
Datum: {original_email.date}
Betreff: {original_email.subject}

{original_email.content}
"""
        
        return EmailResponse(
            to=forward_to,
            subject=subject,
            content=content,
            content_type="text/plain"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken zurück"""
        return {
            'sent_emails': self._sent_count,
            'failed_emails': self._failed_count,
            'success_rate': (self._sent_count / (self._sent_count + self._failed_count) * 100) 
                           if (self._sent_count + self._failed_count) > 0 else 0,
            'connection_active': self.connection is not None
        }
    
    async def test_connection(self) -> bool:
        """Testet die SMTP-Verbindung"""
        try:
            if await self.connect():
                await self.disconnect()
                logger.info("SMTP connection test successful")
                return True
            return False
        except Exception as e:
            logger.error("SMTP connection test failed", error=str(e))
            return False