"""
Super-KI-Agent - Hauptkoordinator für intelligentes E-Mail-Management
"""
import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import signal
import sys

from config_manager import ConfigManager
from email_fetcher import EmailFetcher, EmailData
from email_analyzer import EmailAnalyzer, EmailAnalysis
from response_generator import ResponseGenerator, GeneratedResponse
from telegram_coordinator import TelegramCoordinator
from email_sender import EmailSender
from decision_engine import DecisionEngine, DecisionResult

@dataclass
class ProcessingResult:
    """Ergebnis der E-Mail-Verarbeitung"""
    email_data: EmailData
    analysis: EmailAnalysis
    response: GeneratedResponse
    decision: DecisionResult
    status: str  # processed, approved, rejected, error
    processing_time: float
    error_message: Optional[str] = None

class SuperAgent:
    """Hauptkoordinator für den Super-KI-Agenten"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.stats = {
            'emails_processed': 0,
            'emails_approved': 0,
            'emails_rejected': 0,
            'emails_error': 0,
            'start_time': None,
            'last_activity': None
        }
        
        # Initialisiere Module
        self.config_manager = ConfigManager(config_path)
        self.email_fetcher = EmailFetcher(self.config_manager)
        self.email_analyzer = EmailAnalyzer(self.config_manager)
        self.response_generator = ResponseGenerator(self.config_manager)
        self.telegram_coordinator = TelegramCoordinator(self.config_manager)
        self.email_sender = EmailSender(self.config_manager)
        self.decision_engine = DecisionEngine(self.config_manager)
        
        # Verarbeitungswarteschlange
        self.processing_queue: List[EmailData] = []
        self.pending_approvals: Dict[str, ProcessingResult] = {}
        
        self.logger.info("Super-KI-Agent initialisiert")
    
    async def start(self):
        """Startet den Super-KI-Agenten"""
        try:
            self.logger.info("🚀 Starte Super-KI-Agent...")
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            # Starte Telegram Bot
            await self.telegram_coordinator.start_bot()
            
            # Sende Start-Benachrichtigung
            await self.telegram_coordinator.send_notification(
                "🤖 Super-KI-Agent gestartet und bereit!"
            )
            
            # Starte Hauptschleife
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Super-KI-Agenten: {e}")
            await self.telegram_coordinator.send_notification(f"❌ Fehler beim Starten: {e}")
            raise
    
    async def stop(self):
        """Stoppt den Super-KI-Agenten"""
        try:
            self.logger.info("🛑 Stoppe Super-KI-Agent...")
            self.running = False
            
            # Sende Stop-Benachrichtigung
            await self.telegram_coordinator.send_notification(
                "🛑 Super-KI-Agent wird gestoppt..."
            )
            
            # Stoppe Telegram Bot
            await self.telegram_coordinator.stop_bot()
            
            # Trenne E-Mail-Verbindungen
            self.email_fetcher.disconnect()
            
            self.logger.info("Super-KI-Agent gestoppt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen: {e}")
    
    async def _main_loop(self):
        """Hauptschleife des Super-KI-Agenten"""
        self.logger.info("🔄 Starte Hauptschleife")
        
        while self.running:
            try:
                # Hole neue E-Mails
                await self._fetch_new_emails()
                
                # Verarbeite Warteschlange
                await self._process_queue()
                
                # Warte bis zum nächsten Zyklus
                await asyncio.sleep(self.config_manager.get_email_config().fetch_interval)
                
            except Exception as e:
                self.logger.error(f"Fehler in Hauptschleife: {e}")
                await asyncio.sleep(30)  # Warte bei Fehlern
    
    async def _fetch_new_emails(self):
        """Holt neue E-Mails"""
        try:
            emails = self.email_fetcher.fetch_unread_emails(
                max_count=self.config_manager.get_email_config().max_emails_per_fetch
            )
            
            if emails:
                self.logger.info(f"📧 {len(emails)} neue E-Mails gefunden")
                
                # Füge zur Warteschlange hinzu
                for email in emails:
                    self.processing_queue.append(email)
                
                # Sende Benachrichtigung
                await self.telegram_coordinator.send_notification(
                    f"📧 {len(emails)} neue E-Mails zur Verarbeitung"
                )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen neuer E-Mails: {e}")
    
    async def _process_queue(self):
        """Verarbeitet E-Mails in der Warteschlange"""
        while self.processing_queue and self.running:
            email_data = self.processing_queue.pop(0)
            
            try:
                # Verarbeite E-Mail
                result = await self._process_single_email(email_data)
                
                # Aktualisiere Statistiken
                self._update_stats(result)
                
                # Markiere als gelesen
                self.email_fetcher.mark_as_read(email_data.uid.encode())
                
            except Exception as e:
                self.logger.error(f"Fehler bei Verarbeitung von {email_data.subject}: {e}")
                self.stats['emails_error'] += 1
    
    async def _process_single_email(self, email_data: EmailData) -> ProcessingResult:
        """Verarbeitet eine einzelne E-Mail"""
        start_time = time.time()
        
        try:
            self.logger.info(f"📝 Verarbeite E-Mail: {email_data.subject}")
            
            # 1. Analysiere E-Mail
            analysis = self.email_analyzer.analyze_email(email_data)
            
            # 2. Generiere Antwort
            response = self.response_generator.generate_response(email_data, analysis)
            
            # 3. Treffe Entscheidung
            decision = self.decision_engine.make_decision(email_data, analysis, response)
            
            # 4. Führe Entscheidung aus
            status = await self._execute_decision(email_data, analysis, response, decision)
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                email_data=email_data,
                analysis=analysis,
                response=response,
                decision=decision,
                status=status,
                processing_time=processing_time
            )
            
            self.logger.info(f"✅ E-Mail verarbeitet: {status} ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"❌ Fehler bei E-Mail-Verarbeitung: {e}")
            
            return ProcessingResult(
                email_data=email_data,
                analysis=None,
                response=None,
                decision=None,
                status='error',
                processing_time=processing_time,
                error_message=str(e)
            )
    
    async def _execute_decision(self, email_data: EmailData, analysis: EmailAnalysis,
                              response: GeneratedResponse, decision: DecisionResult) -> str:
        """Führt Entscheidung aus"""
        
        if decision.action == 'auto_send':
            # Automatisch senden
            if self.email_sender.send_email(email_data, response):
                return 'approved'
            else:
                return 'error'
        
        elif decision.action == 'require_approval':
            # Benötigt Genehmigung
            return await self._request_approval(email_data, analysis, response)
        
        elif decision.action == 'reject':
            # Ablehnen
            return 'rejected'
        
        elif decision.action == 'escalate':
            # Eskalieren
            await self.telegram_coordinator.send_notification(
                f"🚨 ESKALATION: E-Mail von {email_data.sender} benötigt sofortige Aufmerksamkeit!"
            )
            return await self._request_approval(email_data, analysis, response)
        
        else:
            return 'error'
    
    async def _request_approval(self, email_data: EmailData, analysis: EmailAnalysis,
                              response: GeneratedResponse) -> str:
        """Sendet Genehmigungsanfrage"""
        try:
            # Erstelle eindeutige ID
            approval_id = f"approval_{int(time.time())}_{email_data.uid}"
            
            # Erstelle ProcessingResult
            result = ProcessingResult(
                email_data=email_data,
                analysis=analysis,
                response=response,
                decision=DecisionResult(
                    action='require_approval',
                    confidence=analysis.confidence_level,
                    reason="Genehmigung erforderlich",
                    requires_human=True,
                    priority='medium',
                    estimated_response_time=30
                ),
                status='pending',
                processing_time=0
            )
            
            # Speichere in pending_approvals
            self.pending_approvals[approval_id] = result
            
            # Sende Telegram-Anfrage
            await self.telegram_coordinator.send_approval_request(
                email_data, analysis, response, 
                lambda status, feedback: self._handle_approval_callback(approval_id, status, feedback)
            )
            
            return 'pending'
            
        except Exception as e:
            self.logger.error(f"Fehler bei Genehmigungsanfrage: {e}")
            return 'error'
    
    async def _handle_approval_callback(self, approval_id: str, status: str, feedback: Optional[str]):
        """Behandelt Telegram-Genehmigungscallback"""
        try:
            if approval_id not in self.pending_approvals:
                self.logger.warning(f"Genehmigung {approval_id} nicht gefunden")
                return
            
            result = self.pending_approvals[approval_id]
            
            if status == 'approved':
                # E-Mail genehmigt - sende
                if self.email_sender.send_email(result.email_data, result.response):
                    result.status = 'approved'
                    self.logger.info(f"✅ E-Mail genehmigt und gesendet: {result.email_data.subject}")
                else:
                    result.status = 'error'
                    self.logger.error(f"❌ Fehler beim Senden der genehmigten E-Mail")
            
            elif status == 'rejected':
                # E-Mail abgelehnt
                result.status = 'rejected'
                self.logger.info(f"❌ E-Mail abgelehnt: {result.email_data.subject}")
            
            elif status == 'edited':
                # E-Mail bearbeitet - generiere neue Antwort
                if feedback:
                    new_response = self.response_generator.improve_response(result.response, feedback)
                    result.response = new_response
                    
                    # Sende bearbeitete Antwort
                    if self.email_sender.send_email(result.email_data, new_response):
                        result.status = 'approved'
                        self.logger.info(f"✅ Bearbeitete E-Mail gesendet: {result.email_data.subject}")
                    else:
                        result.status = 'error'
            
            elif status == 'timeout':
                # Timeout - automatisch ablehnen
                result.status = 'rejected'
                self.logger.info(f"⏰ Timeout - E-Mail automatisch abgelehnt: {result.email_data.subject}")
            
            # Aktualisiere Statistiken
            self._update_stats(result)
            
            # Entferne aus pending_approvals
            del self.pending_approvals[approval_id]
            
        except Exception as e:
            self.logger.error(f"Fehler bei Genehmigungscallback: {e}")
    
    def _update_stats(self, result: ProcessingResult):
        """Aktualisiert Statistiken"""
        self.stats['emails_processed'] += 1
        self.stats['last_activity'] = datetime.now()
        
        if result.status == 'approved':
            self.stats['emails_approved'] += 1
        elif result.status == 'rejected':
            self.stats['emails_rejected'] += 1
        elif result.status == 'error':
            self.stats['emails_error'] += 1
    
    async def get_status(self) -> Dict[str, Any]:
        """Gibt aktuellen Status zurück"""
        uptime = None
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
        
        return {
            'running': self.running,
            'uptime': str(uptime) if uptime else None,
            'stats': self.stats,
            'queue_size': len(self.processing_queue),
            'pending_approvals': len(self.pending_approvals),
            'last_activity': self.stats['last_activity'].isoformat() if self.stats['last_activity'] else None
        }
    
    async def send_status_update(self):
        """Sendet Status-Update über Telegram"""
        status = await self.get_status()
        
        message = f"""
