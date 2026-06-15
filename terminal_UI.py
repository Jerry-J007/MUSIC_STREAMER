import os
import time
from client import Music_Client as client
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" 
import pygame

def clear_screen():
  #clears terminal
    os.system('cls' if os.name == 'nt' else 'clear')

def draw_header(title):
    clear_screen()
    print("=" * 40)
    print(f"🎵  {title.center(34)}  🎵")
    print("=" * 40 + "\n")

def player_controls():
    #play,pause,stop
    pygame.mixer.init()
    
    try:
        pygame.mixer.music.load('downloaded_song.mp3')
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        time.sleep(0.1)
    except pygame.error:
        print("❌ Error loading audio file")
        input("\nPress Enter to return...")
        return
    
    while True:
        draw_header("NOW PLAYING")
        print("▶️  Playing: downloaded_song.mp3\n")
        print("Controls:")
        print("  [P] Pause")
        print("  [R] Resume")
        print("  [S] Stop & Exit Player")
        print("-" * 40)
        
        cmd = input("Enter command: ").strip().upper()
        
        if cmd == 'P':
            pygame.mixer.music.pause()
            print("⏸️  Paused")
            time.sleep(1)
        elif cmd == 'R':
            pygame.mixer.music.unpause()
            print("▶️  Resumed")
            time.sleep(1)
        elif cmd == 'S':
            pygame.mixer.music.stop()
            pygame.mixer.quit() # Safely shut down the audio engine
            print("⏹️  Stopped")
            time.sleep(1)
            break
        else:
            print("Invalid command.")
            time.sleep(0.5)

def main():
    #start client
    backend = client()
    
    draw_header("MUSIC STREAMER")
    print("Connecting to server...")
    
    if not backend.client_connect():
        print("❌ Could not connect to server")
        return
    session_id = None
    logged_in_user = None
    while not session_id:
        draw_header("WELCOME TO MUSIC STREAMER")
        print("1. 🔑 Login")
        print("2. 📝 Register New Account")
        print("3. 🚪 Exit")
        print("-" * 40)
        
        choice = input("Enter choice (1-3): ")
        
        if choice == '3':
            print("\nGoodbye! 👋")
            backend.disconnect()
            return
            
        elif choice == '2':
            draw_header("REGISTER")
            new_user = input("👤 Choose Username: ")
            new_pass = input("🔑 Choose Password: ")
            success, msg = backend.register(new_user, new_pass)
            
            if success:
                print(f"\n✅ {msg}")
            else:
                print(f"\n❌ Registration Failed: {msg}")
            input("\nPress Enter to continue...")
    
        elif choice=="1":
        # 2. Login Screen
            draw_header("LOGIN")
            username = input("👤 Username: ")
            password = input("🔑 Password: ")
    
            print("\nAuthenticating...")
            time.sleep(0.5)#waits sometime for a dramatic effect
    
            success, result = backend.login(username, password)
    
            if success:
                session_id = result
                logged_in_user=username
            else:
                print(f"\n❌ Login Failed: {result}")
                input("\nPress Enter to try again...")
        else:
            print("Invalid choice.")
            time.sleep(1)
    
    # player menu
    while True:
        draw_header(f"WELCOME, {username.upper()}")
        print("1. ▶️  Download & Play Stream")
        print("2. 🌐  Add New Song (Paste YouTube Link)")
        print("3. 🚪  Log Out And Exit")
        print("-" * 40)
        
        choice = input("Enter choice (1 to 3 only): ")
        
        if choice == '1':
            print("\n📥 Fetching library from server...")
            success, songs = backend.get_song_list()
            
            if not success or len(songs) == 0:
                print("❌ No songs found in the server library. Add one from YouTube first!")
                input("\nPress Enter to return...")
                continue
                
            draw_header("JUKEBOX LIBRARY")
            for i, song in enumerate(songs):
                # names only
                clean_name = song.replace(".mp3", "").replace("_", " ")
                print(f"{i + 1}. 🎵 {clean_name}")
            print("-" * 40)
            
            try:
                song_choice = int(input("Enter song number to stream (0 to cancel): "))
                
                if song_choice == 0:
                    continue
                elif 1 <= song_choice <= len(songs):
                    chosen_filename = songs[song_choice - 1]
                    print(f"\n📥 Contacting server for audio stream...")
                    
                    
                    stream_success, msg = backend.download_stream(session_id, chosen_filename) 
                    
                    if stream_success:
                        player_controls() 
                    else:
                        print(f"\n❌ Stream failed: {msg}")
                else:
                    print("❌ Invalid number.")
            except ValueError:
                print("❌ Please enter a valid number.")
                
            input("\nPress Enter to return to menu...")
        
        elif choice == '2':
            draw_header("YOUTUBE LIBRARY AUTOMATION")
            print("Paste any YouTube link, and the server will convert it to an MP3")
            print("and instantly make it available for everyone to stream!\n")
            
            yt_link = input("🔗 YouTube URL: ").strip()
            
            print("\nSending link to server...")
            success, msg = backend.add_youtube_song(yt_link)
            
            if success:
                print(f"✅ {msg}")
                print("Wait about 10-15 seconds, then try streaming it!")
            else:
                print(f"❌ Failed: {msg}")
                
            input("\nPress Enter to return to menu...")
                
        elif choice == '3':
            print("\nGoodbye.Music is the universal language of mankink 👋")
            backend.disconnect()
            break
        else:
            print("Invalid choice.")
            time.sleep(1)

if __name__ == "__main__":
    main()