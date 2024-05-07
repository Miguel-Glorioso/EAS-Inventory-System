import os
import glob
import mysql.connector

# Connection parameters
host = 'localhost'
database = 'eas_inventory'  # replace with your database name
username = 'root'  # replace with your username
password = 'eas'  # replace with your password

# Backup directory
backup_dir = 'C:/backup'  # replace with your backup directory

# Find the most recent backup file
backup_files = glob.glob(os.path.join(backup_dir, '*.sql'))
if not backup_files:
    print("No backup files found in the specified directory.")
    exit(1)

backup_file = max(backup_files, key=os.path.getctime)

# Read SQL file contents
with open(backup_file, 'r') as f:
    sql_commands = f.read()

# Split SQL commands by delimiter (typically ';')
commands = sql_commands.split(';')

# Create a connection object
conn = mysql.connector.connect(host=host, user=username, password=password)

# Create a connection object
conn = mysql.connector.connect(host=host, user=username, password=password, database=database)
cursor = conn.cursor()

for command in commands:
    try:
        cursor.execute(command)
    except mysql.connector.Error as e:
        print(f"Error executing SQL command: {e}")

# Commit changes
conn.commit()
print("Database restored successfully.")

# Close cursor and connection
cursor.close()
conn.close()
