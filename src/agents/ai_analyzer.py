"""
AI Analyzer Agent - Analyzes emails using OpenAI and generates responses
"""

import openai
from typing import Dict, Any, List, Optional, Tuple
import json
import re

from ..models.email import EmailMessage, EmailAnalysis, EmailCategory, EmailSentiment, EmailUrgency, EmailLanguage
from ..core.config import config
from ..core.logger import logger


class AIAnalyzer:
    """AI analyzer agent for email analysis and response generation"""
    
    def __init__(self):
        self.ai_config = config.get_ai_config()
        self.openai_client = openai.OpenAI(api_key=config.openai.api_key)
        self.model = self.ai_config.get('model', 'gpt-4o')
        self.max_tokens = self.ai_config.get('max_tokens', 2000)
        self.temperature = self.ai_config.get('temperature', 0.7)
        self.system_prompt = self.ai_config.get('system_prompt', '')
    
    def analyze_email(self, email: EmailMessage) -> EmailAnalysis:
        """Analyze email content and extract key information"""
        try:
            logger.log_ai_analysis(email.message_id, "started", 0.0)
            
            # Prepare email content for analysis
            email_content = self._prepare_email_content(email)
            
            # Perform comprehensive analysis
            analysis_results = self._perform_analysis(email_content)
            
            # Create EmailAnalysis object
            analysis = EmailAnalysis(
                sentiment=analysis_results['sentiment'],
                category=analysis_results['category'],
                urgency=analysis_results['urgency'],
                language=analysis_results['language'],
                confidence=analysis_results['confidence'],
                key_points=analysis_results['key_points'],
                suggested_actions=analysis_results['suggested_actions'],
                priority_score=analysis_results['priority_score']
            )
            
            logger.log_ai_analysis(email.message_id, "completed", analysis.confidence)
            return analysis
            
        except Exception as e:
            logger.log_error("ai_analysis", str(e), email_id=email.message_id)
            # Return default analysis on error
            return self._create_default_analysis()
    
    def generate_response(self, email: EmailMessage, analysis: EmailAnalysis) -> Tuple[str, float]:
        """Generate appropriate response for email"""
        try:
            logger.log_ai_analysis(email.message_id, "response_generation_started", 0.0)
            
            # Prepare context for response generation
            context = self._prepare_response_context(email, analysis)
            
            # Generate response using OpenAI
            response = self._generate_ai_response(context)
            
            # Calculate confidence score
            confidence = self._calculate_response_confidence(email, analysis, response)
            
            logger.log_ai_analysis(email.message_id, "response_generated", confidence)
            return response, confidence
            
        except Exception as e:
            logger.log_error("response_generation", str(e), email_id=email.message_id)
            return self._generate_fallback_response(email), 0.5
    
    def _prepare_email_content(self, email: EmailMessage) -> str:
        """Prepare email content for analysis"""
        content = f"""
Subject: {email.subject}
From: {email.sender}
To: {', '.join([str(r) for r in email.recipients])}
Date: {email.date_received}

Content:
{email.body_text}

Attachments: {len(email.attachments)} files
"""
        return content.strip()
    
    def _perform_analysis(self, email_content: str) -> Dict[str, Any]:
        """Perform comprehensive email analysis"""
        analysis_prompts = self.ai_config.get('analysis_prompts', {})
        
        # Analyze sentiment
        sentiment_prompt = analysis_prompts.get('sentiment', '')
        sentiment_result = self._call_openai(f"{sentiment_prompt}\n\nEmail:\n{email_content}")
        sentiment = self._parse_sentiment(sentiment_result)
        
        # Analyze category
        category_prompt = analysis_prompts.get('category', '')
        category_result = self._call_openai(f"{category_prompt}\n\nEmail:\n{email_content}")
        category = self._parse_category(category_result)
        
        # Analyze urgency
        urgency_prompt = analysis_prompts.get('urgency', '')
        urgency_result = self._call_openai(f"{urgency_prompt}\n\nEmail:\n{email_content}")
        urgency = self._parse_urgency(urgency_result)
        
        # Detect language
        language = self._detect_language(email_content)
        
        # Extract key points
        key_points = self._extract_key_points(email_content)
        
        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(email_content, category, urgency)
        
        # Calculate priority score
        priority_score = self._calculate_priority_score(sentiment, category, urgency, key_points)
        
        # Calculate overall confidence
        confidence = self._calculate_analysis_confidence(sentiment_result, category_result, urgency_result)
        
        return {
            'sentiment': sentiment,
            'category': category,
            'urgency': urgency,
            'language': language,
            'confidence': confidence,
            'key_points': key_points,
            'suggested_actions': suggested_actions,
            'priority_score': priority_score
        }
    
    def _call_openai(self, prompt: str) -> str:
        """Make OpenAI API call"""
        try:
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.log_error("openai_api_call", str(e))
            return ""
    
    def _parse_sentiment(self, result: str) -> EmailSentiment:
        """Parse sentiment from AI response"""
        result_lower = result.lower()
        if 'positiv' in result_lower:
            return EmailSentiment.POSITIVE
        elif 'negativ' in result_lower:
            return EmailSentiment.NEGATIVE
        else:
            return EmailSentiment.NEUTRAL
    
    def _parse_category(self, result: str) -> EmailCategory:
        """Parse category from AI response"""
        result_lower = result.lower()
        if 'anfrage' in result_lower or 'request' in result_lower:
            return EmailCategory.REQUEST
        elif 'beschwerde' in result_lower or 'complaint' in result_lower:
            return EmailCategory.COMPLAINT
        elif 'bestellung' in result_lower or 'order' in result_lower:
            return EmailCategory.ORDER
        elif 'support' in result_lower:
            return EmailCategory.SUPPORT
        elif 'rechnung' in result_lower or 'invoice' in result_lower:
            return EmailCategory.INVOICE
        else:
            return EmailCategory.OTHER
    
    def _parse_urgency(self, result: str) -> EmailUrgency:
        """Parse urgency from AI response"""
        result_lower = result.lower()
        if 'hoch' in result_lower or 'high' in result_lower:
            return EmailUrgency.HIGH
        elif 'mittel' in result_lower or 'medium' in result_lower:
            return EmailUrgency.MEDIUM
        else:
            return EmailUrgency.LOW
    
    def _detect_language(self, content: str) -> EmailLanguage:
        """Detect email language"""
        # Simple language detection based on common words
        content_lower = content.lower()
        
        german_words = ['der', 'die', 'das', 'und', 'oder', 'für', 'mit', 'von', 'zu']
        french_words = ['le', 'la', 'les', 'et', 'ou', 'pour', 'avec', 'de', 'à']
        spanish_words = ['el', 'la', 'los', 'las', 'y', 'o', 'para', 'con', 'de']
        italian_words = ['il', 'la', 'i', 'gli', 'e', 'o', 'per', 'con', 'di']
        
        if any(word in content_lower for word in german_words):
            return EmailLanguage.GERMAN
        elif any(word in content_lower for word in french_words):
            return EmailLanguage.FRENCH
        elif any(word in content_lower for word in spanish_words):
            return EmailLanguage.SPANISH
        elif any(word in content_lower for word in italian_words):
            return EmailLanguage.ITALIAN
        else:
            return EmailLanguage.ENGLISH
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from email content"""
        prompt = f"""
