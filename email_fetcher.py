import imaplib
import email
import logging
from email.header import decode_header
from typing import List, Dict, Optional
import yaml
from datetime import datetime

class EmailFetcher:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialisiert den E-Mail-Fetcher mit Konfiguration."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self.imap_connection = None
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus der YAML-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def connect(self) -> bool:
        """Stellt Verbindung zum IMAP-Server her."""
        try:
            imap_config = self.config['email']['imap']
            self.imap_connection = imaplib.IMAP4_SSL(
                imap_config['server'], 
                imap_config['port']
            )
            self.imap_connection.login(
                imap_config['username'], 
                imap_config['password']
            )
            self.logger.info("IMAP-Verbindung erfolgreich hergestellt")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei IMAP-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Trennt die IMAP-Verbindung."""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
                self.logger.info("IMAP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der IMAP-Verbindung: {e}")
    
    def fetch_unread_emails(self, max_emails: int = 1) -> List[Dict]:
        """Holt ungelesene E-Mails vom Server."""
        if not self.imap_connection:
            if not self.connect():
                return []
        
        try:
            # Wähle Posteingang aus
            self.imap_connection.select('INBOX')
            
            # Suche nach ungelesenen E-Mails
            status, messages = self.imap_connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                self.logger.error("Fehler beim Suchen nach ungelesenen E-Mails")
                return []
            
            email_list = []
            email_ids = messages[0].split()
            
            # Begrenze auf max_emails
            email_ids = email_ids[-max_emails:] if len(email_ids) > max_emails else email_ids
            
            for email_id in email_ids:
                try:
                    # Lade E-Mail
                    status, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Parse E-Mail-Daten
                    email_info = self._parse_email(email_message, email_id.decode())
                    if email_info:
                        email_list.append(email_info)
                        
                except Exception as e:
                    self.logger.error(f"Fehler beim Parsen der E-Mail {email_id}: {e}")
                    continue
            
            self.logger.info(f"{len(email_list)} ungelesene E-Mail(s) gefunden")
            return email_list
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen ungelesener E-Mails: {e}")
            return []
    
    def _parse_email(self, email_message, email_id: str) -> Optional[Dict]:
        """Parst eine einzelne E-Mail und extrahiert relevante Informationen."""
        try:
            # Betreff dekodieren
            subject = decode_header(email_message["subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode('utf-8', errors='ignore')
            
            # Absender dekodieren
            sender = decode_header(email_message["from"])[0][0]
            if isinstance(sender, bytes):
                sender = sender.decode('utf-8', errors='ignore')
            
            # Datum
            date = email_message["date"]
            
            # E-Mail-Inhalt extrahieren
            content = self._extract_content(email_message)
            
            return {
                'id': email_id,
                'subject': subject or "Kein Betreff",
                'sender': sender or "Unbekannter Absender",
                'date': date,
                'content': content,
                'raw_message': email_message
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der E-Mail: {e}")
            return None
    
    def _extract_content(self, email_message) -> str:
        """Extrahiert den Textinhalt aus einer E-Mail."""
        content = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Überspringe Anhänge
                if "attachment" in content_disposition:
                    continue
                
                # Suche nach Text-Inhalt
                if content_type == "text/plain":
                    try:
                        part_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        content += part_content
                    except Exception as e:
                        self.logger.warning(f"Fehler beim Dekodieren von Text-Inhalt: {e}")
        else:
            # Nicht-Multipart E-Mail
            try:
                content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception as e:
                self.logger.warning(f"Fehler beim Dekodieren von E-Mail-Inhalt: {e}")
        
        return content.strip()
    
    def mark_as_read(self, email_id: str):
        """Markiert eine E-Mail als gelesen."""
        try:
            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
            self.logger.info(f"E-Mail {email_id} als gelesen markiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Markieren als gelesen: {e}")
    
    def mark_as_unread(self, email_id: str):
        """Markiert eine E-Mail als ungelesen."""
        try:
            self.imap_connection.store(email_id, '-FLAGS', '\\Seen')
            self.logger.info(f"E-Mail {email_id} als ungelesen markiert")
        except Exception as e:
            self.logger.error(f"Fehler beim Markieren als ungelesen: {e}")

if __name__ == "__main__":
    # Test des E-Mail-Fetchers
    logging.basicConfig(level=logging.INFO)
    fetcher = EmailFetcher()
    
    try:
        emails = fetcher.fetch_unread_emails()
        for email_info in emails:
            print(f"Von: {email_info['sender']}")
            print(f"Betreff: {email_info['subject']}")
            print(f"Inhalt: {email_info['content'][:200]}...")
            print("-" * 50)
    finally:
        fetcher.disconnect()