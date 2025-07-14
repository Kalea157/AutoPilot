import openai
import logging
import yaml
from typing import Dict, Optional
import json

class EmailResponder:
    """Generiert passende E-Mail-Antworten mit GPT-4o"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.logger = logging.getLogger(__name__)
        self._setup_openai()
        
    def _load_config(self, config_path: str) -> dict:
        """Lädt die Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            raise Exception(f"Fehler beim Laden der Konfiguration: {e}")
    
    def _setup_openai(self):
        """Konfiguriert OpenAI Client"""
        try:
            openai.api_key = self.config['openai']['api_key']
            self.logger.info("OpenAI Client konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei OpenAI-Konfiguration: {e}")
            raise
    
    def generate_response(self, email_info: Dict) -> Dict:
        """Generiert eine passende Antwort für eine E-Mail"""
        try:
            # Erstelle den Prompt für GPT-4o
            prompt = self._create_prompt(email_info)
            
            # Generiere Antwort mit OpenAI
            response = openai.ChatCompletion.create(
                model=self.config['openai']['model'],
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config['openai']['max_tokens'],
                temperature=self.config['openai']['temperature']
            )
            
            generated_response = response.choices[0].message.content.strip()
            
            # Analysiere die generierte Antwort
            analyzed_response = self._analyze_response(generated_response, email_info)
            
            self.logger.info(f"Antwort generiert für E-Mail: {email_info.get('subject', 'Unbekannt')}")
            
            return {
                'original_email': email_info,
                'generated_response': generated_response,
                'subject': analyzed_response['subject'],
                'body': analyzed_response['body'],
                'tone': analyzed_response['tone'],
                'language': analyzed_response['language'],
                'confidence': analyzed_response['confidence']
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Generieren der Antwort: {e}")
            return self._generate_fallback_response(email_info)
    
    def _get_system_prompt(self) -> str:
        """Erstellt den System-Prompt für GPT-4o"""
        return """Du bist ein professioneller E-Mail-Assistent. Deine Aufgabe ist es, höfliche, hilfreiche und angemessene E-Mail-Antworten zu generieren.

WICHTIGE REGELN:
1. Antworte in der gleichen Sprache wie die ursprüngliche E-Mail
2. Sei höflich und professionell
3. Beantworte alle Fragen vollständig
4. Halte die Antwort prägnant aber vollständig
5. Verwende eine angemessene Anrede und Grußformel
6. Berücksichtige den Kontext und die Kategorie der E-Mail
7. Bei Support-Anfragen: Sei hilfsbereit und lösungsorientiert
8. Bei Verkaufsanfragen: Sei informativ und serviceorientiert
9. Bei Beschwerden: Sei verständnisvoll und lösungsorientiert

FORMAT:
- Antworte mit einer JSON-Struktur
- Enthalte: subject, body, tone, language, confidence
- subject: Betreff der Antwort (ohne Re:, Fwd: etc.)
- body: Vollständiger E-Mail-Text mit Anrede und Grußformel
- tone: formal, semi-formal, oder casual
- language: german oder english
- confidence: 0.0 bis 1.0 (wie sicher bist du bei der Antwort)"""
    
    def _create_prompt(self, email_info: Dict) -> str:
        """Erstellt den User-Prompt für GPT-4o"""
        sender_name = email_info.get('sender_name', 'Unbekannt')
        sender_email = email_info.get('sender_email', '')
        subject = email_info.get('subject', '')
        content = email_info.get('content', '')
        category = email_info.get('category', 'general')
        priority = email_info.get('priority', 'normal')
        language = email_info.get('language', 'unknown')
        sentiment = email_info.get('sentiment', 'neutral')
        
        prompt = f"""
E-Mail-Details:
- Absender: {sender_name} ({sender_email})
- Betreff: {subject}
- Inhalt: {content}
- Kategorie: {category}
- Priorität: {priority}
- Sprache: {language}
- Stimmung: {sentiment}

Bitte generiere eine passende Antwort. Berücksichtige:
1. Die Kategorie der E-Mail ({category})
2. Die Priorität ({priority})
3. Die Stimmung des Absenders ({sentiment})
4. Antworte in der gleichen Sprache wie die ursprüngliche E-Mail

Antworte nur mit der JSON-Struktur (subject, body, tone, language, confidence).
"""
        return prompt
    
    def _analyze_response(self, generated_response: str, email_info: Dict) -> Dict:
        """Analysiert die generierte Antwort"""
        try:
            # Versuche JSON zu parsen
            if generated_response.startswith('{') and generated_response.endswith('}'):
                response_data = json.loads(generated_response)
                return {
                    'subject': response_data.get('subject', 'Antwort'),
                    'body': response_data.get('body', generated_response),
                    'tone': response_data.get('tone', 'formal'),
                    'language': response_data.get('language', email_info.get('language', 'german')),
                    'confidence': response_data.get('confidence', 0.8)
                }
            else:
                # Fallback: Verwende die Antwort als Body
                return {
                    'subject': f"Re: {email_info.get('subject', 'Antwort')}",
                    'body': generated_response,
                    'tone': 'formal',
                    'language': email_info.get('language', 'german'),
                    'confidence': 0.7
                }
        except json.JSONDecodeError:
            self.logger.warning("Fehler beim Parsen der JSON-Antwort, verwende Fallback")
            return {
                'subject': f"Re: {email_info.get('subject', 'Antwort')}",
                'body': generated_response,
                'tone': 'formal',
                'language': email_info.get('language', 'german'),
                'confidence': 0.6
            }
    
    def _generate_fallback_response(self, email_info: Dict) -> Dict:
        """Generiert eine Fallback-Antwort bei Fehlern"""
        language = email_info.get('language', 'german')
        sender_name = email_info.get('sender_name', '')
        
        if language == 'english':
            subject = f"Re: {email_info.get('subject', 'Your inquiry')}"
            body = f"""Dear {sender_name if sender_name else 'Sir/Madam'},

Thank you for your email. I have received your message and will get back to you as soon as possible.

Best regards,
Your Email Assistant"""
        else:
            subject = f"Re: {email_info.get('subject', 'Ihre Anfrage')}"
            body = f"""Sehr geehrte{r' ' + sender_name if sender_name else ' Damen und Herren'},

vielen Dank für Ihre E-Mail. Ich habe Ihre Nachricht erhalten und werde mich so schnell wie möglich bei Ihnen melden.

Mit freundlichen Grüßen
Ihr E-Mail-Assistent"""
        
        return {
            'original_email': email_info,
            'generated_response': body,
            'subject': subject,
            'body': body,
            'tone': 'formal',
            'language': language,
            'confidence': 0.5
        }
    
    def improve_response(self, response: Dict, feedback: str) -> Dict:
        """Verbessert eine Antwort basierend auf Feedback"""
        try:
            prompt = f"""
Die folgende E-Mail-Antwort wurde generiert, aber es gibt Feedback zur Verbesserung:

ORIGINALE E-MAIL:
{response['original_email'].get('content', '')}

GENERIERTE ANTWORT:
{response['body']}

FEEDBACK:
{feedback}

Bitte verbessere die Antwort basierend auf dem Feedback. Antworte nur mit der JSON-Struktur (subject, body, tone, language, confidence).
"""
            
            improved_response = openai.ChatCompletion.create(
                model=self.config['openai']['model'],
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config['openai']['max_tokens'],
                temperature=self.config['openai']['temperature']
            )
            
            improved_content = improved_response.choices[0].message.content.strip()
            analyzed_improved = self._analyze_response(improved_content, response['original_email'])
            
            return {
                'original_email': response['original_email'],
                'generated_response': analyzed_improved['body'],
                'subject': analyzed_improved['subject'],
                'body': analyzed_improved['body'],
                'tone': analyzed_improved['tone'],
                'language': analyzed_improved['language'],
                'confidence': analyzed_improved['confidence'],
                'improved': True
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Verbessern der Antwort: {e}")
            return response


if __name__ == "__main__":
    # Test des E-Mail-Responders
    logging.basicConfig(level=logging.INFO)
    
    # Test-E-Mail-Daten
    test_email_info = {
        'sender_name': 'Max Mustermann',
        'sender_email': 'max.mustermann@example.com',
        'subject': 'Anfrage zu Ihrem Produkt',
        'content': 'Hallo, ich interessiere mich für Ihr Produkt. Können Sie mir bitte mehr Informationen geben?',
        'category': 'inquiry',
        'priority': 'normal',
        'language': 'german',
        'sentiment': 'neutral',
        'requires_response': True
    }
    
    responder = EmailResponder()
    response = responder.generate_response(test_email_info)
    
    print("Generierte Antwort:")
    print(f"Betreff: {response['subject']}")
    print(f"Sprache: {response['language']}")
    print(f"Ton: {response['tone']}")
    print(f"Vertrauen: {response['confidence']}")
    print(f"Inhalt:\n{response['body']}")