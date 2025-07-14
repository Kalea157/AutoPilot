"""
Liyana NEXUS v1 - Error Handler
Zentrale Fehlerbehandlung und Logging
"""

import asyncio
import logging
import traceback
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from config import config

class ErrorSeverity(Enum):
    """Fehler-Schweregrade"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Fehler-Kategorien"""
    SYSTEM = "system"
    NETWORK = "network"
    DATABASE = "database"
    API = "api"
    AGENT = "agent"
    TASK = "task"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Informationen über einen Fehler"""
    id: str
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    source: str
    stack_trace: str
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_notes: Optional[str] = None

class ErrorHandler:
    """Zentrale Fehlerbehandlung und Logging"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.errors: Dict[str, ErrorInfo] = {}
        self.error_counters: Dict[str, int] = {}
        
        # Error-Handler
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {
            category: [] for category in ErrorCategory
        }
        
        # Recovery-Strategien
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # Auto-Recovery
        self.auto_recovery_enabled = True
        self.max_retries = 3
        
        # Error-Reporting
        self.error_reporting_enabled = True
        self.error_threshold = 10  # Anzahl Fehler bevor Alarm ausgelöst wird
    
    async def initialize(self):
        """Initialisiert den Error Handler"""
        self.logger.info("Error Handler wird initialisiert...")
        
        # Registriere Standard-Recovery-Strategien
        await self._register_default_recovery_strategies()
        
        # Registriere Standard-Error-Handler
        await self._register_default_error_handlers()
        
        self.logger.info("Error Handler initialisiert")
    
    async def shutdown(self):
        """Beendet den Error Handler"""
        self.logger.info("Error Handler wird beendet...")
        
        # Speichere ungelöste Fehler
        await self._save_unresolved_errors()
        
        self.logger.info("Error Handler beendet")
    
    async def handle_error(self, error: Exception, source: str, 
                          severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                          context: Dict[str, Any] = None) -> str:
        """Behandelt einen Fehler"""
        import uuid
        
        error_id = str(uuid.uuid4())
        error_type = type(error).__name__
        
        # Bestimme Kategorie
        category = self._categorize_error(error, source)
        
        # Erstelle Error-Info
        error_info = ErrorInfo(
            id=error_id,
            timestamp=datetime.now(),
            error_type=error_type,
            message=str(error),
            severity=severity,
            category=category,
            source=source,
            stack_trace=traceback.format_exc(),
            context=context or {}
        )
        
        # Speichere Fehler
        self.errors[error_id] = error_info
        
        # Update Zähler
        self.error_counters[category.value] = self.error_counters.get(category.value, 0) + 1
        
        # Logge Fehler
        await self._log_error(error_info)
        
        # Benachrichtige Handler
        await self._notify_error_handlers(error_info)
        
        # Prüfe Auto-Recovery
        if self.auto_recovery_enabled:
            await self._attempt_auto_recovery(error_info)
        
        # Prüfe Error-Threshold
        await self._check_error_threshold()
        
        self.logger.error(f"Fehler behandelt: {error_id} - {error_type} in {source}")
        return error_id
    
    def _categorize_error(self, error: Exception, source: str) -> ErrorCategory:
        """Kategorisiert einen Fehler"""
        error_type = type(error).__name__
        
        # Netzwerk-Fehler
        if any(network_error in error_type.lower() for network_error in 
               ['connection', 'timeout', 'network', 'socket', 'http']):
            return ErrorCategory.NETWORK
        
        # Datenbank-Fehler
        if any(db_error in error_type.lower() for db_error in 
               ['sqlite', 'database', 'db', 'connection']):
            return ErrorCategory.DATABASE
        
        # API-Fehler
        if any(api_error in error_type.lower() for api_error in 
               ['api', 'http', 'request', 'response']):
            return ErrorCategory.API
        
        # Agent-Fehler
        if 'agent' in source.lower():
            return ErrorCategory.AGENT
        
        # Task-Fehler
        if 'task' in source.lower():
            return ErrorCategory.TASK
        
        # Konfigurations-Fehler
        if any(config_error in error_type.lower() for config_error in 
               ['config', 'configuration', 'setting']):
            return ErrorCategory.CONFIGURATION
        
        # System-Fehler
        if any(system_error in error_type.lower() for system_error in 
               ['system', 'os', 'permission', 'file']):
            return ErrorCategory.SYSTEM
        
        return ErrorCategory.UNKNOWN
    
    async def _log_error(self, error_info: ErrorInfo):
        """Loggt einen Fehler"""
        log_message = (
            f"ERROR [{error_info.severity.value.upper()}] "
            f"[{error_info.category.value}] "
            f"[{error_info.source}] "
            f"{error_info.error_type}: {error_info.message}"
        )
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Logge Stack Trace für HIGH und CRITICAL
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Stack Trace: {error_info.stack_trace}")
    
    async def _notify_error_handlers(self, error_info: ErrorInfo):
        """Benachrichtigt Error-Handler"""
        handlers = self.error_handlers.get(error_info.category, [])
        
        for handler in handlers:
            try:
                await handler(error_info)
            except Exception as e:
                self.logger.error(f"Fehler im Error-Handler: {e}")
    
    async def _attempt_auto_recovery(self, error_info: ErrorInfo):
        """Versucht automatische Wiederherstellung"""
        recovery_strategy = self.recovery_strategies.get(error_info.category.value)
        
        if recovery_strategy:
            try:
                await recovery_strategy(error_info)
                self.logger.info(f"Auto-Recovery erfolgreich für {error_info.id}")
            except Exception as e:
                self.logger.error(f"Auto-Recovery fehlgeschlagen für {error_info.id}: {e}")
    
    async def _check_error_threshold(self):
        """Prüft ob Error-Threshold überschritten wurde"""
        total_errors = sum(self.error_counters.values())
        
        if total_errors >= self.error_threshold:
            await self._trigger_error_alarm()
    
    async def _trigger_error_alarm(self):
        """Löst einen Error-Alarm aus"""
        if self.error_reporting_enabled:
            self.logger.critical(
                f"ERROR THRESHOLD ÜBERSCHRITTEN! "
                f"Gesamtfehler: {sum(self.error_counters.values())}"
            )
            
            # Hier könnte eine Benachrichtigung gesendet werden
            # z.B. Email, Telegram, etc.
    
    async def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """Registriert einen Error-Handler"""
        if category not in self.error_handlers:
            self.error_handlers[category] = []
        
        self.error_handlers[category].append(handler)
        self.logger.info(f"Error-Handler registriert für Kategorie: {category.value}")
    
    async def register_recovery_strategy(self, category: str, strategy: Callable):
        """Registriert eine Recovery-Strategie"""
        self.recovery_strategies[category] = strategy
        self.logger.info(f"Recovery-Strategie registriert für Kategorie: {category}")
    
    async def resolve_error(self, error_id: str, resolution_notes: str = None):
        """Markiert einen Fehler als gelöst"""
        if error_id in self.errors:
            error_info = self.errors[error_id]
            error_info.resolved = True
            error_info.resolution_time = datetime.now()
            error_info.resolution_notes = resolution_notes
            
            self.logger.info(f"Fehler gelöst: {error_id}")
    
    async def get_error_summary(self) -> Dict[str, Any]:
        """Gibt eine Zusammenfassung aller Fehler zurück"""
        total_errors = len(self.errors)
        resolved_errors = len([e for e in self.errors.values() if e.resolved])
        unresolved_errors = total_errors - resolved_errors
        
        # Fehler nach Kategorie
        errors_by_category = {}
        for error in self.errors.values():
            category = error.category.value
            if category not in errors_by_category:
                errors_by_category[category] = 0
            errors_by_category[category] += 1
        
        # Fehler nach Schweregrad
        errors_by_severity = {}
        for error in self.errors.values():
            severity = error.severity.value
            if severity not in errors_by_severity:
                errors_by_severity[severity] = 0
            errors_by_severity[severity] += 1
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_errors,
            'unresolved_errors': unresolved_errors,
            'errors_by_category': errors_by_category,
            'errors_by_severity': errors_by_severity,
            'error_counters': self.error_counters
        }
    
    async def get_recent_errors(self, hours: int = 24) -> List[ErrorInfo]:
        """Gibt kürzlich aufgetretene Fehler zurück"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        return [
            error for error in self.errors.values()
            if error.timestamp.timestamp() > cutoff_time
        ]
    
    async def _register_default_recovery_strategies(self):
        """Registriert Standard-Recovery-Strategien"""
        
        # Netzwerk-Recovery
        async def network_recovery(error_info: ErrorInfo):
            self.logger.info("Versuche Netzwerk-Wiederherstellung...")
            await asyncio.sleep(5)  # Warte 5 Sekunden
            # Hier könnte eine Netzwerk-Verbindung neu aufgebaut werden
        
        # Datenbank-Recovery
        async def database_recovery(error_info: ErrorInfo):
            self.logger.info("Versuche Datenbank-Wiederherstellung...")
            await asyncio.sleep(2)
            # Hier könnte eine Datenbank-Verbindung neu aufgebaut werden
        
        # API-Recovery
        async def api_recovery(error_info: ErrorInfo):
            self.logger.info("Versuche API-Wiederherstellung...")
            await asyncio.sleep(3)
            # Hier könnten API-Clients neu initialisiert werden
        
        self.recovery_strategies['network'] = network_recovery
        self.recovery_strategies['database'] = database_recovery
        self.recovery_strategies['api'] = api_recovery
    
    async def _register_default_error_handlers(self):
        """Registriert Standard-Error-Handler"""
        
        # Kritische Fehler-Handler
        async def critical_error_handler(error_info: ErrorInfo):
            if error_info.severity == ErrorSeverity.CRITICAL:
                self.logger.critical("KRITISCHER FEHLER ERKANNT - System könnte instabil sein!")
                # Hier könnte eine sofortige Benachrichtigung gesendet werden
        
        # System-Fehler-Handler
        async def system_error_handler(error_info: ErrorInfo):
            if error_info.category == ErrorCategory.SYSTEM:
                self.logger.error(f"System-Fehler in {error_info.source}: {error_info.message}")
        
        await self.register_error_handler(ErrorCategory.SYSTEM, critical_error_handler)
        await self.register_error_handler(ErrorCategory.SYSTEM, system_error_handler)
    
    async def _save_unresolved_errors(self):
        """Speichert ungelöste Fehler"""
        unresolved_errors = [e for e in self.errors.values() if not e.resolved]
        
        if unresolved_errors:
            # Hier könnten ungelöste Fehler in eine Datei oder Datenbank gespeichert werden
            self.logger.info(f"{len(unresolved_errors)} ungelöste Fehler gespeichert")
    
    async def clear_old_errors(self, days: int = 30):
        """Bereinigt alte Fehler"""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        errors_to_remove = [
            error_id for error_id, error_info in self.errors.items()
            if error_info.timestamp.timestamp() < cutoff_time
        ]
        
        for error_id in errors_to_remove:
            del self.errors[error_id]
        
        if errors_to_remove:
            self.logger.info(f"{len(errors_to_remove)} alte Fehler bereinigt")