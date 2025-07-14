"""
Liyana NEXUS v1 - Automation Init
GUI-Dialog, der beim Start fragt: „Welche Automatisierung?"
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from config import config, AgentState, AutomationType

class AutomationInit:
    """Automation Initialization Dialog"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = AgentState.WAITING
        self._running = False
        
        # Verfügbare Automatisierungen
        self.available_automations = {
            AutomationType.EMAIL_SUPPORT: {
                'name': 'Email Support',
                'description': 'Automatische Email-Verarbeitung und -Antworten',
                'enabled': True
            },
            AutomationType.CALL_CENTER: {
                'name': 'Call Center',
                'description': 'Sprachverarbeitung und Anrufbehandlung',
                'enabled': False  # Noch nicht implementiert
            },
            AutomationType.DROPSHIPPING: {
                'name': 'Dropshipping',
                'description': 'Automatische Produktverwaltung und Bestellungen',
                'enabled': True
            },
            AutomationType.TELEGRAM_BOT: {
                'name': 'Telegram Bot',
                'description': 'Bot für Rückfragen und Genehmigungen',
                'enabled': True
            },
            AutomationType.VOICE_ASSISTANT: {
                'name': 'Voice Assistant',
                'description': 'Sprachassistenz und Tonaufnahme',
                'enabled': False  # Noch nicht implementiert
            },
            AutomationType.SEARCH_AGENT: {
                'name': 'Search Agent',
                'description': 'Produktsuche und Trendanalysen',
                'enabled': True
            }
        }
        
        # Aktive Automatisierungen
        self.active_automations = []
        
    async def start(self):
        """Startet den Automation Init"""
        self.logger.info("Automation Init gestartet")
        self._running = True
        self.state = AgentState.EXECUTING
    
    async def stop(self):
        """Stoppt den Automation Init"""
        self.logger.info("Automation Init gestoppt")
        self._running = False
        self.state = AgentState.PAUSED
    
    def get_available_automations(self) -> Dict[str, Any]:
        """Gibt verfügbare Automatisierungen zurück"""
        return self.available_automations
    
    def get_active_automations(self) -> list:
        """Gibt aktive Automatisierungen zurück"""
        return self.active_automations
    
    def set_active_automations(self, automation_types: list):
        """Setzt aktive Automatisierungen"""
        self.active_automations = automation_types
        self.logger.info(f"Aktive Automatisierungen gesetzt: {automation_types}")
    
    def is_automation_enabled(self, automation_type: AutomationType) -> bool:
        """Prüft ob eine Automatisierung aktiviert ist"""
        return automation_type in self.active_automations
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet eine Automation Init Task"""
        task_type = task_data.get('type', 'get_automations')
        
        if task_type == 'get_automations':
            return await self._get_automations(task_data)
        elif task_type == 'set_automations':
            return await self._set_automations(task_data)
        elif task_type == 'init_automation':
            return await self._init_automation(task_data)
        else:
            return {'error': f'Unbekannter Task-Typ: {task_type}', 'success': False}
    
    async def _get_automations(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gibt Automatisierungen zurück"""
        return {
            'success': True,
            'available_automations': self.available_automations,
            'active_automations': self.active_automations,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _set_automations(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Setzt Automatisierungen"""
        automation_types = task_data.get('automation_types', [])
        
        # Validiere Automatisierungen
        valid_automations = []
        for automation_type in automation_types:
            if automation_type in self.available_automations:
                if self.available_automations[automation_type]['enabled']:
                    valid_automations.append(automation_type)
                else:
                    self.logger.warning(f"Automatisierung {automation_type} ist deaktiviert")
            else:
                self.logger.warning(f"Unbekannte Automatisierung: {automation_type}")
        
        self.set_active_automations(valid_automations)
        
        return {
            'success': True,
            'active_automations': valid_automations,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _init_automation(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialisiert eine spezifische Automatisierung"""
        automation_type = task_data.get('automation_type')
        
        if not automation_type:
            return {'error': 'Keine Automatisierung angegeben', 'success': False}
        
        if automation_type not in self.available_automations:
            return {'error': f'Unbekannte Automatisierung: {automation_type}', 'success': False}
        
        if not self.available_automations[automation_type]['enabled']:
            return {'error': f'Automatisierung {automation_type} ist deaktiviert', 'success': False}
        
        # Hier würde die spezifische Initialisierung stattfinden
        self.logger.info(f"Initialisiere Automatisierung: {automation_type}")
        
        return {
            'success': True,
            'automation_type': automation_type,
            'initialized': True,
            'timestamp': datetime.now().isoformat()
        }