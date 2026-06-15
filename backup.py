import os
import time
import datetime
import subprocess
import threading

def run_backup_routine():
#infinite loop backsup the database
    backup_dir = "backups"
    
    #new backup folder
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    print("💾backups initialized.")

    while True:
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"music_streamer_{timestamp}.sql"
        filepath = os.path.join(backup_dir, filename)
        mysql_path=r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
        
        # command to backup MySQL
        #///////////////////////////////////////////////////////////////////////////////////////////
        command = f'"{mysql_path}" -u root -pEnter Your Password Here music_streamer > "{filepath}"'
        #///////////////////////////////////////////////////////////////////////////////////////////
        try:
           
            subprocess.run(command, shell=True, check=True)
            print(f"\n💾Database successfully saved to {filename}")
        except subprocess.CalledProcessError as e:
            print(f"\n❌Failed to backup database: {e}")
            
       
       
        time.sleep(24) #every 24 hours

def start_background_backups():
    
    # A 'daemon' thread means it will automatically die when the main server shuts down
    backup_thread = threading.Thread(target=run_backup_routine, daemon=True)
    backup_thread.start()

#test
if __name__ == "__main__":
    start_background_backups()
    # Keep the main thread alive just for this test
    while True:
        time.sleep(1)