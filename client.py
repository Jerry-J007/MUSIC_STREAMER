import socket
import json
import time

class Music_Client:
    def __init__(self,host="127.0.0.1",port=54321):
        #same as server config
        self.HOST = '127.0.0.1'  
        self.PORT = 54321 
        self.client_socket=None   

        

    def client_connect(self):
        #create client socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
        try:
            #connect to the server
            self.client_socket.connect((self.HOST,self.PORT))
            return True
        except ConnectionRefusedError:
             return False
    def login(self,username,password):    
        load_login={
            "action":"login",
            "username":username,
            "password":password,
           
        }
        
        #sends a message to the server
        #network sockets only send raw bytes, so we must .encode() our text
        self.client_socket.sendall(json.dumps(load_login).encode())
        
        #wait for the server's reply
        reply = json.loads(self.client_socket.recv(1024).decode())
       #bytes to string to json (dict format)
        
        if reply.get('status') == 'success':
           return True,reply.get('id')
        return False,reply.get('message')
    def download_stream(self,id,filename):
        stream_load={
            "action": "stream",
            "id": id,
            "filename":filename
        }
        self.client_socket.sendall(json.dumps(stream_load).encode())

        stream_data = self.client_socket.recv(1024)
        stream_reply = json.loads(stream_data.decode())
       
        if stream_reply["status"]!="success":
            return False,stream_reply["message"]
        bytes_to_expect = stream_reply["bytes_to_expect"]
        bytes_received = 0
        self.client_socket.settimeout(15.0)
        
        try:
            # open brand new file in binary writing and save the incoming chunks
            with open('downloaded_song.mp3', 'wb') as file:
                while bytes_received < bytes_to_expect:
                    # Catch the incoming chunks (4096 bytes at a time)
                    chunk = self.client_socket.recv(4096)
                    
                    if not chunk:
                        break
                        
                    # Write the raw bytes directly to the file
                    file.write(chunk)
                    bytes_received+=len(chunk)
               
        except ConnectionRefusedError:
             pass

        except socket.timeout:
                    # If the server stops sending data for 2 seconds, break the loop
                    return False, "Download timed out before finishing!"
        
        finally:
            self.client_socket.settimeout(None)
        return True,"Donload completed"
    
    def register(self,username,password):
        register_load={
              "action":"register",
              "username":username,
              "password":password

         }
        self.client_socket.sendall(json.dumps(register_load).encode())
        
        reply = json.loads(self.client_socket.recv(1024).decode())
        if reply['status'] == 'success':
            return True, reply['message']
        return False, reply['message']
    

    def disconnect(self):
        if self.client_socket:
             self.client_socket.close()
    
    def add_youtube_song(self, url):
        #yt link to download
        load_yt = {"action": "youtube", "url": url}
        self.client_socket.sendall(json.dumps(load_yt).encode())
        
        reply = json.loads(self.client_socket.recv(1024).decode())
        if reply.get('status') == 'success':
            return True, reply.get('message')
        return False, reply.get('message')
    
    def get_song_list(self):
        #array of all available song
        load_songs = {"action": "list_songs"}
        self.client_socket.sendall(json.dumps(load_songs).encode())
        
        reply = json.loads(self.client_socket.recv(1024).decode())
        if reply.get("status") == "success":
            return True, reply.get("songs")
        return False, []
    
    def create_playlist(self, session_id, name):
        load_list = {"action": "create_playlist", "id": session_id, "name": name}
        self.client_socket.sendall(json.dumps(load_list).encode())
        reply = json.loads(self.client_socket.recv(1024).decode())
        return reply.get("status") == "success", reply.get("message")

    def view_playlists(self, session_id):
        load_listview = {"action": "view_playlists", "id": session_id}
        self.client_socket.sendall(json.dumps(load_listview).encode())
        reply = json.loads(self.client_socket.recv(1024).decode())
        return reply.get("status") == "success", reply.get("playlists", [])

    def add_to_playlist(self, playlist_id, filename):
        load_add = {"action": "add_to_playlist", "playlist_id": playlist_id, "filename": filename}
        self.client_socket.sendall(json.dumps(load_add).encode())
        reply = json.loads(self.client_socket.recv(1024).decode())
        return reply.get("status") == "success", reply.get("message")

    def view_playlist_tracks(self, session_id, playlist_id):
        load_tracks = {"action": "view_playlist_tracks", "id": session_id, "playlist_id": playlist_id}
        self.client_socket.sendall(json.dumps(load_tracks).encode())
        reply = json.loads(self.client_socket.recv(1024).decode())
        return reply.get("status") == "success", reply.get("songs", [])