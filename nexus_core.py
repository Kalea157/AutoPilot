"""
Liyana NEXUS v1 - NEXUS Core
Super-KI-Agent Stufe 8 - Zentrale Steuerung
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import config
from memory_vault import MemoryVault
from email_unit import EmailUnit
from responder_unit import ResponderUnit
from telegram_unit import TelegramUnit
from call_center_unit import CallCenterUnit
from voice_clone_unit import VoiceCloneUnit
from drop_unit import DropUnit
from search_agent import SearchAgent
from learning_core import LearningCore

class AgentState(Enum):
    """Agent-Zustände"""
    WAITING = "WAITING"
    THINKING = "THINKING"
    EXECUTING = "EXECUTING"
    LEARNING = "LEARNING"
    ERROR = "ERROR"
    PAUSED = "PAUSED"

@dataclass
class AgentInfo:
    """Informationen über einen Subagenten"""
    name: str
    state: AgentState
    last_activity: float
    error_count: int
    is_active: bool
    description: str

class NexusCore:
    """
    NEXUS Core - Zentrale Steuerung des Super-KI-Agenten
    Verwaltet alle Subagenten und koordiniert deren Aktivitäten
    """
    
    def __init__(self):
        self.logger = logging.getLogger("nexus.core")
        self.logger.info("🚀 Initialisiere Liyana NEXUS v1 Core...")
        
        # System-Status
        self.is_running = False
        self.start_time = None
        self.current_task = None
        
        # Subagenten-Registry
        self.agents: Dict[str, Any] = {}
        self.agent_info: Dict[str, AgentInfo] = {}
        
        # Memory Vault (zentraler Speicher)
        self.memory = MemoryVault()
        
        # Event-Loop und Threading
        self.loop = None
        self.worker_thread = None
        
        # Initialisiere alle Subagenten
        self._initialize_agents()
        
        self.logger.info("✅ NEXUS Core initialisiert")
    
    def _initialize_agents(self):
        """Initialisiert alle Subagenten"""
        try:
            # Core-Agenten
            self.agents["email"] = EmailUnit(self.memory)
            self.agents["responder"] = ResponderUnit(self.memory)
            self.agents["telegram"] = TelegramUnit(self.memory)
            self.agents["call_center"] = CallCenterUnit(self.memory)
            self.agents["voice_clone"] = VoiceCloneUnit(self.memory)
            self.agents["drop"] = DropUnit(self.memory)
            self.agents["search"] = SearchAgent(self.memory)
            self.agents["learning"] = LearningCore(self.memory)
            
            # Agent-Info initialisieren
            agent_descriptions = {
                "email": "E-Mail-Verarbeitung und -Versand",
                "responder": "KI-basierte Antwortgenerierung",
                "telegram": "Telegram-Bot für Rückfragen",
                "call_center": "Sprachverarbeitung und Anrufbehandlung",
                "voice_clone": "Stimmklonen und Text-to-Speech",
                "drop": "Dropshipping-Automatisierung",
                "search": "Produktsuche und Marktforschung",
                "learning": "Selbstlernendes System"
            }
            
            for name, agent in self.agents.items():
                self.agent_info[name] = AgentInfo(
                    name=name,
                    state=AgentState.WAITING,
                    last_activity=time.time(),
                    error_count=0,
                    is_active=False,
                    description=agent_descriptions.get(name, "Unbekannter Agent")
                )
            
            self.logger.info(f"✅ {len(self.agents)} Subagenten initialisiert")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Initialisieren der Agenten: {e}")
            raise
    
    async def start(self, automation_type: str = None):
        """Startet das NEXUS-System"""
        if self.is_running:
            self.logger.warning("⚠️ NEXUS läuft bereits")
            return
        
        self.logger.info("🚀 Starte Liyana NEXUS v1...")
        self.is_running = True
        self.start_time = time.time()
        
        # Starte Event-Loop in separatem Thread
        self.worker_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.worker_thread.start()
        
        # Warte bis Loop läuft
        while self.loop is None:
            await asyncio.sleep(0.1)
        
        # Starte alle aktiven Agenten
        await self._start_agents(automation_type)
        
        self.logger.info("✅ NEXUS erfolgreich gestartet")
    
    def _run_event_loop(self):
        """Führt den Event-Loop in separatem Thread aus"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        except Exception as e:
            self.logger.error(f"❌ Event-Loop Fehler: {e}")
        finally:
            self.loop.close()
    
    async def _start_agents(self, automation_type: str = None):
        """Startet Agenten basierend auf Automatisierungstyp"""
        if automation_type:
            self.current_task = automation_type
            self.logger.info(f"🎯 Starte Automatisierung: {automation_type}")
        
        # Starte Core-Agenten (immer aktiv)
        core_agents = ["email", "responder", "telegram", "memory"]
        
        # Füge spezifische Agenten basierend auf Automatisierung hinzu
        if automation_type == "email_support":
            active_agents = core_agents + ["call_center"]
        elif automation_type == "call_center":
            active_agents = core_agents + ["call_center", "voice_clone"]
        elif automation_type == "dropshipping":
            active_agents = core_agents + ["drop", "search"]
        elif automation_type == "research":
            active_agents = core_agents + ["search", "learning"]
        else:
            active_agents = core_agents
        
        for agent_name in active_agents:
            if agent_name in self.agents:
                await self._start_agent(agent_name)
        
        # Starte Monitoring
        asyncio.create_task(self._monitor_agents())
    
    async def _start_agent(self, agent_name: str):
        """Startet einen einzelnen Agenten"""
        try:
            agent = self.agents[agent_name]
            if hasattr(agent, 'start'):
                await agent.start()
            
            self.agent_info[agent_name].is_active = True
            self.agent_info[agent_name].state = AgentState.WAITING
            self.agent_info[agent_name].last_activity = time.time()
            
            self.logger.info(f"✅ Agent '{agent_name}' gestartet")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Starten von Agent '{agent_name}': {e}")
            self.agent_info[agent_name].state = AgentState.ERROR
            self.agent_info[agent_name].error_count += 1
    
    async def _monitor_agents(self):
        """Überwacht alle Agenten und deren Zustände"""
        while self.is_running:
            try:
                for agent_name, info in self.agent_info.items():
                    if info.is_active:
                        # Prüfe Agent-Status
                        agent = self.agents.get(agent_name)
                        if agent and hasattr(agent, 'get_status'):
                            status = await agent.get_status()
                            info.state = AgentState(status.get('state', 'WAITING'))
                            info.last_activity = time.time()
                        
                        # Auto-Restart bei Fehlern
                        if info.error_count > 0 and info.state == AgentState.ERROR:
                            if config.NEXUS_CONFIG["auto_restart"]:
                                self.logger.warning(f"🔄 Restarte Agent '{agent_name}' nach Fehler")
                                await self._restart_agent(agent_name)
                
                await asyncio.sleep(5)  # Alle 5 Sekunden prüfen
                
            except Exception as e:
                self.logger.error(f"❌ Fehler im Agent-Monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _restart_agent(self, agent_name: str):
        """Startet einen Agenten neu"""
        try:
            agent = self.agents[agent_name]
            if hasattr(agent, 'stop'):
                await agent.stop()
            
            await asyncio.sleep(2)  # Kurze Pause
            
            if hasattr(agent, 'start'):
                await agent.start()
            
            self.agent_info[agent_name].error_count = 0
            self.agent_info[agent_name].state = AgentState.WAITING
            self.agent_info[agent_name].last_activity = time.time()
            
            self.logger.info(f"✅ Agent '{agent_name}' erfolgreich neu gestartet")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Neustart von Agent '{agent_name}': {e}")
    
    async def stop(self):
        """Stoppt das NEXUS-System"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Stoppe Liyana NEXUS v1...")
        self.is_running = False
        
        # Stoppe alle Agenten
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'stop'):
                    await agent.stop()
                self.agent_info[agent_name].is_active = False
                self.agent_info[agent_name].state = AgentState.PAUSED
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Stoppen von Agent '{agent_name}': {e}")
        
        # Stoppe Event-Loop
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
        
        self.logger.info("✅ NEXUS erfolgreich gestoppt")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen System-Status zurück"""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        return {
            "system_name": config.NEXUS_CONFIG["system_name"],
            "version": config.NEXUS_CONFIG["version"],
            "stage": config.NEXUS_CONFIG["stage"],
            "is_running": self.is_running,
            "uptime": uptime,
            "current_task": self.current_task,
            "agents": {
                name: {
                    "state": info.state.value,
                    "is_active": info.is_active,
                    "last_activity": info.last_activity,
                    "error_count": info.error_count,
                    "description": info.description
                }
                for name, info in self.agent_info.items()
            },
            "memory_stats": self.memory.get_stats() if self.memory else {}
        }
    
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Führt eine spezifische Aufgabe aus"""
        try:
            self.logger.info(f"🎯 Führe Aufgabe aus: {task_type}")
            
            # Wähle passende Agenten für die Aufgabe
            if task_type == "email_processing":
                result = await self.agents["email"].process_emails(task_data)
            elif task_type == "generate_response":
                result = await self.agents["responder"].generate_response(task_data)
            elif task_type == "voice_call":
                result = await self.agents["call_center"].handle_call(task_data)
            elif task_type == "product_search":
                result = await self.agents["search"].search_products(task_data)
            elif task_type == "dropshipping":
                result = await self.agents["drop"].process_order(task_data)
            else:
                raise ValueError(f"Unbekannte Aufgabe: {task_type}")
            
            # Speichere in Memory Vault
            await self.memory.store_task_result(task_type, task_data, result)
            
            return {
                "success": True,
                "task_type": task_type,
                "result": result,
                "timestamp": time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Aufgabe '{task_type}': {e}")
            return {
                "success": False,
                "task_type": task_type,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_agent_status(self, agent_name: str) -> Optional[AgentInfo]:
        """Gibt den Status eines spezifischen Agenten zurück"""
        return self.agent_info.get(agent_name)
    
    async def pause_agent(self, agent_name: str):
        """Pausiert einen Agenten"""
        if agent_name in self.agents:
            try:
                agent = self.agents[agent_name]
                if hasattr(agent, 'pause'):
                    await agent.pause()
                
                self.agent_info[agent_name].state = AgentState.PAUSED
                self.logger.info(f"⏸️ Agent '{agent_name}' pausiert")
                
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Pausieren von Agent '{agent_name}': {e}")
    
    async def resume_agent(self, agent_name: str):
        """Setzt einen Agenten fort"""
        if agent_name in self.agents:
            try:
                agent = self.agents[agent_name]
                if hasattr(agent, 'resume'):
                    await agent.resume()
                
                self.agent_info[agent_name].state = AgentState.WAITING
                self.logger.info(f"▶️ Agent '{agent_name}' fortgesetzt")
                
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Fortsetzen von Agent '{agent_name}': {e}")

# Singleton-Instanz
_nexus_instance = None

def get_nexus_core() -> NexusCore:
    """Gibt die Singleton-Instanz des NEXUS Core zurück"""
    global _nexus_instance
    if _nexus_instance is None:
        _nexus_instance = NexusCore()
    return _nexus_instance