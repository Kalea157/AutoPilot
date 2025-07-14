"""
Liyana NEXUS v1 - Telegram Unit
Telegram-Bot für Rückfragen und Genehmigungen
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import config
from memory_vault import RequestData

@dataclass
class TelegramMessage:
    """Telegram-Nachrichten-Struktur"""
    id: str
    chat_id: str
    user_id: str
    text: str
    timestamp: float
    message_type: str = "text"  # text, photo, document, etc.

@dataclass
class ApprovalRequest:
    """Genehmigungsanfrage-Struktur"""
    id: str
    request_id: str
    chat_id: str
    message: str
    options: List[str]
    timeout: int = 300  # 5 Minuten Standard
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class TelegramUnit:
    """
    Telegram Unit - Telegram-Bot für Rückfragen und Genehmigungen
    Ermöglicht JA/NEIN-Antworten, Vorschauen und Antwortauswahl
    """
    
    def __init__(self, memory_vault):
        self.logger = logging.getLogger("nexus.telegram")
        self.memory = memory_vault
        self.is_running = False
        self.bot = None
        self.chat_id = None
        self.pending_approvals = {}
        
        # Telegram-Konfiguration
        self.bot_token = config.TELEGRAM_CONFIG["bot_token"]
        self.chat_id = config.TELEGRAM_CONFIG["chat_id"]
        
        self.logger.info("📱 Telegram Unit initialisiert")
    
    async def start(self):
        """Startet die Telegram Unit"""
        if self.is_running:
            return
        
        if not self.bot_token:
            self.logger.warning("⚠️ Kein Telegram Bot Token konfiguriert")
            return
        
        self.logger.info("🚀 Starte Telegram Unit...")
        self.is_running = True
        
        # Initialisiere Bot
        await self._init_bot()
        
        # Starte Message-Handler
        asyncio.create_task(self._handle_messages())
        
        # Starte Approval-Cleanup
        asyncio.create_task(self._cleanup_expired_approvals())
        
        self.logger.info("✅ Telegram Unit gestartet")
    
    async def stop(self):
        """Stoppt die Telegram Unit"""
        self.logger.info("🛑 Stoppe Telegram Unit...")
        self.is_running = False
        
        if self.bot:
            await self.bot.stop()
        
        self.logger.info("✅ Telegram Unit gestoppt")
    
    async def _init_bot(self):
        """Initialisiert den Telegram-Bot"""
        try:
            # Hier würde die tatsächliche Bot-Initialisierung stehen
            # Für jetzt simulieren wir die Funktionalität
            self.logger.info("🤖 Telegram Bot initialisiert (Simulation)")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Initialisieren des Telegram Bots: {e}")
    
    async def _handle_messages(self):
        """Behandelt eingehende Telegram-Nachrichten"""
        while self.is_running:
            try:
                # Hier würde die tatsächliche Nachrichtenverarbeitung stehen
                # Für jetzt simulieren wir die Funktionalität
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"❌ Fehler bei der Nachrichtenverarbeitung: {e}")
                await asyncio.sleep(5)
    
    async def send_message(self, message: str, chat_id: str = None) -> bool:
        """Sendet eine Nachricht über Telegram"""
        try:
            if not chat_id:
                chat_id = self.chat_id
            
            if not chat_id:
                self.logger.error("❌ Keine Chat-ID konfiguriert")
                return False
            
            # Hier würde die tatsächliche Nachrichtenübermittlung stehen
            # Für jetzt simulieren wir die Funktionalität
            self.logger.info(f"📤 Telegram-Nachricht gesendet an {chat_id}: {message[:50]}...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden der Telegram-Nachricht: {e}")
            return False
    
    async def send_approval_request(self, request_id: str, message: str, 
                                  options: List[str] = None, timeout: int = 300) -> bool:
        """Sendet eine Genehmigungsanfrage"""
        try:
            if not options:
                options = ["✅ Ja", "❌ Nein"]
            
            # Erstelle Approval-Request
            approval = ApprovalRequest(
                id=f"approval_{int(time.time() * 1000)}",
                request_id=request_id,
                chat_id=self.chat_id,
                message=message,
                options=options,
                timeout=timeout
            )
            
            # Speichere in Memory
            self.pending_approvals[approval.id] = approval
            
            # Erstelle Nachricht mit Buttons
            formatted_message = f"🔔 **Genehmigungsanfrage**\n\n{message}\n\n"
            for i, option in enumerate(options, 1):
                formatted_message += f"{i}. {option}\n"
            
            formatted_message += f"\n⏰ Timeout: {timeout} Sekunden"
            
            # Sende Nachricht
            success = await self.send_message(formatted_message)
            
            if success:
                self.logger.info(f"✅ Genehmigungsanfrage gesendet: {approval.id}")
                
                # Logge System-Ereignis
                await self.memory.log_system_event(
                    "INFO",
                    "telegram_unit",
                    f"Genehmigungsanfrage gesendet: {approval.id}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden der Genehmigungsanfrage: {e}")
            return False
    
    async def send_preview(self, content: str, content_type: str = "email") -> bool:
        """Sendet eine Vorschau"""
        try:
            # Erstelle Vorschau-Nachricht
            preview_message = f"👁️ **Vorschau ({content_type})**\n\n"
            preview_message += f"```\n{content[:1000]}\n```"
            
            if len(content) > 1000:
                preview_message += f"\n\n... (gekürzt, {len(content)} Zeichen gesamt)"
            
            # Sende Nachricht
            success = await self.send_message(preview_message)
            
            if success:
                self.logger.info(f"✅ Vorschau gesendet: {content_type}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden der Vorschau: {e}")
            return False
    
    async def send_response_options(self, request_id: str, responses: List[str]) -> bool:
        """Sendet Antwortoptionen zur Auswahl"""
        try:
            # Erstelle Nachricht mit Antwortoptionen
            message = f"📝 **Antwortoptionen für Anfrage {request_id}**\n\n"
            
            for i, response in enumerate(responses, 1):
                message += f"**Option {i}:**\n{response[:200]}...\n\n"
            
            message += "Antworten Sie mit der Nummer der gewünschten Option."
            
            # Sende Nachricht
            success = await self.send_message(message)
            
            if success:
                self.logger.info(f"✅ Antwortoptionen gesendet für Anfrage: {request_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden der Antwortoptionen: {e}")
            return False
    
    async def handle_approval_response(self, approval_id: str, response: str) -> bool:
        """Behandelt eine Antwort auf eine Genehmigungsanfrage"""
        try:
            approval = self.pending_approvals.get(approval_id)
            if not approval:
                self.logger.warning(f"⚠️ Genehmigungsanfrage nicht gefunden: {approval_id}")
                return False
            
            # Prüfe Timeout
            if time.time() - approval.created_at > approval.timeout:
                self.logger.warning(f"⚠️ Genehmigungsanfrage abgelaufen: {approval_id}")
                del self.pending_approvals[approval_id]
                return False
            
            # Verarbeite Antwort
            response_lower = response.lower()
            approved = False
            
            if any(word in response_lower for word in ["ja", "yes", "1", "ok", "genehmigt"]):
                approved = True
            elif any(word in response_lower for word in ["nein", "no", "2", "abgelehnt"]):
                approved = False
            else:
                # Unklare Antwort
                await self.send_message(f"❓ Unklare Antwort: '{response}'. Bitte antworten Sie mit 'Ja' oder 'Nein'.")
                return False
            
            # Aktualisiere ursprüngliche Anfrage
            await self._update_request_with_approval(approval.request_id, approved, response)
            
            # Bestätige Antwort
            status = "✅ Genehmigt" if approved else "❌ Abgelehnt"
            await self.send_message(f"{status}: {approval.message[:100]}...")
            
            # Entferne aus pending_approvals
            del self.pending_approvals[approval_id]
            
            self.logger.info(f"✅ Genehmigungsantwort verarbeitet: {approval_id} -> {approved}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Verarbeiten der Genehmigungsantwort: {e}")
            return False
    
    async def _update_request_with_approval(self, request_id: str, approved: bool, response: str):
        """Aktualisiert eine Anfrage basierend auf der Genehmigung"""
        try:
            # Lade Anfrage
            # Hier würde die tatsächliche Datenbankabfrage stehen
            # Für jetzt simulieren wir die Funktionalität
            
            status = "approved" if approved else "rejected"
            
            # Aktualisiere Status
            await self.memory.update_request_status(
                request_id,
                status,
                {"approval_response": response, "approved": approved}
            )
            
            self.logger.info(f"✅ Anfrage {request_id} aktualisiert: {status}")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Aktualisieren der Anfrage: {e}")
    
    async def _cleanup_expired_approvals(self):
        """Bereinigt abgelaufene Genehmigungsanfragen"""
        while self.is_running:
            try:
                current_time = time.time()
                expired_approvals = []
                
                for approval_id, approval in self.pending_approvals.items():
                    if current_time - approval.created_at > approval.timeout:
                        expired_approvals.append(approval_id)
                
                for approval_id in expired_approvals:
                    approval = self.pending_approvals.pop(approval_id)
                    await self.send_message(f"⏰ Genehmigungsanfrage abgelaufen: {approval.message[:100]}...")
                    
                    # Markiere als abgelaufen
                    await self.memory.update_request_status(
                        approval.request_id,
                        "expired",
                        {"reason": "approval_timeout"}
                    )
                    
                    self.logger.info(f"⏰ Genehmigungsanfrage abgelaufen: {approval_id}")
                
                await asyncio.sleep(60)  # Alle Minute prüfen
                
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Cleanup der Genehmigungsanfragen: {e}")
                await asyncio.sleep(60)
    
    async def send_notification(self, title: str, message: str, level: str = "info") -> bool:
        """Sendet eine Benachrichtigung"""
        try:
            # Emoji basierend auf Level
            emoji_map = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "error": "❌"
            }
            
            emoji = emoji_map.get(level, "ℹ️")
            
            # Formatiere Nachricht
            formatted_message = f"{emoji} **{title}**\n\n{message}"
            
            # Sende Nachricht
            success = await self.send_message(formatted_message)
            
            if success:
                self.logger.info(f"✅ Benachrichtigung gesendet: {title}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden der Benachrichtigung: {e}")
            return False
    
    async def send_system_status(self, status_data: Dict[str, Any]) -> bool:
        """Sendet System-Status"""
        try:
            # Formatiere Status-Nachricht
            message = "🖥️ **System-Status**\n\n"
            
            # System-Info
            message += f"**System:** {status_data.get('system_name', 'N/A')}\n"
            message += f"**Version:** {status_data.get('version', 'N/A')}\n"
            message += f"**Status:** {'🟢 Online' if status_data.get('is_running') else '🔴 Offline'}\n"
            
            # Uptime
            uptime = status_data.get('uptime', 0)
            if uptime > 0:
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                message += f"**Uptime:** {hours}h {minutes}m\n"
            
            # Agenten-Status
            agents = status_data.get('agents', {})
            if agents:
                message += "\n**Agenten:**\n"
                for agent_name, agent_data in agents.items():
                    state = agent_data.get('state', 'unknown')
                    is_active = agent_data.get('is_active', False)
                    status_emoji = "🟢" if is_active else "🔴"
                    message += f"{status_emoji} {agent_name}: {state}\n"
            
            # Sende Nachricht
            success = await self.send_message(message)
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Senden des System-Status: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Gibt den Status der Telegram Unit zurück"""
        return {
            "state": "EXECUTING" if self.is_running else "WAITING",
            "bot_configured": bool(self.bot_token),
            "chat_configured": bool(self.chat_id),
            "pending_approvals": len(self.pending_approvals),
            "last_message": time.time()
        }
    
    async def pause(self):
        """Pausiert die Telegram Unit"""
        self.is_running = False
        self.logger.info("⏸️ Telegram Unit pausiert")
    
    async def resume(self):
        """Setzt die Telegram Unit fort"""
        if not self.is_running:
            await self.start()
        self.logger.info("▶️ Telegram Unit fortgesetzt")