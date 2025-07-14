"""
E-Mail Fetcher für den Super-KI-Agenten
"""
import imaplib
import email
import logging
from typing import List, Dict, Any, Optional
from email.header import decode_header
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EmailData:
    """Datenstruktur für E-Mail-Informationen"""
    uid: str
    subject: str
    sender: str
    recipient: str
    date: datetime
    body: str
    html_body: Optional[str]
    attachments: List[Dict[str, Any]]
    headers: Dict[str, str]
    raw_email: bytes

class EmailFetcher:
    """IMAP E-Mail Fetcher mit erweiterten Funktionen"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_email_config()
        self.logger = logging.getLogger(__name__)
        self.connection: Optional[imaplib.IMAP4_SSL] = None
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
    
    def connect(self) -> bool:
        """Verbindet zum IMAP-Server"""
        try:
            self.connection = imaplib.IMAP4_SSL(
                self.config.imap['server'],
                self.config.imap['port']
            )
            self.connection.login(self.email_address, self.password)
            self.logger.info(f"Erfolgreich mit IMAP-Server verbunden: {self.config.imap['server']}")
            return True
        except Exception as e:
            self.logger.error(f"IMAP-Verbindung fehlgeschlagen: {e}")
            return False
    
    def disconnect(self):
        """Trennt IMAP-Verbindung"""
        if self.connection:
            try:
                self.connection.logout()
                self.logger.info("IMAP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der IMAP-Verbindung: {e}")
            finally:
                self.connection = None
    
    def fetch_unread_emails(self, max_count: Optional[int] = None) -> List[EmailData]:
        """Holt ungelesene E-Mails"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Wähle INBOX
            self.connection.select('INBOX')
            
            # Suche ungelesene E-Mails
            _, message_numbers = self.connection.search(None, 'UNSEEN')
            
            if not message_numbers[0]:
                return []
            
            email_list = message_numbers[0].split()
            
            # Begrenze Anzahl
            if max_count:
                email_list = email_list[-max_count:]
            
            emails = []
            for num in email_list:
                try:
                    email_data = self._fetch_email_by_number(num)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    self.logger.error(f"Fehler beim Abrufen von E-Mail {num}: {e}")
            
            self.logger.info(f"{len(emails)} ungelesene E-Mails abgerufen")
            return emails
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen ungelesener E-Mails: {e}")
            return []
    
    def fetch_recent_emails(self, hours: int = 24, max_count: Optional[int] = None) -> List[EmailData]:
        """Holt E-Mails der letzten X Stunden"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            self.connection.select('INBOX')
            
            # Berechne Datum
            since_date = (datetime.now() - timedelta(hours=hours)).strftime("%d-%b-%Y")
            
            # Suche E-Mails seit Datum
            _, message_numbers = self.connection.search(None, f'SINCE {since_date}')
            
            if not message_numbers[0]:
                return []
            
            email_list = message_numbers[0].split()
            
            if max_count:
                email_list = email_list[-max_count:]
            
            emails = []
            for num in email_list:
                try:
                    email_data = self._fetch_email_by_number(num)
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    self.logger.error(f"Fehler beim Abrufen von E-Mail {num}: {e}")
            
            self.logger.info(f"{len(emails)} E-Mails der letzten {hours} Stunden abgerufen")
            return emails
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen kürzlicher E-Mails: {e}")
            return []
    
    def _fetch_email_by_number(self, message_number: bytes) -> Optional[EmailData]:
        """Holt eine einzelne E-Mail nach Nummer"""
        try:
            # Hole E-Mail-Daten
            _, msg_data = self.connection.fetch(message_number, '(RFC822)')
            email_body = msg_data[0][1]
            
            # Parse E-Mail
            email_message = email.message_from_bytes(email_body)
            
            # Extrahiere Header
            subject = self._decode_header(email_message['subject'] or '')
            sender = self._decode_header(email_message['from'] or '')
            recipient = self._decode_header(email_message['to'] or '')
            date_str = email_message['date'] or ''
            
            # Parse Datum
            try:
                date = email.utils.parsedate_to_datetime(date_str)
            except:
                date = datetime.now()
            
            # Extrahiere Body und Attachments
            body, html_body, attachments = self._extract_body_and_attachments(email_message)
            
            # Extrahiere alle Header
            headers = dict(email_message.items())
            
            return EmailData(
                uid=message_number.decode(),
                subject=subject,
                sender=sender,
                recipient=recipient,
                date=date,
                body=body,
                html_body=html_body,
                attachments=attachments,
                headers=headers,
                raw_email=email_body
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen von E-Mail {message_number}: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Dekodiert E-Mail-Header"""
        if not header:
            return ""
        
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
            return decoded_string
        except Exception as e:
            self.logger.warning(f"Fehler beim Dekodieren von Header '{header}': {e}")
            return str(header)
    
    def _extract_body_and_attachments(self, email_message) -> tuple:
        """Extrahiert Body und Attachments aus E-Mail"""
        body = ""
        html_body = ""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Attachments
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        attachments.append({
                            'filename': filename,
                            'content_type': content_type,
                            'size': len(part.get_payload(decode=True)),
                            'data': part.get_payload(decode=True)
                        })
                
                # Text Body
                elif content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        body += part.get_payload(decode=True).decode('latin-1', errors='ignore')
                
                # HTML Body
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        html_body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        html_body += part.get_payload(decode=True).decode('latin-1', errors='ignore')
        else:
            # Nicht-Multipart E-Mail
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                try:
                    body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = email_message.get_payload(decode=True).decode('latin-1', errors='ignore')
            elif content_type == "text/html":
                try:
                    html_body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    html_body = email_message.get_payload(decode=True).decode('latin-1', errors='ignore')
        
        return body, html_body, attachments
    
    def mark_as_read(self, message_number: bytes) -> bool:
        """Markiert E-Mail als gelesen"""
        try:
            self.connection.store(message_number, '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Markieren als gelesen: {e}")
            return False
    
    def move_to_folder(self, message_number: bytes, folder: str) -> bool:
        """Verschiebt E-Mail in anderen Ordner"""
        try:
            self.connection.store(message_number, '+X-GM-LABELS', folder)
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Verschieben in Ordner {folder}: {e}")
            return False
    
    def delete_email(self, message_number: bytes) -> bool:
        """Löscht E-Mail"""
        try:
            self.connection.store(message_number, '+FLAGS', '\\Deleted')
            self.connection.expunge()
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Löschen der E-Mail: {e}")
            return False