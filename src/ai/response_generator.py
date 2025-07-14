"""
Response Generator - GPT-4o-basierte E-Mail-Antwort-Generierung
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import structlog
import asyncio
from openai import AsyncOpenAI

logger = structlog.get_logger(__name__)


@dataclass
class GeneratedResponse:
    """Datenklasse für generierte Antworten"""
    content: str
    subject: str
    confidence: float
    tone: str
    language: str
    length: str  # short, medium, long
    includes_greeting: bool
    includes_signature: bool
    suggested_follow_up: Optional[str] = None


class ResponseGenerator:
    """GPT-4o-basierter Antwort-Generator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = AsyncOpenAI(api_key=config['api_key'])
        self.model = config['model']
        self.max_tokens = config['max_tokens']
        self.temperature = config['temperature']
        self.system_prompt = config['system_prompt']
        
        # Antwort-Templates für verschiedene Strategien
        self.response_templates = {
            'formal': {
                'greeting': 'Sehr geehrte Damen und Herren,',
                'closing': 'Mit freundlichen Grüßen',
                'tone': 'professionell und höflich'
            },
            'casual': {
                'greeting': 'Hallo,',
                'closing': 'Viele Grüße',
                'tone': 'freundlich und entspannt'
            },
            'apologetic': {
                'greeting': 'Sehr geehrte Damen und Herren,',
                'closing': 'Mit freundlichen Grüßen',
                'tone': 'entschuldigend und lösungsorientiert'
            },
            'informative': {
                'greeting': 'Guten Tag,',
                'closing': 'Mit freundlichen Grüßen',
                'tone': 'klar und informativ'
            }
        }
    
    async def generate_response(self, original_email: Dict[str, Any], 
                              analysis: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> GeneratedResponse:
        """Generiert eine E-Mail-Antwort basierend auf Analyse"""
        try:
            # Erstelle strukturierten Prompt
            prompt = self._create_response_prompt(original_email, analysis, context)
            
            # GPT-4o Antwort-Generierung
            response = await self._call_gpt4o(prompt)
            
            # Parse Response
            response_data = self._parse_response(response)
            
            # Erstelle GeneratedResponse Objekt
            generated_response = GeneratedResponse(
                content=response_data.get('content', ''),
                subject=response_data.get('subject', ''),
                confidence=response_data.get('confidence', 0.8),
                tone=response_data.get('tone', 'standard'),
                language=response_data.get('language', 'de'),
                length=response_data.get('length', 'medium'),
                includes_greeting=response_data.get('includes_greeting', True),
                includes_signature=response_data.get('includes_signature', True),
                suggested_follow_up=response_data.get('suggested_follow_up')
            )
            
            logger.info("Response generated successfully", 
                       confidence=generated_response.confidence,
                       tone=generated_response.tone,
                       length=generated_response.length)
            
            return generated_response
            
        except Exception as e:
            logger.error("Failed to generate response", error=str(e))
            # Fallback-Antwort
            return self._fallback_response(original_email, analysis)
    
    def _create_response_prompt(self, original_email: Dict[str, Any], 
                              analysis: Dict[str, Any], 
                              context: Optional[Dict[str, Any]]) -> str:
        """Erstellt strukturierten Prompt für Antwort-Generierung"""
        
        # Extrahiere relevante Informationen
        sender = original_email.get('sender', '')
        subject = original_email.get('subject', '')
        content = original_email.get('content', '')
        
        category = analysis.get('category', 'general')
        urgency = analysis.get('urgency', 5)
        sentiment = analysis.get('sentiment', 'neutral')
        response_strategy = analysis.get('response_strategy', 'standard')
        key_questions = analysis.get('key_questions', [])
        key_tasks = analysis.get('key_tasks', [])
        
        # Wähle Template
        template = self.response_templates.get(response_strategy, self.response_templates['formal'])
        
        prompt = f"""
{self.system_prompt}

Generiere eine professionelle E-Mail-Antwort basierend auf folgenden Informationen:

ORIGINALE E-MAIL:
Von: {sender}
Betreff: {subject}
Inhalt: {content}

ANALYSE:
- Kategorie: {category}
- Dringlichkeit: {urgency}/10
- Stimmung: {sentiment}
- Antwort-Strategie: {response_strategy}
- Schlüsselfragen: {', '.join(key_questions)}
- Schlüsselaufgaben: {', '.join(key_tasks)}

KONTEXT:
{self._format_context(context) if context else 'Kein zusätzlicher Kontext verfügbar'}

ANFORDERUNGEN:
- Ton: {template['tone']}
- Sprache: Deutsch (außer bei englischen Original-E-Mails)
- Länge: Angemessen für die Dringlichkeit und Kategorie
- Struktur: Begrüßung, Hauptinhalt, Schluss, Signatur
- Beantworte alle gestellten Fragen
- Erwähne alle relevanten Aufgaben

Antworte NUR mit einem gültigen JSON-Objekt:
{{
    "content": "Vollständiger E-Mail-Inhalt mit Begrüßung und Signatur",
    "subject": "Betreff für die Antwort (Re: Original-Betreff)",
    "confidence": 0.0-1.0,
    "tone": "formal|casual|apologetic|informative",
    "language": "de|en",
    "length": "short|medium|long",
    "includes_greeting": true/false,
    "includes_signature": true/false,
    "suggested_follow_up": "Optional: Vorgeschlagene Nachfolgeaktion"
}}
"""
        return prompt
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formatiert Kontext für Prompt"""
        if not context:
            return ""
        
        context_parts = []
        if 'previous_emails' in context:
            context_parts.append(f"Vorherige E-Mails: {len(context['previous_emails'])}")
        if 'user_preferences' in context:
            context_parts.append(f"Benutzereinstellungen: {context['user_preferences']}")
        if 'company_info' in context:
            context_parts.append(f"Firmeninfo: {context['company_info']}")
        
        return "\n".join(context_parts)
    
    async def _call_gpt4o(self, prompt: str) -> str:
        """Ruft GPT-4o API für Antwort-Generierung auf"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du bist ein professioneller E-Mail-Assistent. Antworte nur mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("GPT-4o response generation failed", error=str(e))
            raise
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parst GPT-4o Response"""
        try:
            # Entferne mögliche Markdown-Formatierung
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            return json.loads(clean_response.strip())
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse response JSON", error=str(e), response=response)
            raise
    
    def _fallback_response(self, original_email: Dict[str, Any], 
                          analysis: Dict[str, Any]) -> GeneratedResponse:
        """Fallback-Antwort bei API-Fehlern"""
        logger.warning("Using fallback response generation")
        
        sender = original_email.get('sender', '')
        subject = original_email.get('subject', '')
        category = analysis.get('category', 'general')
        
        # Einfache Template-basierte Antwort
        if category == 'question':
            content = f"""Sehr geehrte Damen und Herren,

vielen Dank für Ihre E-Mail. Ich werde Ihre Anfrage gerne bearbeiten und mich zeitnah bei Ihnen melden.

Mit freundlichen Grüßen
Ihr Team"""
        elif category == 'complaint':
            content = f"""Sehr geehrte Damen und Herren,

vielen Dank für Ihre Nachricht. Ich verstehe Ihr Anliegen und entschuldige mich für etwaige Unannehmlichkeiten. Ich werde das Problem umgehend untersuchen und eine Lösung für Sie finden.

Mit freundlichen Grüßen
Ihr Team"""
        else:
            content = f"""Sehr geehrte Damen und Herren,

vielen Dank für Ihre E-Mail. Ich habe Ihre Nachricht erhalten und werde sie entsprechend bearbeiten.

Mit freundlichen Grüßen
Ihr Team"""
        
        return GeneratedResponse(
            content=content,
            subject=f"Re: {subject}",
            confidence=0.6,
            tone='formal',
            language='de',
            length='medium',
            includes_greeting=True,
            includes_signature=True
        )
    
    async def generate_multiple_options(self, original_email: Dict[str, Any], 
                                      analysis: Dict[str, Any], 
                                      count: int = 3) -> List[GeneratedResponse]:
        """Generiert mehrere Antwort-Optionen"""
        tasks = []
        for i in range(count):
            # Variiere Temperature für verschiedene Optionen
            temp_variation = self.temperature + (i * 0.1)
            task = asyncio.create_task(
                self._generate_with_temperature(original_email, analysis, temp_variation)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtere erfolgreiche Ergebnisse
        responses = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Multiple option generation failed", error=str(result))
            else:
                responses.append(result)
        
        return responses
    
    async def _generate_with_temperature(self, original_email: Dict[str, Any], 
                                       analysis: Dict[str, Any], 
                                       temperature: float) -> GeneratedResponse:
        """Generiert Antwort mit spezifischer Temperature"""
        try:
            # Temporär Temperature ändern
            original_temp = self.temperature
            self.temperature = temperature
            
            response = await self.generate_response(original_email, analysis)
            
            # Temperature zurücksetzen
            self.temperature = original_temp
            
            return response
            
        except Exception as e:
            logger.error("Temperature variation generation failed", error=str(e))
            raise
    
    def validate_response(self, response: GeneratedResponse) -> Dict[str, Any]:
        """Validiert generierte Antwort"""
        validation = {
            'is_valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # Prüfe Länge
        if len(response.content) < 50:
            validation['issues'].append('Antwort zu kurz')
            validation['is_valid'] = False
        
        if len(response.content) > 2000:
            validation['issues'].append('Antwort zu lang')
            validation['suggestions'].append('Antwort kürzen')
        
        # Prüfe Struktur
        if not response.includes_greeting:
            validation['suggestions'].append('Begrüßung hinzufügen')
        
        if not response.includes_signature:
            validation['suggestions'].append('Signatur hinzufügen')
        
        # Prüfe Confidence
        if response.confidence < 0.7:
            validation['issues'].append('Niedrige Konfidenz')
            validation['suggestions'].append('Antwort überprüfen')
        
        return validation
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Gibt Generierungs-Statistiken zurück"""
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'templates': list(self.response_templates.keys())
        }