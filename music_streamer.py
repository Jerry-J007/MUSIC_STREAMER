import mysql.connector

try:
    # Attempt to connect to the database
    db = mysql.connector.connect(
        host="localhost",
        user="root",               
        password="Enter your password here",  
        database="music_streamer"
    )
    
    if db.is_connected():
        print("Successfully connected Python to MySQL.")
        db.close()

except mysql.connector.Error as err:
    print(f"Connection failed: {err}")