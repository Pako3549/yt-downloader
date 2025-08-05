<div align="center">


# yt-downloader 🎵
![](https://img.shields.io/github/last-commit/Pako3549/yt-downloader?&style=for-the-badge&color=8272a4&logoColor=D9E0EE&labelColor=292324)
![](https://img.shields.io/github/stars/Pako3549/yt-downloader?style=for-the-badge&logo=polestar&color=FFB1C8&logoColor=D9E0EE&labelColor=292324)
![](https://img.shields.io/github/repo-size/Pako3549/yt-downloader?color=CAC992&label=SIZE&logo=files&style=for-the-badge&logoColor=D9E0EE&labelColor=292324)

</div>

A Python script to download all singles and albums from a YouTube artist/channel, with optional browser cookies support for private or age-restricted content.

## ✨ Features

- Download all albums and singles from a YouTube artist/channel.
- Download a single song from a YouTube URL.
- Download all tracks from a single playlist (parallel download with 5 jobs).
- Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [aria2c](https://aria2.github.io/) for fast and reliable downloads.
- Supports browser cookies from Firefox, Chrome, Edge, Opera, or no cookies at all.
- Parallel downloads for faster performance.
- Saves album and track info in readable text files (`albums.txt`, `tracks.txt`).

## ⚙️ Requirements

- Python 3.7+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [aria2c](https://aria2.github.io/)
- A supported browser (optional, for cookies): Firefox, Chrome, Edge, Opera

Install dependencies on Linux:
```sh
pip install -r yt-downloader/requirements.txt
```

## 🚀 Usage

1. **Run the script:**
   ```sh
   python yt-downloader/main.py
   ```

2. **Menu options:**
   - `1. Download all singles/albums of an artist`  
     Enter the YouTube channel/artist URL (e.g. `https://www.youtube.com/@ArtistName`).
   - `2. Download a single song`  
     Enter the YouTube song URL (e.g. `https://www.youtube.com/watch?v=xxxx`).
   - `3. Download a single playlist`  
     Enter the YouTube playlist URL (all tracks will be downloaded in parallel).
   - `4. Set browser for cookies`  
     Choose your browser for cookies (or `none` for no cookies).
   - `0. Exit`

3. **Downloads:**
   - Albums and singles are saved in `YouTube_Releases/<artist>/`.
   - Single songs are saved in `YouTube_Songs/`.
   - Playlists are saved in `YouTube_Playlists/<playlist_name>/` (all tracks in one folder).
   - Each album/playlist folder contains:
     - `tracks.txt` (tracklist and links)
     - Downloaded MP3 files

## 📝 Notes

- If you select `none` as browser, downloads will work for public content only.
- For private or age-restricted content, set your browser and make sure you are logged in.
- The browser choice is saved in `browser.json` and reused until changed.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.