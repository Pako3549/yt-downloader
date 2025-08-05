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
- **Advanced web scraping** with Selenium Firefox for channels without `/releases` pages.
- **Automatic consent dialog handling** - automatically accepts GDPR/cookie consent dialogs.
- **Smart playlist discovery** - automatically clicks "View all" buttons to expand hidden playlists.
- **Real channel names** - extracts actual channel names from pages (not just handles/IDs).
- **Real-time title updates** - updates `albums.txt` with actual titles during download process.
- Uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) and [aria2c](https://aria2.github.io/) for fast and reliable downloads.
- Supports browser cookies from Firefox, Chrome, Edge, Opera, or no cookies at all.
- Parallel downloads for faster performance (5 concurrent jobs).
- Saves album and track info in readable text files (`albums.txt`, `tracks.txt`).

## ⚙️ Requirements

- Python 3.7+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [aria2c](https://aria2.github.io/)
- [Firefox browser](https://www.mozilla.org/firefox/) (required for web scraping)
- [Selenium](https://selenium-python.readthedocs.io/) with Firefox WebDriver (for web scraping)
- A supported browser (optional, for cookies): Firefox, Chrome, Edge, Opera

Install dependencies on Linux:
```sh
pip install -r yt-downloader/requirements.txt
```

**Note:** Firefox browser and WebDriver are required for the advanced web scraping functionality that handles consent dialogs and discovers hidden playlists when the `/releases` page is not available.

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
   - Albums and singles are saved in `output/releases/<artist>/` (using real channel names).
   - Single songs are saved in `output/songs/`.
   - Playlists are saved in `output/playlists/<playlist_name>/` (all tracks in one folder).
   - Each album/playlist folder contains:
     - `albums.txt` (album list with real titles updated during download)
     - `tracks.txt` (tracklist and links)
     - Downloaded MP3 files

## 🔧 How It Works

The downloader uses a multi-step approach:

1. **Channel Discovery**: Tries to access the `/releases` page first for fast discovery
2. **Web Scraping Fallback**: If no `/releases` page exists, uses Selenium to:
   - Handle consent/cookie dialogs automatically
   - Click "View all" buttons to expand hidden playlists
   - Scroll through the page to discover all content
   - Extract real channel names from the page DOM
3. **Smart Deduplication**: Removes duplicate playlist/video links
4. **Parallel Download**: Downloads multiple items simultaneously with real-time title updates

## 📝 Notes

- If you select `none` as browser, downloads will work for public content only.
- For private or age-restricted content, set your browser and make sure you are logged in.
- The browser choice is saved in `browser.json` and reused until changed.
- **Web scraping features require Firefox WebDriver** to be installed and accessible.
- The scraper automatically handles various consent dialogs in multiple languages (English, Italian).
- Channel names are automatically cleaned (removes "- Topic" suffixes and invalid characters).
- Real-time title updates mean `albums.txt` starts with placeholder titles that get updated during download.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.