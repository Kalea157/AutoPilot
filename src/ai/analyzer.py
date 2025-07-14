"""
AI Analyzer - GPT-4o-basierte E-Mail-Analyse
"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import structlog
import asyncio
from openai import AsyncOpenAI
from langdetect import detect, LangDetectException

logger = structlog.get_logger(__name__)


@dataclass
class EmailAnalysis:
    """Datenklasse für E-Mail-Analysen"""
    category: str
    urgency: int  # 1-10
    sentiment: str  # positive, neutral, negative
    language: str
    key_questions: List[str]
    key_tasks: List[str]
    response_strategy: str
    confidence: float  # 0.0-1.0
    summary: str
    suggested_actions: List[str]
    priority: str  # low, medium, high, critical


class AIAnalyzer:
    """GPT-4o-basierter E-Mail-Analyzer"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = AsyncOpenAI(api_key=config['api_key'])
        self.model = config['model']
        self.max_tokens = config['max_tokens']
        self.temperature = config['temperature']
        self.analysis_prompt = config['analysis_prompt']
        
        # Vordefinierte Kategorien für bessere Konsistenz
        self.categories = [
            'question', 'complaint', 'order', 'support', 'feedback',
            'appointment', 'invoice', 'general', 'spam', 'urgent'
        ]
        
        # Sentiment-Schlüsselwörter
        self.sentiment_keywords = {
            'positive': ['danke', 'thank', 'great', 'excellent', 'good', 'happy', 'satisfied'],
            'negative': ['problem', 'issue', 'angry', 'frustrated', 'disappointed', 'bad', 'terrible'],
            'neutral': ['info', 'information', 'request', 'inquiry', 'question']
        }
    
    async def analyze_email(self, email_content: str, subject: str = "", 
                          sender: str = "") -> EmailAnalysis:
        """Analysiert eine E-Mail mit GPT-4o"""
        try:
            # Kombiniere Inhalt für Analyse
            full_content = f"Subject: {subject}\nFrom: {sender}\n\n{email_content}"
            
            # Erstelle strukturierten Prompt
            prompt = self._create_analysis_prompt(full_content)
            
            # GPT-4o Analyse
            response = await self._call_gpt4o(prompt)
            
            # Parse JSON Response
            analysis_data = self._parse_analysis_response(response)
            
            # Erstelle EmailAnalysis Objekt
            analysis = EmailAnalysis(
                category=analysis_data.get('category', 'general'),
                urgency=analysis_data.get('urgency', 5),
                sentiment=analysis_data.get('sentiment', 'neutral'),
                language=analysis_data.get('language', 'de'),
                key_questions=analysis_data.get('key_questions', []),
                key_tasks=analysis_data.get('key_tasks', []),
                response_strategy=analysis_data.get('response_strategy', 'standard'),
                confidence=analysis_data.get('confidence', 0.8),
                summary=analysis_data.get('summary', ''),
                suggested_actions=analysis_data.get('suggested_actions', []),
                priority=self._calculate_priority(analysis_data)
            )
            
            logger.info("Email analysis completed", 
                       category=analysis.category,
                       urgency=analysis.urgency,
                       confidence=analysis.confidence)
            
            return analysis
            
        except Exception as e:
            logger.error("Failed to analyze email", error=str(e))
            # Fallback-Analyse
            return self._fallback_analysis(email_content, subject, sender)
    
    def _create_analysis_prompt(self, content: str) -> str:
        """Erstellt strukturierten Prompt für GPT-4o"""
        return f"""
{self.analysis_prompt}

Analysiere diese E-Mail und gib eine JSON-Antwort zurück:

E-Mail-Inhalt:
{content}

Antworte NUR mit einem gültigen JSON-Objekt in folgendem Format:
{{
    "category": "question|complaint|order|support|feedback|appointment|invoice|general|spam|urgent",
    "urgency": 1-10,
    "sentiment": "positive|neutral|negative",
    "language": "de|en|fr|es",
    "key_questions": ["Frage 1", "Frage 2"],
    "key_tasks": ["Aufgabe 1", "Aufgabe 2"],
    "response_strategy": "standard|formal|casual|apologetic|informative",
    "confidence": 0.0-1.0,
    "summary": "Kurze Zusammenfassung",
    "suggested_actions": ["Aktion 1", "Aktion 2"]
}}
"""
    
    async def _call_gpt4o(self, prompt: str) -> str:
        """Ruft GPT-4o API auf"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Du bist ein professioneller E-Mail-Analyzer. Antworte nur mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("GPT-4o API call failed", error=str(e))
            raise
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
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
            logger.error("Failed to parse JSON response", error=str(e), response=response)
            raise
    
    def _calculate_priority(self, analysis_data: Dict[str, Any]) -> str:
        """Berechnet Priorität basierend auf Analyse"""
        urgency = analysis_data.get('urgency', 5)
        sentiment = analysis_data.get('sentiment', 'neutral')
        category = analysis_data.get('category', 'general')
        
        # Kritische Kategorien
        if category in ['urgent', 'complaint'] or urgency >= 9:
            return 'critical'
        elif urgency >= 7 or sentiment == 'negative':
            return 'high'
        elif urgency >= 5:
            return 'medium'
        else:
            return 'low'
    
    def _fallback_analysis(self, content: str, subject: str, sender: str) -> EmailAnalysis:
        """Fallback-Analyse bei API-Fehlern"""
        logger.warning("Using fallback analysis")
        
        # Einfache Regel-basierte Analyse
        category = self._detect_category_fallback(content, subject)
        urgency = self._detect_urgency_fallback(content, subject)
        sentiment = self._detect_sentiment_fallback(content)
        language = self._detect_language_fallback(content)
        
        return EmailAnalysis(
            category=category,
            urgency=urgency,
            sentiment=sentiment,
            language=language,
            key_questions=[],
            key_tasks=[],
            response_strategy='standard',
            confidence=0.6,
            summary=f"Fallback analysis: {category} email",
            suggested_actions=[],
            priority=self._calculate_priority({
                'urgency': urgency,
                'sentiment': sentiment,
                'category': category
            })
        )
    
    def _detect_category_fallback(self, content: str, subject: str) -> str:
        """Fallback-Kategorie-Erkennung"""
        text = f"{subject} {content}".lower()
        
        if any(word in text for word in ['frage', 'question', 'wie', 'how']):
            return 'question'
        elif any(word in text for word in ['beschwerde', 'complaint', 'problem', 'issue']):
            return 'complaint'
        elif any(word in text for word in ['bestellung', 'order', 'kauf', 'buy']):
            return 'order'
        elif any(word in text for word in ['support', 'hilfe', 'help']):
            return 'support'
        elif any(word in text for word in ['termin', 'appointment', 'meeting']):
            return 'appointment'
        else:
            return 'general'
    
    def _detect_urgency_fallback(self, content: str, subject: str) -> int:
        """Fallback-Dringlichkeits-Erkennung"""
        text = f"{subject} {content}".lower()
        
        urgent_words = ['dringend', 'urgent', 'sofort', 'immediately', 'asap']
        if any(word in text for word in urgent_words):
            return 9
        elif any(word in text for word in ['wichtig', 'important']):
            return 7
        else:
            return 5
    
    def _detect_sentiment_fallback(self, content: str) -> str:
        """Fallback-Sentiment-Erkennung"""
        content_lower = content.lower()
        
        positive_count = sum(1 for word in self.sentiment_keywords['positive'] 
                           if word in content_lower)
        negative_count = sum(1 for word in self.sentiment_keywords['negative'] 
                           if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_language_fallback(self, content: str) -> str:
        """Fallback-Spracherkennung"""
        try:
            return detect(content)
        except LangDetectException:
            return 'de'  # Default
    
    async def batch_analyze(self, emails: List[Dict[str, Any]]) -> List[EmailAnalysis]:
        """Analysiert mehrere E-Mails parallel"""
        tasks = []
        for email in emails:
            task = asyncio.create_task(
                self.analyze_email(
                    email['content'],
                    email.get('subject', ''),
                    email.get('sender', '')
                )
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtere Fehler
        analyses = []
        for result in results:
            if isinstance(result, Exception):
                logger.error("Batch analysis failed for email", error=str(result))
            else:
                analyses.append(result)
        
        return analyses
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Gibt Analyse-Statistiken zurück"""
        return {
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'categories': self.categories
        }