📊 <b>Super-KI-Agent Status</b>

🤖 <b>System:</b>
• Status: {'🟢 Aktiv' if status['running'] else '🔴 Gestoppt'}
• Laufzeit: {status['uptime']}
• Letzte Aktivität: {status['last_activity']}

📧 <b>E-Mails:</b>
• Verarbeitet: {status['stats']['emails_processed']}
• Genehmigt: {status['stats']['emails_approved']}
• Abgelehnt: {status['stats']['emails_rejected']}
• Fehler: {status['stats']['emails_error']}

⏳ <b>Warteschlangen:</b>
• Zu verarbeiten: {status['queue_size']}
• Ausstehende Genehmigungen: {status['pending_approvals']}
"""
        
        await self.telegram_coordinator.send_notification(message)
    
    def handle_signal(self, signum, frame):
        """Behandelt System-Signale"""
        self.logger.info(f"Signal {signum} empfangen - Stoppe Agent...")
        asyncio.create_task(self.stop())
    
    async def run_with_signal_handling(self):
        """Startet Agent mit Signal-Behandlung"""
        # Registriere Signal-Handler
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        
        try:
            await self.start()
        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt empfangen")
        finally:
            await self.stop()

# Hauptfunktion
async def main():
    """Hauptfunktion"""
    agent = SuperAgent()
    
    try:
        await agent.run_with_signal_handling()
    except Exception as e:
        logging.error(f"Kritischer Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Konfiguriere Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/super_agent.log'),
            logging.StreamHandler()
        ]
    )
    
    # Starte Agent
    asyncio.run(main())