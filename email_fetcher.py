import imaplib
import email
import logging
from email.header import decode_header
from typing import List, Dict, Optional
import yaml
import os

class EmailFetcher:
    """Holt ungelesene E-Mails über IMAP"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.imap_server = None
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def connect(self) -> bool:
        """Verbindet sich mit dem IMAP-Server"""
        try:
            imap_config = self.config['email']['imap']
            self.imap_server = imaplib.IMAP4_SSL(
                imap_config['server'], 
                imap_config['port']
            )
            
            # Login
            self.imap_server.login(
                imap_config['username'], 
                imap_config['password']
            )
            
            # Wähle Posteingang
            self.imap_server.select(imap_config['folder'])
            self.logger.info("Erfolgreich mit IMAP-Server verbunden")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei IMAP-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Trennt die IMAP-Verbindung"""
        if self.imap_server:
            try:
                self.imap_server.logout()
                self.logger.info("IMAP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der IMAP-Verbindung: {e}")
    
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
            return decoded_string
        except Exception as e:
            self.logger.warning(f"Fehler beim Dekodieren des Headers: {e}")
            return str(header)
    
    def _get_email_content(self, msg: email.message.Message) -> str:
        """Extrahiert den Textinhalt aus einer E-Mail"""
        content = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        content += payload.decode(charset, errors='ignore')
                    except Exception as e:
                        self.logger.warning(f"Fehler beim Lesen des E-Mail-Inhalts: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                content = payload.decode(charset, errors='ignore')
            except Exception as e:
                self.logger.warning(f"Fehler beim Lesen des E-Mail-Inhalts: {e}")
        
        return content.strip()
    
    def fetch_unread_emails(self, limit: int = 5) -> List[Dict]:
        """Holt ungelesene E-Mails"""
        if not self.imap_server:
            if not self.connect():
                return []
        
        try:
            # Suche nach ungelesenen E-Mails
            status, messages = self.imap_server.search(None, 'UNSEEN')
            
            if status != 'OK':
                self.logger.error("Fehler beim Suchen nach ungelesenen E-Mails")
                return []
            
            email_list = []
            email_ids = messages[0].split()
            
            # Begrenze die Anzahl der E-Mails
            email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
            
            for email_id in email_ids:
                try:
                    # Lade E-Mail
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extrahiere E-Mail-Daten
                    email_data = {
                        'id': email_id.decode(),
                        'subject': self._decode_header(msg.get('Subject', '')),
                        'sender': self._decode_header(msg.get('From', '')),
                        'date': msg.get('Date', ''),
                        'content': self._get_email_content(msg),
                        'message_id': msg.get('Message-ID', ''),
                        'raw_message': msg
                    }
                    
                    email_list.append(email_data)
                    self.logger.info(f"E-Mail gefunden: {email_data['subject']} von {email_data['sender']}")
                    
                except Exception as e:
                    self.logger.error(f"Fehler beim Verarbeiten der E-Mail {email_id}: {e}")
                    continue
            
            return email_list
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der E-Mails: {e}")
            return []
    
    def mark_as_read(self, email_id: str):
        """Markiert eine E-Mail als gelesen"""
        try:
            self.imap_server.store(email_id, '+FLAGS', '\\Seen')
            self.logger.info(f"E-Mail {email_id} als gelesen markiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Markieren als gelesen: {e}")
    
    def mark_as_unread(self, email_id: str):
        """Markiert eine E-Mail als ungelesen"""
        try:
            self.imap_server.store(email_id, '-FLAGS', '\\Seen')
            self.logger.info(f"E-Mail {email_id} als ungelesen markiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Markieren als ungelesen: {e}")


if __name__ == "__main__":
    # Test des E-Mail-Fetchers
    logging.basicConfig(level=logging.INFO)
    fetcher = EmailFetcher()
    
    if fetcher.connect():
        emails = fetcher.fetch_unread_emails(limit=3)
        print(f"Gefundene E-Mails: {len(emails)}")
        for email_data in emails:
            print(f"Betreff: {email_data['subject']}")
            print(f"Von: {email_data['sender']}")
            print(f"Inhalt: {email_data['content'][:100]}...")
            print("-" * 50)
        
        fetcher.disconnect()