"""
Liyana NEXUS v1 - Telegram Unit
Rückfragen- und Genehmigungsmodul (JA/NEIN, Vorschau, Antwortauswahl)
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field

from config import config, AgentState

@dataclass
class TelegramMessage:
    """Repräsentiert eine Telegram-Nachricht"""
    message_id: int
    chat_id: int
    user_id: int
    username: str
    text: str
    timestamp: datetime
    is_command: bool = False
    command: str = ""
    args: List[str] = field(default_factory=list)

@dataclass
class ApprovalRequest:
    """Repräsentiert eine Genehmigungsanfrage"""
    id: str
    chat_id: int
    user_id: int
    request_type: str
    data: Dict[str, Any]
    timestamp: datetime
    status: str = "pending"  # pending, approved, rejected, expired
    response: Optional[str] = None
    response_timestamp: Optional[datetime] = None

class TelegramUnit:
    """Telegram Bot für Rückfragen und Genehmigungen"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = AgentState.WAITING
        
        # Telegram Bot
        self.bot = None
        self.bot_token = config.api.telegram_token
        
        # Genehmigungsanfragen
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.request_handlers: Dict[str, Callable] = {}
        
        # Benutzer-Berechtigungen
        self.authorized_users: List[int] = []
        self.admin_users: List[int] = []
        
        # Bot-Kommandos
        self.commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/status': self._handle_status,
            '/approve': self._handle_approve,
            '/reject': self._handle_reject,
            '/list': self._handle_list_requests,
            '/auth': self._handle_auth,
            '/deauth': self._handle_deauth
        }
        
        # Callback-Handler
        self.callback_handlers: Dict[str, Callable] = {}
        
        self._running = False
        self._polling_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Startet den Telegram Unit"""
        if self._running:
            return
        
        self.logger.info("Telegram Unit wird gestartet...")
        self._running = True
        self.state = AgentState.EXECUTING
        
        # Initialisiere Bot
        await self._initialize_bot()
        
        # Registriere Standard-Handler
        await self._register_default_handlers()
        
        # Starte Polling
        self._polling_task = asyncio.create_task(self._polling_loop())
        
        self.logger.info("Telegram Unit gestartet")
    
    async def stop(self):
        """Stoppt den Telegram Unit"""
        self.logger.info("Telegram Unit wird gestoppt...")
        self._running = False
        self.state = AgentState.PAUSED
        
        # Stoppe Polling
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Telegram Unit gestoppt")
    
    async def _initialize_bot(self):
        """Initialisiert den Telegram Bot"""
        try:
            from telegram import Bot
            from telegram.ext import Application
            
            self.bot = Bot(token=self.bot_token)
            
            # Teste Verbindung
            bot_info = await self.bot.get_me()
            self.logger.info(f"Telegram Bot verbunden: @{bot_info.username}")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Bot-Initialisierung: {e}")
            raise
    
    async def _register_default_handlers(self):
        """Registriert Standard-Handler"""
        # Genehmigungs-Handler
        self.request_handlers['email_send'] = self._handle_email_approval
        self.request_handlers['task_execution'] = self._handle_task_approval
        self.request_handlers['system_config'] = self._handle_config_approval
        
        # Callback-Handler
        self.callback_handlers['approve'] = self._handle_approval_callback
        self.callback_handlers['reject'] = self._handle_rejection_callback
        self.callback_handlers['preview'] = self._handle_preview_callback
    
    async def _polling_loop(self):
        """Hauptschleife für Telegram-Polling"""
        offset = 0
        
        while self._running:
            try:
                # Hole Updates
                updates = await self.bot.get_updates(offset=offset, timeout=30)
                
                for update in updates:
                    offset = update.update_id + 1
                    
                    if update.message:
                        await self._handle_message(update.message)
                    elif update.callback_query:
                        await self._handle_callback_query(update.callback_query)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Fehler im Telegram-Polling: {e}")
                await asyncio.sleep(5)
    
    async def _handle_message(self, message):
        """Behandelt eingehende Nachrichten"""
        try:
            # Erstelle Message-Objekt
            msg = TelegramMessage(
                message_id=message.message_id,
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                username=message.from_user.username or str(message.from_user.id),
                text=message.text or "",
                timestamp=datetime.fromtimestamp(message.date)
            )
            
            # Prüfe ob es ein Kommando ist
            if msg.text.startswith('/'):
                parts = msg.text.split()
                msg.is_command = True
                msg.command = parts[0]
                msg.args = parts[1:] if len(parts) > 1 else []
                
                await self._handle_command(msg)
            else:
                await self._handle_text_message(msg)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Nachricht: {e}")
    
    async def _handle_command(self, msg: TelegramMessage):
        """Behandelt Bot-Kommandos"""
        handler = self.commands.get(msg.command)
        if handler:
            await handler(msg)
        else:
            await self._send_message(
                msg.chat_id,
                f"Unbekanntes Kommando: {msg.command}\n"
                "Verwende /help für verfügbare Kommandos."
            )
    
    async def _handle_text_message(self, msg: TelegramMessage):
        """Behandelt normale Textnachrichten"""
        # Prüfe ob Benutzer autorisiert ist
        if not await self._is_user_authorized(msg.user_id):
            await self._send_message(
                msg.chat_id,
                "Sie sind nicht autorisiert, mit diesem Bot zu kommunizieren."
            )
            return
        
        # Verarbeite Nachricht
        response = await self._process_text_message(msg)
        if response:
            await self._send_message(msg.chat_id, response)
    
    async def _handle_callback_query(self, callback_query):
        """Behandelt Callback-Queries"""
        try:
            data = callback_query.data
            user_id = callback_query.from_user.id
            
            # Prüfe Berechtigung
            if not await self._is_user_authorized(user_id):
                await callback_query.answer("Nicht autorisiert")
                return
            
            # Parse Callback-Daten
            if ':' in data:
                action, request_id = data.split(':', 1)
                handler = self.callback_handlers.get(action)
                if handler:
                    await handler(request_id, callback_query)
                else:
                    await callback_query.answer("Unbekannte Aktion")
            else:
                await callback_query.answer("Ungültige Callback-Daten")
                
        except Exception as e:
            self.logger.error(f"Fehler beim Verarbeiten der Callback-Query: {e}")
            await callback_query.answer("Fehler aufgetreten")
    
    async def _handle_start(self, msg: TelegramMessage):
        """Behandelt /start Kommando"""
        welcome_text = """
