"""
E-Mail Analyzer für den Super-KI-Agenten
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import openai
from email_fetcher import EmailData

@dataclass
class EmailAnalysis:
    """Ergebnis der E-Mail-Analyse"""
    category: str
    sentiment: str
    language: str
    urgency: str
    required_action: str
    key_questions: List[str]
    key_concerns: List[str]
    confidence_level: float
    tone: str
    priority_score: float
    is_spam: bool
    requires_human: bool
    suggested_response_type: str
    extracted_info: Dict[str, Any]

class EmailAnalyzer:
    """KI-basierter E-Mail-Analyzer mit erweiterten Funktionen"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_ai_config()
        self.features_config = config_manager.get_features_config()
        self.logger = logging.getLogger(__name__)
        self._setup_openai()
        
        # Vordefinierte Kategorien
        self.categories = [
            "Support", "Sales", "Inquiry", "Complaint", "Feedback", 
            "Appointment", "Order", "Invoice", "General", "Spam"
        ]
        
        # Spam-Indikatoren
        self.spam_indicators = [
            "urgent", "limited time", "act now", "click here", "free money",
            "lottery", "inheritance", "viagra", "casino", "loan",
            "credit card", "password", "account suspended", "verify now"
        ]
    
    def _setup_openai(self):
        """Konfiguriert OpenAI Client"""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API Key nicht gefunden")
        
        openai.api_key = api_key
    
    def analyze_email(self, email_data: EmailData) -> EmailAnalysis:
        """Führt vollständige E-Mail-Analyse durch"""
        try:
            self.logger.info(f"Analysiere E-Mail: {email_data.subject}")
            
            # Grundlegende Analyse
            basic_analysis = self._basic_analysis(email_data)
            
            # KI-basierte Analyse
            ai_analysis = self._ai_analysis(email_data)
            
            # Kombiniere Ergebnisse
            analysis = self._combine_analysis(basic_analysis, ai_analysis, email_data)
            
            self.logger.info(f"Analyse abgeschlossen - Kategorie: {analysis.category}, Confidence: {analysis.confidence_level}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Fehler bei E-Mail-Analyse: {e}")
            return self._fallback_analysis(email_data)
    
    def _basic_analysis(self, email_data: EmailData) -> Dict[str, Any]:
        """Grundlegende regelbasierte Analyse"""
        analysis = {
            'language': self._detect_language(email_data.body),
            'is_spam': self._check_spam_indicators(email_data),
            'urgency': self._detect_urgency(email_data),
            'tone': self._detect_tone(email_data),
            'priority_score': 0.5
        }
        
        return analysis
    
    def _ai_analysis(self, email_data: EmailData) -> Dict[str, Any]:
        """KI-basierte Analyse mit GPT-4o"""
        try:
            prompt = self._build_analysis_prompt(email_data)
            
            response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für E-Mail-Analyse. Analysiere die E-Mail und gib eine strukturierte Antwort zurück."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_ai_response(ai_response)
            
        except Exception as e:
            self.logger.error(f"Fehler bei KI-Analyse: {e}")
            return {}
    
    def _build_analysis_prompt(self, email_data: EmailData) -> str:
        """Erstellt Prompt für KI-Analyse"""
        prompt = f"""
{self.config.analysis_prompts['content_analysis']}

E-Mail-Details:
Betreff: {email_data.subject}
Absender: {email_data.sender}
Empfänger: {email_data.recipient}
Datum: {email_data.date}
Inhalt: {email_data.body[:2000]}

Bitte analysiere diese E-Mail und gib eine JSON-Antwort zurück mit folgender Struktur:
{{
    "category": "Kategorie der E-Mail",
    "sentiment": "positiv/neutral/negativ",
    "language": "DE/EN/FR/ES",
    "urgency": "hoch/mittel/niedrig",
    "required_action": "Beschreibung der erforderlichen Aktion",
    "key_questions": ["Frage 1", "Frage 2"],
    "key_concerns": ["Anliegen 1", "Anliegen 2"],
    "confidence_level": 0.85,
    "tone": "formal/informal/freundlich/aggressiv",
    "priority_score": 0.7,
    "is_spam": false,
    "requires_human": false,
    "suggested_response_type": "auto/human/hybrid",
    "extracted_info": {{
        "contact_info": "Kontaktdaten falls vorhanden",
        "deadlines": "Deadlines falls vorhanden",
        "specific_requests": "Spezifische Anfragen"
    }}
}}
"""
        return prompt
    
    def _parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parst KI-Antwort"""
        try:
            # Suche nach JSON in der Antwort
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                self.logger.warning("Kein JSON in KI-Antwort gefunden")
                return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Fehler beim Parsen der KI-Antwort: {e}")
            return {}
    
    def _combine_analysis(self, basic: Dict[str, Any], ai: Dict[str, Any], email_data: EmailData) -> EmailAnalysis:
        """Kombiniert grundlegende und KI-Analyse"""
        
        # Verwende KI-Ergebnisse wenn verfügbar, sonst Grundlegende
        category = ai.get('category', self._categorize_email(email_data))
        sentiment = ai.get('sentiment', 'neutral')
        language = ai.get('language', basic.get('language', 'DE'))
        urgency = ai.get('urgency', basic.get('urgency', 'mittel'))
        required_action = ai.get('required_action', 'Keine spezifische Aktion erforderlich')
        key_questions = ai.get('key_questions', [])
        key_concerns = ai.get('key_concerns', [])
        confidence_level = ai.get('confidence_level', 0.5)
        tone = ai.get('tone', basic.get('tone', 'neutral'))
        priority_score = ai.get('priority_score', basic.get('priority_score', 0.5))
        is_spam = ai.get('is_spam', basic.get('is_spam', False))
        requires_human = ai.get('requires_human', False)
        suggested_response_type = ai.get('suggested_response_type', 'auto')
        extracted_info = ai.get('extracted_info', {})
        
        # Bestimme ob menschliche Intervention erforderlich
        if confidence_level < self.config.confidence_thresholds['require_human']:
            requires_human = True
        
        if is_spam:
            requires_human = False
            suggested_response_type = 'ignore'
        
        return EmailAnalysis(
            category=category,
            sentiment=sentiment,
            language=language,
            urgency=urgency,
            required_action=required_action,
            key_questions=key_questions,
            key_concerns=key_concerns,
            confidence_level=confidence_level,
            tone=tone,
            priority_score=priority_score,
            is_spam=is_spam,
            requires_human=requires_human,
            suggested_response_type=suggested_response_type,
            extracted_info=extracted_info
        )
    
    def _detect_language(self, text: str) -> str:
        """Erkennt Sprache des Textes"""
        # Einfache Spracherkennung basierend auf Schlüsselwörtern
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['the', 'and', 'or', 'but', 'is', 'are', 'was', 'were']):
            return 'EN'
        elif any(word in text_lower for word in ['le', 'la', 'les', 'et', 'ou', 'est', 'sont']):
            return 'FR'
        elif any(word in text_lower for word in ['el', 'la', 'los', 'las', 'y', 'o', 'es', 'son']):
            return 'ES'
        else:
            return 'DE'  # Standard
    
    def _check_spam_indicators(self, email_data: EmailData) -> bool:
        """Prüft auf Spam-Indikatoren"""
        text = f"{email_data.subject} {email_data.body}".lower()
        
        # Zähle Spam-Indikatoren
        spam_count = sum(1 for indicator in self.spam_indicators if indicator in text)
        
        # Prüfe auf verdächtige Muster
        suspicious_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Viele E-Mail-Adressen
            r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP-Adressen
            r'\b(?:https?://)?(?:www\.)?[^\s<>"]+\.[^\s<>"]+\b'  # Viele URLs
        ]
        
        pattern_count = 0
        for pattern in suspicious_patterns:
            matches = re.findall(pattern, text)
            if len(matches) > 3:  # Mehr als 3 Matches sind verdächtig
                pattern_count += 1
        
        return spam_count >= 2 or pattern_count >= 2
    
    def _detect_urgency(self, email_data: EmailData) -> str:
        """Erkennt Dringlichkeit"""
        text = f"{email_data.subject} {email_data.body}".lower()
        
        urgent_words = ['urgent', 'dringend', 'sofort', 'asap', 'emergency', 'notfall']
        high_urgency_words = ['critical', 'kritisch', 'important', 'wichtig', 'priority', 'priorität']
        
        if any(word in text for word in urgent_words):
            return 'hoch'
        elif any(word in text for word in high_urgency_words):
            return 'mittel'
        else:
            return 'niedrig'
    
    def _detect_tone(self, email_data: EmailData) -> str:
        """Erkennt Ton der E-Mail"""
        text = f"{email_data.subject} {email_data.body}".lower()
        
        formal_words = ['sehr geehrte', 'dear', 'respectfully', 'best regards']
        aggressive_words = ['angry', 'wütend', 'furious', 'wütend', 'complaint', 'beschwerde']
        friendly_words = ['danke', 'thank you', 'freundlich', 'kindly', 'please', 'bitte']
        
        if any(word in text for word in formal_words):
            return 'formal'
        elif any(word in text for word in aggressive_words):
            return 'aggressiv'
        elif any(word in text for word in friendly_words):
            return 'freundlich'
        else:
            return 'neutral'
    
    def _categorize_email(self, email_data: EmailData) -> str:
        """Kategorisiert E-Mail basierend auf Inhalt"""
        text = f"{email_data.subject} {email_data.body}".lower()
        
        category_keywords = {
            'Support': ['help', 'hilfe', 'support', 'problem', 'issue', 'error'],
            'Sales': ['buy', 'kaufen', 'purchase', 'order', 'bestellung', 'price', 'preis'],
            'Inquiry': ['question', 'frage', 'inquiry', 'anfrage', 'information'],
            'Complaint': ['complaint', 'beschwerde', 'angry', 'wütend', 'unhappy'],
            'Feedback': ['feedback', 'review', 'bewertung', 'opinion', 'meinung'],
            'Appointment': ['appointment', 'termin', 'meeting', 'treffen', 'schedule'],
            'Order': ['order', 'bestellung', 'invoice', 'rechnung', 'payment'],
            'Invoice': ['invoice', 'rechnung', 'bill', 'zahlung', 'payment'],
            'Spam': ['lottery', 'viagra', 'casino', 'loan', 'credit card']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'General'
    
    def _fallback_analysis(self, email_data: EmailData) -> EmailAnalysis:
        """Fallback-Analyse bei Fehlern"""
        return EmailAnalysis(
            category='General',
            sentiment='neutral',
            language='DE',
            urgency='niedrig',
            required_action='Manuelle Überprüfung erforderlich',
            key_questions=[],
            key_concerns=[],
            confidence_level=0.1,
            tone='neutral',
            priority_score=0.5,
            is_spam=False,
            requires_human=True,
            suggested_response_type='human',
            extracted_info={}
        )
    
    def extract_contact_info(self, email_data: EmailData) -> Dict[str, str]:
        """Extrahiert Kontaktinformationen"""
        text = email_data.body
        
        # E-Mail-Adressen
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Telefonnummern
        phone_pattern = r'(\+?[\d\s\-\(\)]{7,})'
        phones = re.findall(phone_pattern, text)
        
        # Namen (einfache Erkennung)
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        
        return {
            'emails': emails,
            'phones': phones,
            'names': names
        }
    
    def should_auto_approve(self, analysis: EmailAnalysis) -> bool:
        """Bestimmt ob automatische Genehmigung möglich ist"""
        return (
            analysis.confidence_level >= self.config.confidence_thresholds['auto_approve'] and
            not analysis.is_spam and
            not analysis.requires_human and
            analysis.suggested_response_type == 'auto'
        )