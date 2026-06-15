import yt_dlp
import os

def download_youtube_audio(video_url):
    print(f"🔍 Searching YouTube for: {video_url}")
   
    
    options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s', 
         'restrictfilenames': True,
        # look in the current folder for ffmpeg.exe
        'ffmpeg_location': './', 
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', 
        }],
        'quiet': False 
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])
            print("\n✅ SUCCESS! Download and conversion complete!")
    except Exception as e:
        print(f"\n❌ Failed to download: {e}")

if __name__ == "__main__":

    test_link = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    download_youtube_audio(test_link)