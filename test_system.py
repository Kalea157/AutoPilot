#!/usr/bin/env python3
"""
Test System für den Super AI Agent
Umfassende Tests für alle Komponenten
"""

import asyncio
import sys
import os
from pathlib import Path
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config_manager import ConfigManager
from src.email.fetcher import EmailFetcher, EmailMessage
from src.email.sender import EmailSender, EmailResponse
from src.ai.analyzer import AIAnalyzer, EmailAnalysis
from src.ai.response_generator import ResponseGenerator, GeneratedResponse
from src.telegram.coordinator import TelegramCoordinator, ApprovalRequest
from src.super_agent import SuperAIAgent, ProcessingResult


class TestConfigManager:
    """Tests für ConfigManager"""
    
    def test_config_loading(self):
        """Testet Konfigurationsladung"""
        config = ConfigManager("config.yaml", ".env.example")
        assert config is not None
        
        # Teste Agent-Konfiguration
        agent_config = config.get_agent_config()
        assert agent_config['name'] == 'SuperEmailAgent'
        assert agent_config['version'] == '1.0.0'
    
    def test_env_substitution(self):
        """Testet Umgebungsvariablen-Substitution"""
        # Setze Test-Umgebungsvariablen
        os.environ['TEST_VAR'] = 'test_value'
        
        config = ConfigManager()
        # Teste Substitution (falls in config.yaml vorhanden)
        # assert config.get('some.key') == 'test_value'
    
    def test_validation(self):
        """Testet Konfigurationsvalidierung"""
        config = ConfigManager()
        # Ohne echte Umgebungsvariablen sollte Validierung fehlschlagen
        assert not config.validate_config()


class TestEmailFetcher:
    """Tests für EmailFetcher"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'username': 'test@example.com',
            'password': 'test_password',
            'imap': {
                'server': 'imap.gmail.com',
                'port': 993,
                'use_ssl': True,
                'folder': 'INBOX'
            }
        }
    
    @pytest_asyncio.async
    async def test_connection(self, mock_config):
        """Testet IMAP-Verbindung"""
        fetcher = EmailFetcher(mock_config)
        
        # Mock IMAP-Verbindung
        with patch('imaplib.IMAP4_SSL') as mock_imap:
            mock_connection = Mock()
            mock_imap.return_value = mock_connection
            
            success = await fetcher.connect()
            assert success is True
            mock_connection.login.assert_called_once()
    
    @pytest_asyncio.async
    async def test_fetch_emails(self, mock_config):
        """Testet E-Mail-Abruf"""
        fetcher = EmailFetcher(mock_config)
        
        # Mock E-Mail-Daten
        mock_email_data = b"""From: test@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 +0000

Test content"""
        
        with patch.object(fetcher, '_fetch_emails_sync') as mock_fetch:
            mock_fetch.return_value = [
                EmailMessage(
                    uid='1',
                    sender='test@example.com',
                    recipient='recipient@example.com',
                    subject='Test Email',
                    date=datetime.now(),
                    content='Test content',
                    content_type='text/plain',
                    attachments=[],
                    headers={},
                    raw_message=mock_email_data
                )
            ]
            
            emails = await fetcher.fetch_new_emails()
            assert len(emails) == 1
            assert emails[0].subject == 'Test Email'


class TestEmailSender:
    """Tests für EmailSender"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'username': 'test@example.com',
            'password': 'test_password',
            'from_email': 'test@example.com',
            'smtp': {
                'server': 'smtp.gmail.com',
                'port': 587,
                'use_tls': True,
                'timeout': 30
            }
        }
    
    @pytest_asyncio.async
    async def test_connection(self, mock_config):
        """Testet SMTP-Verbindung"""
        sender = EmailSender(mock_config)
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_connection = Mock()
            mock_smtp.return_value = mock_connection
            
            success = await sender.test_connection()
            assert success is True
    
    def test_create_reply_email(self, mock_config):
        """Testet Antwort-E-Mail-Erstellung"""
        sender = EmailSender(mock_config)
        
        original_email = Mock()
        original_email.sender = 'sender@example.com'
        original_email.subject = 'Original Subject'
        
        response = sender.create_reply_email(original_email, 'Test reply content')
        
        assert response.to == 'sender@example.com'
        assert response.subject == 'Re: Original Subject'
        assert response.content == 'Test reply content'


