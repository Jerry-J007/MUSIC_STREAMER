import socket
import json
import authenticator
import threading
import uuid
import os
import time
import backup
import yt_dlp
import glob
# Configuration
HOST = '127.0.0.1'  # universal ip for local host
PORT = 54321        # random big digit
# A global dictionary to store everyone data
# Format: { "session_id_string": UserState_Object }
class UserState:
    def __init__(self, username, session_id,db_user_id):
        self.username = username
        self.session_id = session_id
        self.db_user_id = db_user_id
        self.current_track = None
        self.playback_position = 0  # we can track the exact byte we left off
active_sessions = {}
connection_attempts={}
failed_logins={}

def process_youtube_link(url):
    #download yt audio in background
    print(f"\n🌐 New youtube link received.start downloading")
    
    options = {
        'format': 'bestaudio/best',
        # Let's save it as the master file so everyone can stream it immediately
        'outtmpl': '%(title)s.%(ext)s',
        'restrictfilenames': True, 
        'ffmpeg_location': './', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', 
        }],
        'quiet': True # Keep the server terminal clean
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        print("✅Track downloaded, converted, and added to the library")
    except Exception as e:
        print(f"❌Download failed: {e}")

def start_server():
    #Create a TCP socket
    # AF_INET means IPv4, SOCK_STREAM means TCP (reliable data transfer)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #socket.AF_INET : IPv4 addresses (192.168.x.x).
    #socket.SOCK_STREAM: This tells the socket to use TCP (Transmission Control Protocol).TCP is the reliable delivery method. It guarantees that data arrives in the exact order it was sent without missing pieces.
    #Bind the socket to the IP and Port

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)#to avoid port already in use bug when restarting
    server_socket.bind((HOST, PORT))#we bind our specific host and port to the server
    
    #Starts listening for incoming connections to the 54321 port
    server_socket.listen()
    print(f"🎧 Server is online and listening on {HOST} : {PORT}")
    backup.start_background_backups()
    while True:
        #accepts a connection when a client calls
        # This  pauses the script until someone connects,waits for as long as someone connects
        connection, address = server_socket.accept()
        #new connection and address specific to this client
        #address contains ip and port of the client in form of a tuple
        ip_address = address[0] #ip string from the tuple
        
        # if already banned
        is_banned, reason, expires = authenticator.is_ip_banned(ip_address)
        if is_banned:
            print(f"🛡️ [BLOCKED] Rejected handshake from banned IP: {ip_address}")
            connection.close() # Drop the phone instantly
            continue
            
        #TCP RATE LIMITING
        current_time = time.time()
        
        # If we haven't seen this IP before, create an empty list for it
        if ip_address not in connection_attempts:
            connection_attempts[ip_address] = []
            
        #current connection timestamp
        connection_attempts[ip_address].append(current_time)
        
        #removes timestamps older than 5 seconds
        connection_attempts[ip_address] = [t for t in connection_attempts[ip_address] if current_time - t < 5]
        
        # if connected more than 10 times in 5 seconds, ban
        if len(connection_attempts[ip_address]) > 10:#deniel of service
            print(f"⚠️ [WARNING] DoS attempt detected from {ip_address}!")
            authenticator.ban_ip(ip_address, "Socket Spam / DoS Attempt", minutes=60)
            connection.close()
            continue

        threading.Thread(target=handle_client, args=(connection, address)).start()
        print(f"🧵 [ACTIVE THREADS] {threading.active_count() - 1}")#-1 for the main server
    