🤖 **Liyana NEXUS v1 - Telegram Bot**

Willkommen beim Super-KI-Agenten der Stufe 8!

**Verfügbare Kommandos:**
/help - Zeigt diese Hilfe an
/status - Systemstatus anzeigen
/list - Genehmigungsanfragen auflisten
/auth <code> - Autorisierung (nur für Admins)
/deauth - Autorisierung entfernen

**Genehmigungsanfragen:**
Der Bot sendet automatisch Anfragen für wichtige Aktionen.
Antworten Sie mit /approve oder /reject gefolgt von der Anfrage-ID.
        """
        
        await self._send_message(msg.chat_id, welcome_text)
    
    async def _handle_help(self, msg: TelegramMessage):
        """Behandelt /help Kommando"""
        help_text = """
📋 **Hilfe - Liyana NEXUS v1**

**System-Kommandos:**
/status - Zeigt aktuellen Systemstatus
/list - Listet alle offenen Genehmigungsanfragen

**Genehmigungen:**
/approve <id> - Genehmigt eine Anfrage
/reject <id> - Lehnt eine Anfrage ab

**Autorisierung (nur Admins):**
/auth <code> - Fügt Benutzer hinzu
/deauth - Entfernt eigene Autorisierung

**Beispiele:**
/approve req_123 - Genehmigt Anfrage req_123
/reject req_456 - Lehnt Anfrage req_456 ab
        """
        
        await self._send_message(msg.chat_id, help_text)
    
    async def _handle_status(self, msg: TelegramMessage):
        """Behandelt /status Kommando"""
        if not await self._is_user_authorized(msg.user_id):
            await self._send_message(msg.chat_id, "Nicht autorisiert")
            return
        
        # Hier könnte der aktuelle Systemstatus abgerufen werden
        status_text = """
📊 **Systemstatus - Liyana NEXUS v1**

🟢 **Status:** Online
⏱️ **Uptime:** 2h 15m
📧 **Emails verarbeitet:** 42
🤖 **Aktive Agenten:** 8/10
💾 **Speichernutzung:** 1.2 GB
🔄 **Tasks in Queue:** 3

