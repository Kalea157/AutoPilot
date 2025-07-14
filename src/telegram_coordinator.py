"""
Telegram Coordinator für den Super-KI-Agenten
"""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from email_fetcher import EmailData
from email_analyzer import EmailAnalysis
from response_generator import GeneratedResponse

@dataclass
class TelegramApproval:
    """Telegram-Genehmigungsanfrage"""
    message_id: str
    email_data: EmailData
    analysis: EmailAnalysis
    response: GeneratedResponse
    timestamp: datetime
    status: str  # pending, approved, rejected, edited
    user_feedback: Optional[str] = None

class TelegramCoordinator:
    """Telegram Bot Coordinator für E-Mail-Genehmigungen"""
    
    def __init__(self, config_manager):
        self.config = config_manager.get_telegram_config()
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.application = None
        self.pending_approvals: Dict[str, TelegramApproval] = {}
        self.approval_callbacks: Dict[str, Callable] = {}
        self._setup_bot()
    
    def _setup_bot(self):
        """Konfiguriert Telegram Bot"""
        try:
            self.bot = telegram.Bot(token=self.config.bot_token)
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # Registriere Handler
            self._register_handlers()
            
            self.logger.info("Telegram Bot erfolgreich konfiguriert")
        except Exception as e:
            self.logger.error(f"Fehler bei Telegram Bot Setup: {e}")
            raise
    
    def _register_handlers(self):
        """Registriert Bot-Handler"""
        # Kommando-Handler
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("approve", self._approve_command))
        self.application.add_handler(CommandHandler("reject", self._reject_command))
        self.application.add_handler(CommandHandler("edit", self._edit_command))
        
        # Nachrichten-Handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.application.add_handler(MessageHandler(filters.CallbackQuery, self._handle_callback))
    
    async def start_bot(self):
        """Startet den Telegram Bot"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            self.logger.info("Telegram Bot gestartet")
        except Exception as e:
            self.logger.error(f"Fehler beim Starten des Telegram Bots: {e}")
            raise
    
    async def stop_bot(self):
        """Stoppt den Telegram Bot"""
        try:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("Telegram Bot gestoppt")
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen des Telegram Bots: {e}")
    
    async def send_approval_request(self, email_data: EmailData, analysis: EmailAnalysis, 
                                  response: GeneratedResponse, callback: Callable) -> str:
        """Sendet Genehmigungsanfrage an Telegram"""
        try:
            # Erstelle eindeutige Message-ID
            message_id = f"approval_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{email_data.uid}"
            
            # Erstelle Nachricht
            message_text = self._format_approval_message(email_data, analysis, response)
            
            # Erstelle Inline-Keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Genehmigen", callback_data=f"approve_{message_id}"),
                    InlineKeyboardButton("❌ Ablehnen", callback_data=f"reject_{message_id}")
                ],
                [
                    InlineKeyboardButton("✏️ Bearbeiten", callback_data=f"edit_{message_id}"),
                    InlineKeyboardButton("📋 Details", callback_data=f"details_{message_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Sende Nachricht
            sent_message = await self.bot.send_message(
                chat_id=self.config.admin_chat_id,
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            
            # Speichere Genehmigungsanfrage
            approval = TelegramApproval(
                message_id=message_id,
                email_data=email_data,
                analysis=analysis,
                response=response,
                timestamp=datetime.now(),
                status='pending'
            )
            
            self.pending_approvals[message_id] = approval
            self.approval_callbacks[message_id] = callback
            
            # Setze Timeout
            asyncio.create_task(self._approval_timeout(message_id))
            
            self.logger.info(f"Genehmigungsanfrage gesendet: {message_id}")
            return message_id
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Genehmigungsanfrage: {e}")
            raise
    
    def _format_approval_message(self, email_data: EmailData, analysis: EmailAnalysis, 
                               response: GeneratedResponse) -> str:
        """Formatiert Genehmigungsnachricht"""
        message = f"""
