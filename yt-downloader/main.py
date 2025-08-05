import os
import re
import sys
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSER_FILE = os.path.join(SCRIPT_DIR, "browser.json")
DEFAULT_BROWSER = "none"

def get_channel_name(url):
    m = re.search(r'youtube\.com/@([^/]+)', url)
    if m:
        return m.group(1)
    m = re.search(r'youtube\.com/channel/([^/]+)', url)
    if m:
        return m.group(1)
    return None

def load_browser():
    if os.path.exists(BROWSER_FILE):
        with open(BROWSER_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("browser", DEFAULT_BROWSER)
            except Exception:
                return DEFAULT_BROWSER
    return DEFAULT_BROWSER

def save_browser(browser):
    with open(BROWSER_FILE, "w") as f:
        json.dump({"browser": browser}, f)

def run_yt_dlp_json(url, browser, cookies=True):
    args = [
        "yt-dlp", "--flat-playlist", "-J", url
    ]
    if cookies and browser != "none":
        args.insert(2, "--cookies-from-browser")
        args.insert(3, browser)
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError:
        return None

def get_release_urls(url, output_dir, browser):
    releases_url = url.rstrip("/") + "/releases"
    data = run_yt_dlp_json(releases_url, browser)
    entries = []
    if data and "entries" in data:
        print("✅ Found /releases page")
        entries = [e for e in data["entries"] if e.get("url")]
    else:
        print("⚠️ /releases page not available. Searching for playlists with 'album' or 'single' in the name...")
        playlists_url = url.rstrip("/") + "/playlists"
        data = run_yt_dlp_json(playlists_url, browser)
        if data and "entries" in data:
            for e in data["entries"]:
                title = e.get("title", "")
                if re.search(r"album|single", title, re.I) and e.get("url"):
                    entries.append(e)
    seen = set()
    filtered = []
    for e in entries:
        if e["url"] not in seen:
            filtered.append(e)
            seen.add(e["url"])
    albums_file = os.path.join(output_dir, "albums.txt")
    with open(albums_file, "w") as f:
        for idx, e in enumerate(filtered, 1):
            title = e.get("title", "Unknown")
            url = e.get("url")
            f.write(f"{idx}. {title}\n{url}\n\n")
    return [e["url"] for e in filtered]

def sanitize_folder(name):
    name = re.sub(r'^Album - ', '', name)
    name = re.sub(r'[:/]', ' -', name)
    return name

def download_release(item_url, index, output_dir, cookie_option, browser):
    if index % 5 == 0 and browser != "none":
        print(f"♻️ Reloading cookies from {browser}...")
        test = run_yt_dlp_json(item_url, browser)
        if test:
            cookie_option = True
        else:
            print("⚠️ Cookies are no longer valid, continuing without cookies.")
            cookie_option = False

    print(f"🎧 Downloading: {item_url}")
    data = run_yt_dlp_json(item_url, browser, cookies=cookie_option)
    release_name = sanitize_folder(data.get("title", "")) if data else None
    if not release_name or release_name == "null":
        release_name = f"Unknown_{int(subprocess.getoutput('date +%s'))}"

    base_folder = os.path.join(output_dir, release_name)
    target_folder = base_folder
    suffix = 1
    while os.path.exists(target_folder):
        target_folder = f"{base_folder} ({suffix})"
        suffix += 1
    os.makedirs(target_folder, exist_ok=True)

    tracks_txt = os.path.join(target_folder, "tracks.txt")
    with open(tracks_txt, "w") as f:
        f.write(f"{release_name}\n{item_url}\n\n")
        entries = data.get("entries", []) if data else []
        for i, entry in enumerate(entries, 1):
            title = entry.get("title", "Unknown Track")
            url = entry.get("url") or entry.get("webpage_url", "")
            f.write(f"{i}. {title}\n{url}\n\n")

    args = [
        "yt-dlp",
        "--yes-playlist",
        "--ignore-errors",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--embed-metadata",
        "--embed-thumbnail",
        "--concurrent-fragments", "8",
        "--limit-rate", "2M",
        "--downloader", "aria2c",
        "--download-archive", tracks_txt,
        "--downloader-args", "aria2c:-x16 -s16 -k1M",
        "--output", os.path.join(target_folder, "%(title)s.%(ext)s"),
        item_url
    ]
    if cookie_option and browser != "none":
        args.insert(1, "--cookies-from-browser")
        args.insert(2, browser)
    subprocess.run(args)

def download_single_song(url, output_dir, cookie_option, browser):
    print(f"🎵 Downloading single song: {url}")
    args = [
        "yt-dlp",
        "--ignore-errors",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--embed-metadata",
        "--embed-thumbnail",
        "--concurrent-fragments", "8",
        "--limit-rate", "2M",
        "--downloader", "aria2c",
        "--downloader-args", "aria2c:-x16 -s16 -k1M",
        "--output", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]
    if cookie_option and browser != "none":
        args.insert(1, "--cookies-from-browser")
        args.insert(2, browser)
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(args)

def download_single_playlist(url, output_dir, cookie_option, browser):
    print(f"📃 Downloading playlist: {url}")
    info = run_yt_dlp_json(url, browser, cookies=cookie_option)
    playlist_title = info.get("title", "Unknown_Playlist") if info else "Unknown_Playlist"
    playlist_folder = os.path.join("YouTube_Playlists", sanitize_folder(playlist_title))
    os.makedirs(playlist_folder, exist_ok=True)
    tracks_txt = os.path.join(playlist_folder, "tracks.txt")
    entries = info.get("entries", []) if info else []
    with open(tracks_txt, "w") as f:
        f.write(f"{playlist_title}\n{url}\n\n")
        for i, entry in enumerate(entries, 1):
            title = entry.get("title", "Unknown Track")
            track_url = entry.get("url") or entry.get("webpage_url", "")
            f.write(f"{i}. {title}\n{track_url}\n\n")
    args = [
        "yt-dlp",
        "--yes-playlist",
        "--ignore-errors",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--embed-metadata",
        "--embed-thumbnail",
        "--concurrent-fragments", "8",
        "--limit-rate", "2M",
        "--downloader", "aria2c",
        "--downloader-args", "aria2c:-x16 -s16 -k1M",
        "--output", os.path.join(playlist_folder, "%(title)s.%(ext)s"),
        url
    ]
    if cookie_option and browser != "none":
        args.insert(1, "--cookies-from-browser")
        args.insert(2, browser)
    subprocess.run(args)

def choose_browser():
    supported_browsers = ["firefox", "chrome", "edge", "opera", "none"]
    while True:
        print("Supported browsers: firefox, chrome, edge, opera, none")
        browser = input("Enter browser name (or 'none' for no cookies): ").strip().lower()
        if browser in supported_browsers:
            save_browser(browser)
            return browser
        print("❌ Unsupported browser.")

def menu():
    browser = load_browser()
    supported_browsers = ["firefox", "chrome", "edge", "opera", "none"]
    if browser not in supported_browsers:
        browser = choose_browser()
    while True:
        print("\n==== YouTube Downloader ====")
        print(f"Current browser for cookies: {browser}")
        print("1. Download all singles/albums of an artist")
        print("2. Download a single song")
        print("3. Download a single playlist")
        print("4. Set browser for cookies")
        print("0. Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            url = input("🔗 Enter the YouTube channel/artist URL: ").strip()
            channel_name = get_channel_name(url)
            if not channel_name:
                print("❌ Invalid URL. Unable to determine channel/artist.")
                continue
            output_dir = os.path.join("YouTube_Releases", channel_name)
            os.makedirs(output_dir, exist_ok=True)
            print("🔍 Searching for available albums and singles...")
            urls = get_release_urls(url, output_dir, browser)
            num_items = len(urls)
            print(f"📦 Found {num_items} albums/singles to download.")
            if num_items == 0:
                print("❌ No content found.")
                continue
            print("🚀 Starting parallel download with 5 jobs...")
            cookie_option = True
            with ThreadPoolExecutor(max_workers=5) as executor:
                for idx, item_url in enumerate(urls):
                    executor.submit(download_release, item_url, idx, output_dir, cookie_option, browser)
            print(f"✅ Download completed. Files saved in: {output_dir}")
        elif choice == "2":
            url = input("🔗 Enter the YouTube song URL: ").strip()
            output_dir = os.path.join("YouTube_Songs")
            cookie_option = True
            download_single_song(url, output_dir, cookie_option, browser)
            print(f"✅ Song downloaded to: {output_dir}")
        elif choice == "3":
            url = input("🔗 Enter the YouTube playlist URL: ").strip()
            cookie_option = True
            download_single_playlist(url, None, cookie_option, browser)
            print(f"✅ Playlist downloaded to: YouTube_Playlists/<playlist_name>")
        elif choice == "4":
            browser = choose_browser()
            print(f"✅ Browser for cookies set to {browser}.")
        elif choice == "0":
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    menu()