"""
Liyana NEXUS v1 - Responder Unit
GPT/LLM-basierte automatische Antwortgenerierung
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import config, AgentState

class ResponderUnit:
    """GPT/LLM-basierte Antwortgenerierung"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = AgentState.WAITING
        
        # AI-Clients
        self.openai_client = None
        self.gemini_client = None
        
        # Antwort-Templates
        self.response_templates = {
            'support': {
                'system_prompt': '''Du bist ein hilfreicher Kundensupport-Mitarbeiter. 
                Antworte professionell, freundlich und lösungsorientiert. 
                Verwende eine höfliche, aber nicht zu formelle Sprache.'''
            },
            'sales': {
                'system_prompt': '''Du bist ein erfahrener Verkaufsberater. 
                Antworte überzeugend, aber nicht aufdringlich. 
                Fokussiere dich auf die Bedürfnisse des Kunden.'''
            },
            'technical': {
                'system_prompt': '''Du bist ein technischer Experte. 
                Erkläre technische Konzepte verständlich. 
                Verwende Beispiele und Schritt-für-Schritt-Anleitungen.'''
            },
            'general': {
                'system_prompt': '''Du bist ein professioneller Kommunikationsassistent. 
                Antworte höflich, informativ und hilfreich. 
                Passe deinen Ton an die Situation an.'''
            }
        }
        
        # Kontext-Management
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        self.max_history_length = 10
        
        # Antwort-Kategorien
        self.response_categories = {
            'support': ['hilfe', 'problem', 'fehler', 'support', 'kunde'],
            'sales': ['verkauf', 'preis', 'kauf', 'bestellung', 'angebot'],
            'technical': ['technisch', 'anleitung', 'installation', 'konfiguration'],
            'general': ['allgemein', 'info', 'frage', 'anfrage']
        }
        
        self._running = False
    
    async def start(self):
        """Startet den Responder Unit"""
        if self._running:
            return
        
        self.logger.info("Responder Unit wird gestartet...")
        self._running = True
        self.state = AgentState.EXECUTING
        
        # Initialisiere AI-Clients
        await self._initialize_ai_clients()
        
        self.logger.info("Responder Unit gestartet")
    
    async def stop(self):
        """Stoppt den Responder Unit"""
        self.logger.info("Responder Unit wird gestoppt...")
        self._running = False
        self.state = AgentState.PAUSED
        self.logger.info("Responder Unit gestoppt")
    
    async def _initialize_ai_clients(self):
        """Initialisiert die AI-Clients"""
        try:
            # OpenAI Client
            if config.api.openai_api_key:
                import openai
                self.openai_client = openai.AsyncOpenAI(api_key=config.api.openai_api_key)
                self.logger.info("OpenAI Client initialisiert")
            
            # Gemini Client
            if config.api.gemini_api_key:
                import google.generativeai as genai
                genai.configure(api_key=config.api.gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                self.logger.info("Gemini Client initialisiert")
            
            if not self.openai_client and not self.gemini_client:
                self.logger.warning("Keine AI-Clients verfügbar")
                
        except Exception as e:
            self.logger.error(f"Fehler bei AI-Client-Initialisierung: {e}")
    
    async def generate_response(self, message: str, context: Dict[str, Any] = None, 
                               response_type: str = 'general') -> Dict[str, Any]:
        """Generiert eine Antwort basierend auf der Nachricht"""
        try:
            # Bestimme Antwort-Typ falls nicht angegeben
            if not response_type or response_type == 'auto':
                response_type = await self._categorize_message(message)
            
            # Hole Template
            template = self.response_templates.get(response_type, self.response_templates['general'])
            
            # Erstelle Prompt
            prompt = await self._create_prompt(message, context, template)
            
            # Generiere Antwort
            response = await self._generate_ai_response(prompt, response_type)
            
            # Speichere in Konversationshistorie
            conversation_id = context.get('conversation_id', 'default')
            await self._add_to_history(conversation_id, message, response)
            
            return {
                'success': True,
                'response': response,
                'response_type': response_type,
                'confidence': 0.85,  # Placeholder
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Fehler bei Antwortgenerierung: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_response': 'Entschuldigung, ich konnte Ihre Anfrage nicht verarbeiten. Bitte versuchen Sie es später erneut.'
            }
    
    async def _categorize_message(self, message: str) -> str:
        """Kategorisiert eine Nachricht"""
        message_lower = message.lower()
        
        # Prüfe Kategorien
        for category, keywords in self.response_categories.items():
            if any(keyword in message_lower for keyword in keywords):
                return category
        
        return 'general'
    
    async def _create_prompt(self, message: str, context: Dict[str, Any], 
                           template: Dict[str, str]) -> str:
        """Erstellt einen Prompt für die AI"""
        system_prompt = template['system_prompt']
        
        # Füge Kontext hinzu
        context_info = ""
        if context:
            if 'customer_name' in context:
                context_info += f"\nKundenname: {context['customer_name']}"
            if 'product' in context:
                context_info += f"\nProdukt: {context['product']}"
            if 'order_id' in context:
                context_info += f"\nBestellnummer: {context['order_id']}"
            if 'previous_messages' in context:
                context_info += f"\nVorherige Nachrichten: {context['previous_messages']}"
        
        # Erstelle vollständigen Prompt
        full_prompt = f"{system_prompt}\n\nKontext:{context_info}\n\nKundenanfrage: {message}\n\nAntwort:"
        
        return full_prompt
    
    async def _generate_ai_response(self, prompt: str, response_type: str) -> str:
        """Generiert eine Antwort mit AI"""
        # Versuche OpenAI zuerst
        if self.openai_client:
            try:
                response = await self.openai_client.chat.completions.create(
                    model=config.api.openai_model,
                    messages=[
                        {"role": "system", "content": "Du bist ein hilfreicher Assistent."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                self.logger.warning(f"OpenAI Fehler: {e}")
        
        # Fallback zu Gemini
        if self.gemini_client:
            try:
                response = await self.gemini_client.generate_content_async(prompt)
                return response.text.strip()
            except Exception as e:
                self.logger.warning(f"Gemini Fehler: {e}")
        
        # Fallback-Antwort
        return await self._generate_fallback_response(response_type)
    
    async def _generate_fallback_response(self, response_type: str) -> str:
        """Generiert eine Fallback-Antwort"""
        fallback_responses = {
            'support': 'Vielen Dank für Ihre Anfrage. Unser Support-Team wird sich schnellstmöglich bei Ihnen melden.',
            'sales': 'Vielen Dank für Ihr Interesse. Ein Verkaufsberater wird sich in Kürze bei Ihnen melden.',
            'technical': 'Vielen Dank für Ihre technische Anfrage. Unser technisches Team wird Ihnen weiterhelfen.',
            'general': 'Vielen Dank für Ihre Nachricht. Wir werden uns schnellstmöglich bei Ihnen melden.'
        }
        
        return fallback_responses.get(response_type, fallback_responses['general'])
    
    async def _add_to_history(self, conversation_id: str, message: str, response: str):
        """Fügt Nachricht zur Konversationshistorie hinzu"""
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        # Füge Nachricht hinzu
        self.conversation_history[conversation_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response
        })
        
        # Begrenze Historie
        if len(self.conversation_history[conversation_id]) > self.max_history_length:
            self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-self.max_history_length:]
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Gibt die Konversationshistorie zurück"""
        return self.conversation_history.get(conversation_id, [])
    
    async def clear_conversation_history(self, conversation_id: str = None):
        """Löscht die Konversationshistorie"""
        if conversation_id:
            if conversation_id in self.conversation_history:
                del self.conversation_history[conversation_id]
        else:
            self.conversation_history.clear()
    
    async def generate_email_response(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert eine Email-Antwort"""
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        sender_name = email_data.get('sender_name', 'Kunde')
        
        # Kombiniere Subject und Body für Analyse
        full_message = f"Betreff: {subject}\n\nNachricht: {body}"
        
        # Erstelle Kontext
        context = {
            'customer_name': sender_name,
            'email_subject': subject,
            'message_type': 'email'
        }
        
        # Generiere Antwort
        response = await self.generate_response(full_message, context, 'auto')
        
        if response['success']:
            # Formatiere für Email
            email_response = await self._format_email_response(
                response['response'], 
                sender_name, 
                subject
            )
            
            return {
                'success': True,
                'subject': f"Re: {subject}",
                'body': email_response,
                'response_type': response['response_type']
            }
        else:
            return response
    
    async def _format_email_response(self, response: str, customer_name: str, 
                                   original_subject: str) -> str:
        """Formatiert eine Antwort für Email"""
        email_template = f"""
Sehr geehrte/r {customer_name},

{response}

Mit freundlichen Grüßen
Liyana NEXUS Team

---
Antwort auf: {original_subject}
        """
        
        return email_template.strip()
    
    async def generate_chat_response(self, message: str, user_id: str, 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generiert eine Chat-Antwort"""
        # Hole Konversationshistorie
        history = await self.get_conversation_history(user_id)
        
        # Erstelle erweiterten Kontext
        full_context = context or {}
        if history:
            full_context['previous_messages'] = history[-3:]  # Letzte 3 Nachrichten
        
        # Generiere Antwort
        response = await self.generate_response(message, full_context, 'auto')
        
        return response
    
    async def generate_support_response(self, issue_description: str, 
                                      customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert eine Support-Antwort"""
        context = {
            'customer_name': customer_info.get('name', 'Kunde'),
            'issue_type': customer_info.get('issue_type', 'general'),
            'priority': customer_info.get('priority', 'normal')
        }
        
        # Erstelle strukturierte Anfrage
        structured_message = f"""
Problembeschreibung: {issue_description}
Kunde: {context['customer_name']}
Problemtyp: {context['issue_type']}
Priorität: {context['priority']}

Bitte generiere eine hilfreiche Support-Antwort.
        """
        
        return await self.generate_response(structured_message, context, 'support')
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet eine Responder-Task"""
        task_type = task_data.get('type', 'generate_response')
        
        if task_type == 'generate_response':
            return await self._handle_generate_response_task(task_data)
        elif task_type == 'generate_email_response':
            return await self._handle_generate_email_response_task(task_data)
        elif task_type == 'generate_chat_response':
            return await self._handle_generate_chat_response_task(task_data)
        elif task_type == 'generate_support_response':
            return await self._handle_generate_support_response_task(task_data)
        else:
            return {'error': f'Unbekannter Task-Typ: {task_type}', 'success': False}
    
    async def _handle_generate_response_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Response-Generierungs-Task"""
        message = task_data.get('message')
        context = task_data.get('context', {})
        response_type = task_data.get('response_type', 'auto')
        
        if not message:
            return {'error': 'Keine Nachricht angegeben', 'success': False}
        
        return await self.generate_response(message, context, response_type)
    
    async def _handle_generate_email_response_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Email-Response-Generierungs-Task"""
        email_data = task_data.get('email_data', {})
        
        if not email_data:
            return {'error': 'Keine Email-Daten angegeben', 'success': False}
        
        return await self.generate_email_response(email_data)
    
    async def _handle_generate_chat_response_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Chat-Response-Generierungs-Task"""
        message = task_data.get('message')
        user_id = task_data.get('user_id')
        context = task_data.get('context', {})
        
        if not all([message, user_id]):
            return {'error': 'Nachricht oder User-ID fehlt', 'success': False}
        
        return await self.generate_chat_response(message, user_id, context)
    
    async def _handle_generate_support_response_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Support-Response-Generierungs-Task"""
        issue_description = task_data.get('issue_description')
        customer_info = task_data.get('customer_info', {})
        
        if not issue_description:
            return {'error': 'Keine Problembeschreibung angegeben', 'success': False}
        
        return await self.generate_support_response(issue_description, customer_info)