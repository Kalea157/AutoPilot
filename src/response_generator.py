"""
Response Generator für den Super-KI-Agenten
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import openai
from email_fetcher import EmailData
from email_analyzer import EmailAnalysis

@dataclass
class GeneratedResponse:
    """Generierte Antwort"""
    subject: str
    body: str
    language: str
    tone: str
    confidence_level: float
    suggested_improvements: List[str]
    is_ready_to_send: bool
    requires_review: bool

class ResponseGenerator:
    """KI-basierter Response Generator mit GPT-4o"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_ai_config()
        self.logger = logging.getLogger(__name__)
        self._setup_openai()
        
        # Response Templates für verschiedene Kategorien
        self.response_templates = {
            'Support': {
                'formal': "Vielen Dank für Ihre Anfrage. Wir werden uns umgehend um Ihr Anliegen kümmern.",
                'friendly': "Hallo! Danke für Ihre Nachricht. Wir helfen Ihnen gerne weiter!",
                'aggressive': "Wir verstehen Ihre Frustration und werden das Problem sofort angehen."
            },
            'Sales': {
                'formal': "Vielen Dank für Ihr Interesse an unseren Produkten.",
                'friendly': "Hallo! Wir freuen uns über Ihr Interesse!",
                'aggressive': "Wir verstehen Ihre Dringlichkeit und werden schnell reagieren."
            },
            'Inquiry': {
                'formal': "Vielen Dank für Ihre Anfrage. Hier sind die gewünschten Informationen.",
                'friendly': "Hallo! Gerne beantworte ich Ihre Fragen.",
                'aggressive': "Wir werden Ihre Anfrage umgehend bearbeiten."
            }
        }
    
    def _setup_openai(self):
        """Konfiguriert OpenAI Client"""
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API Key nicht gefunden")
        
        openai.api_key = api_key
    
    def generate_response(self, email_data: EmailData, analysis: EmailAnalysis) -> GeneratedResponse:
        """Generiert eine intelligente Antwort auf die E-Mail"""
        try:
            self.logger.info(f"Generiere Antwort für: {email_data.subject}")
            
            # Erstelle Prompt für Antwortgenerierung
            prompt = self._build_response_prompt(email_data, analysis)
            
            # Generiere Antwort mit GPT-4o
            response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "Du bist ein professioneller E-Mail-Assistent. Erstelle hilfreiche, freundliche und präzise Antworten."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_generated_response(ai_response, analysis)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Antwortgenerierung: {e}")
            return self._fallback_response(email_data, analysis)
    
    def _build_response_prompt(self, email_data: EmailData, analysis: EmailAnalysis) -> str:
        """Erstellt Prompt für Antwortgenerierung"""
        
        # Bestimme Sprache für Prompt
        language_instructions = {
            'DE': 'Antworte auf Deutsch',
            'EN': 'Reply in English',
            'FR': 'Répondez en français',
            'ES': 'Responda en español'
        }
        
        language_instruction = language_instructions.get(analysis.language, 'Antworte auf Deutsch')
        
        # Bestimme Ton-Anweisung
        tone_instructions = {
            'formal': 'Verwende einen formellen, professionellen Ton',
            'friendly': 'Verwende einen freundlichen, herzlichen Ton',
            'aggressive': 'Verwende einen verständnisvollen, lösungsorientierten Ton',
            'neutral': 'Verwende einen neutralen, professionellen Ton'
        }
        
        tone_instruction = tone_instructions.get(analysis.tone, 'Verwende einen professionellen Ton')
        
        prompt = f"""
{self.config.analysis_prompts['response_generation']}

{language_instruction}. {tone_instruction}.

Original E-Mail:
Betreff: {email_data.subject}
Absender: {email_data.sender}
Inhalt: {email_data.body}

Analyse:
- Kategorie: {analysis.category}
- Stimmung: {analysis.sentiment}
- Dringlichkeit: {analysis.urgency}
- Erforderte Aktion: {analysis.required_action}
- Schlüsselfragen: {', '.join(analysis.key_questions)}
- Schlüsselanliegen: {', '.join(analysis.key_concerns)}

Erstelle eine professionelle Antwort mit:
1. Angemessener Anrede
2. Bezugnahme auf das Anliegen
3. Hilfreiche Antwort oder Lösung
4. Professionelle Grußformel

Antworte im folgenden JSON-Format:
{{
    "subject": "Betreff der Antwort",
    "body": "Vollständiger Antworttext",
    "language": "{analysis.language}",
    "tone": "{analysis.tone}",
    "confidence_level": 0.85,
    "suggested_improvements": ["Verbesserung 1", "Verbesserung 2"],
    "is_ready_to_send": true,
    "requires_review": false
}}
"""
        return prompt
    
    def _parse_generated_response(self, ai_response: str, analysis: EmailAnalysis) -> GeneratedResponse:
        """Parst die generierte KI-Antwort"""
        try:
            # Suche nach JSON in der Antwort
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                response_data = json.loads(json_str)
                
                return GeneratedResponse(
                    subject=response_data.get('subject', 'Re: Antwort'),
                    body=response_data.get('body', ''),
                    language=response_data.get('language', analysis.language),
                    tone=response_data.get('tone', analysis.tone),
                    confidence_level=response_data.get('confidence_level', 0.5),
                    suggested_improvements=response_data.get('suggested_improvements', []),
                    is_ready_to_send=response_data.get('is_ready_to_send', False),
                    requires_review=response_data.get('requires_review', True)
                )
            else:
                # Fallback: Verwende gesamte Antwort als Body
                return GeneratedResponse(
                    subject=f"Re: Antwort",
                    body=ai_response,
                    language=analysis.language,
                    tone=analysis.tone,
                    confidence_level=0.3,
                    suggested_improvements=["Manuelle Überprüfung erforderlich"],
                    is_ready_to_send=False,
                    requires_review=True
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Fehler beim Parsen der generierten Antwort: {e}")
            return self._fallback_response(None, analysis)
    
    def _fallback_response(self, email_data: Optional[EmailData], analysis: EmailAnalysis) -> GeneratedResponse:
        """Fallback-Antwort bei Fehlern"""
        if email_data:
            subject = f"Re: {email_data.subject}"
        else:
            subject = "Re: Ihre Nachricht"
        
        # Verwende Template basierend auf Kategorie und Ton
        template = self.response_templates.get(analysis.category, {}).get(analysis.tone, 
            "Vielen Dank für Ihre Nachricht. Wir werden uns umgehend um Ihr Anliegen kümmern.")
        
        return GeneratedResponse(
            subject=subject,
            body=template,
            language=analysis.language,
            tone=analysis.tone,
            confidence_level=0.1,
            suggested_improvements=["Manuelle Überprüfung erforderlich"],
            is_ready_to_send=False,
            requires_review=True
        )
    
    def improve_response(self, response: GeneratedResponse, feedback: str) -> GeneratedResponse:
        """Verbessert eine Antwort basierend auf Feedback"""
        try:
            prompt = f"""
Verbessere diese E-Mail-Antwort basierend auf dem Feedback:

Original Antwort:
{response.body}

Feedback:
{feedback}

Erstelle eine verbesserte Version und gib sie im JSON-Format zurück:
{{
    "body": "Verbesserte Antwort",
    "confidence_level": 0.9,
    "suggested_improvements": [],
    "is_ready_to_send": true,
    "requires_review": false
}}
"""
            
            ai_response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für E-Mail-Kommunikation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            improved_data = json.loads(ai_response.choices[0].message.content)
            
            return GeneratedResponse(
                subject=response.subject,
                body=improved_data.get('body', response.body),
                language=response.language,
                tone=response.tone,
                confidence_level=improved_data.get('confidence_level', response.confidence_level),
                suggested_improvements=improved_data.get('suggested_improvements', []),
                is_ready_to_send=improved_data.get('is_ready_to_send', response.is_ready_to_send),
                requires_review=improved_data.get('requires_review', response.requires_review)
            )
            
        except Exception as e:
            self.logger.error(f"Fehler bei Antwortverbesserung: {e}")
            return response
    
    def generate_multilingual_response(self, email_data: EmailData, analysis: EmailAnalysis, target_language: str) -> GeneratedResponse:
        """Generiert Antwort in spezifischer Sprache"""
        try:
            prompt = f"""
Generiere eine Antwort auf diese E-Mail in {target_language}:

Original E-Mail:
Betreff: {email_data.subject}
Inhalt: {email_data.body}

Analyse:
- Kategorie: {analysis.category}
- Stimmung: {analysis.sentiment}
- Erforderte Aktion: {analysis.required_action}

Erstelle eine professionelle Antwort in {target_language}.
"""
            
            response = openai.ChatCompletion.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": f"Du bist ein professioneller E-Mail-Assistent. Antworte in {target_language}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            
            ai_response = response.choices[0].message.content
            
            return GeneratedResponse(
                subject=f"Re: {email_data.subject}",
                body=ai_response,
                language=target_language,
                tone=analysis.tone,
                confidence_level=0.8,
                suggested_improvements=[],
                is_ready_to_send=True,
                requires_review=False
            )
            
        except Exception as e:
            self.logger.error(f"Fehler bei mehrsprachiger Antwortgenerierung: {e}")
            return self._fallback_response(email_data, analysis)
    
    def validate_response(self, response: GeneratedResponse) -> Tuple[bool, List[str]]:
        """Validiert eine generierte Antwort"""
        issues = []
        
        # Prüfe Länge
        if len(response.body) < 10:
            issues.append("Antwort ist zu kurz")
        
        if len(response.body) > 2000:
            issues.append("Antwort ist zu lang")
        
        # Prüfe auf unangemessene Inhalte
        inappropriate_words = ['spam', 'lottery', 'viagra', 'casino']
        if any(word in response.body.lower() for word in inappropriate_words):
            issues.append("Antwort enthält unangemessene Inhalte")
        
        # Prüfe Struktur
        if not any(word in response.body.lower() for word in ['danke', 'thank', 'merci', 'gracias']):
            issues.append("Antwort sollte Dankbarkeit ausdrücken")
        
        # Prüfe Professionalität
        if any(word in response.body.lower() for word in ['hey', 'hi', 'hello']):
            if response.tone == 'formal':
                issues.append("Formeller Ton sollte verwendet werden")
        
        return len(issues) == 0, issues
    
    def get_response_template(self, category: str, tone: str) -> str:
        """Gibt Template für bestimmte Kategorie und Ton zurück"""
        return self.response_templates.get(category, {}).get(tone, 
            "Vielen Dank für Ihre Nachricht. Wir werden uns umgehend um Ihr Anliegen kümmern.")
    
    def should_auto_send(self, response: GeneratedResponse, analysis: EmailAnalysis) -> bool:
        """Bestimmt ob Antwort automatisch gesendet werden kann"""
        is_valid, issues = self.validate_response(response)
        
        return (
            response.is_ready_to_send and
            not response.requires_review and
            response.confidence_level >= 0.8 and
            is_valid and
            not analysis.requires_human
        )