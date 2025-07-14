"""
Liyana NEXUS v1 - Email Unit
IMAP/SMTP Parser und Dispatcher für E-Mail-Verarbeitung
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from email import message_from_bytes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import smtplib
import ssl
from pathlib import Path

import config
from memory_vault import CustomerData, RequestData

@dataclass
class EmailMessage:
    """E-Mail-Nachrichten-Struktur"""
    id: str
    from_email: str
    to_email: str
    subject: str
    body: str
    timestamp: float
    attachments: List[str] = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.headers is None:
            self.headers = {}

class EmailUnit:
    """
    Email Unit - E-Mail-Verarbeitung und -Versand
    Unterstützt Gmail, Yahoo, Outlook und andere IMAP/SMTP-Provider
    """
    
    def __init__(self, memory_vault):
        self.logger = logging.getLogger("nexus.email")
        self.memory = memory_vault
        self.is_running = False
        self.connections = {}
        self.email_configs = {}
        
        # E-Mail-Provider-Konfigurationen
        self._load_email_configs()
        
        self.logger.info("📧 Email Unit initialisiert")
    
    def _load_email_configs(self):
        """Lädt E-Mail-Konfigurationen aus der Config"""
        self.email_configs = config.EMAIL_CONFIG.copy()
        
        # Füge Umgebungsvariablen hinzu
        for provider in self.email_configs:
            self.email_configs[provider].update({
                "username": config.get(f"{provider.upper()}_EMAIL"),
                "password": config.get(f"{provider.upper()}_PASSWORD"),
                "app_password": config.get(f"{provider.upper()}_APP_PASSWORD")
            })
    
    async def start(self):
        """Startet die E-Mail-Verarbeitung"""
        if self.is_running:
            return
        
        self.logger.info("🚀 Starte Email Unit...")
        self.is_running = True
        
        # Starte E-Mail-Monitoring für alle konfigurierten Provider
        for provider, config in self.email_configs.items():
            if config.get("username") and config.get("password"):
                asyncio.create_task(self._monitor_emails(provider))
        
        self.logger.info("✅ Email Unit gestartet")
    
    async def stop(self):
        """Stoppt die E-Mail-Verarbeitung"""
        self.logger.info("🛑 Stoppe Email Unit...")
        self.is_running = False
        
        # Schließe alle Verbindungen
        for provider, connection in self.connections.items():
            try:
                if connection:
                    connection.logout()
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Schließen der {provider}-Verbindung: {e}")
        
        self.connections.clear()
        self.logger.info("✅ Email Unit gestoppt")
    
    async def _monitor_emails(self, provider: str):
        """Überwacht E-Mails für einen spezifischen Provider"""
        while self.is_running:
            try:
                await self._check_new_emails(provider)
                await asyncio.sleep(30)  # Alle 30 Sekunden prüfen
                
            except Exception as e:
                self.logger.error(f"❌ Fehler beim E-Mail-Monitoring für {provider}: {e}")
                await asyncio.sleep(60)  # Längere Pause bei Fehlern
    
    async def _check_new_emails(self, provider: str):
        """Prüft auf neue E-Mails"""
        try:
            config = self.email_configs[provider]
            
            # Verbinde zu IMAP-Server
            imap_connection = await self._connect_imap(provider)
            if not imap_connection:
                return
            
            # Wähle INBOX aus
            imap_connection.select('INBOX')
            
            # Suche nach ungelesenen E-Mails
            _, message_numbers = imap_connection.search(None, 'UNSEEN')
            
            if message_numbers[0]:
                for num in message_numbers[0].split():
                    try:
                        # Lade E-Mail
                        _, msg_data = imap_connection.fetch(num, '(RFC822)')
                        email_body = msg_data[0][1]
                        
                        # Parse E-Mail
                        email_message = await self._parse_email(email_body, provider)
                        if email_message:
                            # Verarbeite E-Mail
                            await self._process_email(email_message)
                            
                            # Markiere als gelesen
                            imap_connection.store(num, '+FLAGS', '\\Seen')
                    
                    except Exception as e:
                        self.logger.error(f"❌ Fehler beim Verarbeiten der E-Mail {num}: {e}")
            
            # Schließe Verbindung
            imap_connection.close()
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Prüfen neuer E-Mails für {provider}: {e}")
    
    async def _connect_imap(self, provider: str):
        """Verbindet zu einem IMAP-Server"""
        try:
            config = self.email_configs[provider]
            
            # Erstelle SSL-Kontext
            context = ssl.create_default_context()
            
            # Verbinde zu IMAP-Server
            imap_server = imaplib.IMAP4_SSL(
                config["imap_server"],
                config["imap_port"],
                ssl_context=context
            )
            
            # Login
            password = config.get("app_password") or config.get("password")
            imap_server.login(config["username"], password)
            
            return imap_server
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim IMAP-Verbindung zu {provider}: {e}")
            return None
    
    async def _parse_email(self, email_data: bytes, provider: str) -> Optional[EmailMessage]:
        """Parst eine E-Mail-Nachricht"""
        try:
            # Parse E-Mail mit email-Modul
            msg = message_from_bytes(email_data)
            
            # Extrahiere Header
            from_email = msg.get('From', '')
            to_email = msg.get('To', '')
            subject = msg.get('Subject', '')
            date = msg.get('Date', '')
            
            # Extrahiere Body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Erstelle EmailMessage-Objekt
            email_message = EmailMessage(
                id=str(uuid.uuid4()),
                from_email=from_email,
                to_email=to_email,
                subject=subject,
                body=body,
                timestamp=time.time(),
                headers=dict(msg.items())
            )
            
            return email_message
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Parsen der E-Mail: {e}")
            return None
    
    async def _process_email(self, email_message: EmailMessage):
        """Verarbeitet eine E-Mail-Nachricht"""
        try:
            self.logger.info(f"📧 Verarbeite E-Mail: {email_message.subject}")
            
            # Extrahiere E-Mail-Adresse des Absenders
            sender_email = self._extract_email_address(email_message.from_email)
            
            # Lade oder erstelle Kunden-Daten
            customer = await self.memory.get_customer_by_email(sender_email)
            if not customer:
                customer = CustomerData(
                    id=str(uuid.uuid4()),
                    email=sender_email,
                    name=self._extract_name(email_message.from_email),
                    preferences={},
                    created_at=time.time()
                )
                await self.memory.store_customer(customer)
            
            # Erstelle Anfrage
            request = RequestData(
                id=str(uuid.uuid4()),
                customer_id=customer.id,
                type="email",
                content=f"Subject: {email_message.subject}\n\n{email_message.body}",
                status="pending",
                priority=self._determine_priority(email_message),
                created_at=time.time()
            )
            
            await self.memory.store_request(request)
            
            # Logge System-Ereignis
            await self.memory.log_system_event(
                "INFO",
                "email_unit",
                f"E-Mail von {sender_email} verarbeitet: {email_message.subject}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Verarbeiten der E-Mail: {e}")
    
    def _extract_email_address(self, email_string: str) -> str:
        """Extrahiert E-Mail-Adresse aus einem String"""
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        match = re.search(email_pattern, email_string)
        return match.group() if match else email_string
    
    def _extract_name(self, email_string: str) -> str:
        """Extrahiert Namen aus E-Mail-String"""
        if '<' in email_string and '>' in email_string:
            name_part = email_string.split('<')[0].strip()
            if name_part:
                return name_part.strip('"')
        return "Unbekannt"
    
    def _determine_priority(self, email_message: EmailMessage) -> int:
        """Bestimmt die Priorität einer E-Mail"""
        subject_lower = email_message.subject.lower()
        body_lower = email_message.body.lower()
        
        # Hohe Priorität
        high_priority_keywords = ['dringend', 'urgent', 'wichtig', 'important', 'sofort', 'immediately']
        for keyword in high_priority_keywords:
            if keyword in subject_lower or keyword in body_lower:
                return 5
        
        # Mittlere Priorität
        medium_priority_keywords = ['frage', 'question', 'anfrage', 'inquiry', 'support', 'hilfe']
        for keyword in medium_priority_keywords:
            if keyword in subject_lower or keyword in body_lower:
                return 3
        
        # Normale Priorität
        return 1
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        from_email: str = None, provider: str = "gmail") -> bool:
        """Sendet eine E-Mail"""
        try:
            config = self.email_configs.get(provider)
            if not config:
                self.logger.error(f"❌ Keine Konfiguration für Provider: {provider}")
                return False
            
            # Verwende Standard-E-Mail falls nicht angegeben
            if not from_email:
                from_email = config["username"]
            
            # Erstelle E-Mail-Nachricht
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Füge Body hinzu
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Sende E-Mail
            await self._send_smtp_email(msg, provider)
            
            self.logger.info(f"✅ E-Mail gesendet an {to_email}: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden der E-Mail: {e}")
            return False
    
    async def _send_smtp_email(self, msg: MIMEMultipart, provider: str):
        """Sendet E-Mail über SMTP"""
        try:
            config = self.email_configs[provider]
            
            # Erstelle SSL-Kontext
            context = ssl.create_default_context()
            
            # Verbinde zu SMTP-Server
            with smtplib.SMTP_SSL(
                config["smtp_server"],
                config["smtp_port"],
                context=context
            ) as server:
                # Login
                password = config.get("app_password") or config.get("password")
                server.login(config["username"], password)
                
                # Sende E-Mail
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"❌ SMTP-Fehler: {e}")
            raise
    
    async def process_emails(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet E-Mails basierend auf den übergebenen Daten"""
        try:
            provider = data.get("provider", "gmail")
            action = data.get("action", "check")
            
            if action == "check":
                # Prüfe neue E-Mails
                await self._check_new_emails(provider)
                return {"success": True, "action": "checked_new_emails"}
            
            elif action == "send":
                # Sende E-Mail
                to_email = data.get("to_email")
                subject = data.get("subject")
                body = data.get("body")
                
                if not all([to_email, subject, body]):
                    return {"success": False, "error": "Fehlende E-Mail-Daten"}
                
                success = await self.send_email(to_email, subject, body, provider=provider)
                return {"success": success, "action": "sent_email"}
            
            else:
                return {"success": False, "error": f"Unbekannte Aktion: {action}"}
                
        except Exception as e:
            self.logger.error(f"❌ Fehler bei E-Mail-Verarbeitung: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Gibt den Status der Email Unit zurück"""
        return {
            "state": "EXECUTING" if self.is_running else "WAITING",
            "providers": list(self.email_configs.keys()),
            "connections": len(self.connections),
            "last_check": time.time()
        }
    
    async def pause(self):
        """Pausiert die E-Mail-Verarbeitung"""
        self.is_running = False
        self.logger.info("⏸️ Email Unit pausiert")
    
    async def resume(self):
        """Setzt die E-Mail-Verarbeitung fort"""
        if not self.is_running:
            await self.start()
        self.logger.info("▶️ Email Unit fortgesetzt")