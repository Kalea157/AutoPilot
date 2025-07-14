"""
Telegram Coordinator - Telegram-basierte Kommunikation und Freigabe
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

logger = structlog.get_logger(__name__)


@dataclass
class ApprovalRequest:
    """Datenklasse für Freigabe-Anfragen"""
    id: str
    email_data: Dict[str, Any]
    analysis: Dict[str, Any]
    response: Dict[str, Any]
    timestamp: datetime
    status: str  # pending, approved, rejected, edited, ignored
    user_response: Optional[str] = None
    response_time: Optional[datetime] = None


class TelegramCoordinator:
    """Telegram-basierter Koordinator für E-Mail-Freigaben"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = config['bot_token']
        self.chat_id = config['chat_id']
        self.approval_timeout = config['approval_timeout']
        self.message_format = config['message_format']
        self.templates = config['templates']
        
        # Bot und Application
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # Pending approvals
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        
        # Callbacks
        self.on_approval_callback: Optional[Callable] = None
        self.on_rejection_callback: Optional[Callable] = None
        self.on_edit_callback: Optional[Callable] = None
        self.on_ignore_callback: Optional[Callable] = None
        
        # Statistics
        self._sent_requests = 0
        self._approved_count = 0
        self._rejected_count = 0
        self._timeout_count = 0
    
    async def initialize(self) -> bool:
        """Initialisiert Telegram Bot"""
        try:
            self.bot = Bot(token=self.bot_token)
            self.application = Application.builder().token(self.bot_token).build()
            
            # Registriere Handler
            self._register_handlers()
            
            # Starte Bot
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Telegram coordinator initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Telegram coordinator", error=str(e))
            return False
    
    async def shutdown(self) -> None:
        """Beendet Telegram Bot"""
        if self.application:
            try:
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram coordinator shutdown completed")
            except Exception as e:
                logger.error("Error during Telegram shutdown", error=str(e))
    
    def _register_handlers(self) -> None:
        """Registriert Telegram Command Handler"""
        if not self.application:
            return
        
        # Command Handler
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        
        # Callback Query Handler für Inline Buttons
        self.application.add_handler(CallbackQueryHandler(self._button_callback))
        
        # Custom Command Handler für Approvals
        self.application.add_handler(CommandHandler("approve", self._approve_command))
        self.application.add_handler(CommandHandler("reject", self._reject_command))
        self.application.add_handler(CommandHandler("edit", self._edit_command))
        self.application.add_handler(CommandHandler("ignore", self._ignore_command))
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Start Command Handler"""
        welcome_message = """
🤖 **Super AI Email Agent**

Willkommen! Ich bin Ihr E-Mail-Assistent und sende Ihnen E-Mails zur Freigabe.

**Verfügbare Befehle:**
/status - Aktuelle Statistiken
/help - Hilfe anzeigen

**Automatische Freigabe:**
- E-Mails mit >95% Vertrauen werden automatisch gesendet
- Alle anderen E-Mails werden zur manuellen Freigabe vorgelegt
"""
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Status Command Handler"""
        stats = self.get_stats()
        status_message = f"""
📊 **Agent Status**

**Verarbeitete E-Mails:** {stats['total_requests']}
**Genehmigt:** {stats['approved_count']}
**Abgelehnt:** {stats['rejected_count']}
**Timeout:** {stats['timeout_count']}
**Ausstehend:** {len(self.pending_approvals)}

**Erfolgsrate:** {stats['success_rate']:.1f}%
**Durchschnittliche Antwortzeit:** {stats['avg_response_time']:.1f}s
"""
        await update.message.reply_text(status_message, parse_mode=ParseMode.MARKDOWN)
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Help Command Handler"""
        help_message = """
❓ **Hilfe - E-Mail-Freigabe**

**Automatische Freigabe:**
- E-Mails mit sehr hohem Vertrauen (>95%) werden automatisch gesendet
- Sie erhalten eine Benachrichtigung nach dem Versand

**Manuelle Freigabe:**
- E-Mails werden mit Details und vorgeschlagener Antwort gesendet
- Verwenden Sie die Inline-Buttons oder Commands:

**Commands:**
/approve_[ID] - E-Mail genehmigen
/reject_[ID] - E-Mail ablehnen
/edit_[ID] - E-Mail bearbeiten
/ignore_[ID] - E-Mail ignorieren

