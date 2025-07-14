"""
Liyana NEXUS v1 - State Manager
Verwaltet Systemzustände und Persistierung
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from config import config, AgentState

class StateManager:
    """Verwaltet Systemzustände und Persistierung"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db_path = config.system.db_path
        self.connection: Optional[sqlite3.Connection] = None
        
        # In-Memory Cache
        self.state_cache: Dict[str, Any] = {}
        self._cache_lock = asyncio.Lock()
        
        # Event-Handler für Zustandsänderungen
        self.state_change_handlers: List[callable] = []
    
    async def initialize(self):
        """Initialisiert den State Manager"""
        self.logger.info("State Manager wird initialisiert...")
        
        # Erstelle Datenbank
        await self._create_database()
        
        # Lade initiale Zustände
        await self._load_initial_states()
        
        self.logger.info("State Manager initialisiert")
    
    async def shutdown(self):
        """Beendet den State Manager"""
        self.logger.info("State Manager wird beendet...")
        
        # Speichere alle Zustände
        await self._save_all_states()
        
        # Schließe Datenbankverbindung
        if self.connection:
            self.connection.close()
        
        self.logger.info("State Manager beendet")
    
    async def _create_database(self):
        """Erstellt die Datenbank und Tabellen"""
        self.connection = sqlite3.connect(self.db_path)
        
        # Erstelle Tabellen
        cursor = self.connection.cursor()
        
        # System-Zustände
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_states (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Agent-Zustände
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                agent_name TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                metadata TEXT,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_count INTEGER DEFAULT 0
            )
        """)
        
        # Task-Zustände
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_states (
                task_id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                data TEXT,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Metriken
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Konfiguration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuration (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
    
    async def _load_initial_states(self):
        """Lädt initiale Zustände aus der Datenbank"""
        cursor = self.connection.cursor()
        
        # Lade System-Zustände
        cursor.execute("SELECT key, value FROM system_states")
        for key, value in cursor.fetchall():
            try:
                self.state_cache[f"system:{key}"] = json.loads(value)
            except json.JSONDecodeError:
                self.state_cache[f"system:{key}"] = value
        
        # Lade Agent-Zustände
        cursor.execute("SELECT agent_name, state, metadata FROM agent_states")
        for agent_name, state, metadata in cursor.fetchall():
            try:
                self.state_cache[f"agent:{agent_name}"] = {
                    'state': state,
                    'metadata': json.loads(metadata) if metadata else {}
                }
            except json.JSONDecodeError:
                self.state_cache[f"agent:{agent_name}"] = {
                    'state': state,
                    'metadata': {}
                }
    
    async def set_system_state(self, key: str, value: Any):
        """Setzt einen System-Zustand"""
        async with self._cache_lock:
            self.state_cache[f"system:{key}"] = value
            
            # Persistiere in Datenbank
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO system_states (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now()))
            self.connection.commit()
            
            # Benachrichtige Handler
            await self._notify_state_change('system', key, value)
    
    async def get_system_state(self, key: str, default: Any = None) -> Any:
        """Gibt einen System-Zustand zurück"""
        async with self._cache_lock:
            return self.state_cache.get(f"system:{key}", default)
    
    async def set_agent_state(self, agent_name: str, state: AgentState, metadata: Dict[str, Any] = None):
        """Setzt den Zustand eines Agenten"""
        async with self._cache_lock:
            agent_state = {
                'state': state.value,
                'metadata': metadata or {},
                'last_activity': datetime.now().isoformat()
            }
            
            self.state_cache[f"agent:{agent_name}"] = agent_state
            
            # Persistiere in Datenbank
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_states 
                (agent_name, state, metadata, last_activity)
                VALUES (?, ?, ?, ?)
            """, (agent_name, state.value, json.dumps(metadata or {}), datetime.now()))
            self.connection.commit()
            
            # Benachrichtige Handler
            await self._notify_state_change('agent', agent_name, agent_state)
    
    async def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Gibt den Zustand eines Agenten zurück"""
        async with self._cache_lock:
            return self.state_cache.get(f"agent:{agent_name}")
    
    async def update_agent_metadata(self, agent_name: str, metadata: Dict[str, Any]):
        """Aktualisiert die Metadaten eines Agenten"""
        current_state = await self.get_agent_state(agent_name)
        if current_state:
            current_state['metadata'].update(metadata)
            await self.set_agent_state(
                agent_name, 
                AgentState(current_state['state']), 
                current_state['metadata']
            )
    
    async def increment_agent_error_count(self, agent_name: str):
        """Erhöht den Fehlerzähler eines Agenten"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE agent_states 
            SET error_count = error_count + 1 
            WHERE agent_name = ?
        """, (agent_name,))
        self.connection.commit()
    
    async def save_task_state(self, task_id: str, task_type: str, status: str, 
                             data: Dict[str, Any] = None, result: Dict[str, Any] = None):
        """Speichert den Zustand einer Aufgabe"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO task_states 
            (task_id, task_type, status, data, result, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, 
            task_type, 
            status, 
            json.dumps(data) if data else None,
            json.dumps(result) if result else None,
            datetime.now(),
            datetime.now() if status in ['completed', 'failed', 'cancelled'] else None
        ))
        self.connection.commit()
    
    async def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Gibt den Zustand einer Aufgabe zurück"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT task_type, status, data, result, created_at, completed_at
            FROM task_states WHERE task_id = ?
        """, (task_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'task_type': row[0],
                'status': row[1],
                'data': json.loads(row[2]) if row[2] else None,
                'result': json.loads(row[3]) if row[3] else None,
                'created_at': row[4],
                'completed_at': row[5]
            }
        return None
    
    async def save_metric(self, metric_name: str, metric_value: float):
        """Speichert eine Metrik"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO metrics (metric_name, metric_value, timestamp)
            VALUES (?, ?, ?)
        """, (metric_name, metric_value, datetime.now()))
        self.connection.commit()
    
    async def get_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Gibt Metriken für einen Zeitraum zurück"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT metric_value, timestamp
            FROM metrics 
            WHERE metric_name = ? AND timestamp >= datetime('now', '-{} hours')
            ORDER BY timestamp DESC
        """.format(hours), (metric_name,))
        
        return [
            {'value': row[0], 'timestamp': row[1]}
            for row in cursor.fetchall()
        ]
    
    async def set_configuration(self, key: str, value: Any, description: str = None):
        """Setzt eine Konfiguration"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO configuration (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
        """, (key, json.dumps(value), description, datetime.now()))
        self.connection.commit()
    
    async def get_configuration(self, key: str, default: Any = None) -> Any:
        """Gibt eine Konfiguration zurück"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT value FROM configuration WHERE key = ?", (key,))
        row = cursor.fetchone()
        
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
        return default
    
    async def add_state_change_handler(self, handler: callable):
        """Fügt einen Handler für Zustandsänderungen hinzu"""
        self.state_change_handlers.append(handler)
    
    async def _notify_state_change(self, state_type: str, key: str, value: Any):
        """Benachrichtigt Handler über Zustandsänderungen"""
        for handler in self.state_change_handlers:
            try:
                await handler(state_type, key, value)
            except Exception as e:
                self.logger.error(f"Fehler im State Change Handler: {e}")
    
    async def _save_all_states(self):
        """Speichert alle Zustände in die Datenbank"""
        # System-Zustände sind bereits gespeichert
        # Agent-Zustände sind bereits gespeichert
        self.logger.info("Alle Zustände gespeichert")
    
    async def get_all_states(self) -> Dict[str, Any]:
        """Gibt alle aktuellen Zustände zurück"""
        async with self._cache_lock:
            return {
                'system_states': {
                    k.replace('system:', ''): v 
                    for k, v in self.state_cache.items() 
                    if k.startswith('system:')
                },
                'agent_states': {
                    k.replace('agent:', ''): v 
                    for k, v in self.state_cache.items() 
                    if k.startswith('agent:')
                }
            }
    
    async def cleanup_old_data(self, days: int = 30):
        """Bereinigt alte Daten"""
        cursor = self.connection.cursor()
        
        # Lösche alte Metriken
        cursor.execute("""
            DELETE FROM metrics 
            WHERE timestamp < datetime('now', '-{} days')
        """.format(days))
        
        # Lösche alte Task-Zustände
        cursor.execute("""
            DELETE FROM task_states 
            WHERE created_at < datetime('now', '-{} days')
        """.format(days))
        
        deleted_metrics = cursor.rowcount
        self.connection.commit()
        
        self.logger.info(f"Alte Daten bereinigt: {deleted_metrics} Einträge gelöscht")