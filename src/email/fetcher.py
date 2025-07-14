"""
Email Fetcher - IMAP-basierte E-Mail-Abrufung
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = structlog.get_logger(__name__)


@dataclass
class EmailMessage:
    """Datenklasse für E-Mail-Nachrichten"""
    uid: str
    sender: str
    recipient: str
    subject: str
    date: datetime
    content: str
    content_type: str
    attachments: List[Dict[str, Any]]
    headers: Dict[str, str]
    raw_message: bytes


class EmailFetcher:
    """IMAP-basierter E-Mail-Fetcher mit asynchroner Verarbeitung"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.imap_config = config['imap']
        self.credentials = {
            'username': config['username'],
            'password': config['password']
        }
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        self._processed_uids = set()
        
    async def connect(self) -> bool:
        """Stellt IMAP-Verbindung her"""
        try:
            loop = asyncio.get_event_loop()
            self.connection = await loop.run_in_executor(
                self.executor,
                self._connect_sync
            )
            logger.info("IMAP connection established", 
                       server=self.imap_config['server'])
            return True
        except Exception as e:
            logger.error("Failed to connect to IMAP server", error=str(e))
            return False
    
    def _connect_sync(self) -> imaplib.IMAP4_SSL:
        """Synchrone IMAP-Verbindung"""
        connection = imaplib.IMAP4_SSL(
            self.imap_config['server'],
            self.imap_config['port']
        )
        connection.login(
            self.credentials['username'],
            self.credentials['password']
        )
        return connection
    
    async def disconnect(self) -> None:
        """Trennt IMAP-Verbindung"""
        if self.connection:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self.executor,
                    self.connection.logout
                )
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.error("Error closing IMAP connection", error=str(e))
            finally:
                self.connection = None
    
    async def fetch_new_emails(self, max_count: int = 10) -> List[EmailMessage]:
        """Holt neue E-Mails vom Server"""
        if not self.connection:
            if not await self.connect():
                return []
        
        try:
            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(
                self.executor,
                self._fetch_emails_sync,
                max_count
            )
            
            # Filtere bereits verarbeitete E-Mails
            new_emails = [email for email in emails 
                         if email.uid not in self._processed_uids]
            
            # Markiere als verarbeitet
            for email_msg in new_emails:
                self._processed_uids.add(email_msg.uid)
            
            logger.info("Fetched new emails", count=len(new_emails))
            return new_emails
            
        except Exception as e:
            logger.error("Failed to fetch emails", error=str(e))
            return []
    
    def _fetch_emails_sync(self, max_count: int) -> List[EmailMessage]:
        """Synchrone E-Mail-Abrufung"""
        self.connection.select(self.imap_config['folder'])
        
        # Suche nach ungelesenen E-Mails
        _, message_numbers = self.connection.search(None, 'UNSEEN')
        
        if not message_numbers[0]:
            return []
        
        email_list = message_numbers[0].split()
        # Begrenze auf max_count
        email_list = email_list[-max_count:] if len(email_list) > max_count else email_list
        
        emails = []
        for num in email_list:
            try:
                # Hole E-Mail mit UID
                _, msg_data = self.connection.fetch(num, '(RFC822.HEADER)')
                uid = num.decode('utf-8')
                
                # Hole vollständige E-Mail
                _, full_msg_data = self.connection.fetch(num, '(RFC822)')
                email_body = full_msg_data[0][1]
                
                # Parse E-Mail
                email_message = self._parse_email(uid, email_body)
                if email_message:
                    emails.append(email_message)
                    
            except Exception as e:
                logger.error("Failed to fetch email", uid=num, error=str(e))
                continue
        
        return emails
    
    def _parse_email(self, uid: str, raw_email: bytes) -> Optional[EmailMessage]:
        """Parst eine E-Mail-Nachricht"""
        try:
            msg = email.message_from_bytes(raw_email)
            
            # Extrahiere Header
            sender = self._decode_header(msg.get('From', ''))
            recipient = self._decode_header(msg.get('To', ''))
            subject = self._decode_header(msg.get('Subject', ''))
            date_str = msg.get('Date', '')
            
            # Parse Datum
            try:
                date = email.utils.parsedate_to_datetime(date_str)
            except:
                date = datetime.now()
            
            # Extrahiere Inhalt
            content, content_type, attachments = self._extract_content(msg)
            
            # Extrahiere alle Header
            headers = dict(msg.items())
            
            return EmailMessage(
                uid=uid,
                sender=sender,
                recipient=recipient,
                subject=subject,
                date=date,
                content=content,
                content_type=content_type,
                attachments=attachments,
                headers=headers,
                raw_message=raw_email
            )
            
        except Exception as e:
            logger.error("Failed to parse email", uid=uid, error=str(e))
            return None
    
    def _decode_header(self, header: str) -> str:
        """Dekodiert E-Mail-Header"""
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            return decoded_string.strip()
        except:
            return header.strip()
    
    def _extract_content(self, msg: email.message.Message) -> tuple:
        """Extrahiert Inhalt, Content-Type und Anhänge"""
        content = ""
        content_type = "text/plain"
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                
                content_disposition = part.get('Content-Disposition', '')
                
                if 'attachment' in content_disposition:
                    # Anhang
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        attachments.append({
                            'filename': filename,
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True))
                        })
                else:
                    # Inhalt
                    if part.get_content_type() in ['text/plain', 'text/html']:
                        payload = part.get_payload(decode=True)
                        if payload:
                            try:
                                charset = part.get_content_charset() or 'utf-8'
                                content += payload.decode(charset, errors='ignore')
                                content_type = part.get_content_type()
                            except:
                                content += payload.decode('utf-8', errors='ignore')
        else:
            # Einfache E-Mail
            payload = msg.get_payload(decode=True)
            if payload:
                try:
                    charset = msg.get_content_charset() or 'utf-8'
                    content = payload.decode(charset, errors='ignore')
                    content_type = msg.get_content_type()
                except:
                    content = payload.decode('utf-8', errors='ignore')
        
        return content.strip(), content_type, attachments
    
    async def mark_as_read(self, uid: str) -> bool:
        """Markiert E-Mail als gelesen"""
        if not self.connection:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._mark_as_read_sync,
                uid
            )
            logger.info("Email marked as read", uid=uid)
            return True
        except Exception as e:
            logger.error("Failed to mark email as read", uid=uid, error=str(e))
            return False
    
    def _mark_as_read_sync(self, uid: str) -> None:
        """Synchrone Markierung als gelesen"""
        self.connection.store(uid, '+FLAGS', '\\Seen')
    
    async def move_to_folder(self, uid: str, folder: str) -> bool:
        """Verschiebt E-Mail in einen anderen Ordner"""
        if not self.connection:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._move_to_folder_sync,
                uid,
                folder
            )
            logger.info("Email moved to folder", uid=uid, folder=folder)
            return True
        except Exception as e:
            logger.error("Failed to move email", uid=uid, folder=folder, error=str(e))
            return False
    
    def _move_to_folder_sync(self, uid: str, folder: str) -> None:
        """Synchrone Verschiebung"""
        self.connection.store(uid, '+X-GM-LABELS', folder)
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken zurück"""
        return {
            'processed_emails': len(self._processed_uids),
            'connection_active': self.connection is not None
        }