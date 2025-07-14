"""
Liyana NEXUS v1 - NEXUS Core
Super-KI-Agent Stufe 8 - Zentrale Steuerung und Koordination
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from config import AgentState, config
from .task_manager import TaskManager
from .state_manager import StateManager
from .error_handler import ErrorHandler

@dataclass
class AgentInfo:
    """Informationen über einen Subagenten"""
    name: str
    module: str
    state: AgentState = AgentState.WAITING
    last_activity: datetime = field(default_factory=datetime.now)
    error_count: int = 0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class NexusCore:
    """
    Zentrale Steuerung des Liyana NEXUS v1 Systems
    Koordiniert alle Subagenten und verwaltet den Systemzustand
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = AgentState.WAITING
        self.start_time = datetime.now()
        
        # Manager-Instanzen
        self.task_manager = TaskManager()
        self.state_manager = StateManager()
        self.error_handler = ErrorHandler()
        
        # Subagenten-Registry
        self.agents: Dict[str, AgentInfo] = {}
        self.agent_modules: Dict[str, Any] = {}
        
        # Event-Handler
        self.event_handlers: Dict[str, List[Callable]] = {
            'agent_started': [],
            'agent_stopped': [],
            'task_completed': [],
            'error_occurred': [],
            'state_changed': []
        }
        
        # System-Metriken
        self.metrics = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_runtime': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        self.logger.info("NEXUS Core initialisiert")
    
    async def initialize(self) -> bool:
        """Initialisiert das NEXUS-System"""
        try:
            self.logger.info("Starte NEXUS Core Initialisierung...")
            
            # Validiere Konfiguration
            config_errors = config.validate_config()
            if config_errors:
                for error in config_errors:
                    self.logger.error(f"Konfigurationsfehler: {error}")
                return False
            
            # Initialisiere Manager
            await self.task_manager.initialize()
            await self.state_manager.initialize()
            await self.error_handler.initialize()
            
            # Registriere Standard-Subagenten
            await self._register_default_agents()
            
            self.state = AgentState.WAITING
            self.logger.info("NEXUS Core erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei NEXUS Core Initialisierung: {e}")
            self.error_handler.handle_error(e, "NEXUS_CORE_INIT")
            return False
    
    async def _register_default_agents(self):
        """Registriert die Standard-Subagenten"""
        default_agents = [
            ("EmailUnit", "units.email_unit.EmailUnit"),
            ("ResponderUnit", "units.responder_unit.ResponderUnit"),
            ("TelegramUnit", "units.telegram_unit.TelegramUnit"),
            ("CallCenterUnit", "units.call_center_unit.CallCenterUnit"),
            ("VoiceCloneUnit", "units.voice_clone_unit.VoiceCloneUnit"),
            ("DropUnit", "units.drop_unit.DropUnit"),
            ("SearchAgent", "units.search_agent.SearchAgent"),
            ("MemoryVault", "units.memory_vault.MemoryVault"),
            ("LearningCore", "units.learning_core.LearningCore"),
            ("AutomationInit", "units.automation_init.AutomationInit")
        ]
        
        for agent_name, module_path in default_agents:
            await self.register_agent(agent_name, module_path)
    
    async def register_agent(self, name: str, module_path: str) -> bool:
        """Registriert einen neuen Subagenten"""
        try:
            # Dynamischer Import des Moduls
            module_parts = module_path.split('.')
            module = __import__(module_parts[0])
            for part in module_parts[1:]:
                module = getattr(module, part)
            
            # Erstelle Agent-Instanz
            agent_instance = module()
            
            # Registriere Agent
            self.agents[name] = AgentInfo(
                name=name,
                module=module_path,
                state=AgentState.WAITING
            )
            self.agent_modules[name] = agent_instance
            
            self.logger.info(f"Subagent '{name}' registriert")
            await self._emit_event('agent_started', {'name': name})
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Registrieren von Agent '{name}': {e}")
            self.error_handler.handle_error(e, f"AGENT_REGISTER_{name}")
            return False
    
    async def start_agent(self, name: str) -> bool:
        """Startet einen Subagenten"""
        if name not in self.agents:
            self.logger.error(f"Agent '{name}' nicht gefunden")
            return False
        
        try:
            agent = self.agents[name]
            agent_instance = self.agent_modules[name]
            
            # Starte Agent
            if hasattr(agent_instance, 'start'):
                await agent_instance.start()
            
            agent.state = AgentState.EXECUTING
            agent.is_active = True
            agent.last_activity = datetime.now()
            
            self.logger.info(f"Agent '{name}' gestartet")
            await self._emit_event('agent_started', {'name': name})
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Starten von Agent '{name}': {e}")
            self.error_handler.handle_error(e, f"AGENT_START_{name}")
            return False
    
    async def stop_agent(self, name: str) -> bool:
        """Stoppt einen Subagenten"""
        if name not in self.agents:
            return False
        
        try:
            agent = self.agents[name]
            agent_instance = self.agent_modules[name]
            
            # Stoppe Agent
            if hasattr(agent_instance, 'stop'):
                await agent_instance.stop()
            
            agent.state = AgentState.PAUSED
            agent.is_active = False
            
            self.logger.info(f"Agent '{name}' gestoppt")
            await self._emit_event('agent_stopped', {'name': name})
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Stoppen von Agent '{name}': {e}")
            return False
    
    async def execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Führt eine Aufgabe aus"""
        try:
            self.state = AgentState.EXECUTING
            
            # Erstelle Task
            task_id = await self.task_manager.create_task(task_type, task_data)
            
            # Verteile Task an passenden Agent
            result = await self._distribute_task(task_id, task_type, task_data)
            
            self.metrics['tasks_completed'] += 1
            await self._emit_event('task_completed', {
                'task_id': task_id,
                'task_type': task_type,
                'result': result
            })
            
            return result
            
        except Exception as e:
            self.metrics['tasks_failed'] += 1
            self.logger.error(f"Fehler bei Task-Ausführung: {e}")
            self.error_handler.handle_error(e, f"TASK_EXECUTION_{task_type}")
            return {'error': str(e), 'success': False}
        
        finally:
            self.state = AgentState.WAITING
    
    async def _distribute_task(self, task_id: str, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verteilt eine Aufgabe an den passenden Subagenten"""
        
        # Mapping von Task-Typen zu Agenten
        task_agent_mapping = {
            'email_processing': 'EmailUnit',
            'response_generation': 'ResponderUnit',
            'telegram_interaction': 'TelegramUnit',
            'voice_processing': 'CallCenterUnit',
            'voice_cloning': 'VoiceCloneUnit',
            'dropshipping': 'DropUnit',
            'product_search': 'SearchAgent',
            'memory_operation': 'MemoryVault',
            'learning_task': 'LearningCore'
        }
        
        agent_name = task_agent_mapping.get(task_type)
        if not agent_name or agent_name not in self.agents:
            return {'error': f'Kein Agent für Task-Typ {task_type} verfügbar', 'success': False}
        
        agent_instance = self.agent_modules[agent_name]
        
        # Führe Task aus
        if hasattr(agent_instance, 'process_task'):
            result = await agent_instance.process_task(task_data)
        else:
            result = {'error': f'Agent {agent_name} hat keine process_task Methode', 'success': False}
        
        return result
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Gibt den aktuellen Systemstatus zurück"""
        return {
            'core_state': self.state.value,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'agents': {
                name: {
                    'state': agent.state.value,
                    'is_active': agent.is_active,
                    'last_activity': agent.last_activity.isoformat(),
                    'error_count': agent.error_count
                }
                for name, agent in self.agents.items()
            },
            'metrics': self.metrics,
            'task_queue_size': await self.task_manager.get_queue_size(),
            'memory_usage': self._get_memory_usage(),
            'cpu_usage': self._get_cpu_usage()
        }
    
    def _get_memory_usage(self) -> float:
        """Gibt die aktuelle Speichernutzung zurück"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Gibt die aktuelle CPU-Nutzung zurück"""
        try:
            import psutil
            return psutil.cpu_percent()
        except:
            return 0.0
    
    async def add_event_handler(self, event_type: str, handler: Callable):
        """Fügt einen Event-Handler hinzu"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Sendet ein Event an alle registrierten Handler"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    self.logger.error(f"Fehler im Event-Handler: {e}")
    
    async def start(self):
        """Startet das NEXUS-System"""
        if self._running:
            return
        
        self._running = True
        self.logger.info("NEXUS Core gestartet")
        
        # Starte alle aktiven Agenten
        for name in self.agents:
            await self.start_agent(name)
        
        # Hauptschleife
        while self._running and not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(1)
                
                # Update Metriken
                self.metrics['total_runtime'] = (datetime.now() - self.start_time).total_seconds()
                self.metrics['memory_usage'] = self._get_memory_usage()
                self.metrics['cpu_usage'] = self._get_cpu_usage()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Fehler in NEXUS Hauptschleife: {e}")
    
    async def stop(self):
        """Stoppt das NEXUS-System"""
        self._running = False
        self._shutdown_event.set()
        
        # Stoppe alle Agenten
        for name in self.agents:
            await self.stop_agent(name)
        
        # Stoppe Manager
        await self.task_manager.shutdown()
        await self.state_manager.shutdown()
        await self.error_handler.shutdown()
        
        self.logger.info("NEXUS Core gestoppt")
    
    async def __aenter__(self):
        """Async Context Manager Entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async Context Manager Exit"""
        await self.stop()