import os
import re
import sys
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BROWSER_FILE = os.path.join(SCRIPT_DIR, "browser.json")
DEFAULT_BROWSER = "none"

def get_channel_name(url, browser, scraped_name=None):
    if scraped_name:
        return scraped_name
    
    try:
        print("🔍 Fetching channel name with yt-dlp...")
        data = run_yt_dlp_json(url, browser, cookies=True)
        if data:
            channel_name = data.get("channel") or data.get("uploader") or data.get("channel_name")
            if channel_name:
                print(f"✅ Found channel name: {channel_name}")
                channel_name = re.sub(r'[<>:"/\\|?*]', '_', channel_name)
                channel_name = channel_name.strip()
                return channel_name
            else:
                print("⚠️ Channel name not found in yt-dlp data")
        else:
            print("⚠️ yt-dlp failed to get channel data")
    except Exception as e:
        print(f"⚠️ Error getting channel name: {e}")
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
        "yt-dlp", "--flat-playlist", "-J", "--extractor-args", "youtube:player-client=default,-tv_simply", url
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
    base_url = url.rstrip("/").split("?")[0]
    base_url = re.sub(r'/(releases|playlists?|videos|channels|featured|about|community|store|search).*$', '', base_url)
    releases_url = base_url + "/releases"
    data = run_yt_dlp_json(releases_url, browser)
    entries = []
    scraped_channel_name = None
    
    if data and "entries" in data:
        print("✅ Found /releases page")
        entries = [e for e in data["entries"] if e.get("url")]
    else:
        print("❌ /releases page not available, trying web scraping...")
        try:
            scrape_result = scrape_topic_channel_links(base_url, browser)
            if isinstance(scrape_result, dict):
                entries = scrape_result.get("links", [])
                scraped_channel_name = scrape_result.get("channel_name")
            else:
                entries = scrape_result if scrape_result else []
        except Exception as e:
            print(f"❌ Web scraping failed: {e}")
            entries = []
    
    seen = set()
    filtered = []
    for e in entries:
        if isinstance(e, dict):
            url_entry = e.get("url")
            title = e.get("title", "Unknown")
        else:
            url_entry = e
            title = "Unknown"
        if url_entry and url_entry not in seen:
            filtered.append({"url": url_entry, "title": title})
            seen.add(url_entry)
    albums_file = os.path.join(output_dir, "albums.txt")
    with open(albums_file, "w") as f:
        for idx, e in enumerate(filtered, 1):
            title = e.get("title", "Unknown")
            url = e.get("url")
            f.write(f"{idx}. {title}\n{url}\n\n")
    
    result = [e["url"] for e in filtered]
    if scraped_channel_name:
        return {"urls": result, "channel_name": scraped_channel_name}
    return result

