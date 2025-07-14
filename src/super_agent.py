"""
Super AI Agent - Haupt-Orchestrator für das E-Mail-System
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog
from pathlib import Path

# Core components
from .core.config_manager import ConfigManager

# Email components
from .email.fetcher import EmailFetcher, EmailMessage
from .email.sender import EmailSender, EmailResponse

# AI components
from .ai.analyzer import AIAnalyzer, EmailAnalysis
from .ai.response_generator import ResponseGenerator, GeneratedResponse

# Telegram components
from .telegram.coordinator import TelegramCoordinator, ApprovalRequest

logger = structlog.get_logger(__name__)


@dataclass
class ProcessingResult:
    """Datenklasse für Verarbeitungsergebnisse"""
    email_id: str
    status: str  # processed, approved, rejected, timeout, error
    analysis: Optional[EmailAnalysis] = None
    response: Optional[GeneratedResponse] = None
    processing_time: float = 0.0
    error_message: Optional[str] = None


class SuperAIAgent:
    """Haupt-Super-Agent für autonome E-Mail-Verarbeitung"""
    
    def __init__(self, config_path: str = "config.yaml", env_path: str = ".env"):
        # Konfiguration
        self.config_manager = ConfigManager(config_path, env_path)
        self.agent_config = self.config_manager.get_agent_config()
        self.email_config = self.config_manager.get_email_config()
        self.ai_config = self.config_manager.get_ai_config()
        self.telegram_config = self.config_manager.get_telegram_config()
        
        # Komponenten
        self.email_fetcher: Optional[EmailFetcher] = None
        self.email_sender: Optional[EmailSender] = None
        self.ai_analyzer: Optional[AIAnalyzer] = None
        self.response_generator: Optional[ResponseGenerator] = None
        self.telegram_coordinator: Optional[TelegramCoordinator] = None
        
        # Status und Statistiken
        self.is_running = False
        self.processing_queue: List[EmailMessage] = []
        self.processed_emails: Dict[str, ProcessingResult] = {}
        self.approval_pending: Dict[str, ApprovalRequest] = {}
        
        # Performance Tracking
        self.start_time = None
        self.total_processed = 0
        self.total_approved = 0
        self.total_rejected = 0
        self.total_errors = 0
        
        # Setup Logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Konfiguriert Logging"""
        logging_config = self.config_manager.get_logging_config()
        
        import structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    async def initialize(self) -> bool:
        """Initialisiert alle Komponenten"""
        try:
            logger.info("Initializing Super AI Agent", version=self.agent_config['version'])
            
            # Validiere Konfiguration
            if not self.config_manager.validate_config():
                logger.error("Configuration validation failed")
                return False
            
            # Initialisiere E-Mail-Komponenten
            self.email_fetcher = EmailFetcher(self.email_config)
            self.email_sender = EmailSender(self.email_config)
            
            # Initialisiere AI-Komponenten
            self.ai_analyzer = AIAnalyzer(self.ai_config)
            self.response_generator = ResponseGenerator(self.ai_config)
            
            # Initialisiere Telegram-Koordinator
            self.telegram_coordinator = TelegramCoordinator(self.telegram_config)
            
            # Setze Callbacks
            self._setup_telegram_callbacks()
            
            # Initialisiere Telegram
            if not await self.telegram_coordinator.initialize():
                logger.error("Failed to initialize Telegram coordinator")
                return False
            
            # Teste Verbindungen
            if not await self._test_connections():
                logger.error("Connection tests failed")
                return False
            
            logger.info("Super AI Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Super AI Agent", error=str(e))
            return False
    
    async def _test_connections(self) -> bool:
        """Testet alle Verbindungen"""
        try:
            # Teste E-Mail-Verbindungen
            if not await self.email_fetcher.connect():
                logger.error("IMAP connection test failed")
                return False
            
            if not await self.email_sender.test_connection():
                logger.error("SMTP connection test failed")
                return False
            
            logger.info("All connections tested successfully")
            return True
            
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False
    
    def _setup_telegram_callbacks(self) -> None:
        """Setzt Telegram-Callbacks"""
        if not self.telegram_coordinator:
            return
        
        self.telegram_coordinator.set_callbacks(
            on_approval=self._on_telegram_approval,
            on_rejection=self._on_telegram_rejection,
            on_edit=self._on_telegram_edit,
            on_ignore=self._on_telegram_ignore
        )
    
    async def _on_telegram_approval(self, approval_request: ApprovalRequest) -> None:
        """Callback für Telegram-Genehmigung"""
        try:
            logger.info("Telegram approval received", approval_id=approval_request.id)
            
            # Sende E-Mail
            email_response = self.email_sender.create_reply_email(
                approval_request.email_data,
                approval_request.response['content']
            )
            
            success = await self.email_sender.send_email(email_response)
            
            if success:
                # Markiere als gelesen
                await self.email_fetcher.mark_as_read(approval_request.email_data['uid'])
                
                # Update Statistiken
                self.total_approved += 1
                
                logger.info("Email sent successfully after approval", 
                           approval_id=approval_request.id)
            else:
                logger.error("Failed to send email after approval", 
                           approval_id=approval_request.id)
                
        except Exception as e:
            logger.error("Error processing telegram approval", 
                        approval_id=approval_request.id, error=str(e))
    
    async def _on_telegram_rejection(self, approval_request: ApprovalRequest) -> None:
        """Callback für Telegram-Ablehnung"""
        try:
            logger.info("Telegram rejection received", approval_id=approval_request.id)
            
            # Markiere als gelesen (ohne Antwort)
            await self.email_fetcher.mark_as_read(approval_request.email_data['uid'])
            
            # Update Statistiken
            self.total_rejected += 1
            
            logger.info("Email rejected, marked as read", approval_id=approval_request.id)
            
        except Exception as e:
            logger.error("Error processing telegram rejection", 
                        approval_id=approval_request.id, error=str(e))
    
    async def _on_telegram_edit(self, approval_request: ApprovalRequest) -> None:
        """Callback für Telegram-Bearbeitung"""
        try:
            logger.info("Telegram edit request received", approval_id=approval_request.id)
            
            # Hier könnte eine Bearbeitungsoberfläche implementiert werden
            # Für jetzt: Sende Benachrichtigung
            if self.telegram_coordinator:
                await self.telegram_coordinator._send_confirmation_message(
                    f"✏️ Bearbeitung für E-Mail-ID {approval_request.id} erforderlich.\n"
                    f"Bitte bearbeiten Sie die Antwort manuell."
                )
                
        except Exception as e:
            logger.error("Error processing telegram edit request", 
                        approval_id=approval_request.id, error=str(e))
    
    async def _on_telegram_ignore(self, approval_request: ApprovalRequest) -> None:
        """Callback für Telegram-Ignorieren"""
        try:
            logger.info("Telegram ignore received", approval_id=approval_request.id)
            
            # Markiere als gelesen (ohne Antwort)
            await self.email_fetcher.mark_as_read(approval_request.email_data['uid'])
            
            logger.info("Email ignored, marked as read", approval_id=approval_request.id)
            
        except Exception as e:
            logger.error("Error processing telegram ignore", 
                        approval_id=approval_request.id, error=str(e))
    
    async def start(self) -> None:
        """Startet den Super-Agenten"""
        if self.is_running:
            logger.warning("Super AI Agent is already running")
            return
        
        try:
            logger.info("Starting Super AI Agent")
            self.is_running = True
            self.start_time = datetime.now()
            
            # Starte Hauptschleife
            await self._main_loop()
            
        except Exception as e:
            logger.error("Error in main loop", error=str(e))
            self.is_running = False
        finally:
            await self.shutdown()
    
    async def _main_loop(self) -> None:
        """Hauptverarbeitungsschleife"""
        check_interval = self.email_config['imap'].get('check_interval', 60)
        
        while self.is_running:
            try:
                # Hole neue E-Mails
                new_emails = await self.email_fetcher.fetch_new_emails(
                    self.email_config['imap'].get('max_emails_per_check', 10)
                )
                
                if new_emails:
                    logger.info("Processing new emails", count=len(new_emails))
                    
                    # Verarbeite E-Mails parallel
                    tasks = []
                    for email in new_emails:
                        task = asyncio.create_task(self._process_email(email))
                        tasks.append(task)
                    
                    # Warte auf alle Tasks
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Verarbeite Ergebnisse
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error("Email processing failed", error=str(result))
                            self.total_errors += 1
                        else:
                            self.total_processed += 1
                
                # Warte bis zur nächsten Prüfung
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error("Error in main loop iteration", error=str(e))
                await asyncio.sleep(10)  # Kurze Pause bei Fehlern
    
    async def _process_email(self, email: EmailMessage) -> ProcessingResult:
        """Verarbeitet eine einzelne E-Mail"""
        start_time = time.time()
        result = ProcessingResult(
            email_id=email.uid,
            status='error',
            processing_time=0.0
        )
        
        try:
            logger.info("Processing email", uid=email.uid, subject=email.subject)
            
            # 1. Analysiere E-Mail
            analysis = await self.ai_analyzer.analyze_email(
                email.content, email.subject, email.sender
            )
            result.analysis = analysis
            
            # 2. Generiere Antwort
            email_data = {
                'uid': email.uid,
                'sender': email.sender,
                'subject': email.subject,
                'content': email.content,
                'date': email.date
            }
            
            analysis_dict = {
                'category': analysis.category,
                'urgency': analysis.urgency,
                'sentiment': analysis.sentiment,
                'language': analysis.language,
                'key_questions': analysis.key_questions,
                'key_tasks': analysis.key_tasks,
                'response_strategy': analysis.response_strategy,
                'confidence': analysis.confidence,
                'priority': analysis.priority
            }
            
            response = await self.response_generator.generate_response(
                email_data, analysis_dict
            )
            result.response = response
            
            # 3. Entscheide über automatische Freigabe
            if analysis.confidence >= self.agent_config['auto_approve_threshold']:
                # Automatische Freigabe
                await self._auto_approve_email(email, response)
                result.status = 'auto_approved'
                
            elif analysis.confidence >= self.agent_config['confidence_threshold']:
                # Manuelle Freigabe erforderlich
                approval_id = await self.telegram_coordinator.request_approval(
                    email_data, analysis_dict, {
                        'content': response.content,
                        'subject': response.subject,
                        'confidence': response.confidence
                    }
                )
                
                if approval_id:
                    result.status = 'pending_approval'
                else:
                    result.status = 'approval_failed'
            else:
                # Zu niedrige Konfidenz - ignoriere
                result.status = 'low_confidence'
                logger.info("Email ignored due to low confidence", 
                           uid=email.uid, confidence=analysis.confidence)
            
            result.processing_time = time.time() - start_time
            logger.info("Email processing completed", 
                       uid=email.uid, status=result.status, 
                       processing_time=result.processing_time)
            
        except Exception as e:
            result.status = 'error'
            result.error_message = str(e)
            result.processing_time = time.time() - start_time
            logger.error("Email processing failed", 
                        uid=email.uid, error=str(e))
        
        # Speichere Ergebnis
        self.processed_emails[email.uid] = result
        return result
    
    async def _auto_approve_email(self, email: EmailMessage, response: GeneratedResponse) -> None:
        """Genehmigt und sendet E-Mail automatisch"""
        try:
            # Erstelle E-Mail-Antwort
            email_response = self.email_sender.create_reply_email(
                email, response.content
            )
            
            # Sende E-Mail
            success = await self.email_sender.send_email(email_response)
            
            if success:
                # Markiere als gelesen
                await self.email_fetcher.mark_as_read(email.uid)
                
                # Benachrichtige über automatische Freigabe
                if self.telegram_coordinator:
                    await self.telegram_coordinator._send_confirmation_message(
                        f"🤖 **Automatische Freigabe**\n\n"
                        f"E-Mail automatisch beantwortet:\n"
                        f"**Von:** {email.sender}\n"
                        f"**Betreff:** {email.subject}\n"
                        f"**Vertrauen:** {int(response.confidence * 100)}%\n\n"
                        f"Antwort wurde gesendet."
                    )
                
                self.total_approved += 1
                logger.info("Email auto-approved and sent", uid=email.uid)
            else:
                logger.error("Failed to send auto-approved email", uid=email.uid)
                
        except Exception as e:
            logger.error("Error in auto-approval", uid=email.uid, error=str(e))
    
    async def stop(self) -> None:
        """Stoppt den Super-Agenten"""
        logger.info("Stopping Super AI Agent")
        self.is_running = False
    
    async def shutdown(self) -> None:
        """Beendet alle Komponenten"""
        try:
            logger.info("Shutting down Super AI Agent")
            
            # Stoppe Hauptschleife
            self.is_running = False
            
            # Beende Komponenten
            if self.email_fetcher:
                await self.email_fetcher.disconnect()
            
            if self.email_sender:
                await self.email_sender.disconnect()
            
            if self.telegram_coordinator:
                await self.telegram_coordinator.shutdown()
            
            logger.info("Super AI Agent shutdown completed")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt umfassende Statistiken zurück"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'agent': {
                'name': self.agent_config['name'],
                'version': self.agent_config['version'],
                'is_running': self.is_running,
                'uptime_seconds': uptime
            },
            'processing': {
                'total_processed': self.total_processed,
                'total_approved': self.total_approved,
                'total_rejected': self.total_rejected,
                'total_errors': self.total_errors,
                'success_rate': (self.total_approved / self.total_processed * 100) 
                               if self.total_processed > 0 else 0,
                'pending_approvals': len(self.telegram_coordinator.get_pending_approvals()) 
                                   if self.telegram_coordinator else 0
            },
            'components': {
                'email_fetcher': self.email_fetcher.get_stats() if self.email_fetcher else {},
                'email_sender': self.email_sender.get_stats() if self.email_sender else {},
                'telegram': self.telegram_coordinator.get_stats() if self.telegram_coordinator else {},
                'ai_analyzer': self.ai_analyzer.get_analysis_stats() if self.ai_analyzer else {},
                'response_generator': self.response_generator.get_generation_stats() 
                                    if self.response_generator else {}
            }
        }
    
    async def reload_config(self) -> bool:
        """Lädt Konfiguration neu"""
        try:
            logger.info("Reloading configuration")
            
            # Lade Konfiguration neu
            self.config_manager.reload()
            
            # Update Komponenten-Konfigurationen
            self.agent_config = self.config_manager.get_agent_config()
            self.email_config = self.config_manager.get_email_config()
            self.ai_config = self.config_manager.get_ai_config()
            self.telegram_config = self.config_manager.get_telegram_config()
            
            logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to reload configuration", error=str(e))
            return False