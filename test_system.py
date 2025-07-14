"""
Test-System für den Super-KI-Agenten
"""
import asyncio
import logging
import json
from typing import Dict, Any, List
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.config_manager import ConfigManager
from src.email_fetcher import EmailFetcher, EmailData
from src.email_analyzer import EmailAnalyzer, EmailAnalysis
from src.response_generator import ResponseGenerator, GeneratedResponse
from src.telegram_coordinator import TelegramCoordinator
from src.email_sender import EmailSender
from src.decision_engine import DecisionEngine, DecisionResult
from src.super_agent import SuperAgent, ProcessingResult

class TestSuperAgent:
    """Umfassende Tests für den Super-KI-Agenten"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        # Mock-Konfiguration
        self.mock_config = {
            'email': {
                'imap': {'server': 'imap.test.com', 'port': 993, 'use_ssl': True},
                'smtp': {'server': 'smtp.test.com', 'port': 587, 'use_tls': True},
                'fetch_interval': 30,
                'max_emails_per_fetch': 10,
                'auto_delete_processed': False
            },
            'ai': {
                'model': 'gpt-4o',
                'max_tokens': 2000,
                'temperature': 0.7,
                'confidence_thresholds': {
                    'auto_approve': 0.95,
                    'auto_reject': 0.3,
                    'require_human': 0.7
                },
                'analysis_prompts': {
                    'content_analysis': 'Test prompt',
                    'response_generation': 'Test response prompt'
                }
            },
            'telegram': {
                'bot_token': 'test_token',
                'admin_chat_id': 'test_chat_id',
                'notification_chat_id': 'test_notification_id',
                'auto_approve_commands': ['ja', 'yes'],
                'reject_commands': ['nein', 'no'],
                'edit_commands': ['edit'],
                'timeout_seconds': 300
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/test.log',
                'max_size_mb': 10,
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'features': {
                'auto_categorization': True,
                'priority_detection': True,
                'multilingual_support': True,
                'sentiment_analysis': True,
                'auto_archiving': True,
                'smart_filtering': True,
                'response_templates': True,
                'escalation_rules': True
            },
            'security': {
                'encrypt_sensitive_data': True,
                'max_retry_attempts': 3,
                'rate_limiting': True,
                'suspicious_content_detection': True
            }
        }
        
        # Test-E-Mail-Daten
        self.test_email = EmailData(
            uid="test_123",
            subject="Test E-Mail",
            sender="test@example.com",
            recipient="agent@company.com",
            date=datetime.now(),
            body="Dies ist eine Test-E-Mail für den Super-KI-Agenten.",
            html_body="<p>Dies ist eine Test-E-Mail für den Super-KI-Agenten.</p>",
            attachments=[],
            headers={},
            raw_email=b"test email data"
        )
        
        # Test-Analyse
        self.test_analysis = EmailAnalysis(
            category="Inquiry",
            sentiment="neutral",
            language="DE",
            urgency="niedrig",
            required_action="Standardantwort senden",
            key_questions=["Test-Frage"],
            key_concerns=[],
            confidence_level=0.85,
            tone="formal",
            priority_score=0.5,
            is_spam=False,
            requires_human=False,
            suggested_response_type="auto",
            extracted_info={}
        )
        
        # Test-Antwort
        self.test_response = GeneratedResponse(
            subject="Re: Test E-Mail",
            body="Vielen Dank für Ihre Nachricht. Wir werden uns umgehend um Ihr Anliegen kümmern.",
            language="DE",
            tone="formal",
            confidence_level=0.9,
            suggested_improvements=[],
            is_ready_to_send=True,
            requires_review=False
        )
    
    @patch('src.config_manager.os.getenv')
    def test_config_manager(self, mock_getenv):
        """Testet ConfigManager"""
        mock_getenv.return_value = "test_value"
        
        config_manager = ConfigManager()
        
        # Teste Konfigurationsladung
        assert config_manager.config is not None
        
        # Teste E-Mail-Konfiguration
        email_config = config_manager.get_email_config()
        assert email_config is not None
        
        # Teste AI-Konfiguration
        ai_config = config_manager.get_ai_config()
        assert ai_config is not None
    
    def test_email_fetcher(self):
        """Testet EmailFetcher"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_email_config.return_value = self.mock_config['email']
            
            fetcher = EmailFetcher(mock_config.return_value)
            
            # Teste Verbindung
            with patch('imaplib.IMAP4_SSL') as mock_imap:
                mock_imap.return_value.login.return_value = ('OK', [b'Logged in'])
                assert fetcher.connect() == True
    
    @patch('openai.ChatCompletion.create')
    def test_email_analyzer(self, mock_openai):
        """Testet EmailAnalyzer"""
        # Mock OpenAI Response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "category": "Inquiry",
            "sentiment": "neutral",
            "language": "DE",
            "urgency": "niedrig",
            "required_action": "Standardantwort senden",
            "key_questions": ["Test-Frage"],
            "key_concerns": [],
            "confidence_level": 0.85,
            "tone": "formal",
            "priority_score": 0.5,
            "is_spam": False,
            "requires_human": False,
            "suggested_response_type": "auto",
            "extracted_info": {}
        })
        mock_openai.return_value = mock_response
        
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_ai_config.return_value = self.mock_config['ai']
            mock_config.return_value.get_features_config.return_value = self.mock_config['features']
            
            analyzer = EmailAnalyzer(mock_config.return_value)
            
            # Teste E-Mail-Analyse
            analysis = analyzer.analyze_email(self.test_email)
            assert analysis is not None
            assert analysis.category == "Inquiry"
            assert analysis.confidence_level > 0
    
    @patch('openai.ChatCompletion.create')
    def test_response_generator(self, mock_openai):
        """Testet ResponseGenerator"""
        # Mock OpenAI Response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "subject": "Re: Test E-Mail",
            "body": "Vielen Dank für Ihre Nachricht.",
            "language": "DE",
            "tone": "formal",
            "confidence_level": 0.9,
            "suggested_improvements": [],
            "is_ready_to_send": True,
            "requires_review": False
        })
        mock_openai.return_value = mock_response
        
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_ai_config.return_value = self.mock_config['ai']
            
            generator = ResponseGenerator(mock_config.return_value)
            
            # Teste Antwortgenerierung
            response = generator.generate_response(self.test_email, self.test_analysis)
            assert response is not None
            assert response.subject == "Re: Test E-Mail"
            assert response.confidence_level > 0
    
    def test_decision_engine(self):
        """Testet DecisionEngine"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_ai_config.return_value = self.mock_config['ai']
            mock_config.return_value.get_security_config.return_value = self.mock_config['security']
            
            engine = DecisionEngine(mock_config.return_value)
            
            # Teste Entscheidungsfindung
            decision = engine.make_decision(self.test_email, self.test_analysis, self.test_response)
            assert decision is not None
            assert decision.action in ['auto_send', 'require_approval', 'reject', 'escalate']
            assert 0 <= decision.confidence <= 1
    
    def test_email_sender(self):
        """Testet EmailSender"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_email_config.return_value = self.mock_config['email']
            
            sender = EmailSender(mock_config.return_value)
            
            # Teste SMTP-Info
            smtp_info = sender.get_smtp_info()
            assert smtp_info['server'] == 'smtp.test.com'
            assert smtp_info['port'] == 587
    
    @pytest.mark.asyncio
    async def test_telegram_coordinator(self):
        """Testet TelegramCoordinator"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_telegram_config.return_value = self.mock_config['telegram']
            
            coordinator = TelegramCoordinator(mock_config.return_value)
            
            # Teste Bot-Setup
            assert coordinator.bot is not None
            assert coordinator.application is not None
    
    @pytest.mark.asyncio
    async def test_super_agent_integration(self):
        """Testet SuperAgent Integration"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_email_config.return_value = self.mock_config['email']
            mock_config.return_value.get_ai_config.return_value = self.mock_config['ai']
            mock_config.return_value.get_telegram_config.return_value = self.mock_config['telegram']
            mock_config.return_value.get_features_config.return_value = self.mock_config['features']
            mock_config.return_value.get_security_config.return_value = self.mock_config['security']
            
            agent = SuperAgent()
            
            # Teste Initialisierung
            assert agent.running == False
            assert len(agent.processing_queue) == 0
            assert len(agent.pending_approvals) == 0
    
    def test_processing_result(self):
        """Testet ProcessingResult"""
        result = ProcessingResult(
            email_data=self.test_email,
            analysis=self.test_analysis,
            response=self.test_response,
            decision=DecisionResult(
                action='auto_send',
                confidence=0.85,
                reason='Test',
                requires_human=False,
                priority='medium',
                estimated_response_time=1
            ),
            status='approved',
            processing_time=1.5
        )
        
        assert result.email_data == self.test_email
        assert result.status == 'approved'
        assert result.processing_time == 1.5

