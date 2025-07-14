"""
Liyana NEXUS v1 - Memory Vault
Speicherstruktur mit JSON/SQLite für Kunden, Anfragen, Stimme
"""

import asyncio
import logging
import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from config import config, AgentState

class MemoryVault:
    """Speicherstruktur für NEXUS"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.state = AgentState.WAITING
        self.db_path = config.system.db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._running = False
    
    async def start(self):
        """Startet den Memory Vault"""
        self.logger.info("Memory Vault gestartet")
        self._running = True
        self.state = AgentState.EXECUTING
        await self._initialize_database()
    
    async def stop(self):
        """Stoppt den Memory Vault"""
        self.logger.info("Memory Vault gestoppt")
        self._running = False
        self.state = AgentState.PAUSED
        if self.connection:
            self.connection.close()
    
    async def _initialize_database(self):
        """Initialisiert die Datenbank"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        # Erstelle Tabellen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_contact TIMESTAMP,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                request_type TEXT,
                content TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                file_path TEXT,
                duration REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            )
        """)
        
        self.connection.commit()
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verarbeitet eine Memory Vault Task"""
        task_type = task_data.get('type', 'store_data')
        
        if task_type == 'store_data':
            return await self._store_data(task_data)
        elif task_type == 'retrieve_data':
            return await self._retrieve_data(task_data)
        elif task_type == 'update_data':
            return await self._update_data(task_data)
        else:
            return {'error': f'Unbekannter Task-Typ: {task_type}', 'success': False}
    
    async def _store_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Speichert Daten"""
        data_type = task_data.get('data_type')
        data = task_data.get('data', {})
        
        if data_type == 'customer':
            return await self._store_customer(data)
        elif data_type == 'request':
            return await self._store_request(data)
        elif data_type == 'voice_sample':
            return await self._store_voice_sample(data)
        else:
            return {'error': f'Unbekannter Datentyp: {data_type}', 'success': False}
    
    async def _store_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Speichert Kundendaten"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO customers (email, name, phone, last_contact, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get('email'),
            data.get('name'),
            data.get('phone'),
            datetime.now(),
            json.dumps(data.get('metadata', {}))
        ))
        self.connection.commit()
        
        return {
            'success': True,
            'customer_id': cursor.lastrowid,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _store_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Speichert Anfrage"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO requests (customer_id, request_type, content, status)
            VALUES (?, ?, ?, ?)
        """, (
            data.get('customer_id'),
            data.get('request_type'),
            data.get('content'),
            data.get('status', 'pending')
        ))
        self.connection.commit()
        
        return {
            'success': True,
            'request_id': cursor.lastrowid,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _store_voice_sample(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Speichert Stimmprobe"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO voice_samples (customer_id, file_path, duration, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            data.get('customer_id'),
            data.get('file_path'),
            data.get('duration'),
            json.dumps(data.get('metadata', {}))
        ))
        self.connection.commit()
        
        return {
            'success': True,
            'voice_sample_id': cursor.lastrowid,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _retrieve_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ruft Daten ab"""
        data_type = task_data.get('data_type')
        query_params = task_data.get('query_params', {})
        
        if data_type == 'customer':
            return await self._retrieve_customer(query_params)
        elif data_type == 'request':
            return await self._retrieve_request(query_params)
        elif data_type == 'voice_sample':
            return await self._retrieve_voice_sample(query_params)
        else:
            return {'error': f'Unbekannter Datentyp: {data_type}', 'success': False}
    
    async def _retrieve_customer(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Ruft Kundendaten ab"""
        cursor = self.connection.cursor()
        
        if 'email' in query_params:
            cursor.execute("SELECT * FROM customers WHERE email = ?", (query_params['email'],))
        elif 'id' in query_params:
            cursor.execute("SELECT * FROM customers WHERE id = ?", (query_params['id'],))
        else:
            cursor.execute("SELECT * FROM customers")
        
        rows = cursor.fetchall()
        customers = []
        
        for row in rows:
            customers.append({
                'id': row[0],
                'email': row[1],
                'name': row[2],
                'phone': row[3],
                'created_at': row[4],
                'last_contact': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            })
        
        return {
            'success': True,
            'customers': customers,
            'count': len(customers)
        }
    
    async def _retrieve_request(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Ruft Anfragen ab"""
        cursor = self.connection.cursor()
        
        if 'customer_id' in query_params:
            cursor.execute("SELECT * FROM requests WHERE customer_id = ?", (query_params['customer_id'],))
        elif 'status' in query_params:
            cursor.execute("SELECT * FROM requests WHERE status = ?", (query_params['status'],))
        else:
            cursor.execute("SELECT * FROM requests")
        
        rows = cursor.fetchall()
        requests = []
        
        for row in rows:
            requests.append({
                'id': row[0],
                'customer_id': row[1],
                'request_type': row[2],
                'content': row[3],
                'status': row[4],
                'created_at': row[5],
                'resolved_at': row[6]
            })
        
        return {
            'success': True,
            'requests': requests,
            'count': len(requests)
        }
    
    async def _retrieve_voice_sample(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Ruft Stimmproben ab"""
        cursor = self.connection.cursor()
        
        if 'customer_id' in query_params:
            cursor.execute("SELECT * FROM voice_samples WHERE customer_id = ?", (query_params['customer_id'],))
        else:
            cursor.execute("SELECT * FROM voice_samples")
        
        rows = cursor.fetchall()
        voice_samples = []
        
        for row in rows:
            voice_samples.append({
                'id': row[0],
                'customer_id': row[1],
                'file_path': row[2],
                'duration': row[3],
                'created_at': row[4],
                'metadata': json.loads(row[5]) if row[5] else {}
            })
        
        return {
            'success': True,
            'voice_samples': voice_samples,
            'count': len(voice_samples)
        }
    
    async def _update_data(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert Daten"""
        data_type = task_data.get('data_type')
        data = task_data.get('data', {})
        
        if data_type == 'customer':
            return await self._update_customer(data)
        elif data_type == 'request':
            return await self._update_request(data)
        else:
            return {'error': f'Unbekannter Datentyp: {data_type}', 'success': False}
    
    async def _update_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert Kundendaten"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE customers 
            SET name = ?, phone = ?, last_contact = ?, metadata = ?
            WHERE id = ?
        """, (
            data.get('name'),
            data.get('phone'),
            datetime.now(),
            json.dumps(data.get('metadata', {})),
            data.get('id')
        ))
        self.connection.commit()
        
        return {
            'success': True,
            'rows_affected': cursor.rowcount,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _update_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert Anfrage"""
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE requests 
            SET status = ?, resolved_at = ?
            WHERE id = ?
        """, (
            data.get('status'),
            datetime.now() if data.get('status') == 'resolved' else None,
            data.get('id')
        ))
        self.connection.commit()
        
        return {
            'success': True,
            'rows_affected': cursor.rowcount,
            'timestamp': datetime.now().isoformat()
        }