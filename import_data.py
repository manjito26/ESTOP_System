#!/usr/bin/env python3
"""
ESTOP System Data Import Script
Analyzes Excel file and imports machine/device data to SQL Server
"""
import pandas as pd
import sys
import os
import logging
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.database import ESTOPDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_excel_file(file_path):
    """Analyze the Excel file structure"""
    logger.info(f"Analyzing Excel file: {file_path}")
    
    try:
        # Read the Excel file to get all worksheet names
        xl_file = pd.ExcelFile(file_path)
        worksheets = xl_file.sheet_names
        
        logger.info(f"Found {len(worksheets)} worksheets:")
        for i, sheet in enumerate(worksheets):
            logger.info(f"  {i+1}. {sheet}")
        
        # Analyze each worksheet
        worksheet_data = {}
        for sheet_name in worksheets:
            logger.info(f"\nAnalyzing worksheet: {sheet_name}")
            
            try:
                # Read the worksheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                logger.info(f"  Shape: {df.shape} (rows x columns)")
                logger.info(f"  Columns: {list(df.columns)}")
                
                # Show first few rows
                logger.info("  First few rows:")
                logger.info(df.head().to_string())
                
                # Store the data
                worksheet_data[sheet_name] = df
                
            except Exception as e:
                logger.error(f"Error reading worksheet {sheet_name}: {e}")
                
        return worksheet_data
        
    except Exception as e:
        logger.error(f"Error analyzing Excel file: {e}")
        return {}

def create_database_tables():
    """Create database tables"""
    logger.info("Creating database tables...")
    
    try:
        db = ESTOPDatabase()
        db.create_tables()
        logger.info("Database tables created successfully")
        return db
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def import_machine_data(db, machine_name, device_data):
    """Import machine and device data"""
    logger.info(f"Importing data for machine: {machine_name}")
    
    try:
        # Insert machine if it doesn't exist
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM machines WHERE machine_name = %s)
            INSERT INTO machines (machine_name, location) VALUES (%s, %s)
        """, (machine_name, machine_name, f"Location for {machine_name}"))
        
        # Get machine ID
        cursor.execute("SELECT machine_id FROM machines WHERE machine_name = %s", (machine_name,))
        result = cursor.fetchone()
        if not result:
            raise Exception(f"Failed to get machine_id for {machine_name}")
        
        machine_id = result[0]
        logger.info(f"Machine ID: {machine_id}")
        
        # Import devices
        device_count = 0
        for index, row in device_data.iterrows():
            # Try to identify device name and type columns
            device_name = None
            device_type = None
            
            # Common column names to look for
            for col in device_data.columns:
                col_lower = str(col).lower()
                
                # Look for device name
                if device_name is None and any(keyword in col_lower for keyword in ['name', 'device', 'description', 'item']):
                    device_name = str(row[col]) if pd.notna(row[col]) else None
                
                # Look for device type
                if device_type is None and any(keyword in col_lower for keyword in ['type', 'category', 'class']):
                    device_type = str(row[col]) if pd.notna(row[col]) else None
            
            # If no specific columns found, use the first non-empty column as device name
            if device_name is None:
                for col in device_data.columns:
                    if pd.notna(row[col]) and str(row[col]).strip():
                        device_name = str(row[col])
                        break
            
            # Set default type if not found
            if device_type is None:
                device_type = "Safety Device"
            
            # Skip empty rows
            if device_name is None or not str(device_name).strip():
                continue
            
            device_name = str(device_name).strip()
            device_type = str(device_type).strip()
            
            # Insert device
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM safety_devices WHERE device_name = %s AND machine_id = %s)
                INSERT INTO safety_devices (machine_id, device_name, device_type) 
                VALUES (%s, %s, %s)
            """, (device_name, machine_id, machine_id, device_name, device_type))
            
            device_count += 1
            logger.info(f"  Added device: {device_name} ({device_type})")
        
        conn.close()
        logger.info(f"Imported {device_count} devices for machine {machine_name}")
        
    except Exception as e:
        logger.error(f"Error importing data for machine {machine_name}: {e}")
        raise

def main():
    """Main import function"""
    excel_file = "/home/eraser/Downloads/data.xlsx"
    
    logger.info("="*60)
    logger.info("ESTOP System Data Import Starting...")
    logger.info(f"Excel file: {excel_file}")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # Check if file exists
    if not os.path.exists(excel_file):
        logger.error(f"Excel file not found: {excel_file}")
        return False
    
    try:
        # 1. Analyze Excel file
        worksheet_data = analyze_excel_file(excel_file)
        
        if not worksheet_data:
            logger.error("No data found in Excel file")
            return False
        
        # 2. Create database tables
        db = create_database_tables()
        
        # 3. Import data for each worksheet (machine)
        for machine_name, device_data in worksheet_data.items():
            try:
                import_machine_data(db, machine_name, device_data)
            except Exception as e:
                logger.error(f"Failed to import data for {machine_name}: {e}")
                continue
        
        logger.info("="*60)
        logger.info("Data import completed successfully!")
        logger.info(f"Imported {len(worksheet_data)} machines")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)