import re
import logging
from typing import Dict, List, Optional
from email.utils import parseaddr, parsedate_to_datetime
from datetime import datetime

class EmailParser:
    """Analysiert und strukturiert E-Mail-Inhalte"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_email(self, email_data: Dict) -> Dict:
        """Parst eine E-Mail und extrahiert alle wichtigen Informationen"""
        try:
            parsed_email = {
                'id': email_data.get('id', ''),
                'subject': self._clean_subject(email_data.get('subject', '')),
                'sender': self._parse_sender(email_data.get('sender', '')),
                'date': self._parse_date(email_data.get('date', '')),
                'content': self._clean_content(email_data.get('content', '')),
                'message_id': email_data.get('message_id', ''),
                'priority': self._detect_priority(email_data.get('subject', ''), email_data.get('content', '')),
                'category': self._categorize_email(email_data.get('subject', ''), email_data.get('content', '')),
                'language': self._detect_language(email_data.get('content', '')),
                'sentiment': self._analyze_sentiment(email_data.get('content', '')),
                'requires_response': self._needs_response(email_data.get('subject', ''), email_data.get('content', '')),
                'original_data': email_data
            }
            
            self.logger.info(f"E-Mail geparst: {parsed_email['subject']} (Kategorie: {parsed_email['category']})")
            return parsed_email
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der E-Mail: {e}")
            return email_data
    
    def _clean_subject(self, subject: str) -> str:
        """Bereinigt den Betreff"""
        if not subject:
            return "Kein Betreff"
        
        # Entferne häufige Präfixe
        subject = re.sub(r'^(Re|Fwd|Fw|AW|Ant):\s*', '', subject, flags=re.IGNORECASE)
        
        # Entferne überflüssige Leerzeichen
        subject = re.sub(r'\s+', ' ', subject).strip()
        
        return subject
    
    def _parse_sender(self, sender: str) -> Dict:
        """Parst Absender-Informationen"""
        try:
            name, email = parseaddr(sender)
            
            # Extrahiere Domain
            domain = ""
            if '@' in email:
                domain = email.split('@')[1]
            
            return {
                'full': sender,
                'name': name.strip() if name else "",
                'email': email.strip() if email else "",
                'domain': domain
            }
        except Exception as e:
            self.logger.warning(f"Fehler beim Parsen des Absenders: {e}")
            return {
                'full': sender,
                'name': "",
                'email': "",
                'domain': ""
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parst das Datum der E-Mail"""
        try:
            if date_str:
                return parsedate_to_datetime(date_str)
            return None
        except Exception as e:
            self.logger.warning(f"Fehler beim Parsen des Datums: {e}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """Bereinigt den E-Mail-Inhalt"""
        if not content:
            return ""
        
        # Entferne HTML-Tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Entferne überflüssige Leerzeichen und Zeilenumbrüche
        content = re.sub(r'\s+', ' ', content)
        
        # Entferne häufige E-Mail-Signaturen
        signature_patterns = [
            r'--\s*\n.*',  # Signature nach --
            r'Best regards,.*',
            r'Mit freundlichen Grüßen.*',
            r'Kind regards,.*',
            r'Thanks,.*',
            r'Thank you,.*'
        ]
        
        for pattern in signature_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        return content.strip()
    
    def _detect_priority(self, subject: str, content: str) -> str:
        """Erkennt die Priorität der E-Mail"""
        text = f"{subject} {content}".lower()
        
        # Hohe Priorität
        high_priority_keywords = ['urgent', 'dringend', 'asap', 'sofort', 'wichtig', 'important', 'kritisch', 'critical']
        if any(keyword in text for keyword in high_priority_keywords):
            return "high"
        
        # Niedrige Priorität
        low_priority_keywords = ['newsletter', 'news', 'update', 'info', 'information', 'werbung', 'advertisement']
        if any(keyword in text for keyword in low_priority_keywords):
            return "low"
        
        return "normal"
    
    def _categorize_email(self, subject: str, content: str) -> str:
        """Kategorisiert die E-Mail"""
        text = f"{subject} {content}".lower()
        
        categories = {
            'support': ['support', 'hilfe', 'help', 'problem', 'issue', 'bug', 'fehler'],
            'sales': ['sales', 'verkauf', 'preis', 'price', 'angebot', 'offer', 'kauf', 'buy'],
            'inquiry': ['anfrage', 'inquiry', 'frage', 'question', 'info', 'information'],
            'complaint': ['beschwerde', 'complaint', 'unzufrieden', 'dissatisfied', 'problem'],
            'newsletter': ['newsletter', 'news', 'update', 'newsletter'],
            'spam': ['viagra', 'casino', 'lottery', 'winner', 'free money', 'kostenlos geld'],
            'personal': ['meeting', 'treffen', 'appointment', 'termin', 'call', 'anruf']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "general"
    
    def _detect_language(self, content: str) -> str:
        """Erkennt die Sprache der E-Mail"""
        if not content:
            return "unknown"
        
        # Einfache Spracherkennung basierend auf häufigen Wörtern
        german_words = ['der', 'die', 'das', 'und', 'oder', 'mit', 'für', 'von', 'zu', 'in', 'auf', 'ist', 'sind', 'wird', 'haben', 'sein']
        english_words = ['the', 'and', 'or', 'with', 'for', 'from', 'to', 'in', 'on', 'is', 'are', 'will', 'have', 'be']
        
        content_lower = content.lower()
        
        german_count = sum(1 for word in german_words if word in content_lower)
        english_count = sum(1 for word in english_words if word in content_lower)
        
        if german_count > english_count:
            return "german"
        elif english_count > german_count:
            return "english"
        else:
            return "unknown"
    
    def _analyze_sentiment(self, content: str) -> str:
        """Analysiert die Stimmung der E-Mail"""
        if not content:
            return "neutral"
        
        content_lower = content.lower()
        
        # Positive Wörter
        positive_words = ['danke', 'thanks', 'thank you', 'gut', 'good', 'great', 'excellent', 'wunderbar', 'fantastic', 'super', 'toll']
        # Negative Wörter
        negative_words = ['schlecht', 'bad', 'terrible', 'awful', 'problem', 'issue', 'fehler', 'error', 'unzufrieden', 'dissatisfied', 'wütend', 'angry']
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def _needs_response(self, subject: str, content: str) -> bool:
        """Prüft, ob die E-Mail eine Antwort benötigt"""
        text = f"{subject} {content}".lower()
        
        # E-Mails, die wahrscheinlich keine Antwort benötigen
        no_response_patterns = [
            'newsletter',
            'news',
            'update',
            'notification',
            'automatisch',
            'automatic',
            'system',
            'noreply',
            'no-reply',
            'donotreply',
            'do-not-reply'
        ]
        
        if any(pattern in text for pattern in no_response_patterns):
            return False
        
        # E-Mails mit direkten Fragen oder Aufforderungen
        question_patterns = [
            '?',
            'frage',
            'question',
            'können sie',
            'can you',
            'würden sie',
            'would you',
            'bitte',
            'please'
        ]
        
        if any(pattern in text for pattern in question_patterns):
            return True
        
        return True  # Standardmäßig annehmen, dass eine Antwort benötigt wird
    
    def extract_key_information(self, parsed_email: Dict) -> Dict:
        """Extrahiert wichtige Informationen für die Antwortgenerierung"""
        return {
            'sender_name': parsed_email['sender']['name'],
            'sender_email': parsed_email['sender']['email'],
            'subject': parsed_email['subject'],
            'content': parsed_email['content'],
            'category': parsed_email['category'],
            'priority': parsed_email['priority'],
            'language': parsed_email['language'],
            'sentiment': parsed_email['sentiment'],
            'requires_response': parsed_email['requires_response']
        }


if __name__ == "__main__":
    # Test des E-Mail-Parsers
    logging.basicConfig(level=logging.INFO)
    parser = EmailParser()
    
    test_email = {
        'id': '1',
        'subject': 'Re: Wichtige Anfrage zu unserem Produkt',
        'sender': 'Max Mustermann <max.mustermann@example.com>',
        'date': 'Mon, 15 Jan 2024 10:30:00 +0100',
        'content': 'Hallo, ich habe eine Frage zu Ihrem Produkt. Können Sie mir bitte mehr Informationen geben? Vielen Dank!',
        'message_id': '<test@example.com>'
    }
    
    parsed = parser.parse_email(test_email)
    print("Geparste E-Mail:")
    print(f"Betreff: {parsed['subject']}")
    print(f"Absender: {parsed['sender']['name']} ({parsed['sender']['email']})")
    print(f"Kategorie: {parsed['category']}")
    print(f"Priorität: {parsed['priority']}")
    print(f"Sprache: {parsed['language']}")
    print(f"Stimmung: {parsed['sentiment']}")
    print(f"Benötigt Antwort: {parsed['requires_response']}")