**Offene Genehmigungen:** 2
        """
        
        await self._send_message(msg.chat_id, status_text)
    
    async def _handle_approve(self, msg: TelegramMessage):
        """Behandelt /approve Kommando"""
        if not await self._is_user_authorized(msg.user_id):
            await self._send_message(msg.chat_id, "Nicht autorisiert")
            return
        
        if not msg.args:
            await self._send_message(msg.chat_id, "Verwendung: /approve <anfrage_id>")
            return
        
        request_id = msg.args[0]
        await self._approve_request(request_id, msg.user_id, msg.username)
    
    async def _handle_reject(self, msg: TelegramMessage):
        """Behandelt /reject Kommando"""
        if not await self._is_user_authorized(msg.user_id):
            await self._send_message(msg.chat_id, "Nicht autorisiert")
            return
        
        if not msg.args:
            await self._send_message(msg.chat_id, "Verwendung: /reject <anfrage_id>")
            return
        
        request_id = msg.args[0]
        await self._reject_request(request_id, msg.user_id, msg.username)
    
    async def _handle_list_requests(self, msg: TelegramMessage):
        """Behandelt /list Kommando"""
        if not await self._is_user_authorized(msg.user_id):
            await self._send_message(msg.chat_id, "Nicht autorisiert")
            return
        
        pending_requests = [
            req for req in self.approval_requests.values()
            if req.status == "pending"
        ]
        
        if not pending_requests:
            await self._send_message(msg.chat_id, "Keine offenen Genehmigungsanfragen.")
            return
        
        list_text = "📋 **Offene Genehmigungsanfragen:**\n\n"
        
        for req in pending_requests:
            age = datetime.now() - req.timestamp
            age_str = f"{age.seconds // 60}m" if age.seconds < 3600 else f"{age.seconds // 3600}h"
            
            list_text += f"🆔 **{req.id}**\n"
            list_text += f"📝 **Typ:** {req.request_type}\n"
            list_text += f"⏰ **Alter:** {age_str}\n"
            list_text += f"👤 **Von:** {req.username}\n\n"
        
        await self._send_message(msg.chat_id, list_text)
    
    async def _handle_auth(self, msg: TelegramMessage):
        """Behandelt /auth Kommando"""
        if not await self._is_user_admin(msg.user_id):
            await self._send_message(msg.chat_id, "Nur Administratoren können Benutzer autorisieren.")
            return
        
        if not msg.args:
            await self._send_message(msg.chat_id, "Verwendung: /auth <user_id>")
            return
        
        try:
            user_id = int(msg.args[0])
            self.authorized_users.append(user_id)
            await self._send_message(msg.chat_id, f"Benutzer {user_id} wurde autorisiert.")
        except ValueError:
            await self._send_message(msg.chat_id, "Ungültige User-ID.")
    
    async def _handle_deauth(self, msg: TelegramMessage):
        """Behandelt /deauth Kommando"""
        if msg.user_id in self.authorized_users:
            self.authorized_users.remove(msg.user_id)
            await self._send_message(msg.chat_id, "Ihre Autorisierung wurde entfernt.")
        else:
            await self._send_message(msg.chat_id, "Sie waren nicht autorisiert.")
    
    async def _is_user_authorized(self, user_id: int) -> bool:
        """Prüft ob ein Benutzer autorisiert ist"""
        return user_id in self.authorized_users or user_id in self.admin_users
    
    async def _is_user_admin(self, user_id: int) -> bool:
        """Prüft ob ein Benutzer Administrator ist"""
        return user_id in self.admin_users
    
    async def _send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown"):
        """Sendet eine Nachricht"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Nachricht: {e}")
    
    async def _send_inline_keyboard(self, chat_id: int, text: str, keyboard_data: List[List[Dict[str, str]]]):
        """Sendet eine Nachricht mit Inline-Keyboard"""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = []
            for row in keyboard_data:
                keyboard_row = []
                for button in row:
                    keyboard_row.append(InlineKeyboardButton(
                        text=button['text'],
                        callback_data=button['callback_data']
                    ))
                keyboard.append(keyboard_row)
            
            markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Senden der Inline-Keyboard: {e}")
    
    async def request_approval(self, request_type: str, data: Dict[str, Any], 
                             user_id: int, username: str) -> str:
        """Erstellt eine Genehmigungsanfrage"""
        import uuid
        
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        # Erstelle Anfrage
        request = ApprovalRequest(
            id=request_id,
            chat_id=user_id,  # Sende an den Benutzer selbst
            user_id=user_id,
            request_type=request_type,
            data=data,
            timestamp=datetime.now()
        )
        
        self.approval_requests[request_id] = request
        
        # Sende Anfrage an alle autorisierten Benutzer
        await self._send_approval_request(request)
        
        return request_id
    
    async def _send_approval_request(self, request: ApprovalRequest):
        """Sendet eine Genehmigungsanfrage"""
        # Erstelle Nachrichtentext
        message_text = f"""
🔔 **Genehmigungsanfrage: {request.id}**

📝 **Typ:** {request.request_type}
👤 **Benutzer:** {request.username}
⏰ **Zeitstempel:** {request.timestamp.strftime('%H:%M:%S')}

📋 **Details:**
{self._format_request_data(request.data)}

Bitte genehmigen oder lehnen Sie diese Anfrage ab.
        """
        
        # Erstelle Inline-Keyboard
        keyboard_data = [
            [
                {'text': '✅ Genehmigen', 'callback_data': f'approve:{request.id}'},
                {'text': '❌ Ablehnen', 'callback_data': f'reject:{request.id}'}
            ],
            [
                {'text': '👁️ Vorschau', 'callback_data': f'preview:{request.id}'}
            ]
        ]
        
        # Sende an alle autorisierten Benutzer
        for user_id in self.authorized_users + self.admin_users:
            try:
                await self._send_inline_keyboard(user_id, message_text, keyboard_data)
            except Exception as e:
                self.logger.error(f"Fehler beim Senden der Anfrage an {user_id}: {e}")
    
    def _format_request_data(self, data: Dict[str, Any]) -> str:
        """Formatiert Anfragedaten für Anzeige"""
        formatted = ""
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            formatted += f"• **{key}:** {value}\n"
        return formatted
    
    async def _approve_request(self, request_id: str, approver_id: int, approver_name: str):
        """Genehmigt eine Anfrage"""
        if request_id not in self.approval_requests:
            await self._send_message(approver_id, f"Anfrage {request_id} nicht gefunden.")
            return
        
        request = self.approval_requests[request_id]
        
        if request.status != "pending":
            await self._send_message(approver_id, f"Anfrage {request_id} wurde bereits bearbeitet.")
            return
        
        # Markiere als genehmigt
        request.status = "approved"
        request.response = "approved"
        request.response_timestamp = datetime.now()
        
        # Benachrichtige alle Beteiligten
        approval_text = f"""
✅ **Anfrage genehmigt: {request_id}**

👤 **Genehmigt von:** {approver_name}
⏰ **Zeitstempel:** {request.response_timestamp.strftime('%H:%M:%S')}
        """
        
        # Sende Benachrichtigung an alle autorisierten Benutzer
        for user_id in self.authorized_users + self.admin_users:
            try:
                await self._send_message(user_id, approval_text)
            except Exception as e:
                self.logger.error(f"Fehler beim Senden der Genehmigung an {user_id}: {e}")
        
        # Führe genehmigte Aktion aus
        await self._execute_approved_request(request)
    
    async def _reject_request(self, request_id: str, rejecter_id: int, rejecter_name: str):
        """Lehnt eine Anfrage ab"""
        if request_id not in self.approval_requests:
            await self._send_message(rejecter_id, f"Anfrage {request_id} nicht gefunden.")
            return
        
        request = self.approval_requests[request_id]
        
        if request.status != "pending":
            await self._send_message(rejecter_id, f"Anfrage {request_id} wurde bereits bearbeitet.")
            return
        
        # Markiere als abgelehnt
        request.status = "rejected"
        request.response = "rejected"
        request.response_timestamp = datetime.now()
        
        # Benachrichtige alle Beteiligten
        rejection_text = f"""
❌ **Anfrage abgelehnt: {request_id}**

👤 **Abgelehnt von:** {rejecter_name}
⏰ **Zeitstempel:** {request.response_timestamp.strftime('%H:%M:%S')}
        """
        
        # Sende Benachrichtigung an alle autorisierten Benutzer
        for user_id in self.authorized_users + self.admin_users:
            try:
                await self._send_message(user_id, rejection_text)
            except Exception as e:
                self.logger.error(f"Fehler beim Senden der Ablehnung an {user_id}: {e}")
    
    async def _handle_approval_callback(self, request_id: str, callback_query):
        """Behandelt Genehmigungs-Callback"""
        await self._approve_request(request_id, callback_query.from_user.id, callback_query.from_user.username)
        await callback_query.answer("Anfrage genehmigt")
    
    async def _handle_rejection_callback(self, request_id: str, callback_query):
        """Behandelt Ablehnungs-Callback"""
        await self._reject_request(request_id, callback_query.from_user.id, callback_query.from_user.username)
        await callback_query.answer("Anfrage abgelehnt")
    
    async def _handle_preview_callback(self, request_id: str, callback_query):
        """Behandelt Vorschau-Callback"""
        if request_id not in self.approval_requests:
            await callback_query.answer("Anfrage nicht gefunden")
            return
        
        request = self.approval_requests[request_id]
        
        # Zeige detaillierte Vorschau
        preview_text = f"""
👁️ **Vorschau: {request_id}**

📝 **Typ:** {request.request_type}
👤 **Benutzer:** {request.username}
⏰ **Erstellt:** {request.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

📋 **Vollständige Daten:**
{json.dumps(request.data, indent=2, ensure_ascii=False)}
        """
        
        await self._send_message(callback_query.from_user.id, f"```\n{preview_text}\n```", "Markdown")
        await callback_query.answer("Vorschau gesendet")
    
    async def _execute_approved_request(self, request: ApprovalRequest):
        """Führt eine genehmigte Anfrage aus"""
        handler = self.request_handlers.get(request.request_type)
        if handler:
            try:
                await handler(request)
                self.logger.info(f"Genehmigte Anfrage ausgeführt: {request.id}")
            except Exception as e:
                self.logger.error(f"Fehler beim Ausführen der genehmigten Anfrage: {e}")
        else:
            self.logger.warning(f"Kein Handler für Anfrage-Typ: {request.request_type}")
    
    async def _handle_email_approval(self, request: ApprovalRequest):
        """Behandelt Email-Genehmigungsanfragen"""
        # Hier würde die Email gesendet werden
        self.logger.info(f"Email-Genehmigung ausgeführt: {request.id}")
    
    async def _handle_task_approval(self, request: ApprovalRequest):
        """Behandelt Task-Genehmigungsanfragen"""
        # Hier würde der Task ausgeführt werden
        self.logger.info(f"Task-Genehmigung ausgeführt: {request.id}")
    
    async def _handle_config_approval(self, request: ApprovalRequest):
        """Behandelt Konfigurations-Genehmigungsanfragen"""
        # Hier würde die Konfiguration geändert werden
        self.logger.info(f"Konfigurations-Genehmigung ausgeführt: {request.id}")
    
    async def _process_text_message(self, msg: TelegramMessage) -> Optional[str]:
        """Verarbeitet normale Textnachrichten"""
        # Einfache Echo-Funktion
        return f"Nachricht empfangen: {msg.text}"
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet eine Telegram-Task"""
        task_type = task_data.get('type', 'send_message')
        
        if task_type == 'send_message':
            return await self._handle_send_message_task(task_data)
        elif task_type == 'request_approval':
            return await self._handle_request_approval_task(task_data)
        elif task_type == 'broadcast':
            return await self._handle_broadcast_task(task_data)
        else:
            return {'error': f'Unbekannter Task-Typ: {task_type}', 'success': False}
    
    async def _handle_send_message_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Message-Send-Task"""
        chat_id = task_data.get('chat_id')
        message = task_data.get('message')
        
        if not all([chat_id, message]):
            return {'error': 'chat_id und message erforderlich', 'success': False}
        
        await self._send_message(chat_id, message)
        
        return {
            'success': True,
            'chat_id': chat_id,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _handle_request_approval_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Approval-Request-Task"""
        request_type = task_data.get('request_type')
        data = task_data.get('data', {})
        user_id = task_data.get('user_id')
        username = task_data.get('username', 'Unknown')
        
        if not all([request_type, user_id]):
            return {'error': 'request_type und user_id erforderlich', 'success': False}
        
        request_id = await self.request_approval(request_type, data, user_id, username)
        
        return {
            'success': True,
            'request_id': request_id,
            'request_type': request_type,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _handle_broadcast_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Behandelt Broadcast-Task"""
        message = task_data.get('message')
        
        if not message:
            return {'error': 'message erforderlich', 'success': False}
        
        # Sende an alle autorisierten Benutzer
        sent_count = 0
        for user_id in self.authorized_users + self.admin_users:
            try:
                await self._send_message(user_id, message)
                sent_count += 1
            except Exception as e:
                self.logger.error(f"Fehler beim Broadcast an {user_id}: {e}")
        
        return {
            'success': True,
            'message': message,
            'sent_count': sent_count,
            'total_users': len(self.authorized_users + self.admin_users),
            'timestamp': datetime.now().isoformat()
        }