**Beispiel:** `/approve_12345`
"""
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
    
    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Inline Button Callback Handler"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data.startswith('approve_'):
            await self._handle_approval(data.split('_')[1], query.from_user.username or "Unknown")
        elif data.startswith('reject_'):
            await self._handle_rejection(data.split('_')[1], query.from_user.username or "Unknown")
        elif data.startswith('edit_'):
            await self._handle_edit_request(data.split('_')[1], query.from_user.username or "Unknown")
        elif data.startswith('ignore_'):
            await self._handle_ignore(data.split('_')[1], query.from_user.username or "Unknown")
    
    async def _approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Approve Command Handler"""
        if not context.args:
            await update.message.reply_text("❌ Bitte geben Sie eine E-Mail-ID an: `/approve [ID]`")
            return
        
        email_id = context.args[0]
        await self._handle_approval(email_id, update.from_user.username or "Unknown")
    
    async def _reject_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Reject Command Handler"""
        if not context.args:
            await update.message.reply_text("❌ Bitte geben Sie eine E-Mail-ID an: `/reject [ID]`")
            return
        
        email_id = context.args[0]
        await self._handle_rejection(email_id, update.from_user.username or "Unknown")
    
    async def _edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Edit Command Handler"""
        if not context.args:
            await update.message.reply_text("❌ Bitte geben Sie eine E-Mail-ID an: `/edit [ID]`")
            return
        
        email_id = context.args[0]
        await self._handle_edit_request(email_id, update.from_user.username or "Unknown")
    
    async def _ignore_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Ignore Command Handler"""
        if not context.args:
            await update.message.reply_text("❌ Bitte geben Sie eine E-Mail-ID an: `/ignore [ID]`")
            return
        
        email_id = context.args[0]
        await self._handle_ignore(email_id, update.from_user.username or "Unknown")
    
    async def request_approval(self, email_data: Dict[str, Any], 
                             analysis: Dict[str, Any], 
                             response: Dict[str, Any]) -> str:
        """Sendet Freigabe-Anfrage an Telegram"""
        try:
            # Generiere eindeutige ID
            approval_id = self._generate_approval_id()
            
            # Erstelle ApprovalRequest
            approval_request = ApprovalRequest(
                id=approval_id,
                email_data=email_data,
                analysis=analysis,
                response=response,
                timestamp=datetime.now(),
                status='pending'
            )
            
            # Speichere Request
            self.pending_approvals[approval_id] = approval_request
            
            # Erstelle Telegram Message
            message = self._create_approval_message(approval_request)
            
            # Sende Message
            if self.bot:
                sent_message = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=self._create_inline_keyboard(approval_id)
                )
                
                # Starte Timeout Timer
                asyncio.create_task(self._start_approval_timeout(approval_id))
                
                self._sent_requests += 1
                logger.info("Approval request sent", approval_id=approval_id)
                
                return approval_id
            
        except Exception as e:
            logger.error("Failed to send approval request", error=str(e))
            return ""
    
    def _create_approval_message(self, approval_request: ApprovalRequest) -> str:
        """Erstellt Telegram-Nachricht für Freigabe-Anfrage"""
        template = self.templates.get('approval_request', '')
        
        # Extrahiere Daten
        email_data = approval_request.email_data
        analysis = approval_request.analysis
        response = approval_request.response
        
        # Formatiere Content Preview
        content_preview = email_data.get('content', '')[:200]
        if len(email_data.get('content', '')) > 200:
            content_preview += "..."
        
        # Formatiere Response Preview
        response_preview = response.get('content', '')[:300]
        if len(response.get('content', '')) > 300:
            response_preview += "..."
        
        # Ersetze Platzhalter
        message = template.format(
            sender=email_data.get('sender', 'Unbekannt'),
            subject=email_data.get('subject', 'Kein Betreff'),
            category=analysis.get('category', 'Unbekannt'),
            urgency=analysis.get('urgency', 5),
            confidence=int(analysis.get('confidence', 0.8) * 100),
            content_preview=content_preview,
            response_preview=response_preview,
            id=approval_request.id
        )
        
        return message
    
    def _create_inline_keyboard(self, approval_id: str) -> InlineKeyboardMarkup:
        """Erstellt Inline-Keyboard für Freigabe-Aktionen"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Genehmigen", callback_data=f"approve_{approval_id}"),
                InlineKeyboardButton("❌ Ablehnen", callback_data=f"reject_{approval_id}")
            ],
            [
                InlineKeyboardButton("✏️ Bearbeiten", callback_data=f"edit_{approval_id}"),
                InlineKeyboardButton("🚫 Ignorieren", callback_data=f"ignore_{approval_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def _handle_approval(self, approval_id: str, username: str) -> None:
        """Behandelt Genehmigung"""
        if approval_id not in self.pending_approvals:
            await self._send_error_message(f"E-Mail-ID {approval_id} nicht gefunden")
            return
        
        approval_request = self.pending_approvals[approval_id]
        approval_request.status = 'approved'
        approval_request.user_response = username
        approval_request.response_time = datetime.now()
        
        # Entferne aus pending
        del self.pending_approvals[approval_id]
        
        # Callback aufrufen
        if self.on_approval_callback:
            await self.on_approval_callback(approval_request)
        
        # Bestätigung senden
        await self._send_confirmation_message(
            f"✅ E-Mail genehmigt von @{username}\n"
            f"ID: {approval_id}\n"
            f"Antwort wird gesendet..."
        )
        
        self._approved_count += 1
        logger.info("Email approved", approval_id=approval_id, user=username)
    
    async def _handle_rejection(self, approval_id: str, username: str) -> None:
        """Behandelt Ablehnung"""
        if approval_id not in self.pending_approvals:
            await self._send_error_message(f"E-Mail-ID {approval_id} nicht gefunden")
            return
        
        approval_request = self.pending_approvals[approval_id]
        approval_request.status = 'rejected'
        approval_request.user_response = username
        approval_request.response_time = datetime.now()
        
        # Entferne aus pending
        del self.pending_approvals[approval_id]
        
        # Callback aufrufen
        if self.on_rejection_callback:
            await self.on_rejection_callback(approval_request)
        
        # Bestätigung senden
        await self._send_confirmation_message(
            f"❌ E-Mail abgelehnt von @{username}\n"
            f"ID: {approval_id}\n"
            f"Keine Antwort wird gesendet."
        )
        
        self._rejected_count += 1
        logger.info("Email rejected", approval_id=approval_id, user=username)
    
    async def _handle_edit_request(self, approval_id: str, username: str) -> None:
        """Behandelt Bearbeitungsanfrage"""
        if approval_id not in self.pending_approvals:
            await self._send_error_message(f"E-Mail-ID {approval_id} nicht gefunden")
            return
        
        approval_request = self.pending_approvals[approval_id]
        approval_request.status = 'edited'
        approval_request.user_response = username
        approval_request.response_time = datetime.now()
        
        # Callback aufrufen
        if self.on_edit_callback:
            await self.on_edit_callback(approval_request)
        
        # Bestätigung senden
        await self._send_confirmation_message(
            f"✏️ E-Mail zur Bearbeitung markiert von @{username}\n"
            f"ID: {approval_id}\n"
            f"Bitte bearbeiten Sie die Antwort."
        )
        
        logger.info("Email marked for editing", approval_id=approval_id, user=username)
    
    async def _handle_ignore(self, approval_id: str, username: str) -> None:
        """Behandelt Ignorieren"""
        if approval_id not in self.pending_approvals:
            await self._send_error_message(f"E-Mail-ID {approval_id} nicht gefunden")
            return
        
        approval_request = self.pending_approvals[approval_id]
        approval_request.status = 'ignored'
        approval_request.user_response = username
        approval_request.response_time = datetime.now()
        
        # Entferne aus pending
        del self.pending_approvals[approval_id]
        
        # Callback aufrufen
        if self.on_ignore_callback:
            await self.on_ignore_callback(approval_request)
        
        # Bestätigung senden
        await self._send_confirmation_message(
            f"🚫 E-Mail ignoriert von @{username}\n"
            f"ID: {approval_id}\n"
            f"E-Mail wird nicht beantwortet."
        )
        
        logger.info("Email ignored", approval_id=approval_id, user=username)
    
    async def _start_approval_timeout(self, approval_id: str) -> None:
        """Startet Timeout-Timer für Freigabe"""
        await asyncio.sleep(self.approval_timeout)
        
        if approval_id in self.pending_approvals:
            approval_request = self.pending_approvals[approval_id]
            approval_request.status = 'timeout'
            approval_request.response_time = datetime.now()
            
            # Entferne aus pending
            del self.pending_approvals[approval_id]
            
            # Timeout-Benachrichtigung senden
            await self._send_confirmation_message(
                f"⏰ Timeout für E-Mail-ID {approval_id}\n"
                f"Keine Antwort innerhalb von {self.approval_timeout}s erhalten.\n"
                f"E-Mail wird nicht beantwortet."
            )
            
            self._timeout_count += 1
            logger.warning("Approval timeout", approval_id=approval_id)
    
    async def _send_confirmation_message(self, message: str) -> None:
        """Sendet Bestätigungsnachricht"""
        if self.bot:
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error("Failed to send confirmation message", error=str(e))
    
    async def _send_error_message(self, message: str) -> None:
        """Sendet Fehlermeldung"""
        if self.bot:
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"❌ {message}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error("Failed to send error message", error=str(e))
    
    def _generate_approval_id(self) -> str:
        """Generiert eindeutige Approval-ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def set_callbacks(self, on_approval: Callable = None, on_rejection: Callable = None,
                     on_edit: Callable = None, on_ignore: Callable = None) -> None:
        """Setzt Callback-Funktionen"""
        self.on_approval_callback = on_approval
        self.on_rejection_callback = on_rejection
        self.on_edit_callback = on_edit
        self.on_ignore_callback = on_ignore
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Gibt ausstehende Freigaben zurück"""
        return list(self.pending_approvals.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken zurück"""
        total = self._sent_requests
        success_rate = ((self._approved_count + self._rejected_count) / total * 100) if total > 0 else 0
        
        return {
            'total_requests': total,
            'approved_count': self._approved_count,
            'rejected_count': self._rejected_count,
            'timeout_count': self._timeout_count,
            'pending_count': len(self.pending_approvals),
            'success_rate': success_rate,
            'avg_response_time': 0.0  # TODO: Implement response time tracking
        }