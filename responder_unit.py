"""
Liyana NEXUS v1 - Responder Unit
KI-basierte automatische Antwortgenerierung
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import config
from memory_vault import RequestData, CustomerData

@dataclass
class ResponseTemplate:
    """Antwort-Template-Struktur"""
    id: str
    name: str
    category: str
    template: str
    variables: List[str]
    ai_model: str = "gpt-3.5-turbo"

class ResponderUnit:
    """
    Responder Unit - KI-basierte Antwortgenerierung
    Verwendet OpenAI, Gemini und lokale LLMs für automatische Antworten
    """
    
    def __init__(self, memory_vault):
        self.logger = logging.getLogger("nexus.responder")
        self.memory = memory_vault
        self.is_running = False
        self.ai_models = {}
        self.response_templates = {}
        
        # Initialisiere AI-Modelle
        self._init_ai_models()
        self._load_response_templates()
        
        self.logger.info("🤖 Responder Unit initialisiert")
    
    def _init_ai_models(self):
        """Initialisiert die verfügbaren AI-Modelle"""
        try:
            # OpenAI
            if config.AI_CONFIG["openai"]["api_key"]:
                import openai
                openai.api_key = config.AI_CONFIG["openai"]["api_key"]
                self.ai_models["openai"] = {
                    "client": openai,
                    "config": config.AI_CONFIG["openai"]
                }
            
            # Gemini
            if config.AI_CONFIG["gemini"]["api_key"]:
                import google.generativeai as genai
                genai.configure(api_key=config.AI_CONFIG["gemini"]["api_key"])
                self.ai_models["gemini"] = {
                    "client": genai,
                    "config": config.AI_CONFIG["gemini"]
                }
            
            # Lokales LLM (Platzhalter für später)
            self.ai_models["local"] = {
                "client": None,
                "config": config.AI_CONFIG["local_llm"]
            }
            
            self.logger.info(f"✅ {len(self.ai_models)} AI-Modelle initialisiert")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Initialisieren der AI-Modelle: {e}")
    
    def _load_response_templates(self):
        """Lädt vordefinierte Antwort-Templates"""
        self.response_templates = {
            "greeting": ResponseTemplate(
                id="greeting",
                name="Begrüßung",
                category="general",
                template="Hallo {name},\n\nvielen Dank für Ihre Nachricht. {custom_response}\n\nMit freundlichen Grüßen\n{company_name}",
                variables=["name", "custom_response", "company_name"]
            ),
            "support": ResponseTemplate(
                id="support",
                name="Support-Anfrage",
                category="support",
                template="Hallo {name},\n\nvielen Dank für Ihre Support-Anfrage bezüglich {issue}.\n\n{resolution}\n\nFalls Sie weitere Fragen haben, stehen wir Ihnen gerne zur Verfügung.\n\nMit freundlichen Grüßen\n{company_name}",
                variables=["name", "issue", "resolution", "company_name"]
            ),
            "order": ResponseTemplate(
                id="order",
                name="Bestellbestätigung",
                category="sales",
                template="Hallo {name},\n\nvielen Dank für Ihre Bestellung (Bestellnummer: {order_id}).\n\n{order_details}\n\nWir werden Ihre Bestellung schnellstmöglich bearbeiten.\n\nMit freundlichen Grüßen\n{company_name}",
                variables=["name", "order_id", "order_details", "company_name"]
            ),
            "complaint": ResponseTemplate(
                id="complaint",
                name="Beschwerde",
                category="support",
                template="Hallo {name},\n\nwir bedauern sehr, dass Sie mit {issue} nicht zufrieden sind.\n\n{apology_and_solution}\n\nWir hoffen, dass wir Ihnen damit weiterhelfen können.\n\nMit freundlichen Grüßen\n{company_name}",
                variables=["name", "issue", "apology_and_solution", "company_name"]
            )
        }
    
    async def start(self):
        """Startet die Responder Unit"""
        if self.is_running:
            return
        
        self.logger.info("🚀 Starte Responder Unit...")
        self.is_running = True
        
        # Starte Antwort-Generator
        asyncio.create_task(self._process_pending_requests())
        
        self.logger.info("✅ Responder Unit gestartet")
    
    async def stop(self):
        """Stoppt die Responder Unit"""
        self.logger.info("🛑 Stoppe Responder Unit...")
        self.is_running = False
        self.logger.info("✅ Responder Unit gestoppt")
    
    async def _process_pending_requests(self):
        """Verarbeitet ausstehende Anfragen und generiert Antworten"""
        while self.is_running:
            try:
                # Lade ausstehende Anfragen
                pending_requests = await self.memory.get_pending_requests(limit=5)
                
                for request in pending_requests:
                    if request.type == "email":
                        await self._generate_email_response(request)
                
                await asyncio.sleep(10)  # Alle 10 Sekunden prüfen
                
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Verarbeiten ausstehender Anfragen: {e}")
                await asyncio.sleep(30)
    
    async def _generate_email_response(self, request: RequestData):
        """Generiert eine E-Mail-Antwort für eine Anfrage"""
        try:
            self.logger.info(f"📝 Generiere Antwort für Anfrage: {request.id}")
            
            # Lade Kundendaten
            customer = await self.memory.get_customer(request.customer_id)
            if not customer:
                self.logger.error(f"❌ Kunde nicht gefunden: {request.customer_id}")
                return
            
            # Analysiere Anfrage-Inhalt
            analysis = await self._analyze_request_content(request.content)
            
            # Wähle passendes Template
            template = self._select_response_template(analysis)
            
            # Generiere Antwort mit AI
            response_text = await self._generate_ai_response(request, customer, template, analysis)
            
            # Speichere Antwort
            await self._store_response(request.id, response_text, analysis)
            
            # Aktualisiere Anfrage-Status
            await self.memory.update_request_status(
                request.id, 
                "completed", 
                {"response": response_text, "analysis": analysis}
            )
            
            self.logger.info(f"✅ Antwort generiert für Anfrage: {request.id}")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Generieren der E-Mail-Antwort: {e}")
            await self.memory.update_request_status(request.id, "failed", {"error": str(e)})
    
    async def _analyze_request_content(self, content: str) -> Dict[str, Any]:
        """Analysiert den Inhalt einer Anfrage"""
        try:
            # Einfache Keyword-basierte Analyse
            content_lower = content.lower()
            
            analysis = {
                "category": "general",
                "sentiment": "neutral",
                "urgency": "normal",
                "keywords": [],
                "language": "de"
            }
            
            # Kategorie-Erkennung
            if any(word in content_lower for word in ["support", "hilfe", "problem", "fehler"]):
                analysis["category"] = "support"
            elif any(word in content_lower for word in ["bestellung", "order", "kauf", "preis"]):
                analysis["category"] = "sales"
            elif any(word in content_lower for word in ["beschwerde", "complaint", "unzufrieden"]):
                analysis["category"] = "complaint"
            
            # Sentiment-Analyse
            positive_words = ["danke", "gut", "zufrieden", "toll", "super"]
            negative_words = ["schlecht", "unzufrieden", "ärgerlich", "enttäuscht"]
            
            if any(word in content_lower for word in positive_words):
                analysis["sentiment"] = "positive"
            elif any(word in content_lower for word in negative_words):
                analysis["sentiment"] = "negative"
            
            # Dringlichkeit
            urgent_words = ["dringend", "urgent", "sofort", "wichtig"]
            if any(word in content_lower for word in urgent_words):
                analysis["urgency"] = "high"
            
            # Keyword-Extraktion
            import re
            words = re.findall(r'\b\w+\b', content_lower)
            analysis["keywords"] = [word for word in words if len(word) > 3][:10]
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei der Inhaltsanalyse: {e}")
            return {"category": "general", "sentiment": "neutral", "urgency": "normal", "keywords": [], "language": "de"}
    
    def _select_response_template(self, analysis: Dict[str, Any]) -> ResponseTemplate:
        """Wählt ein passendes Antwort-Template basierend auf der Analyse"""
        category = analysis.get("category", "general")
        
        # Wähle Template basierend auf Kategorie
        if category == "support":
            return self.response_templates["support"]
        elif category == "sales":
            return self.response_templates["order"]
        elif category == "complaint":
            return self.response_templates["complaint"]
        else:
            return self.response_templates["greeting"]
    
    async def _generate_ai_response(self, request: RequestData, customer: CustomerData, 
                                  template: ResponseTemplate, analysis: Dict[str, Any]) -> str:
        """Generiert eine Antwort mit AI"""
        try:
            # Erstelle Prompt für AI
            prompt = self._create_ai_prompt(request, customer, template, analysis)
            
            # Versuche verschiedene AI-Modelle
            for model_name, model_config in self.ai_models.items():
                if model_config["client"]:
                    try:
                        response = await self._call_ai_model(model_name, prompt, model_config)
                        if response:
                            return response
                    except Exception as e:
                        self.logger.warning(f"⚠️ Fehler mit AI-Modell {model_name}: {e}")
                        continue
            
            # Fallback: Verwende Template ohne AI
            return self._generate_fallback_response(request, customer, template, analysis)
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei AI-Antwortgenerierung: {e}")
            return self._generate_fallback_response(request, customer, template, analysis)
    
    def _create_ai_prompt(self, request: RequestData, customer: CustomerData, 
                         template: ResponseTemplate, analysis: Dict[str, Any]) -> str:
        """Erstellt einen Prompt für die AI"""
        prompt = f"""
        Erstelle eine professionelle, freundliche E-Mail-Antwort basierend auf folgenden Informationen:
        
        Kunde: {customer.name} ({customer.email})
        Anfrage: {request.content}
        Kategorie: {analysis['category']}
        Sentiment: {analysis['sentiment']}
        Dringlichkeit: {analysis['urgency']}
        
        Template: {template.template}
        
        Anforderungen:
        - Verwende das Template als Grundlage
        - Sei professionell und freundlich
        - Antworte auf Deutsch
        - Berücksichtige das Sentiment der Anfrage
        - Sei hilfsbereit und lösungsorientiert
        
        Antwort:
        """
        return prompt
    
    async def _call_ai_model(self, model_name: str, prompt: str, model_config: Dict[str, Any]) -> Optional[str]:
        """Ruft ein AI-Modell auf"""
        try:
            if model_name == "openai":
                response = await asyncio.to_thread(
                    model_config["client"].ChatCompletion.create,
                    model=model_config["config"]["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=model_config["config"]["max_tokens"],
                    temperature=model_config["config"]["temperature"]
                )
                return response.choices[0].message.content.strip()
            
            elif model_name == "gemini":
                model = model_config["client"].GenerativeModel(model_config["config"]["model"])
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt
                )
                return response.text.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim AI-Modell-Aufruf {model_name}: {e}")
            return None
    
    def _generate_fallback_response(self, request: RequestData, customer: CustomerData, 
                                  template: ResponseTemplate, analysis: Dict[str, Any]) -> str:
        """Generiert eine Fallback-Antwort ohne AI"""
        try:
            # Einfache Template-basierte Antwort
            response = template.template
            
            # Ersetze Variablen
            response = response.replace("{name}", customer.name)
            response = response.replace("{company_name}", "Liyana NEXUS")
            
            # Füge spezifische Inhalte basierend auf Kategorie hinzu
            if analysis["category"] == "support":
                response = response.replace("{issue}", "Ihrer Anfrage")
                response = response.replace("{resolution}", "Wir werden uns schnellstmöglich um Ihr Anliegen kümmern.")
            elif analysis["category"] == "sales":
                response = response.replace("{order_id}", "N/A")
                response = response.replace("{order_details}", "Vielen Dank für Ihr Interesse an unseren Produkten.")
            elif analysis["category"] == "complaint":
                response = response.replace("{issue}", "Ihrer Erfahrung")
                response = response.replace("{apology_and_solution}", "Wir entschuldigen uns für die Unannehmlichkeiten und werden das Problem umgehend untersuchen.")
            else:
                response = response.replace("{custom_response}", "Wir haben Ihre Nachricht erhalten und werden uns schnellstmöglich bei Ihnen melden.")
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Fallback-Antwort: {e}")
            return f"Hallo {customer.name},\n\nvielen Dank für Ihre Nachricht. Wir werden uns schnellstmöglich bei Ihnen melden.\n\nMit freundlichen Grüßen\nLiyana NEXUS"
    
    async def _store_response(self, request_id: str, response_text: str, analysis: Dict[str, Any]):
        """Speichert eine generierte Antwort"""
        try:
            # Hier könnte die Antwort in einer separaten Tabelle gespeichert werden
            # Für jetzt loggen wir sie nur
            self.logger.info(f"💾 Antwort gespeichert für Anfrage {request_id}")
            
            # Logge System-Ereignis
            await self.memory.log_system_event(
                "INFO",
                "responder_unit",
                f"Antwort generiert für Anfrage {request_id}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Speichern der Antwort: {e}")
    
    async def generate_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert eine Antwort basierend auf den übergebenen Daten"""
        try:
            content = data.get("content", "")
            customer_id = data.get("customer_id", "")
            response_type = data.get("type", "email")
            
            if not content or not customer_id:
                return {"success": False, "error": "Fehlende Daten"}
            
            # Lade Kundendaten
            customer = await self.memory.get_customer(customer_id)
            if not customer:
                return {"success": False, "error": "Kunde nicht gefunden"}
            
            # Analysiere Inhalt
            analysis = await self._analyze_request_content(content)
            
            # Wähle Template
            template = self._select_response_template(analysis)
            
            # Generiere Antwort
            response = await self._generate_ai_response(
                RequestData(id="temp", customer_id=customer_id, type=response_type, content=content, status="pending", created_at=time.time()),
                customer,
                template,
                analysis
            )
            
            return {
                "success": True,
                "response": response,
                "analysis": analysis,
                "template_used": template.id
            }
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Antwortgenerierung: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Gibt den Status der Responder Unit zurück"""
        return {
            "state": "EXECUTING" if self.is_running else "WAITING",
            "ai_models": list(self.ai_models.keys()),
            "templates": len(self.response_templates),
            "last_response": time.time()
        }
    
    async def pause(self):
        """Pausiert die Responder Unit"""
        self.is_running = False
        self.logger.info("⏸️ Responder Unit pausiert")
    
    async def resume(self):
        """Setzt die Responder Unit fort"""
        if not self.is_running:
            await self.start()
        self.logger.info("▶️ Responder Unit fortgesetzt")