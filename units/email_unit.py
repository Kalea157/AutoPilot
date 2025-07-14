"""
Liyana NEXUS v1 - Email Unit
IMAP/SMTP Parser + Dispatcher für Gmail, Yahoo, Outlook
"""

import asyncio
import logging
import email
import email.header
import email.utils
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
import re

from config import config, AgentState

class EmailUnit:
    """Email-Verarbeitung und -Versand"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = AgentState.WAITING
        
        # Email-Konfiguration
        self.email_config = config.api
        self.imap_connection: Optional[imaplib.IMAP4_SSL] = None
        self.smtp_connection: Optional[smtplib.SMTP] = None
        
        # Email-Templates
        self.email_templates = {
            'support_response': {
                'subject': 'Re: {original_subject}',
                'body': '''
Sehr geehrte/r {customer_name},

vielen Dank für Ihre Nachricht. {response_content}

Mit freundlichen Grüßen
{company_name}
                '''
            },
            'order_confirmation': {
                'subject': 'Bestellbestätigung - {order_id}',
                'body': '''
Sehr geehrte/r {customer_name},

vielen Dank für Ihre Bestellung. Hier sind die Details:

Bestellnummer: {order_id}
Gesamtbetrag: {total_amount}
Lieferdatum: {delivery_date}

Mit freundlichen Grüßen
{company_name}
                '''
            },
            'general_inquiry': {
                'subject': 'Antwort auf Ihre Anfrage',
                'body': '''
Sehr geehrte/r {customer_name},

vielen Dank für Ihre Anfrage. {response_content}

Mit freundlichen Grüßen
{company_name}
                '''
            }
        }
        
        # Email-Kategorien
        self.email_categories = {
            'support': ['support', 'hilfe', 'problem', 'fehler', 'bug'],
            'order': ['bestellung', 'order', 'kauf', 'purchase'],
            'inquiry': ['anfrage', 'frage', 'inquiry', 'question'],
            'complaint': ['beschwerde', 'complaint', 'reklamation'],
            'spam': ['spam', 'newsletter', 'marketing']
        }
        
        self._running = False
        self._polling_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Startet den Email Unit"""
        if self._running:
            return
        
        self.logger.info("Email Unit wird gestartet...")
        self._running = True
        self.state = AgentState.EXECUTING
        
        # Verbinde zu IMAP
        await self._connect_imap()
        
        # Starte Email-Polling
        self._polling_task = asyncio.create_task(self._email_polling_loop())
        
        self.logger.info("Email Unit gestartet")
    
    async def stop(self):
        """Stoppt den Email Unit"""
        self.logger.info("Email Unit wird gestoppt...")
        self._running = False
        self.state = AgentState.PAUSED
        
        # Stoppe Polling
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        # Schließe Verbindungen
        await self._disconnect_imap()
        await self._disconnect_smtp()
        
        self.logger.info("Email Unit gestoppt")
    
    async def _connect_imap(self) -> bool:
        """Verbindet zu IMAP-Server"""
        try:
            self.imap_connection = imaplib.IMAP4_SSL(
                self.email_config.imap_server,
                self.email_config.imap_port
            )
            
            # Login
            self.imap_connection.login(
                self.email_config.email_address,
                self.email_config.email_password
            )
            
            self.logger.info("IMAP-Verbindung hergestellt")
            return True
            
        except Exception as e:
            self.logger.error(f"IMAP-Verbindungsfehler: {e}")
            return False
    
    async def _disconnect_imap(self):
        """Trennt IMAP-Verbindung"""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
                self.imap_connection = None
                self.logger.info("IMAP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der IMAP-Verbindung: {e}")
    
    async def _connect_smtp(self) -> bool:
        """Verbindet zu SMTP-Server"""
        try:
            self.smtp_connection = smtplib.SMTP(
                self.email_config.smtp_server,
                self.email_config.smtp_port
            )
            self.smtp_connection.starttls()
            
            # Login
            self.smtp_connection.login(
                self.email_config.email_address,
                self.email_config.email_password
            )
            
            self.logger.info("SMTP-Verbindung hergestellt")
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP-Verbindungsfehler: {e}")
            return False
    
    async def _disconnect_smtp(self):
        """Trennt SMTP-Verbindung"""
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
                self.smtp_connection = None
                self.logger.info("SMTP-Verbindung getrennt")
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der SMTP-Verbindung: {e}")
    
    async def _email_polling_loop(self):
        """Hauptschleife für Email-Polling"""
        while self._running:
            try:
                # Prüfe neue Emails
                await self._check_new_emails()
                
                # Warte 30 Sekunden
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Fehler im Email-Polling: {e}")
                await asyncio.sleep(60)  # Warte länger bei Fehlern
    
    async def _check_new_emails(self):
        """Prüft auf neue Emails"""
        if not self.imap_connection:
            return
        
        try:
            # Wähle INBOX
            self.imap_connection.select('INBOX')
            
            # Suche ungelesene Emails
            _, message_numbers = self.imap_connection.search(None, 'UNSEEN')
            
            if message_numbers[0]:
                email_ids = message_numbers[0].split()
                
                for email_id in email_ids:
                    await self._process_email(email_id)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen neuer Emails: {e}")
    
    async def _process_email(self, email_id: bytes):
        """Verarbeitet eine einzelne Email"""
        try:
            # Lade Email
            _, msg_data = self.imap_connection.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Extrahiere Email-Daten
            email_data = await self._extract_email_data(email_message)
            
            # Kategorisiere Email
            category = await self._categorize_email(email_data)
            
            # Markiere als gelesen
            self.imap_connection.store(email_id, '+FLAGS', '\\Seen')
            
            # Verarbeite Email basierend auf Kategorie
            await self._handle_email_by_category(email_data, category)
            
            self.logger.info(f"Email verarbeitet: {email_data['subject']} ({category})")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Email: {e}")
    
    async def _extract_email_data(self, email_message) -> Dict[str, Any]:
        """Extrahiert Daten aus einer Email"""
        # Betreff
        subject = email_message.get('Subject', '')
        if subject:
            # Decodiere Subject
            decoded_subject = email.header.decode_header(subject)
            subject = ''.join([text.decode(charset or 'utf-8') if isinstance(text, bytes) else text 
                              for text, charset in decoded_subject])
        
        # Absender
        from_header = email_message.get('From', '')
        sender_email = re.search(r'<(.+?)>', from_header)
        sender_email = sender_email.group(1) if sender_email else from_header
        
        # Empfänger
        to_header = email_message.get('To', '')
        recipient_email = re.search(r'<(.+?)>', to_header)
        recipient_email = recipient_email.group(1) if recipient_email else to_header
        
        # Datum
        date_header = email_message.get('Date', '')
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_header)
        except:
            parsed_date = datetime.now()
        
        # Body
        body = await self._extract_email_body(email_message)
        
        return {
            'subject': subject,
            'sender_email': sender_email,
            'sender_name': from_header.split('<')[0].strip() if '<' in from_header else '',
            'recipient_email': recipient_email,
            'date': parsed_date,
            'body': body,
            'headers': dict(email_message.items())
        }
    
    async def _extract_email_body(self, email_message) -> str:
        """Extrahiert den Email-Body"""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))
                
                # Überspringe Attachments
                if 'attachment' in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        continue
                elif content_type == "text/html":
                    try:
                        body = part.get_payload(decode=True).decode()
                        # Einfache HTML-zu-Text Konvertierung
                        body = re.sub(r'<[^>]+>', '', body)
                        break
                    except:
                        continue
        else:
            # Nicht-Multipart Email
            try:
                body = email_message.get_payload(decode=True).decode()
            except:
                body = str(email_message.get_payload())
        
        return body.strip()
    
    async def _categorize_email(self, email_data: Dict[str, Any]) -> str:
        """Kategorisiert eine Email"""
        subject = email_data['subject'].lower()
        body = email_data['body'].lower()
        
        # Prüfe Spam
        if any(spam_word in subject or spam_word in body 
               for spam_word in self.email_categories['spam']):
            return 'spam'
        
        # Prüfe Bestellungen
        if any(order_word in subject or order_word in body 
               for order_word in self.email_categories['order']):
            return 'order'
        
        # Prüfe Support
        if any(support_word in subject or support_word in body 
               for support_word in self.email_categories['support']):
            return 'support'
        
        # Prüfe Beschwerden
        if any(complaint_word in subject or complaint_word in body 
               for complaint_word in self.email_categories['complaint']):
            return 'complaint'
        
        # Standard: Anfrage
        return 'inquiry'
    
    async def _handle_email_by_category(self, email_data: Dict[str, Any], category: str):
        """Behandelt Email basierend auf Kategorie"""
        if category == 'spam':
            # Markiere als Spam
            await self._mark_as_spam(email_data)
        elif category == 'order':
            # Verarbeite Bestellung
            await self._process_order_email(email_data)
        elif category == 'support':
            # Verarbeite Support-Anfrage
            await self._process_support_email(email_data)
        elif category == 'complaint':
            # Verarbeite Beschwerde
            await self._process_complaint_email(email_data)
        else:
            # Verarbeite allgemeine Anfrage
            await self._process_inquiry_email(email_data)
    
    async def _mark_as_spam(self, email_data: Dict[str, Any]):
        """Markiert Email als Spam"""
        self.logger.info(f"Email als Spam markiert: {email_data['subject']}")
        # Hier könnte die Email in einen Spam-Ordner verschoben werden
    
    async def _process_order_email(self, email_data: Dict[str, Any]):
        """Verarbeitet Bestell-Email"""
        # Extrahiere Bestelldaten
        order_data = await self._extract_order_data(email_data)
        
        # Erstelle Bestellbestätigung
        response_data = {
            'template': 'order_confirmation',
            'customer_name': email_data['sender_name'] or 'Kunde',
            'order_id': order_data.get('order_id', 'UNKNOWN'),
            'total_amount': order_data.get('total_amount', '0.00'),
            'delivery_date': order_data.get('delivery_date', 'TBD'),
            'company_name': 'Liyana NEXUS'
        }
        
        # Sende Antwort
        await self.send_email(
            to_email=email_data['sender_email'],
            subject=f"Bestellbestätigung - {order_data.get('order_id', 'UNKNOWN')}",
            body=await self._generate_email_response(response_data)
        )
    
    async def _process_support_email(self, email_data: Dict[str, Any]):
        """Verarbeitet Support-Email"""
        # Erstelle Support-Antwort
        response_data = {
            'template': 'support_response',
            'customer_name': email_data['sender_name'] or 'Kunde',
            'original_subject': email_data['subject'],
            'response_content': 'Wir bearbeiten Ihre Anfrage und melden uns innerhalb von 24 Stunden bei Ihnen.',
            'company_name': 'Liyana NEXUS Support'
        }
        
        # Sende Antwort
        await self.send_email(
            to_email=email_data['sender_email'],
            subject=f"Re: {email_data['subject']}",
            body=await self._generate_email_response(response_data)
        )
    
    async def _process_complaint_email(self, email_data: Dict[str, Any]):
        """Verarbeitet Beschwerde-Email"""
        # Erstelle Beschwerde-Antwort
        response_data = {
            'template': 'general_inquiry',
            'customer_name': email_data['sender_name'] or 'Kunde',
            'response_content': 'Wir entschuldigen uns für das Problem und werden es umgehend untersuchen.',
            'company_name': 'Liyana NEXUS'
        }
        
        # Sende Antwort
        await self.send_email(
            to_email=email_data['sender_email'],
            subject=f"Re: {email_data['subject']}",
            body=await self._generate_email_response(response_data)
        )
    
    async def _process_inquiry_email(self, email_data: Dict[str, Any]):
        """Verarbeitet allgemeine Anfrage"""
        # Erstelle Standard-Antwort
        response_data = {
            'template': 'general_inquiry',
            'customer_name': email_data['sender_name'] or 'Kunde',
            'response_content': 'Vielen Dank für Ihre Nachricht. Wir werden uns schnellstmöglich bei Ihnen melden.',
            'company_name': 'Liyana NEXUS'
        }
        
        # Sende Antwort
        await self.send_email(
            to_email=email_data['sender_email'],
            subject=f"Re: {email_data['subject']}",
            body=await self._generate_email_response(response_data)
        )
    
    async def _extract_order_data(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrahiert Bestelldaten aus Email"""
        # Einfache Extraktion - könnte erweitert werden
        body = email_data['body']
        
        # Suche nach Bestellnummer
        order_id_match = re.search(r'bestell(?:ung|nr|nummer)[:\s]*([A-Z0-9-]+)', body, re.IGNORECASE)
        order_id = order_id_match.group(1) if order_id_match else 'UNKNOWN'
        
        # Suche nach Betrag
        amount_match = re.search(r'betrag[:\s]*([0-9,]+\.?[0-9]*)\s*€?', body, re.IGNORECASE)
        total_amount = amount_match.group(1) if amount_match else '0.00'
        
        return {
            'order_id': order_id,
            'total_amount': total_amount,
            'delivery_date': 'TBD'
        }
    
    async def _generate_email_response(self, response_data: Dict[str, Any]) -> str:
        """Generiert Email-Antwort basierend auf Template"""
        template = self.email_templates.get(response_data['template'])
        if not template:
            return "Vielen Dank für Ihre Nachricht."
        
        body = template['body']
        
        # Ersetze Platzhalter
        for key, value in response_data.items():
            if key != 'template':
                body = body.replace(f'{{{key}}}', str(value))
        
        return body.strip()
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        from_name: str = None, html_body: str = None) -> bool:
        """Sendet eine Email"""
        try:
            # Verbinde zu SMTP falls nötig
            if not self.smtp_connection:
                await self._connect_smtp()
            
            if not self.smtp_connection:
                return False
            
            # Erstelle Email
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name or 'Liyana NEXUS'} <{self.email_config.email_address}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Text-Version
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # HTML-Version falls vorhanden
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Sende Email
            self.smtp_connection.send_message(msg)
            
            self.logger.info(f"Email gesendet an: {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Email: {e}")
            return False
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet eine Email-Task"""
        task_type = task_data.get('type', 'send_email')
        
        if task_type == 'send_email':
            return await self._handle_send_email_task(task_data)
        elif task_type == 'check_emails':
            return await self._handle_check_emails_task(task_data)
        elif task_type == 'categorize_email':
            return await self._handle_categorize_email_task(task_data)
        else:
            return {'error': f'Unbekannter Task-Typ: {task_type}', 'success': False}
    
    async def _handle_send_email_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Email-Send-Task"""
        to_email = task_data.get('to_email')
        subject = task_data.get('subject')
        body = task_data.get('body')
        from_name = task_data.get('from_name')
        html_body = task_data.get('html_body')
        
        if not all([to_email, subject, body]):
            return {'error': 'Fehlende Email-Parameter', 'success': False}
        
        success = await self.send_email(to_email, subject, body, from_name, html_body)
        
        return {
            'success': success,
            'to_email': to_email,
            'subject': subject,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _handle_check_emails_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Email-Check-Task"""
        await self._check_new_emails()
        
        return {
            'success': True,
            'message': 'Email-Check durchgeführt',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _handle_categorize_email_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Email-Kategorisierungs-Task"""
        email_data = task_data.get('email_data', {})
        
        if not email_data:
            return {'error': 'Keine Email-Daten vorhanden', 'success': False}
        
        category = await self._categorize_email(email_data)
        
        return {
            'success': True,
            'category': category,
            'email_data': email_data,
            'timestamp': datetime.now().isoformat()
        }