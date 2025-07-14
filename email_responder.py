import openai
import logging
import yaml
from typing import Dict, Optional, List
import re

class EmailResponder:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialisiert den E-Mail-Responder mit OpenAI-Integration."""
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self._setup_openai()
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus der YAML-Datei."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_openai(self):
        """Konfiguriert OpenAI mit API-Key."""
        try:
            openai.api_key = self.config['openai']['api_key']
            self.logger.info("OpenAI erfolgreich konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei OpenAI-Konfiguration: {e}")
            raise
    
    def generate_response(self, parsed_email: Dict, context: Optional[Dict] = None) -> Dict:
        """Generiert eine passende Antwort für eine E-Mail."""
        try:
            # Erstelle Prompt für OpenAI
            prompt = self._create_prompt(parsed_email, context)
            
            # Generiere Antwort mit OpenAI
            response = self._call_openai(prompt)
            
            # Verarbeite und strukturiere die Antwort
            structured_response = self._structure_response(response, parsed_email)
            
            self.logger.info(f"Antwort erfolgreich generiert für: {parsed_email['subject']}")
            return structured_response
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Antwortgenerierung: {e}")
            return self._create_fallback_response(parsed_email)
    
    def _create_prompt(self, parsed_email: Dict, context: Optional[Dict] = None) -> str:
        """Erstellt einen strukturierten Prompt für OpenAI."""
        sender_name = parsed_email['sender']['name']
        sender_email = parsed_email['sender']['email']
        subject = parsed_email['subject']
        content = parsed_email['content']
        category = parsed_email['category']
        priority = parsed_email['priority']
        
        # Basis-Prompt
        prompt = f"""Du bist ein professioneller E-Mail-Assistent. Generiere eine passende, höfliche und hilfreiche Antwort auf die folgende E-Mail.

E-Mail-Details:
- Absender: {sender_name} ({sender_email})
- Betreff: {subject}
- Kategorie: {category}
- Priorität: {priority}
- Inhalt: {content}

Kontext-Informationen:
- Antworte immer höflich und professionell
- Verwende eine angemessene Anrede (Herr/Frau + Name wenn bekannt)
- Gehe auf alle Fragen und Punkte in der E-Mail ein
- Halte die Antwort prägnant aber vollständig
- Verwende eine passende Grußformel am Ende
- Antworte auf Deutsch, es sei denn die ursprüngliche E-Mail ist auf Englisch

Zusätzliche Regeln:
- Bei Support-Anfragen: Biete konkrete Hilfe an
- Bei Verkaufsanfragen: Sei hilfreich aber nicht aufdringlich
- Bei Beschwerden: Zeige Verständnis und biete Lösungen an
- Bei allgemeinen Anfragen: Gib hilfreiche Informationen

Generiere nur die Antwort-E-Mail ohne zusätzliche Erklärungen oder Formatierung."""

        # Füge Kontext hinzu, falls vorhanden
        if context:
            prompt += f"\n\nZusätzlicher Kontext: {context}"
        
        return prompt
    
    def _call_openai(self, prompt: str) -> str:
        """Ruft OpenAI API auf und generiert eine Antwort."""
        try:
            response = openai.ChatCompletion.create(
                model=self.config['openai']['model'],
                messages=[
                    {"role": "system", "content": "Du bist ein professioneller E-Mail-Assistent, der höfliche und hilfreiche Antworten generiert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config['openai']['max_tokens'],
                temperature=self.config['openai']['temperature']
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Fehler beim OpenAI API-Aufruf: {e}")
            raise
    
    def _structure_response(self, response: str, parsed_email: Dict) -> Dict:
        """Strukturiert die generierte Antwort."""
        try:
            # Extrahiere Betreff und Inhalt
            subject, content = self._extract_subject_and_content(response, parsed_email)
            
            return {
                'original_email_id': parsed_email['id'],
                'subject': subject,
                'content': content,
                'to_email': parsed_email['sender']['email'],
                'to_name': parsed_email['sender']['name'],
                'category': parsed_email['category'],
                'priority': parsed_email['priority'],
                'generated_at': self._get_current_timestamp(),
                'confidence_score': self._calculate_confidence(response, parsed_email)
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Strukturieren der Antwort: {e}")
            return self._create_fallback_response(parsed_email)
    
    def _extract_subject_and_content(self, response: str, parsed_email: Dict) -> tuple:
        """Extrahiert Betreff und Inhalt aus der generierten Antwort."""
        # Standardmäßig verwende den ursprünglichen Betreff mit "Re:" Präfix
        subject = f"Re: {parsed_email['subject']}"
        
        # Bereinige den Inhalt
        content = response.strip()
        
        # Entferne mögliche Betreff-Zeilen am Anfang
        lines = content.split('\n')
        if lines and lines[0].startswith('Betreff:'):
            subject = lines[0].replace('Betreff:', '').strip()
            content = '\n'.join(lines[1:]).strip()
        
        return subject, content
    
    def _calculate_confidence(self, response: str, parsed_email: Dict) -> float:
        """Berechnet ein Konfidenz-Score für die generierte Antwort."""
        confidence = 0.5  # Basis-Konfidenz
        
        # Höhere Konfidenz für längere, detaillierte Antworten
        if len(response) > 100:
            confidence += 0.2
        
        # Höhere Konfidenz für Antworten mit spezifischen Elementen
        if any(keyword in response.lower() for keyword in ['danke', 'thank', 'freue', 'glad', 'hilfe', 'help']):
            confidence += 0.1
        
        # Niedrigere Konfidenz für sehr kurze Antworten
        if len(response) < 50:
            confidence -= 0.2
        
        # Niedrigere Konfidenz für Antworten mit Unsicherheitsindikatoren
        if any(keyword in response.lower() for keyword in ['vielleicht', 'maybe', 'unsicher', 'uncertain']):
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _create_fallback_response(self, parsed_email: Dict) -> Dict:
        """Erstellt eine Fallback-Antwort bei Fehlern."""
        fallback_content = f"""Sehr geehrte/r {parsed_email['sender']['name']},

