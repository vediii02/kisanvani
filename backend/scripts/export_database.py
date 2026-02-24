import asyncio
from sqlalchemy import text
from db.base import AsyncSessionLocal
from datetime import datetime

async def export_database():
    """Export complete MySQL database structure and data"""
    
    output = []
    output.append("-- =====================================================")
    output.append("-- Kisan Vani AI - MySQL Database Dump")
    output.append(f"-- Generated: {datetime.now().isoformat()}")
    output.append("-- Database: kisanvani_db")
    output.append("-- =====================================================\n")
    
    output.append("-- Drop and create database")
    output.append("DROP DATABASE IF EXISTS kisanvani_db;")
    output.append("CREATE DATABASE kisanvani_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    output.append("USE kisanvani_db;\n")
    
    async with AsyncSessionLocal() as db:
        # Get all tables
        result = await db.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"📊 Exporting {len(tables)} tables...")
        
        for table in tables:
            print(f"  ✓ Exporting table: {table}")
            
            # Get CREATE TABLE statement
            result = await db.execute(text(f"SHOW CREATE TABLE {table}"))
            create_table = result.fetchone()[1]
            
            output.append(f"-- Table structure for {table}")
            output.append(f"DROP TABLE IF EXISTS `{table}`;")
            output.append(create_table + ";")
            output.append("")
            
            # Get table data
            result = await db.execute(text(f"SELECT * FROM {table}"))
            rows = result.fetchall()
            
            if rows:
                output.append(f"-- Data for table {table}")
                output.append(f"INSERT INTO `{table}` VALUES")
                
                # Get column info
                result = await db.execute(text(f"DESCRIBE {table}"))
                columns = result.fetchall()
                
                values = []
                for row in rows:
                    row_values = []
                    for i, val in enumerate(row):
                        if val is None:
                            row_values.append("NULL")
                        elif isinstance(val, (int, float)):
                            row_values.append(str(val))
                        elif isinstance(val, datetime):
                            row_values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                        else:
                            # Escape single quotes
                            escaped = str(val).replace("'", "''").replace("\\", "\\\\")
                            row_values.append(f"'{escaped}'")
                    
                    values.append(f"({','.join(row_values)})")
                
                output.append(',\n'.join(values) + ";")
                output.append(f"-- {len(rows)} rows inserted\n")
            else:
                output.append(f"-- No data for table {table}\n")
    
    # Write to file
    sql_dump = '\n'.join(output)
    
    with open('/app/kisanvani_db_dump.sql', 'w', encoding='utf-8') as f:
        f.write(sql_dump)
    
    print(f"\n✅ Database dump created: /app/kisanvani_db_dump.sql")
    print(f"📦 Size: {len(sql_dump)} bytes")
    print(f"📋 Tables exported: {len(tables)}")
    
    return sql_dump

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/app/backend')
    asyncio.run(export_database())
