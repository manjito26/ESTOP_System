"""
Database model for ESTOP System
Handles SQL Server connection and database operations
"""
import pytds
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ESTOPDatabase:
    def __init__(self):
        self.connection_params = {
            'dsn': '192.168.10.69',
            'port': 1433,
            'database': 'EFRS',
            'user': 'SA',
            'password': 'GreenCandyOneBang',
            'autocommit': True,
            'timeout': 10
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = pytds.connect(**self.connection_params)
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Create AUTH database
            cursor.execute("IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'AUTH') CREATE DATABASE AUTH")
            
            # Create machines table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='machines' AND xtype='U')
                CREATE TABLE machines (
                    machine_id INT IDENTITY(1,1) PRIMARY KEY,
                    machine_name NVARCHAR(100) NOT NULL,
                    location NVARCHAR(100),
                    created_date DATETIME DEFAULT GETDATE()
                )
            """)
            
            # Create safety_devices table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='safety_devices' AND xtype='U')
                CREATE TABLE safety_devices (
                    device_id INT IDENTITY(1,1) PRIMARY KEY,
                    machine_id INT NOT NULL,
                    device_name NVARCHAR(100) NOT NULL,
                    device_type NVARCHAR(50),
                    created_date DATETIME DEFAULT GETDATE(),
                    FOREIGN KEY (machine_id) REFERENCES machines(machine_id)
                )
            """)
            
            # Create test_records table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='test_records' AND xtype='U')
                CREATE TABLE test_records (
                    record_id INT IDENTITY(1,1) PRIMARY KEY,
                    machine_id INT NOT NULL,
                    device_id INT NOT NULL,
                    username NVARCHAR(50) NOT NULL,
                    test_result NVARCHAR(10) NOT NULL,
                    test_date DATETIME DEFAULT GETDATE(),
                    notes NVARCHAR(500),
                    FOREIGN KEY (machine_id) REFERENCES machines(machine_id),
                    FOREIGN KEY (device_id) REFERENCES safety_devices(device_id)
                )
            """)
            
            # Create user tables for each user
            for username in ['ckull', 'mhiggins', 'jpetereit', 'smyers']:
                cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{username}_auth' AND xtype='U')
                    CREATE TABLE {username}_auth (
                        auth_id INT IDENTITY(1,1) PRIMARY KEY,
                        login_time DATETIME DEFAULT GETDATE(),
                        logout_time DATETIME,
                        session_active BIT DEFAULT 1
                    )
                """)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            conn.close()
    
    def get_machines(self) -> List[Dict]:
        """Get all machines"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT machine_id, machine_name, location FROM machines ORDER BY machine_name")
            rows = cursor.fetchall()
            return [{'machine_id': row[0], 'machine_name': row[1], 'location': row[2]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting machines: {e}")
            return []
        finally:
            conn.close()
    
    def get_safety_devices(self, machine_id: int) -> List[Dict]:
        """Get safety devices for a specific machine"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT device_id, device_name, device_type 
                FROM safety_devices 
                WHERE machine_id = %s 
                ORDER BY device_name
            """, (machine_id,))
            rows = cursor.fetchall()
            return [{'device_id': row[0], 'device_name': row[1], 'device_type': row[2]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting safety devices: {e}")
            return []
        finally:
            conn.close()
    
    def record_test(self, machine_id: int, device_id: int, username: str, test_result: str, notes: str = "") -> bool:
        """Record a test result"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_records (machine_id, device_id, username, test_result, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (machine_id, device_id, username, test_result, notes))
            logger.info(f"Test recorded: Machine {machine_id}, Device {device_id}, Result {test_result} by {username}")
            return True
        except Exception as e:
            logger.error(f"Error recording test: {e}")
            return False
        finally:
            conn.close()
    
    def get_device_tests(self, search_query: str = "", machine_filter: str = "", user_filter: str = "") -> List[Dict]:
        """Get all device tests with search and filter capabilities"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            base_query = """
                SELECT 
                    tr.record_id,
                    m.machine_name,
                    sd.device_name,
                    tr.username,
                    tr.test_result,
                    tr.test_date,
                    DATEDIFF(day, tr.test_date, GETDATE()) as days_since_test
                FROM test_records tr
                JOIN machines m ON tr.machine_id = m.machine_id
                JOIN safety_devices sd ON tr.device_id = sd.device_id
                WHERE 1=1
            """
            
            params = []
            
            if search_query:
                base_query += " AND (sd.device_name LIKE %s OR m.machine_name LIKE %s)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param])
            
            if machine_filter:
                base_query += " AND m.machine_name = %s"
                params.append(machine_filter)
            
            if user_filter:
                base_query += " AND tr.username = %s"
                params.append(user_filter)
            
            base_query += " ORDER BY tr.test_date DESC"
            
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'record_id': row[0],
                    'machine_name': row[1],
                    'device_name': row[2],
                    'username': row[3],
                    'test_result': row[4],
                    'test_date': row[5],
                    'days_since_test': row[6]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting device tests: {e}")
            return []
        finally:
            conn.close()
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Sample machines
            machines = [
                ("Machine A", "Production Floor"),
                ("Machine B", "Assembly Line 1"),
                ("Machine C", "Assembly Line 2"),
                ("CNC Mill", "Machine Shop"),
                ("Press 1", "Stamping Department")
            ]
            
            for machine in machines:
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM machines WHERE machine_name = %s)
                    INSERT INTO machines (machine_name, location) VALUES (%s, %s)
                """, (machine[0], machine[0], machine[1]))
            
            # Get machine IDs
            cursor.execute("SELECT machine_id, machine_name FROM machines")
            machine_ids = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Sample safety devices
            devices = [
                ("Machine A", "Emergency Stop Button 1", "E-Stop"),
                ("Machine A", "Emergency Stop Button 2", "E-Stop"),
                ("Machine A", "Safety Light Curtain", "Light Curtain"),
                ("Machine B", "Emergency Stop Button", "E-Stop"),
                ("Machine B", "Safety Mat", "Pressure Mat"),
                ("Machine C", "Emergency Stop Button 1", "E-Stop"),
                ("Machine C", "Emergency Stop Button 2", "E-Stop"),
                ("CNC Mill", "Emergency Stop Button", "E-Stop"),
                ("CNC Mill", "Door Interlock", "Interlock"),
                ("Press 1", "Two-Hand Control", "Control"),
                ("Press 1", "Emergency Stop Button", "E-Stop")
            ]
            
            for device in devices:
                machine_name, device_name, device_type = device
                if machine_name in machine_ids:
                    cursor.execute("""
                        IF NOT EXISTS (SELECT 1 FROM safety_devices WHERE device_name = %s AND machine_id = %s)
                        INSERT INTO safety_devices (machine_id, device_name, device_type) 
                        VALUES (%s, %s, %s)
                    """, (device_name, machine_ids[machine_name], machine_ids[machine_name], device_name, device_type))
            
            logger.info("Sample data inserted successfully")
            
        except Exception as e:
            logger.error(f"Error inserting sample data: {e}")
        finally:
            conn.close()