"""
Liyana NEXUS v1 - Memory Vault
Zentraler Speicher für alle Agenten-Daten und System-Informationen
"""

import json
import sqlite3
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import config

@dataclass
class CustomerData:
    """Kundendaten-Struktur"""
    id: str
    email: str
    name: str
    preferences: Dict[str, Any]
    created_at: float
    phone: Optional[str] = None
    voice_profile: Optional[str] = None
    last_contact: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()
        if not self.preferences:
            self.preferences = {}

@dataclass
class RequestData:
    """Anfrage-Daten-Struktur"""
    id: str
    customer_id: str
    type: str  # email, call, chat, order
    content: str
    status: str  # pending, processing, completed, failed
    priority: int = 1  # 1-5, 5 = höchste Priorität
    created_at: float = None
    processed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

@dataclass
class VoiceProfile:
    """Stimmprofil-Daten"""
    id: str
    customer_id: str
    voice_file: str
    characteristics: Dict[str, Any]
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class MemoryVault:
    """
    Memory Vault - Zentraler Speicher für alle System-Daten
    Verwaltet Kunden, Anfragen, Stimmprofile und System-Informationen
    """
    
    def __init__(self):
        self.logger = logging.getLogger("nexus.memory")
        self.logger.info("🗄️ Initialisiere Memory Vault...")
        
        # Datenbank-Verbindung
        self.db_path = Path(config.DATABASE_CONFIG["sqlite"]["path"])
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Thread-Sicherheit
        self.lock = threading.RLock()
        
        # Cache für schnellen Zugriff
        self.cache = {}
        self.cache_ttl = config.PERFORMANCE_CONFIG["caching"]["ttl"]
        self.cache_timestamps = {}
        
        # Initialisiere Datenbank
        self._init_database()
        
        # Starte Cleanup-Timer
        self._start_cleanup_timer()
        
        self.logger.info("✅ Memory Vault initialisiert")
    
    def _init_database(self):
        """Initialisiert die SQLite-Datenbank mit allen Tabellen"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Kunden-Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT,
                        voice_profile TEXT,
                        preferences TEXT,
                        created_at REAL NOT NULL,
                        last_contact REAL
                    )
                """)
                
                # Anfragen-Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS requests (
                        id TEXT PRIMARY KEY,
                        customer_id TEXT NOT NULL,
                        type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        status TEXT NOT NULL,
                        priority INTEGER DEFAULT 1,
                        created_at REAL NOT NULL,
                        processed_at REAL,
                        result TEXT,
                        FOREIGN KEY (customer_id) REFERENCES customers (id)
                    )
                """)
                
                # Stimmprofile-Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS voice_profiles (
                        id TEXT PRIMARY KEY,
                        customer_id TEXT NOT NULL,
                        voice_file TEXT NOT NULL,
                        characteristics TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        FOREIGN KEY (customer_id) REFERENCES customers (id)
                    )
                """)
                
                # System-Logs-Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        level TEXT NOT NULL,
                        module TEXT NOT NULL,
                        message TEXT NOT NULL
                    )
                """)
                
                # Aufgaben-Ergebnisse-Tabelle
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_results (
                        id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        task_data TEXT NOT NULL,
                        result TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        timestamp REAL NOT NULL
                    )
                """)
                
                # Indizes für bessere Performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers (email)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_customer ON requests (customer_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON requests (status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_created ON requests (created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_voice_profiles_customer ON voice_profiles (customer_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs (timestamp)")
                
                conn.commit()
                
            self.logger.info("✅ Datenbank-Tabellen erstellt")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Initialisieren der Datenbank: {e}")
            raise
    
    def _start_cleanup_timer(self):
        """Startet den Cleanup-Timer für alte Daten"""
        def cleanup_old_data():
            try:
                with self.lock:
                    cutoff_time = time.time() - (30 * 24 * 3600)  # 30 Tage
                    
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        
                        # Lösche alte System-Logs
                        cursor.execute(
                            "DELETE FROM system_logs WHERE timestamp < ?",
                            (cutoff_time,)
                        )
                        
                        # Lösche alte Aufgaben-Ergebnisse
                        cursor.execute(
                            "DELETE FROM task_results WHERE timestamp < ?",
                            (cutoff_time,)
                        )
                        
                        conn.commit()
                    
                    # Cache leeren
                    self.cache.clear()
                    self.cache_timestamps.clear()
                    
            except Exception as e:
                self.logger.error(f"❌ Fehler beim Cleanup: {e}")
        
        # Führe Cleanup alle 24 Stunden aus
        timer = threading.Timer(24 * 3600, cleanup_old_data)
        timer.daemon = True
        timer.start()
    
    # Kunden-Management
    async def store_customer(self, customer: CustomerData) -> bool:
        """Speichert einen neuen Kunden"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO customers 
                        (id, email, name, phone, voice_profile, preferences, created_at, last_contact)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        customer.id,
                        customer.email,
                        customer.name,
                        customer.phone,
                        customer.voice_profile,
                        json.dumps(customer.preferences),
                        customer.created_at,
                        customer.last_contact
                    ))
                    conn.commit()
                
                # Cache aktualisieren
                cache_key = f"customer_{customer.id}"
                self.cache[cache_key] = customer
                self.cache_timestamps[cache_key] = time.time()
                
                self.logger.info(f"✅ Kunde gespeichert: {customer.email}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Speichern des Kunden: {e}")
            return False
    
    async def get_customer(self, customer_id: str) -> Optional[CustomerData]:
        """Lädt einen Kunden aus der Datenbank"""
        try:
            # Prüfe Cache
            cache_key = f"customer_{customer_id}"
            if cache_key in self.cache:
                if time.time() - self.cache_timestamps[cache_key] < self.cache_ttl:
                    return self.cache[cache_key]
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, email, name, phone, voice_profile, preferences, created_at, last_contact
                        FROM customers WHERE id = ?
                    """, (customer_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        customer = CustomerData(
                            id=row[0],
                            email=row[1],
                            name=row[2],
                            phone=row[3],
                            voice_profile=row[4],
                            preferences=json.loads(row[5]) if row[5] else {},
                            created_at=row[6],
                            last_contact=row[7]
                        )
                        
                        # Cache aktualisieren
                        self.cache[cache_key] = customer
                        self.cache_timestamps[cache_key] = time.time()
                        
                        return customer
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden des Kunden: {e}")
            return None
    
    async def get_customer_by_email(self, email: str) -> Optional[CustomerData]:
        """Lädt einen Kunden anhand der E-Mail-Adresse"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, email, name, phone, voice_profile, preferences, created_at, last_contact
                        FROM customers WHERE email = ?
                    """, (email,))
                    
                    row = cursor.fetchone()
                    if row:
                        return CustomerData(
                            id=row[0],
                            email=row[1],
                            name=row[2],
                            phone=row[3],
                            voice_profile=row[4],
                            preferences=json.loads(row[5]) if row[5] else {},
                            created_at=row[6],
                            last_contact=row[7]
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden des Kunden per E-Mail: {e}")
            return None
    
    # Anfragen-Management
    async def store_request(self, request: RequestData) -> bool:
        """Speichert eine neue Anfrage"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO requests 
                        (id, customer_id, type, content, status, priority, created_at, processed_at, result)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        request.id,
                        request.customer_id,
                        request.type,
                        request.content,
                        request.status,
                        request.priority,
                        request.created_at,
                        request.processed_at,
                        json.dumps(request.result) if request.result else None
                    ))
                    conn.commit()
                
                self.logger.info(f"✅ Anfrage gespeichert: {request.id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Speichern der Anfrage: {e}")
            return False
    
    async def get_pending_requests(self, limit: int = 10) -> List[RequestData]:
        """Lädt ausstehende Anfragen"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, customer_id, type, content, status, priority, created_at, processed_at, result
                        FROM requests 
                        WHERE status = 'pending' 
                        ORDER BY priority DESC, created_at ASC 
                        LIMIT ?
                    """, (limit,))
                    
                    requests = []
                    for row in cursor.fetchall():
                        request = RequestData(
                            id=row[0],
                            customer_id=row[1],
                            type=row[2],
                            content=row[3],
                            status=row[4],
                            priority=row[5],
                            created_at=row[6],
                            processed_at=row[7],
                            result=json.loads(row[8]) if row[8] else None
                        )
                        requests.append(request)
                    
                    return requests
                    
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden der ausstehenden Anfragen: {e}")
            return []
    
    async def update_request_status(self, request_id: str, status: str, result: Dict[str, Any] = None) -> bool:
        """Aktualisiert den Status einer Anfrage"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE requests 
                        SET status = ?, processed_at = ?, result = ?
                        WHERE id = ?
                    """, (
                        status,
                        time.time(),
                        json.dumps(result) if result else None,
                        request_id
                    ))
                    conn.commit()
                
                self.logger.info(f"✅ Anfrage-Status aktualisiert: {request_id} -> {status}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Aktualisieren der Anfrage: {e}")
            return False
    
    # Stimmprofile-Management
    async def store_voice_profile(self, profile: VoiceProfile) -> bool:
        """Speichert ein Stimmprofil"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO voice_profiles 
                        (id, customer_id, voice_file, characteristics, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        profile.id,
                        profile.customer_id,
                        profile.voice_file,
                        json.dumps(profile.characteristics),
                        profile.created_at
                    ))
                    conn.commit()
                
                self.logger.info(f"✅ Stimmprofil gespeichert: {profile.id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Speichern des Stimmprofils: {e}")
            return False
    
    async def get_voice_profile(self, customer_id: str) -> Optional[VoiceProfile]:
        """Lädt das Stimmprofil eines Kunden"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, customer_id, voice_file, characteristics, created_at
                        FROM voice_profiles WHERE customer_id = ?
                    """, (customer_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        return VoiceProfile(
                            id=row[0],
                            customer_id=row[1],
                            voice_file=row[2],
                            characteristics=json.loads(row[3]),
                            created_at=row[4]
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden des Stimmprofils: {e}")
            return None
    
    # System-Logs
    async def log_system_event(self, level: str, module: str, message: str):
        """Loggt ein System-Ereignis"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO system_logs (timestamp, level, module, message)
                        VALUES (?, ?, ?, ?)
                    """, (time.time(), level, module, message))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Loggen des System-Ereignisses: {e}")
    
    # Aufgaben-Ergebnisse
    async def store_task_result(self, task_type: str, task_data: Dict[str, Any], result: Dict[str, Any]) -> bool:
        """Speichert das Ergebnis einer Aufgabe"""
        try:
            task_id = f"{task_type}_{int(time.time() * 1000)}"
            
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO task_results (id, task_type, task_data, result, success, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        task_id,
                        task_type,
                        json.dumps(task_data),
                        json.dumps(result),
                        result.get('success', False),
                        time.time()
                    ))
                    conn.commit()
                
                self.logger.info(f"✅ Aufgaben-Ergebnis gespeichert: {task_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Speichern des Aufgaben-Ergebnisses: {e}")
            return False
    
    # Statistiken
    def get_stats(self) -> Dict[str, Any]:
        """Gibt System-Statistiken zurück"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Kunden-Statistiken
                    cursor.execute("SELECT COUNT(*) FROM customers")
                    total_customers = cursor.fetchone()[0]
                    
                    # Anfragen-Statistiken
                    cursor.execute("SELECT COUNT(*) FROM requests")
                    total_requests = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'")
                    pending_requests = cursor.fetchone()[0]
                    
                    # Stimmprofile-Statistiken
                    cursor.execute("SELECT COUNT(*) FROM voice_profiles")
                    total_voice_profiles = cursor.fetchone()[0]
                    
                    # Cache-Statistiken
                    cache_size = len(self.cache)
                    
                    return {
                        "customers": {
                            "total": total_customers
                        },
                        "requests": {
                            "total": total_requests,
                            "pending": pending_requests
                        },
                        "voice_profiles": {
                            "total": total_voice_profiles
                        },
                        "cache": {
                            "size": cache_size,
                            "ttl": self.cache_ttl
                        },
                        "database": {
                            "path": str(self.db_path),
                            "size_mb": self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                        }
                    }
                    
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Laden der Statistiken: {e}")
            return {}
    
    # Backup-Funktionen
    async def create_backup(self) -> str:
        """Erstellt ein Backup der Datenbank"""
        try:
            backup_path = self.db_path.parent / f"nexus_backup_{int(time.time())}.db"
            
            with sqlite3.connect(self.db_path) as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)
            
            self.logger.info(f"✅ Backup erstellt: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Erstellen des Backups: {e}")
            return ""
    
    async def cleanup_old_backups(self):
        """Löscht alte Backups"""
        try:
            backup_dir = self.db_path.parent
            backup_files = list(backup_dir.glob("nexus_backup_*.db"))
            
            # Sortiere nach Erstellungsdatum
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Behalte nur die neuesten Backups
            max_backups = config.DATABASE_CONFIG["sqlite"]["max_backups"]
            for backup_file in backup_files[max_backups:]:
                backup_file.unlink()
                self.logger.info(f"🗑️ Altes Backup gelöscht: {backup_file}")
                
        except Exception as e:
            self.logger.error(f"❌ Fehler beim Cleanup der Backups: {e}")