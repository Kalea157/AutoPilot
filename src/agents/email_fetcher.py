"""
Email Fetcher Agent - Retrieves emails from IMAP server
"""

import imaplib
import email
import ssl
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
import logging

from ..models.email import EmailMessage, EmailAddress, EmailAttachment
from ..core.config import config
from ..core.logger import logger


class EmailFetcher:
    """Email fetcher agent for retrieving emails from IMAP server"""
    
    def __init__(self):
        self.email_config = config.get_email_config()
        self.imap_config = self.email_config.get('imap', {})
        self.connection = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to server
            self.connection = imaplib.IMAP4_SSL(
                self.imap_config.get('server', 'imap.gmail.com'),
                self.imap_config.get('port', 993),
                ssl_context=context
            )
            
            # Login
            self.connection.login(
                config.email.username,
                config.email.password
            )
            
            self.is_connected = True
            logger.info("Successfully connected to IMAP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {str(e)}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection and self.is_connected:
            try:
                self.connection.logout()
                self.is_connected = False
                logger.info("Disconnected from IMAP server")
            except Exception as e:
                logger.error(f"Error disconnecting from IMAP server: {str(e)}")
    
    def select_folder(self, folder: str = "INBOX") -> bool:
        """Select email folder"""
        if not self.is_connected:
            return False
        
        try:
            status, messages = self.connection.select(folder)
            if status == 'OK':
                logger.info(f"Selected folder: {folder}")
                return True
            else:
                logger.error(f"Failed to select folder {folder}: {status}")
                return False
        except Exception as e:
            logger.error(f"Error selecting folder {folder}: {str(e)}")
            return False
    
    def fetch_unread_emails(self, limit: int = 10) -> List[EmailMessage]:
        """Fetch unread emails from selected folder"""
        if not self.is_connected:
            return []
        
        try:
            # Search for unread emails
            status, messages = self.connection.search(None, 'UNSEEN')
            if status != 'OK':
                logger.error(f"Failed to search for unread emails: {status}")
                return []
            
            email_ids = messages[0].split()
            if not email_ids:
                logger.info("No unread emails found")
                return []
            
            # Limit the number of emails to fetch
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for email_id in email_ids:
                try:
                    email_msg = self._fetch_email_by_id(email_id)
                    if email_msg:
                        emails.append(email_msg)
                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(emails)} unread emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching unread emails: {str(e)}")
            return []
    
    def fetch_recent_emails(self, hours: int = 24, limit: int = 10) -> List[EmailMessage]:
        """Fetch recent emails from the last N hours"""
        if not self.is_connected:
            return []
        
        try:
            # Calculate date threshold
            threshold_date = datetime.now() - timedelta(hours=hours)
            date_str = threshold_date.strftime("%d-%b-%Y")
            
            # Search for recent emails
            status, messages = self.connection.search(None, f'SINCE {date_str}')
            if status != 'OK':
                logger.error(f"Failed to search for recent emails: {status}")
                return []
            
            email_ids = messages[0].split()
            if not email_ids:
                logger.info(f"No emails found since {date_str}")
                return []
            
            # Limit the number of emails to fetch
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            emails = []
            for email_id in email_ids:
                try:
                    email_msg = self._fetch_email_by_id(email_id)
                    if email_msg:
                        emails.append(email_msg)
                except Exception as e:
                    logger.error(f"Error fetching email {email_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully fetched {len(emails)} recent emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching recent emails: {str(e)}")
            return []
    
    def _fetch_email_by_id(self, email_id: bytes) -> Optional[EmailMessage]:
        """Fetch a single email by ID"""
        try:
            # Fetch email data
            status, data = self.connection.fetch(email_id, '(RFC822)')
            if status != 'OK':
                logger.error(f"Failed to fetch email {email_id}: {status}")
                return None
            
            # Parse email
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract email components
            message_id = email_message.get('Message-ID', f"<{email_id.decode()}>")
            subject = self._decode_header(email_message.get('Subject', ''))
            sender = self._parse_email_address(email_message.get('From', ''))
            recipients = self._parse_email_addresses(email_message.get('To', ''))
            cc = self._parse_email_addresses(email_message.get('Cc', ''))
            bcc = self._parse_email_addresses(email_message.get('Bcc', ''))
            
            # Parse date
            date_received = self._parse_date(email_message.get('Date'))
            date_sent = self._parse_date(email_message.get('Date'))
            
            # Extract body and attachments
            body_text, body_html, attachments = self._extract_content(email_message)
            
            # Create EmailMessage object
            email_msg = EmailMessage(
                message_id=message_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                cc=cc,
                bcc=bcc,
                body_text=body_text,
                body_html=body_html,
                attachments=attachments,
                date_received=date_received,
                date_sent=date_sent,
                thread_id=email_message.get('References'),
                in_reply_to=email_message.get('In-Reply-To')
            )
            
            return email_msg
            
        except Exception as e:
            logger.error(f"Error parsing email {email_id}: {str(e)}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decode email header"""
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
        except Exception:
            return header
    
    def _parse_email_address(self, address_str: str) -> EmailAddress:
        """Parse single email address"""
        try:
            if '<' in address_str and '>' in address_str:
                # Format: "Name <email@domain.com>"
                name_part = address_str.split('<')[0].strip().strip('"')
                email_part = address_str.split('<')[1].split('>')[0].strip()
                return EmailAddress(email=email_part, name=name_part if name_part else None)
            else:
                # Format: "email@domain.com"
                return EmailAddress(email=address_str.strip())
        except Exception:
            return EmailAddress(email=address_str.strip())
    
    def _parse_email_addresses(self, addresses_str: str) -> List[EmailAddress]:
        """Parse multiple email addresses"""
        if not addresses_str:
            return []
        
        addresses = []
        for address in addresses_str.split(','):
            address = address.strip()
            if address:
                addresses.append(self._parse_email_address(address))
        
        return addresses
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date"""
        try:
            if date_str:
                return parsedate_to_datetime(date_str)
            return datetime.now()
        except Exception:
            return datetime.now()
    
    def _extract_content(self, email_message) -> tuple:
        """Extract text, HTML and attachments from email"""
        body_text = ""
        body_html = ""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip multipart containers
                if content_type == "multipart/alternative":
                    continue
                
                # Handle attachments
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filename = self._decode_header(filename)
                        attachment = EmailAttachment(
                            filename=filename,
                            content_type=content_type,
                            size=len(part.get_payload(decode=True)),
                            data=part.get_payload(decode=True)
                        )
                        attachments.append(attachment)
                
                # Handle text content
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body_text += payload.decode(charset, errors='ignore')
                        except Exception:
                            body_text += payload.decode('utf-8', errors='ignore')
                
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        try:
                            body_html += payload.decode(charset, errors='ignore')
                        except Exception:
                            body_html += payload.decode('utf-8', errors='ignore')
        else:
            # Single part message
            content_type = email_message.get_content_type()
            payload = email_message.get_payload(decode=True)
            
            if payload:
                charset = email_message.get_content_charset() or 'utf-8'
                try:
                    decoded_payload = payload.decode(charset, errors='ignore')
                except Exception:
                    decoded_payload = payload.decode('utf-8', errors='ignore')
                
                if content_type == "text/plain":
                    body_text = decoded_payload
                elif content_type == "text/html":
                    body_html = decoded_payload
        
        return body_text, body_html, attachments
    
    def mark_as_read(self, email_id: str) -> bool:
        """Mark email as read"""
        if not self.is_connected:
            return False
        
        try:
            # Convert email_id to bytes if needed
            if isinstance(email_id, str):
                email_id = email_id.encode()
            
            status, _ = self.connection.store(email_id, '+FLAGS', '\\Seen')
            if status == 'OK':
                logger.info(f"Marked email {email_id} as read")
                return True
            else:
                logger.error(f"Failed to mark email {email_id} as read: {status}")
                return False
        except Exception as e:
            logger.error(f"Error marking email {email_id} as read: {str(e)}")
            return False
    
    def get_folder_info(self) -> Dict[str, Any]:
        """Get information about current folder"""
        if not self.is_connected:
            return {}
        
        try:
            status, data = self.connection.status('INBOX', '(MESSAGES UNSEEN)')
            if status == 'OK':
                info = {}
                for item in data[0].decode().split():
                    if 'MESSAGES' in item:
                        info['total_messages'] = int(item.split('(')[1])
                    elif 'UNSEEN' in item:
                        info['unread_messages'] = int(item.split('(')[1])
                return info
            else:
                logger.error(f"Failed to get folder info: {status}")
                return {}
        except Exception as e:
            logger.error(f"Error getting folder info: {str(e)}")
            return {}