def scrape_topic_channel_links(channel_url, browser_name):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        driver = webdriver.Firefox(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(channel_url)
        accept_buttons = [
            "//button[contains(text(), 'Accept all')]",
            "//button[contains(text(), 'I agree')]", 
            "//button[contains(text(), 'Accetta tutto')]",
            "//button[contains(text(), 'Reject all')]",
            "//button[contains(text(), 'Rifiuta tutto')]",
            "//form[@action='https://consent.youtube.com/save']//button[1]",
            "//button[@aria-label='Accept all']",
            "//button[@aria-label='Reject all']"
        ]
        button_clicked = False
        for xpath in accept_buttons:
            try:
                button = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                button.click()
                button_clicked = True
                time.sleep(2)
                break
            except:
                continue
        time.sleep(3)
        
        channel_name = None
        try:
            channel_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/div[4]/ytd-tabbed-page-header/div/div[2]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-dynamic-text-view-model/h1/span"))
            )
            channel_name = channel_element.text.strip()
            if channel_name:
                channel_name = re.sub(r' - Topic$', '', channel_name)
                channel_name = re.sub(r'[<>:"/\\|?*]', '_', channel_name)
                print(f"✅ Extracted channel name from page: {channel_name}")
        except:
            print("⚠️ Could not extract channel name from page")
        
        try:
            show_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//html/body/ytd-app/div[1]/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]/ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-shelf-renderer/div[1]/div[1]/div/div[3]/ytd-menu-renderer/div[1]/ytd-button-renderer/yt-button-shape/button"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_button)
            time.sleep(1)
            try:
                show_button.click()
            except:
                driver.execute_script("arguments[0].click();", show_button)
            time.sleep(3)
        except Exception:
            pass
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 8
        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1
        for i in range(2):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        js_script = """
        const allLinks = [...document.querySelectorAll('a[href]')]
            .map(a => a.href)
            .filter(href => href && (href.includes('/playlist?list=') || href.includes('/watch?v=')))
            .filter(href => !href.includes('music.youtube.com'))
            .filter(href => !href.includes('youtube.com/shorts'))
            .map(href => {
                try {
                    const url = new URL(href);
                    if (url.pathname.includes('/playlist')) {
                        const listId = url.searchParams.get('list');
                        return listId ? `https://www.youtube.com/playlist?list=${listId}` : null;
                    } else if (url.pathname.includes('/watch')) {
                        const videoId = url.searchParams.get('v');
                        const listId = url.searchParams.get('list');
                        if (videoId && listId) {
                            return `https://www.youtube.com/playlist?list=${listId}`;
                        } else if (videoId) {
                            return `https://www.youtube.com/watch?v=${videoId}`;
                        }
                    }
                    return null;
                } catch (e) {
                    return null;
                }
            })
            .filter(href => href !== null)
            .filter((href, index, array) => array.indexOf(href) === index);
        return allLinks;
        """
        links = driver.execute_script(js_script)
        driver.quit()
        filtered_links = []
        seen_playlists = set()
        seen_videos = set()
        seen_video_playlist_pairs = set()
        for link in links:
            if '/playlist?list=' in link:
                playlist_id = link.split('list=')[1].split('&')[0]
                if playlist_id not in seen_playlists and len(playlist_id) > 10:
                    seen_playlists.add(playlist_id)
                    filtered_links.append({"url": link, "title": "Unknown"})
            elif '/watch?v=' in link:
                if '&list=' in link:
                    video_id = link.split('v=')[1].split('&')[0]
                    playlist_id = link.split('list=')[1].split('&')[0]
                    pair = f"{video_id}:{playlist_id}"
                    if pair not in seen_video_playlist_pairs and len(video_id) == 11 and len(playlist_id) > 10:
                        seen_video_playlist_pairs.add(pair)
                        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
                        if playlist_id not in seen_playlists:
                            seen_playlists.add(playlist_id)
                            filtered_links.append({"url": playlist_url, "title": "Unknown"})
                else:
                    video_id = link.split('v=')[1].split('&')[0]
                    if video_id not in seen_videos and len(video_id) == 11:
                        seen_videos.add(video_id)
                        filtered_links.append({"url": link, "title": "Unknown"})
        
        result = {"links": filtered_links}
        if channel_name:
            result["channel_name"] = channel_name
        return result
    except Exception:
        if 'driver' in locals():
            try:
                driver.quit()
            except:
                pass
        return {"links": []}

def sanitize_folder(name):
    name = re.sub(r'^Album - ', '', name)
    name = re.sub(r'[:/]', ' -', name)
    return name

def update_albums_txt(output_dir, url, real_title):
    albums_file = os.path.join(output_dir, "albums.txt")
    if not os.path.exists(albums_file):
        return
    try:
        with open(albums_file, "r") as f:
            content = f.read()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() == url:
                if i > 0 and "Unknown" in lines[i-1]:
                    prev_line = lines[i-1]
                    if ". Unknown" in prev_line:
                        number_part = prev_line.split(". Unknown")[0] + ". "
                        lines[i-1] = number_part + real_title
                    else:
                        lines[i-1] = prev_line.replace("Unknown", real_title)
                break
        with open(albums_file, "w") as f:
            f.write('\n'.join(lines))
    except Exception as e:
        print(f"⚠️ Could not update albums.txt: {e}")

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
    real_title = data.get("title", "") if data else ""
    if not release_name or release_name == "null":
        release_name = f"Unknown_{int(subprocess.getoutput('date +%s'))}"
    if real_title and real_title != "null":
        update_albums_txt(output_dir, item_url, real_title)
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
            url = entry.get("webpage_url", "")
            if not url:
                yt_id = entry.get("id") or entry.get("url", "")
                if yt_id:
                    url = f"https://www.youtube.com/watch?v={yt_id}"
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
        "--extractor-args", "youtube:player-client=default,-tv_simply",
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
        "--extractor-args", "youtube:player-client=default,-tv_simply",
        "--output", os.path.join(output_dir, "%(title)s.%(ext)s"),
        url
    ]
    if cookie_option and browser != "none":
        args.insert(1, "--cookies-from-browser")
        args.insert(2, browser)
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(args)