def handle_client(connection,address):
    ip_address=address[0]
    try :
        print(f"✅ NEW CONNECTION {address} connected")
        with connection:#in case of a crash,the connection  is closed with the client
            print(f"✅ Connection is established with the address : {address}")
            while True:
                #waits for the client to send us a message
                data_raw = connection.recv(1024) #receives up to 1024 bytes of data(1024*8 bits)
                if not data_raw:
                    return
                load=json.loads(data_raw.decode())#converts string to dictionary format
                print(f"📥 Client requests the following action : {load.get('action')}")
                if load.get("action") == "login":
                    username = load.get("username")
                    password = load.get("password")
            
                    # returns true or false from the authenticator
                    is_valid,db_user_id = authenticator.login_user(username, password)
            
                    if is_valid:
                        failed_logins[ip_address] = 0
                        id=str(uuid.uuid4())
                        active_sessions[id] = UserState(username, id,db_user_id)
                        response = {"status": "success", "message": "Login successful.Ready to stream.","id":id}
                    else:
                        failed_logins[ip_address] = failed_logins.get(ip_address, 0) + 1
                        response = {"status": "error", "message": "Invalid username or password."}
                        
                        if failed_logins[ip_address] >= 5:
                            authenticator.ban_ip(ip_address, "Brute Force Password Guessing", minutes=15)
                            response = {"status": "error", "message": "Too many attempts. Your IP has been banned."}
                            connection.sendall(json.dumps(response).encode())
                            return #abort the connection
                    
                    # Convert the response dictionary back to a JSON string, encode to bytes, and sends it
                    connection.sendall(json.dumps(response).encode())
            
                elif load.get('action') == 'stream':
                    session_id = load.get('id')
                    target_file = load.get("filename")
                    print(f"🎵 [{address}] Requested an audio track to stream.")
               
                    if session_id not in active_sessions:
                        
                        response = {"status": "error", "message": "Invalid or expired session."}
                        connection.sendall(json.dumps(response).encode())
                        continue #stops if no valid id

                    if not target_file or not os.path.exists(target_file):
                        response = {"status": "error", "message": f"Song '{target_file}' not found."}
                        connection.sendall(json.dumps(response).encode())
                        continue
                    user_state = active_sessions[session_id]
                    
                    #informing the success to client
                    
                    if user_state.current_track != target_file:
                        user_state.current_track = target_file
                        user_state.playback_position = 0
                
                    #we test open mp3 file in reading binary mode
                    try:
                        with open(target_file, 'rb') as audio_file:
                            total_size = os.path.getsize(target_file)
                            remaining_bytes = total_size - user_state.playback_position
                            
                            response = {
                                "status": "success", 
                                "message": "Stream starting.",
                                "bytes_to_expect": remaining_bytes # Tell the client how big the download is!
                            }
                            connection.sendall(json.dumps(response).encode())
                            
                            audio_file.seek(user_state.playback_position)
                            print(f"▶️ Starting playback at byte {user_state.playback_position}")
                            while True:
                                # reading 4096 bytes (4KB) at a time
                                chunk = audio_file.read(4096)
                            
                                if not chunk:
                                #song transfer over ,so no data in chunk
                                    print(f"Finished sending song to {address}")
                                    user_state.playback_position=0
                                    break
                                
                                # Send the raw bytes directly ,no need to .encode() because it is already in binary
                                connection.sendall(chunk)
                                user_state.playback_position += len(chunk)
                            
                    except FileNotFoundError:
                        print("❌ ERROR: song not found on the server!!!")

                # new user
                elif load.get("action") == "register":
                    username = load.get("username")
                    password = load.get("password")
                    
                    # 
                    success = authenticator.register_user(username, password)
                    
                    if success:
                        response = {"status": "success", "message": "Account created! You can now log in."}
                    else:
                        response = {"status": "error", "message": "Username already exists."}
                        
                    connection.sendall(json.dumps(response).encode())
                elif load.get("action") == "youtube":
                    url = load.get("url")
                    
                   
                    # This allows the server to keep talking to the client while the download happens
                    threading.Thread(target=process_youtube_link, args=(url,), daemon=True).start()
                    
                    response = {"status": "success", "message": "Server has started downloading track in the background"}
                    connection.sendall(json.dumps(response).encode())
                
                elif load.get("action") == "list_songs":
                    # glob finds all files with.mp3
                    available_songs = glob.glob("*.mp3")
                    if "downloaded_song.mp3" in available_songs:
                        available_songs.remove("downloaded_song.mp3")
                    
                    response = {"status": "success", "songs": available_songs}
                    connection.sendall(json.dumps(response).encode())
                
                elif load.get("action") == "create_playlist":
                    playlist_name = load.get("name")
                    session_id = load.get("id")
                    user_id = active_sessions[session_id].db_user_id
                    
                    db = authenticator.get_connection()
                    cursor = db.cursor()
                    try:
                        cursor.execute("INSERT INTO Playlists (user_id, name) VALUES (%s, %s)", (user_id, playlist_name))
                        db.commit()
                        response = {"status": "success", "message": f"Playlist '{playlist_name}' created!"}
                    except Exception as e:
                        response = {"status": "error", "message": str(e)}
                    finally:
                        cursor.close()
                        db.close()
                    connection.sendall(json.dumps(response).encode())

                elif load.get("action") == "view_playlists":
                    session_id = load.get("id")
                    user_id = active_sessions[session_id].db_user_id
                    
                    db = authenticator.get_connection()
                    cursor = db.cursor()
                    try:
                        cursor.execute("SELECT playlist_id, name FROM Playlists WHERE user_id = %s", (user_id,))
                        # Fetch all rows and format them as a list of dictionaries so JSON can send it easily
                        playlists = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
                        response = {"status": "success", "playlists": playlists}
                    except Exception as e:
                        response = {"status": "error", "message": str(e)}
                    finally:
                        cursor.close()
                        db.close()
                    connection.sendall(json.dumps(response).encode())

                elif load.get("action") == "add_to_playlist":
                    playlist_id = load.get("playlist_id")
                    filename = load.get("filename")
                    
                    db = authenticator.get_connection()
                    cursor = db.cursor()
                    try:
                        cursor.execute("INSERT INTO Playlist_Tracks (playlist_id, filename) VALUES (%s, %s)", (playlist_id, filename))
                        db.commit()
                        response = {"status": "success", "message": "Song added to playlist!"}
                    except Exception as e:
                        # duplicate entry code for my sql
                        if "1062" in str(e):
                            response = {"status": "error", "message": "Song is already in this playlist!"}
                        else:
                            response = {"status": "error", "message": str(e)}
                    finally:
                        cursor.close()
                        db.close()
                    connection.sendall(json.dumps(response).encode())

                elif load.get("action") == "view_playlist_tracks":
                    playlist_id = load.get("playlist_id")
                    session_id = load.get("id")
                    
                    db = authenticator.get_connection()
                    cursor = db.cursor()
                    try:
                        if session_id not in active_sessions:
                            response = {"status": "error", "message": "Session expired. Please restart your client and log in again."}
                        else:
                            user_id = active_sessions[session_id].db_user_id
                            
                            db = authenticator.get_connection()
                            cursor = db.cursor()
                       
                         # We ask the Junction Table (pt) for the filename, but we JOIN it with the 
                         # Playlists table (p) to verify this playlist actually belongs to this user_id!
                            query = """
                                SELECT pt.filename 
                                FROM Playlist_Tracks pt 
                                JOIN Playlists p ON pt.playlist_id = p.playlist_id 
                                WHERE pt.playlist_id = %s AND p.user_id = %s
                            """
                            cursor.execute(query, (playlist_id, user_id))
                        
                        # Grab the first item from every tuple returned
                            songs = [row[0] for row in cursor.fetchall()]
                        
                        # We hide the client downloaded 
                            if "downloaded_song.mp3" in songs:
                                songs.remove("downloaded_song.mp3")
                            
                            response = {"status": "success", "songs": songs}
                            cursor.close()
                            db.close()
                    except Exception as e:
                        response = {"status": "error", "message": str(e)}
                    connection.sendall(json.dumps(response).encode())
    except Exception as err:
        print(f"❌ERROR {err}")

    print(f"🔴Address : {address} disconnected")




if __name__ == "__main__":
    start_server()