Extract the 3-5 most important key points from this email. 
Return them as a simple list, one point per line.

Email:
{content}
"""
        result = self._call_openai(prompt)
        if result:
            return [point.strip() for point in result.split('\n') if point.strip()]
        return []
    
    def _generate_suggested_actions(self, content: str, category: EmailCategory, urgency: EmailUrgency) -> List[str]:
        """Generate suggested actions based on email content and analysis"""
        prompt = f"""
Based on this email (category: {category.value}, urgency: {urgency.value}), 
suggest 2-3 appropriate actions. Return them as a simple list.

Email:
{content}
"""
        result = self._call_openai(prompt)
        if result:
            return [action.strip() for action in result.split('\n') if action.strip()]
        return []
    
    def _calculate_priority_score(self, sentiment: EmailSentiment, category: EmailCategory, 
                                urgency: EmailUrgency, key_points: List[str]) -> float:
        """Calculate priority score based on various factors"""
        score = 0.0
        
        # Urgency weight
        urgency_weights = {
            EmailUrgency.HIGH: 0.4,
            EmailUrgency.MEDIUM: 0.2,
            EmailUrgency.LOW: 0.1
        }
        score += urgency_weights.get(urgency, 0.1)
        
        # Category weight
        category_weights = {
            EmailCategory.COMPLAINT: 0.3,
            EmailCategory.SUPPORT: 0.25,
            EmailCategory.REQUEST: 0.2,
            EmailCategory.ORDER: 0.15,
            EmailCategory.INVOICE: 0.1,
            EmailCategory.OTHER: 0.05
        }
        score += category_weights.get(category, 0.05)
        
        # Sentiment weight
        if sentiment == EmailSentiment.NEGATIVE:
            score += 0.2
        elif sentiment == EmailSentiment.POSITIVE:
            score += 0.1
        
        # Key points weight
        score += min(len(key_points) * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _calculate_analysis_confidence(self, sentiment_result: str, category_result: str, urgency_result: str) -> float:
        """Calculate confidence in analysis results"""
        # Simple confidence calculation based on response quality
        confidence = 0.7  # Base confidence
        
        # Adjust based on response length and clarity
        if len(sentiment_result) > 10:
            confidence += 0.1
        if len(category_result) > 10:
            confidence += 0.1
        if len(urgency_result) > 10:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _prepare_response_context(self, email: EmailMessage, analysis: EmailAnalysis) -> str:
        """Prepare context for response generation"""
        context = f"""