class TestEmailProcessing:
    """Tests für E-Mail-Verarbeitung"""
    
    def test_spam_detection(self):
        """Testet Spam-Erkennung"""
        spam_email = EmailData(
            uid="spam_123",
            subject="URGENT: You won $1,000,000!",
            sender="spam@lottery.com",
            recipient="user@company.com",
            date=datetime.now(),
            body="Click here to claim your prize! Limited time offer!",
            html_body="<p>Click here to claim your prize!</p>",
            attachments=[],
            headers={},
            raw_email=b"spam email data"
        )
        
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_ai_config.return_value = {
                'model': 'gpt-4o',
                'max_tokens': 2000,
                'temperature': 0.7,
                'confidence_thresholds': {'auto_approve': 0.95, 'auto_reject': 0.3, 'require_human': 0.7},
                'analysis_prompts': {'content_analysis': 'Test', 'response_generation': 'Test'}
            }
            mock_config.return_value.get_features_config.return_value = {
                'auto_categorization': True,
                'priority_detection': True,
                'multilingual_support': True,
                'sentiment_analysis': True,
                'auto_archiving': True,
                'smart_filtering': True,
                'response_templates': True,
                'escalation_rules': True
            }
            
            analyzer = EmailAnalyzer(mock_config.return_value)
            
            # Teste Spam-Erkennung
            is_spam = analyzer._check_spam_indicators(spam_email)
            assert is_spam == True
    
    def test_language_detection(self):
        """Testet Spracherkennung"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_ai_config.return_value = {
                'model': 'gpt-4o',
                'max_tokens': 2000,
                'temperature': 0.7,
                'confidence_thresholds': {'auto_approve': 0.95, 'auto_reject': 0.3, 'require_human': 0.7},
                'analysis_prompts': {'content_analysis': 'Test', 'response_generation': 'Test'}
            }
            mock_config.return_value.get_features_config.return_value = {
                'auto_categorization': True,
                'priority_detection': True,
                'multilingual_support': True,
                'sentiment_analysis': True,
                'auto_archiving': True,
                'smart_filtering': True,
                'response_templates': True,
                'escalation_rules': True
            }
            
            analyzer = EmailAnalyzer(mock_config.return_value)
            
            # Teste deutsche Sprache
            german_text = "Dies ist ein deutscher Text."
            assert analyzer._detect_language(german_text) == "DE"
            
            # Teste englische Sprache
            english_text = "This is an English text."
            assert analyzer._detect_language(english_text) == "EN"

class TestPerformance:
    """Performance-Tests"""
    
    def test_decision_engine_performance(self):
        """Testet DecisionEngine Performance"""
        with patch('src.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get_ai_config.return_value = {
                'model': 'gpt-4o',
                'max_tokens': 2000,
                'temperature': 0.7,
                'confidence_thresholds': {'auto_approve': 0.95, 'auto_reject': 0.3, 'require_human': 0.7},
                'analysis_prompts': {'content_analysis': 'Test', 'response_generation': 'Test'}
            }
            mock_config.return_value.get_security_config.return_value = {
                'encrypt_sensitive_data': True,
                'max_retry_attempts': 3,
                'rate_limiting': True,
                'suspicious_content_detection': True
            }
            
            engine = DecisionEngine(mock_config.return_value)
            
            # Performance-Test mit vielen E-Mails
            start_time = datetime.now()
            
            for i in range(100):
                email = EmailData(
                    uid=f"test_{i}",
                    subject=f"Test E-Mail {i}",
                    sender=f"test{i}@example.com",
                    recipient="agent@company.com",
                    date=datetime.now(),
                    body=f"Test E-Mail Inhalt {i}",
                    html_body=f"<p>Test E-Mail Inhalt {i}</p>",
                    attachments=[],
                    headers={},
                    raw_email=b"test email data"
                )
                
                analysis = EmailAnalysis(
                    category="Inquiry",
                    sentiment="neutral",
                    language="DE",
                    urgency="niedrig",
                    required_action="Standardantwort senden",
                    key_questions=[],
                    key_concerns=[],
                    confidence_level=0.8,
                    tone="formal",
                    priority_score=0.5,
                    is_spam=False,
                    requires_human=False,
                    suggested_response_type="auto",
                    extracted_info={}
                )
                
                response = GeneratedResponse(
                    subject=f"Re: Test E-Mail {i}",
                    body="Test Antwort",
                    language="DE",
                    tone="formal",
                    confidence_level=0.9,
                    suggested_improvements=[],
                    is_ready_to_send=True,
                    requires_review=False
                )
                
                decision = engine.make_decision(email, analysis, response)
                assert decision is not None
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Sollte unter 10 Sekunden für 100 E-Mails sein
            assert processing_time < 10

def run_tests():
    """Führt alle Tests aus"""
    print("🧪 Starte Super-KI-Agent Tests...")
    
    # Konfiguriere Logging für Tests
    logging.basicConfig(level=logging.WARNING)
    
    # Führe Tests aus
    test_classes = [
        TestSuperAgent,
        TestEmailProcessing,
        TestPerformance
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        test_instance = test_class()
        
        # Finde alle Test-Methoden
        test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                
                # Führe Test aus
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                
                print(f"✅ {test_class.__name__}.{method_name}")
                passed_tests += 1
                
            except Exception as e:
                print(f"❌ {test_class.__name__}.{method_name}: {e}")
    
    print(f"\n📊 Test-Ergebnisse: {passed_tests}/{total_tests} Tests bestanden")
    
    if passed_tests == total_tests:
        print("🎉 Alle Tests erfolgreich!")
        return True
    else:
        print("⚠️  Einige Tests fehlgeschlagen!")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)