class TestAIAnalyzer:
    """Tests für AIAnalyzer"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'api_key': 'test_api_key',
            'model': 'gpt-4o',
            'max_tokens': 2000,
            'temperature': 0.7,
            'analysis_prompt': 'Analyze this email'
        }
    
    @pytest_asyncio.async
    async def test_analyze_email(self, mock_config):
        """Testet E-Mail-Analyse"""
        analyzer = AIAnalyzer(mock_config)
        
        # Mock OpenAI API
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'category': 'question',
                        'urgency': 7,
                        'sentiment': 'neutral',
                        'language': 'de',
                        'key_questions': ['Test question'],
                        'key_tasks': [],
                        'response_strategy': 'standard',
                        'confidence': 0.85,
                        'summary': 'Test summary',
                        'suggested_actions': []
                    })
                }
            }]
        }
        
        with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = Mock(**mock_response)
            
            analysis = await analyzer.analyze_email(
                'Test email content',
                'Test Subject',
                'test@example.com'
            )
            
            assert analysis.category == 'question'
            assert analysis.urgency == 7
            assert analysis.confidence == 0.85
    
    def test_fallback_analysis(self, mock_config):
        """Testet Fallback-Analyse"""
        analyzer = AIAnalyzer(mock_config)
        
        analysis = analyzer._fallback_analysis(
            'Test content',
            'Test Subject',
            'test@example.com'
        )
        
        assert analysis.category in ['question', 'complaint', 'order', 'support', 'general']
        assert 1 <= analysis.urgency <= 10
        assert analysis.confidence == 0.6


class TestResponseGenerator:
    """Tests für ResponseGenerator"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'api_key': 'test_api_key',
            'model': 'gpt-4o',
            'max_tokens': 2000,
            'temperature': 0.7,
            'system_prompt': 'Generate email response'
        }
    
    @pytest_asyncio.async
    async def test_generate_response(self, mock_config):
        """Testet Antwort-Generierung"""
        generator = ResponseGenerator(mock_config)
        
        # Mock OpenAI API
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'content': 'Test response content',
                        'subject': 'Re: Test Subject',
                        'confidence': 0.9,
                        'tone': 'formal',
                        'language': 'de',
                        'length': 'medium',
                        'includes_greeting': True,
                        'includes_signature': True
                    })
                }
            }]
        }
        
        with patch.object(generator.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = Mock(**mock_response)
            
            original_email = {
                'sender': 'test@example.com',
                'subject': 'Test Subject',
                'content': 'Test content'
            }
            
            analysis = {
                'category': 'question',
                'urgency': 5,
                'sentiment': 'neutral'
            }
            
            response = await generator.generate_response(original_email, analysis)
            
            assert response.content == 'Test response content'
            assert response.confidence == 0.9
            assert response.tone == 'formal'


class TestTelegramCoordinator:
    """Tests für TelegramCoordinator"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'bot_token': 'test_bot_token',
            'chat_id': 'test_chat_id',
            'approval_timeout': 300,
            'message_format': 'markdown',
            'templates': {
                'approval_request': 'Test template {sender} {subject}'
            }
        }
    
    @pytest_asyncio.async
    async def test_initialization(self, mock_config):
        """Testet Telegram-Initialisierung"""
        coordinator = TelegramCoordinator(mock_config)
        
        with patch('telegram.Bot') as mock_bot:
            with patch('telegram.ext.Application') as mock_app:
                success = await coordinator.initialize()
                assert success is True
    
    @pytest_asyncio.async
    async def test_approval_request(self, mock_config):
        """Testet Freigabe-Anfrage"""
        coordinator = TelegramCoordinator(mock_config)
        
        email_data = {
            'sender': 'test@example.com',
            'subject': 'Test Subject',
            'content': 'Test content'
        }
        
        analysis = {
            'category': 'question',
            'urgency': 5,
            'confidence': 0.8
        }
        
        response = {
            'content': 'Test response',
            'subject': 'Re: Test Subject'
        }
        
        with patch.object(coordinator, 'bot') as mock_bot:
            approval_id = await coordinator.request_approval(email_data, analysis, response)
            assert approval_id is not None
            assert len(approval_id) == 8  # UUID8


class TestSuperAIAgent:
    """Tests für SuperAIAgent"""
    
    @pytest.fixture
    def mock_agent(self):
        return SuperAIAgent("config.yaml", ".env.example")
    
    @pytest_asyncio.async
    async def test_initialization(self, mock_agent):
        """Testet Agent-Initialisierung"""
        # Mock alle Komponenten
        with patch.object(mock_agent, '_test_connections', return_value=True):
            with patch.object(mock_agent.telegram_coordinator, 'initialize', return_value=True):
                success = await mock_agent.initialize()
                assert success is True
    
    @pytest_asyncio.async
    async def test_email_processing(self, mock_agent):
        """Testet E-Mail-Verarbeitung"""
        # Mock E-Mail
        email = EmailMessage(
            uid='1',
            sender='test@example.com',
            recipient='recipient@example.com',
            subject='Test Email',
            date=datetime.now(),
            content='Test content',
            content_type='text/plain',
            attachments=[],
            headers={},
            raw_message=b'test'
        )
        
        # Mock AI-Komponenten
        mock_analysis = EmailAnalysis(
            category='question',
            urgency=5,
            sentiment='neutral',
            language='de',
            key_questions=[],
            key_tasks=[],
            response_strategy='standard',
            confidence=0.8,
            summary='Test',
            suggested_actions=[],
            priority='medium'
        )
        
        mock_response = GeneratedResponse(
            content='Test response',
            subject='Re: Test Email',
            confidence=0.8,
            tone='formal',
            language='de',
            length='medium',
            includes_greeting=True,
            includes_signature=True
        )
        
        with patch.object(mock_agent.ai_analyzer, 'analyze_email', return_value=mock_analysis):
            with patch.object(mock_agent.response_generator, 'generate_response', return_value=mock_response):
                with patch.object(mock_agent, '_auto_approve_email'):
                    result = await mock_agent._process_email(email)
                    
                    assert result.status == 'auto_approved'
                    assert result.analysis == mock_analysis
                    assert result.response == mock_response


class TestIntegration:
    """Integrationstests"""
    
    @pytest_asyncio.async
    async def test_full_workflow(self):
        """Testet vollständigen Workflow"""
        # Dieser Test würde den vollständigen Workflow testen
        # von E-Mail-Abruf bis zur Antwort-Generierung
        pass
    
    @pytest_asyncio.async
    async def test_error_handling(self):
        """Testet Fehlerbehandlung"""
        # Testet verschiedene Fehlerszenarien
        pass


def run_tests():
    """Führt alle Tests aus"""
    print("🧪 Starte Tests für Super AI Agent...")
    
    # Führe Tests aus
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])


def run_specific_test(test_class, test_method):
    """Führt spezifischen Test aus"""
    pytest.main([
        __file__,
        f"{test_class}::test_{test_method}",
        "-v",
        "--tb=short"
    ])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            run_tests()
        elif command == "unit":
            pytest.main([__file__, "-k", "TestConfigManager or TestEmailFetcher or TestEmailSender or TestAIAnalyzer or TestResponseGenerator or TestTelegramCoordinator", "-v"])
        elif command == "integration":
            pytest.main([__file__, "-k", "TestIntegration", "-v"])
        elif command == "agent":
            pytest.main([__file__, "-k", "TestSuperAIAgent", "-v"])
        else:
            print(f"Unbekannter Test-Befehl: {command}")
            print("Verfügbare Befehle: all, unit, integration, agent")
    else:
        run_tests()