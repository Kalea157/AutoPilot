import re
import logging
from typing import Dict, List, Optional, Tuple
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime

class EmailParser:
    def __init__(self):
        """Initialisiert den E-Mail-Parser."""
        self.logger = logging.getLogger(__name__)
        
    def parse_email(self, email_data: Dict) -> Dict:
        """Parst eine E-Mail und extrahiert alle relevanten Informationen."""
        try:
            parsed_email = {
                'id': email_data.get('id'),
                'sender': self._parse_sender(email_data.get('sender', '')),
                'subject': self._clean_subject(email_data.get('subject', '')),
                'date': self._parse_date(email_data.get('date')),
                'content': self._clean_content(email_data.get('content', '')),
                'content_preview': self._create_preview(email_data.get('content', '')),
                'priority': self._detect_priority(email_data.get('subject', ''), email_data.get('content', '')),
                'category': self._categorize_email(email_data.get('subject', ''), email_data.get('content', '')),
                'requires_response': self._needs_response(email_data.get('subject', ''), email_data.get('content', '')),
                'original_data': email_data
            }
            
            self.logger.info(f"E-Mail erfolgreich geparst: {parsed_email['subject']}")
            return parsed_email
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der E-Mail: {e}")
            return self._create_fallback_parsed_email(email_data)
    
    def _parse_sender(self, sender: str) -> Dict:
        """Parst den Absender und extrahiert Name und E-Mail-Adresse."""
        try:
            name, email = parseaddr(sender)
            
            # Bereinige Name und E-Mail
            name = name.strip() if name else "Unbekannter Absender"
            email = email.strip() if email else ""
            
            # Extrahiere Domain für weitere Analyse
            domain = ""
            if email and '@' in email:
                domain = email.split('@')[1].lower()
            
            return {
                'full': sender,
                'name': name,
                'email': email,
                'domain': domain,
                'is_internal': self._is_internal_domain(domain)
            }
        except Exception as e:
            self.logger.warning(f"Fehler beim Parsen des Absenders: {e}")
            return {
                'full': sender,
                'name': "Unbekannter Absender",
                'email': "",
                'domain': "",
                'is_internal': False
            }
    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parst das Datum der E-Mail."""
        try:
            if date_string:
                return parsedate_to_datetime(date_string)
            return None
        except Exception as e:
            self.logger.warning(f"Fehler beim Parsen des Datums: {e}")
            return None
    
    def _clean_subject(self, subject: str) -> str:
        """Bereinigt den Betreff der E-Mail."""
        if not subject:
            return "Kein Betreff"
        
        # Entferne häufige Präfixe
        subject = re.sub(r'^(RE|AW|FWD|FW|Ant|Re|Aw|Fwd|Fw):\s*', '', subject, flags=re.IGNORECASE)
        
        # Entferne überflüssige Leerzeichen
        subject = re.sub(r'\s+', ' ', subject).strip()
        
        return subject
    
    def _clean_content(self, content: str) -> str:
        """Bereinigt den E-Mail-Inhalt."""
        if not content:
            return ""
        
        # Entferne HTML-Tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Entferne überflüssige Leerzeichen und Zeilenumbrüche
        content = re.sub(r'\s+', ' ', content)
        
        # Entferne häufige E-Mail-Signaturen
        content = self._remove_signature(content)
        
        return content.strip()
    
    def _remove_signature(self, content: str) -> str:
        """Entfernt E-Mail-Signaturen aus dem Inhalt."""
        # Häufige Signaturen-Marker
        signature_markers = [
            r'--\s*\n',
            r'Best regards,',
            r'Mit freundlichen Grüßen,',
            r'Kind regards,',
            r'Yours sincerely,',
            r'Viele Grüße,',
            r'Liebe Grüße,',
            r'Beste Grüße,',
            r'Thanks,',
            r'Thank you,',
            r'Danke,',
            r'Vielen Dank,'
        ]
        
        for marker in signature_markers:
            parts = re.split(marker, content, flags=re.IGNORECASE)
            if len(parts) > 1:
                content = parts[0].strip()
                break
        
        return content
    
    def _create_preview(self, content: str, max_length: int = 200) -> str:
        """Erstellt eine Vorschau des E-Mail-Inhalts."""
        if not content:
            return "Kein Inhalt"
        
        # Entferne Zeilenumbrüche für Vorschau
        preview = re.sub(r'\s+', ' ', content)
        
        if len(preview) <= max_length:
            return preview
        
        return preview[:max_length] + "..."
    
    def _detect_priority(self, subject: str, content: str) -> str:
        """Erkennt die Priorität der E-Mail."""
        text = f"{subject} {content}".lower()
        
        # Hohe Priorität
        high_priority_keywords = [
            'urgent', 'dringend', 'wichtig', 'important', 'asap', 'sofort',
            'kritisch', 'critical', 'notfall', 'emergency', 'fehler', 'error'
        ]
        
        # Niedrige Priorität
        low_priority_keywords = [
            'newsletter', 'news', 'werbung', 'advertisement', 'spam',
            'automatisch', 'automatic', 'system', 'noreply', 'no-reply'
        ]
        
        for keyword in high_priority_keywords:
            if keyword in text:
                return "high"
        
        for keyword in low_priority_keywords:
            if keyword in text:
                return "low"
        
        return "normal"
    
    def _categorize_email(self, subject: str, content: str) -> str:
        """Kategorisiert die E-Mail basierend auf Inhalt."""
        text = f"{subject} {content}".lower()
        
        categories = {
            'support': ['support', 'hilfe', 'help', 'problem', 'issue', 'fehler', 'error'],
            'sales': ['verkauf', 'sale', 'preis', 'price', 'angebot', 'offer', 'kauf', 'buy'],
            'inquiry': ['anfrage', 'inquiry', 'frage', 'question', 'info', 'information'],
            'complaint': ['beschwerde', 'complaint', 'unzufrieden', 'dissatisfied', 'problem'],
            'confirmation': ['bestätigung', 'confirmation', 'bestätigen', 'confirm'],
            'newsletter': ['newsletter', 'news', 'update', 'aktualisierung'],
            'spam': ['spam', 'werbung', 'advertisement', 'casino', 'viagra', 'lottery']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return "general"
    
    def _needs_response(self, subject: str, content: str) -> bool:
        """Ermittelt, ob die E-Mail eine Antwort benötigt."""
        text = f"{subject} {content}".lower()
        
        # E-Mails, die keine Antwort benötigen
        no_response_keywords = [
            'newsletter', 'news', 'werbung', 'advertisement', 'spam',
            'automatisch', 'automatic', 'system', 'noreply', 'no-reply',
            'bestätigung', 'confirmation', 'receipt', 'quittung'
        ]
        
        for keyword in no_response_keywords:
            if keyword in text:
                return False
        
        # E-Mails, die definitiv eine Antwort benötigen
        response_keywords = [
            'frage', 'question', 'anfrage', 'inquiry', 'hilfe', 'help',
            'problem', 'issue', 'fehler', 'error', 'beschwerde', 'complaint'
        ]
        
        for keyword in response_keywords:
            if keyword in text:
                return True
        
        # Standardmäßig annehmen, dass eine Antwort benötigt wird
        return True
    
    def _is_internal_domain(self, domain: str) -> bool:
        """Prüft, ob es sich um eine interne Domain handelt."""
        internal_domains = [
            'company.com', 'firma.de', 'internal.local'
        ]
        
        return domain in internal_domains
    
    def _create_fallback_parsed_email(self, email_data: Dict) -> Dict:
        """Erstellt eine Fallback-version der geparsten E-Mail bei Fehlern."""
        return {
            'id': email_data.get('id', 'unknown'),
            'sender': {
                'full': email_data.get('sender', 'Unbekannter Absender'),
                'name': 'Unbekannter Absender',
                'email': '',
                'domain': '',
                'is_internal': False
            },
            'subject': email_data.get('subject', 'Kein Betreff'),
            'date': None,
            'content': email_data.get('content', ''),
            'content_preview': 'Fehler beim Parsen',
            'priority': 'normal',
            'category': 'general',
            'requires_response': True,
            'original_data': email_data
        }
    
    def extract_key_information(self, parsed_email: Dict) -> Dict:
        """Extrahiert wichtige Informationen aus der geparsten E-Mail."""
        return {
            'sender_name': parsed_email['sender']['name'],
            'sender_email': parsed_email['sender']['email'],
            'subject': parsed_email['subject'],
            'priority': parsed_email['priority'],
            'category': parsed_email['category'],
            'content_summary': self._summarize_content(parsed_email['content']),
            'action_required': parsed_email['requires_response']
        }
    
    def _summarize_content(self, content: str, max_sentences: int = 3) -> str:
        """Erstellt eine Zusammenfassung des Inhalts."""
        if not content:
            return "Kein Inhalt verfügbar"
        
        # Teile in Sätze auf
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Nimm die ersten max_sentences Sätze
        summary_sentences = sentences[:max_sentences]
        
        return '. '.join(summary_sentences) + ('.' if summary_sentences else '')

if __name__ == "__main__":
    # Test des E-Mail-Parsers
    logging.basicConfig(level=logging.INFO)
    parser = EmailParser()
    
    test_email = {
        'id': '1',
        'sender': 'Max Mustermann <max.mustermann@example.com>',
        'subject': 'RE: Wichtige Anfrage',
        'date': 'Mon, 1 Jan 2024 10:00:00 +0100',
        'content': 'Hallo, ich habe eine wichtige Frage zu Ihrem Produkt. Können Sie mir bitte antworten?'
    }
    
    parsed = parser.parse_email(test_email)
    print("Geparste E-Mail:")
    print(f"Absender: {parsed['sender']['name']} ({parsed['sender']['email']})")
    print(f"Betreff: {parsed['subject']}")
    print(f"Priorität: {parsed['priority']}")
    print(f"Kategorie: {parsed['category']}")
    print(f"Antwort erforderlich: {parsed['requires_response']}")
    print(f"Vorschau: {parsed['content_preview']}")