def download_single_playlist(url, cookie_option, browser):
    print(f"📃 Downloading playlist: {url}")
    info = run_yt_dlp_json(url, browser, cookies=cookie_option)
    playlist_title = info.get("title", "Unknown_Playlist") if info else "Unknown_Playlist"
    playlist_folder = os.path.join("output", "playlists", sanitize_folder(playlist_title))
    os.makedirs(playlist_folder, exist_ok=True)
    tracks_txt = os.path.join(playlist_folder, "tracks.txt")
    entries = info.get("entries", []) if info else []
    with open(tracks_txt, "w") as f:
        f.write(f"{playlist_title}\n{url}\n\n")
        for i, entry in enumerate(entries, 1):
            title = entry.get("title", "Unknown Track")
            track_url = entry.get("webpage_url", "")
            f.write(f"{i}. {title}\n{track_url}\n\n")
    def download_track(entry):
        track_url = entry.get("url") or entry.get("webpage_url", url)
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
            "--extractor-args", "youtube:player-client=default,-tv_simply",
            "--output", os.path.join(playlist_folder, "%(title)s.%(ext)s"),
            track_url
        ]
        if cookie_option and browser != "none":
            args.insert(1, "--cookies-from-browser")
            args.insert(2, browser)
        subprocess.run(args)
    if entries:
        print(f"🚀 Starting parallel download of playlist tracks with 5 jobs...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            for entry in entries:
                executor.submit(download_track, entry)
        print(f"✅ Playlist downloaded to: {playlist_folder}")
    else:
        print("❌ No tracks found in playlist.")

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
        if browser == "none":
            print("WARNING: To avoid YouTube rate limiting or issues with restricted content, it is STRONGLY RECOMMENDED to set browser cookies.")
            print("WARNING: Firefox browser is also required for downloading songs from artists with topic channels (web scraping fallback).")
        print(f"Current browser for cookies: {browser}")
        print("1. Download all singles/albums of an artist")
        print("2. Download a single song")
        print("3. Download a single playlist")
        print("4. Set browser for cookies")
        print("0. Exit")
        choice = input("Select an option: ").strip()
        if choice == "1":
            url = input("🔗 Enter the YouTube channel/artist URL: ").strip()
            print("🔍 Getting channel name...")
            output_dir_temp = os.path.join("output", "releases", "temp")
            os.makedirs(output_dir_temp, exist_ok=True)
            print("🔍 Searching for available albums and singles...")
            urls_result = get_release_urls(url, output_dir_temp, browser)
            
            scraped_channel_name = None
            if isinstance(urls_result, dict):
                urls = urls_result.get("urls", [])
                scraped_channel_name = urls_result.get("channel_name")
            else:
                urls = urls_result
            
            channel_name = get_channel_name(url, browser, scraped_channel_name)
            if not channel_name:
                print("❌ Invalid URL. Unable to determine channel/artist.")
                continue
            print(f"📺 Channel: {channel_name}")
            
            output_dir = os.path.join("output", "releases", channel_name)
            if output_dir != output_dir_temp:
                os.makedirs(output_dir, exist_ok=True)
                import shutil
                if os.path.exists(os.path.join(output_dir_temp, "albums.txt")):
                    shutil.move(os.path.join(output_dir_temp, "albums.txt"), os.path.join(output_dir, "albums.txt"))
                try:
                    os.rmdir(output_dir_temp)
                except:
                    pass
            
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
            output_dir = os.path.join("output", "songs")
            cookie_option = True
            download_single_song(url, output_dir, cookie_option, browser)
            print(f"✅ Song downloaded to: {output_dir}")
        elif choice == "3":
            url = input("🔗 Enter the YouTube playlist URL: ").strip()
            cookie_option = True
            download_single_playlist(url, cookie_option, browser)
            print(f"✅ Playlist downloaded to: output/playlists/<playlist_name>")
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