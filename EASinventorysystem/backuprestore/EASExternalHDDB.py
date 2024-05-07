import os
import subprocess
from datetime import datetime

# Connection parameters
host = 'localhost'
database = 'eas_inventory'
username = 'root'
password = 'eas'

# Backup directory on external hard drive
backup_dir = 'D:/backup'
os.makedirs(backup_dir, exist_ok=True)

# Backup file name
backup_file = 'mydatabase_backup_' + str(datetime.now().strftime('%Y%m%d_%H%M%S')) + '.sql'

# Full path to the backup file
backup_file_path = os.path.join(backup_dir, backup_file)

# Backup command
backup_command = f'mysqldump -u {username} -p{password} -h {host} {database} > {backup_file_path}'

# Execute the backup command
subprocess.run(backup_command, shell=True)