Original Email:
Subject: {email.subject}
From: {email.sender}
Content: {email.body_text}

Analysis:
- Category: {analysis.category.value}
- Sentiment: {analysis.sentiment.value}
- Urgency: {analysis.urgency.value}
- Language: {analysis.language.value}
- Key Points: {', '.join(analysis.key_points)}
- Suggested Actions: {', '.join(analysis.suggested_actions)}

Generate a professional, appropriate response to this email.
"""
        return context
    
    def _generate_ai_response(self, context: str) -> str:
        """Generate response using OpenAI"""
        prompt = f"""
{context}

Please generate a professional email response that:
1. Addresses the key points from the original email
2. Matches the tone and urgency level
3. Is clear, concise, and helpful
4. Uses appropriate language and formatting

Response:
"""
        return self._call_openai(prompt)
    
    def _calculate_response_confidence(self, email: EmailMessage, analysis: EmailAnalysis, response: str) -> float:
        """Calculate confidence in generated response"""
        confidence = analysis.confidence  # Start with analysis confidence
        
        # Adjust based on response quality
        if len(response) > 50:
            confidence += 0.1
        if len(response) > 100:
            confidence += 0.1
        
        # Check for key elements
        if any(keyword in response.lower() for keyword in ['danke', 'thank', 'vielen dank']):
            confidence += 0.05
        if any(keyword in response.lower() for keyword in ['gerne', 'gladly', 'willing']):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _generate_fallback_response(self, email: EmailMessage) -> str:
        """Generate fallback response when AI fails"""
        return f"""
Vielen Dank für Ihre E-Mail.

Wir haben Ihre Nachricht erhalten und werden uns so schnell wie möglich bei Ihnen melden.

Mit freundlichen Grüßen
"""
    
    def _create_default_analysis(self) -> EmailAnalysis:
        """Create default analysis when AI analysis fails"""
        return EmailAnalysis(
            sentiment=EmailSentiment.NEUTRAL,
            category=EmailCategory.OTHER,
            urgency=EmailUrgency.LOW,
            language=EmailLanguage.GERMAN,
            confidence=0.5,
            key_points=["Email received"],
            suggested_actions=["Manual review required"],
            priority_score=0.3
        )