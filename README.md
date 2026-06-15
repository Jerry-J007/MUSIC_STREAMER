## ⚙️ Installation & Local Setup

Because this project relies on a live TCP server and a custom SQL database, there are a few steps required to spin it up locally.

### 1. Prerequisites
You must have the following installed on your machine:
* **Python 3.x**
* **MySQL Server** (Running locally on default port 3306)
* **FFmpeg** (Required for the YouTube-DL conversion)

### 2. Clone the Repository
Open your terminal and pull down the code:
```bash
git clone [https://github.com/Jerry-J007/MUSIC_STREAMER.git](https://github.com/Jerry-J007/MUSIC_STREAMER.git)
cd MUSIC_STREAMER
```

### 3. Install the following python libraries
mysql-connector-python , pygame , yt-dlp

### 4. Download FFmpeg for Windows using this Link
https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

### 5. Create the local database architecture in MySql workbench using the schema provided in Database_Schema.png

### 6.Change your local password in the following files
authenticator.py , backup.py , music_streamer.py

### 7.Boot UP the server.py file

### 8.Open a  new terminal and boot up the terminal_UI.py file