vielen Dank für Ihre E-Mail.

Ich habe Ihre Nachricht erhalten und werde mich so schnell wie möglich bei Ihnen melden.

Mit freundlichen Grüßen
[Automatische Antwort]"""

        return {
            'original_email_id': parsed_email['id'],
            'subject': f"Re: {parsed_email['subject']}",
            'content': fallback_content,
            'to_email': parsed_email['sender']['email'],
            'to_name': parsed_email['sender']['name'],
            'category': parsed_email['category'],
            'priority': parsed_email['priority'],
            'generated_at': self._get_current_timestamp(),
            'confidence_score': 0.3,
            'is_fallback': True
        }
    
    def _get_current_timestamp(self) -> str:
        """Gibt den aktuellen Zeitstempel zurück."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def validate_response(self, response: Dict) -> bool:
        """Validiert eine generierte Antwort."""
        required_fields = ['subject', 'content', 'to_email']
        
        for field in required_fields:
            if field not in response or not response[field]:
                self.logger.warning(f"Fehlendes oder leeres Feld in Antwort: {field}")
                return False
        
        # Prüfe Mindestlänge der Antwort
        if len(response['content']) < 20:
            self.logger.warning("Antwort ist zu kurz")
            return False
        
        # Prüfe auf unangemessene Inhalte
        inappropriate_keywords = ['spam', 'casino', 'viagra', 'lottery']
        content_lower = response['content'].lower()
        if any(keyword in content_lower for keyword in inappropriate_keywords):
            self.logger.warning("Antwort enthält unangemessene Inhalte")
            return False
        
        return True
    
    def improve_response(self, response: Dict, feedback: str) -> Dict:
        """Verbessert eine Antwort basierend auf Feedback."""
        try:
            prompt = f"""Verbessere die folgende E-Mail-Antwort basierend auf dem Feedback:

Ursprüngliche Antwort:
Betreff: {response['subject']}
Inhalt: {response['content']}

Feedback: {feedback}

Generiere eine verbesserte Version der Antwort."""

            improved_content = self._call_openai(prompt)
            
            improved_response = response.copy()
            improved_response['content'] = improved_content
            improved_response['improved_at'] = self._get_current_timestamp()
            improved_response['improvement_feedback'] = feedback
            
            self.logger.info("Antwort erfolgreich verbessert")
            return improved_response
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbessern der Antwort: {e}")
            return response

if __name__ == "__main__":
    # Test des E-Mail-Responders
    logging.basicConfig(level=logging.INFO)
    
    test_parsed_email = {
        'id': '1',
        'sender': {
            'name': 'Max Mustermann',
            'email': 'max.mustermann@example.com'
        },
        'subject': 'Anfrage zu Produkt',
        'content': 'Hallo, ich interessiere mich für Ihr Produkt. Können Sie mir mehr Informationen geben?',
        'category': 'inquiry',
        'priority': 'normal'
    }
    
    responder = EmailResponder()
    response = responder.generate_response(test_parsed_email)
    
    print("Generierte Antwort:")
    print(f"Betreff: {response['subject']}")
    print(f"An: {response['to_name']} ({response['to_email']})")
    print(f"Inhalt: {response['content']}")
    print(f"Konfidenz: {response['confidence_score']}")