📧 <b>Neue E-Mail zur Genehmigung</b>

📋 <b>Original E-Mail:</b>
• <b>Von:</b> {email_data.sender}
• <b>Betreff:</b> {email_data.subject}
• <b>Datum:</b> {email_data.date.strftime('%d.%m.%Y %H:%M')}

🔍 <b>Analyse:</b>
• <b>Kategorie:</b> {analysis.category}
• <b>Stimmung:</b> {analysis.sentiment}
• <b>Dringlichkeit:</b> {analysis.urgency}
• <b>Confidence:</b> {analysis.confidence_level:.1%}
• <b>Sprache:</b> {analysis.language}

📝 <b>Generierte Antwort:</b>
• <b>Betreff:</b> {response.subject}
• <b>Ton:</b> {response.tone}
• <b>Confidence:</b> {response.confidence_level:.1%}

{response.body[:500]}{'...' if len(response.body) > 500 else ''}

⏰ <b>Timeout:</b> {self.config.timeout_seconds} Sekunden
"""
        return message
    
    async def _approval_timeout(self, message_id: str):
        """Behandelt Timeout für Genehmigungsanfrage"""
        await asyncio.sleep(self.config.timeout_seconds)
        
        if message_id in self.pending_approvals:
            approval = self.pending_approvals[message_id]
            if approval.status == 'pending':
                # Timeout erreicht - automatisch ablehnen
                await self._handle_timeout(message_id)
    
    async def _handle_timeout(self, message_id: str):
        """Behandelt Timeout"""
        try:
            approval = self.pending_approvals[message_id]
            approval.status = 'timeout'
            
            # Sende Timeout-Nachricht
            await self.bot.send_message(
                chat_id=self.config.admin_chat_id,
                text=f"⏰ <b>Timeout für Genehmigung {message_id}</b>\nE-Mail wurde automatisch abgelehnt.",
                parse_mode='HTML'
            )
            
            # Führe Callback aus
            if message_id in self.approval_callbacks:
                await self.approval_callbacks[message_id]('timeout', None)
            
            # Cleanup
            self._cleanup_approval(message_id)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Timeout-Behandlung: {e}")
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Behandelt Callback-Queries"""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            action, message_id = data.split('_', 1)
            
            if message_id not in self.pending_approvals:
                await query.edit_message_text("❌ Genehmigungsanfrage nicht mehr verfügbar.")
                return
            
            approval = self.pending_approvals[message_id]
            
            if action == 'approve':
                await self._handle_approval(message_id, query)
            elif action == 'reject':
                await self._handle_rejection(message_id, query)
            elif action == 'edit':
                await self._handle_edit_request(message_id, query)
            elif action == 'details':
                await self._show_details(message_id, query)
                
        except Exception as e:
            self.logger.error(f"Fehler bei Callback-Behandlung: {e}")
    
    async def _handle_approval(self, message_id: str, query):
        """Behandelt Genehmigung"""
        try:
            approval = self.pending_approvals[message_id]
            approval.status = 'approved'
            
            # Update Nachricht
            await query.edit_message_text(
                f"✅ <b>Genehmigt!</b>\nE-Mail wird gesendet.",
                parse_mode='HTML'
            )
            
            # Führe Callback aus
            if message_id in self.approval_callbacks:
                await self.approval_callbacks[message_id]('approved', None)
            
            # Cleanup
            self._cleanup_approval(message_id)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Genehmigung: {e}")
    
    async def _handle_rejection(self, message_id: str, query):
        """Behandelt Ablehnung"""
        try:
            approval = self.pending_approvals[message_id]
            approval.status = 'rejected'
            
            # Update Nachricht
            await query.edit_message_text(
                f"❌ <b>Abgelehnt!</b>\nE-Mail wird nicht gesendet.",
                parse_mode='HTML'
            )
            
            # Führe Callback aus
            if message_id in self.approval_callbacks:
                await self.approval_callbacks[message_id]('rejected', None)
            
            # Cleanup
            self._cleanup_approval(message_id)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Ablehnung: {e}")
    
    async def _handle_edit_request(self, message_id: str, query):
        """Behandelt Bearbeitungsanfrage"""
        try:
            approval = self.pending_approvals[message_id]
            
            # Sende Bearbeitungsanweisung
            await query.edit_message_text(
                f"✏️ <b>Bearbeitung erforderlich</b>\n"
                f"Bitte sende deine Änderungen als Nachricht.\n"
                f"Format: /edit {message_id} [deine Änderungen]",
                parse_mode='HTML'
            )
            
        except Exception as e:
            self.logger.error(f"Fehler bei Bearbeitungsanfrage: {e}")
    
    async def _show_details(self, message_id: str, query):
        """Zeigt Details der E-Mail"""
        try:
            approval = self.pending_approvals[message_id]
            email_data = approval.email_data
            analysis = approval.analysis
            
            details = f"""
📧 <b>E-Mail Details</b>

<b>Vollständiger Inhalt:</b>
{email_data.body}

<b>Analyse Details:</b>
• Erforderte Aktion: {analysis.required_action}
• Schlüsselfragen: {', '.join(analysis.key_questions)}
• Schlüsselanliegen: {', '.join(analysis.key_concerns)}
• Extrahierte Info: {json.dumps(analysis.extracted_info, indent=2, ensure_ascii=False)}

<b>Generierte Antwort:</b>
{approval.response.body}
"""
            
            await query.edit_message_text(details, parse_mode='HTML')
            
        except Exception as e:
            self.logger.error(f"Fehler beim Anzeigen der Details: {e}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Behandelt normale Nachrichten"""
        try:
            message = update.message
            text = message.text
            
            # Prüfe auf Bearbeitungsanweisung
            if text.startswith('/edit '):
                await self._handle_edit_message(message)
            else:
                # Normale Nachricht - prüfe auf Auto-Approval
                await self._check_auto_approval(message)
                
        except Exception as e:
            self.logger.error(f"Fehler bei Nachrichtenbehandlung: {e}")
    
    async def _handle_edit_message(self, message):
        """Behandelt Bearbeitungsnachrichten"""
        try:
            parts = message.text.split(' ', 2)
            if len(parts) < 3:
                await message.reply_text("❌ Format: /edit [message_id] [Änderungen]")
                return
            
            message_id = parts[1]
            feedback = parts[2]
            
            if message_id not in self.pending_approvals:
                await message.reply_text("❌ Genehmigungsanfrage nicht gefunden.")
                return
            
            approval = self.pending_approvals[message_id]
            approval.status = 'edited'
            approval.user_feedback = feedback
            
            # Führe Callback aus
            if message_id in self.approval_callbacks:
                await self.approval_callbacks[message_id]('edited', feedback)
            
            await message.reply_text("✅ Bearbeitung gespeichert. Neue Antwort wird generiert.")
            
            # Cleanup
            self._cleanup_approval(message_id)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Bearbeitungsnachricht: {e}")
    
    async def _check_auto_approval(self, message):
        """Prüft auf Auto-Approval Kommandos"""
        try:
            text = message.text.lower().strip()
            
            # Prüfe auf Auto-Approval Kommandos
            if text in [cmd.lower() for cmd in self.config.auto_approve_commands]:
                # Auto-approve alle pending Genehmigungen
                for message_id, approval in self.pending_approvals.items():
                    if approval.status == 'pending':
                        await self._handle_approval(message_id, None)
                
                await message.reply_text("✅ Alle ausstehenden Genehmigungen wurden automatisch genehmigt.")
            
            elif text in [cmd.lower() for cmd in self.config.reject_commands]:
                # Auto-reject alle pending Genehmigungen
                for message_id, approval in self.pending_approvals.items():
                    if approval.status == 'pending':
                        await self._handle_rejection(message_id, None)
                
                await message.reply_text("❌ Alle ausstehenden Genehmigungen wurden automatisch abgelehnt.")
                
        except Exception as e:
            self.logger.error(f"Fehler bei Auto-Approval Prüfung: {e}")
    
    def _cleanup_approval(self, message_id: str):
        """Räumt Genehmigungsanfrage auf"""
        if message_id in self.pending_approvals:
            del self.pending_approvals[message_id]
        if message_id in self.approval_callbacks:
            del self.approval_callbacks[message_id]
    
    async def send_notification(self, message: str, chat_id: Optional[str] = None):
        """Sendet Benachrichtigung"""
        try:
            target_chat = chat_id or self.config.notification_chat_id
            await self.bot.send_message(
                chat_id=target_chat,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Benachrichtigung: {e}")
    
    async def send_status_update(self, status: str):
        """Sendet Status-Update"""
        try:
            message = f"""
🤖 <b>Super-KI-Agent Status</b>

📊 <b>Aktuelle Statistiken:</b>
• Ausstehende Genehmigungen: {len(self.pending_approvals)}
• Status: {status}

⏰ <b>Letzte Aktivität:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
            await self.send_notification(message)
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Status-Updates: {e}")
    
    # Kommando-Handler
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start-Kommando"""
        await update.message.reply_text(
            "🤖 Willkommen beim Super-KI-Agent!\n"
            "Verwende /help für verfügbare Kommandos."
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hilfe-Kommando"""
        help_text = """
🤖 <b>Super-KI-Agent Hilfe</b>

<b>Verfügbare Kommandos:</b>
/start - Startet den Bot
/help - Zeigt diese Hilfe
/status - Zeigt aktuellen Status
/approve [id] - Genehmigt E-Mail
/reject [id] - Lehnt E-Mail ab
/edit [id] [feedback] - Bearbeitet E-Mail

<b>Auto-Approval Kommandos:</b>
• ja, yes, ok, approve - Genehmigt alle ausstehenden E-Mails
• nein, no, reject - Lehnt alle ausstehenden E-Mails ab

<b>Bearbeitung:</b>
/edit [message_id] [deine Änderungen]
"""
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Status-Kommando"""
        status_text = f"""
📊 <b>Super-KI-Agent Status</b>

• Ausstehende Genehmigungen: {len(self.pending_approvals)}
• Bot Status: Aktiv
• Letzte Aktivität: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
"""
        await update.message.reply_text(status_text, parse_mode='HTML')
    
    async def _approve_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Approve-Kommando"""
        if not context.args:
            await update.message.reply_text("❌ Bitte gib eine Message-ID an: /approve [id]")
            return
        
        message_id = context.args[0]
        if message_id in self.pending_approvals:
            await self._handle_approval(message_id, None)
            await update.message.reply_text(f"✅ E-Mail {message_id} genehmigt!")
        else:
            await update.message.reply_text("❌ Message-ID nicht gefunden.")
    
    async def _reject_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reject-Kommando"""
        if not context.args:
            await update.message.reply_text("❌ Bitte gib eine Message-ID an: /reject [id]")
            return
        
        message_id = context.args[0]
        if message_id in self.pending_approvals:
            await self._handle_rejection(message_id, None)
            await update.message.reply_text(f"❌ E-Mail {message_id} abgelehnt!")
        else:
            await update.message.reply_text("❌ Message-ID nicht gefunden.")
    
    async def _edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit-Kommando"""
        if len(context.args) < 2:
            await update.message.reply_text("❌ Format: /edit [id] [feedback]")
            return
        
        message_id = context.args[0]
        feedback = ' '.join(context.args[1:])
        
        if message_id in self.pending_approvals:
            await self._handle_edit_message(update.message)
            await update.message.reply_text(f"✏️ E-Mail {message_id} wird bearbeitet!")
        else:
            await update.message.reply_text("❌ Message-ID nicht gefunden.")