import mysql.connector
import hashlib
import datetime

#function to connect to DB 
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="PASSWORD GOES HERE", 
        database="music_streamer"
    )



#Registration function
def register_user(username, password):
    db = get_connection()
    cursor= db.cursor()
    
    hashed_pass = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # We use %s as placeholders to prevent SQL Injection attacks,thus we don't use f strings
        query = "INSERT INTO Users (username, password_hashed) VALUES (%s, %s)"
        values = (username, hashed_pass)
        
        cursor.execute(query, values)
        db.commit() # we should always commit after a update delete add command
        print(f"✅ User '{username}' registered successfully!")
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Error registering user,Error type : {err}")
        if str((err))[:4]=="1062":
            print("User already exists")
        return False
        
    finally:
        cursor.close()
        db.close()

# login Function 
def login_user(username, password):
    db = get_connection()
    cursor= db.cursor()
    
    input_hashed =hashlib.sha256(password.encode()).hexdigest()
    if not db:
        return False, None
    
    try:
        query = "SELECT user_id, password_hashed FROM Users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone() # Fetches the first matching row
        
        if result is None:
            print("❌ Username not found.")
            return False,None
            
        stored_user_id = result[0]
        stored_hash = result[1]#result will be a tuple,only the 0th index will be our required hashed password
        
        if input_hashed == stored_hash:
            print(f"✅ Welcome back, {username}! Login successful.")
            return True,stored_user_id
        else:
            print("❌ Incorrect password.")
            return False,None
    
    except Exception as e:
        print(f"❌ Database error during login: {e}")
        return False, None
            
    finally:
        cursor.close()
        db.close()

def is_ip_banned(ip_address):
    #checks if the ip is banned
    db = get_connection()
    cursor = db.cursor()
    
    try:
       #look for bans where ban time is not yet finished
        query = "SELECT reason, expires_at FROM Active_Bans WHERE ip_address = %s AND expires_at > NOW()"
        cursor.execute(query, (ip_address,))
        result = cursor.fetchone()
        
        if result:
            return True, result[0], result[1] # Returns True, reason, and the expiration
        return False, None, None
            
    finally:
        cursor.close()
        db.close()

def ban_ip(ip_address, reason, minutes=15):
   #banning ip for malicious activities
    db = get_connection()
    cursor = db.cursor()
    
    #calculate the exact time the ban should be removed
    expires = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    
    try:
        #
        query = """
            INSERT INTO Active_Bans 
            (ip_address, expires_at, reason) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE expires_at = %s, reason = %s
        """
        cursor.execute(query, (ip_address, expires, reason, expires, reason))
        db.commit()
        print(f"🚫 [SECURITY] Banned IP {ip_address} for {minutes} minutes. Reason: {reason}")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error while banning IP: {err}")
        
    finally:
        cursor.close()
        db.close()

#testing
if __name__ == "__main__":
    print("Test Registration ")
    register_user("test123", "batmansupermanspiderman")
    
    print("\nTest Login")
    login_user("test123", "susss")#failure
    login_user("test123", "batmansupermanspiderman") #success

# To understand it, you have to understand that every Python file has a "split personality." It can be used in two totally different ways:

# As a standalone program (running it directly, like you just did).

# As a library/module (where another file borrows its functions).

# Here is exactly how if __name__ == "__main__": manages those two personalities.

# 1. The Secret __name__ Variable
# Whenever you run a Python script, Python secretly creates a few background variables before it even looks at your code. One of these hidden variables is called __name__.

# Python automatically assigns a string value to __name__ depending on how the file was opened:

# Scenario A (Running directly): If you open your terminal and type python auth.py, Python says, "Ah, this is the main show!" and it sets the hidden variable to: __name__ = "__main__".

# Scenario B (Importing): If you create a new file tomorrow called server.py and write import auth at the top of it, Python says, "Ah, we are just borrowing tools from auth.py." In this case, Python sets the hidden variable to the file's actual name: __name__ = "auth".

# 2. The if Statement Check
# Python
# if __name__ == "__main__":
# This line is essentially a bouncer at the door of your testing code. It asks: "Is this file the main program being run right now?"

# If the answer is Yes (because __name__ is "__main__"), the code indented underneath it will run.

# If the answer is No (because it was imported by another file), the code indented underneath it is completely ignored.

# 3. Why is this critical for your Music Streamer?
# Think about what will happen in a few days when you build your server.

# Your server.py file is going to need to verify user passwords, so you will put import auth at the top of it to use your login_user function.

# If you DID NOT have this if statement: The moment you started your server, it would read the auth.py file from top to bottom and accidentally run your test code. It would try to register "jerry_tunes" and test the login every single time you booted up the server!

# Because you DO have this if statement: When server.py imports auth.py, __name__ becomes "auth". The if statement evaluates to False, and your test prints are safely ignored. You get to borrow the functions without triggering the test code.