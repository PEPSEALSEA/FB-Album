"""
Facebook Album Scraper - Modern GUI Version with Black/Pink Theme (Updated for 2025)
WARNING: This script is for educational purposes only.
Please ensure you comply with Facebook's Terms of Service and applicable laws.
Consider using Facebook's official API for legitimate use cases.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
from urllib.parse import urljoin, urlparse, parse_qs

class FacebookAlbumScraper:
    def __init__(self, headless=False, progress_callback=None, log_callback=None, speed="Medium"):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.stop_requested = False
        self.speed = speed
        self.delay_map = {
            "Slow": {"grab": 1.0, "download": 0.5},
            "Medium": {"grab": 0.5, "download": 0.3},
            "Fast": {"grab": 0.2, "download": 0.1}
        }
        
    def log(self, message, level="INFO"):
        if self.log_callback:
            self.log_callback(f"[{level}] {message}")
        
    def update_progress(self, current, total, message=""):
        if self.progress_callback:
            self.progress_callback(current, total, message)
    
    def setup_driver(self):
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--remote-debugging-port=9222')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 20)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.log("Browser driver initialized successfully")
        except Exception as e:
            self.log(f"Failed to setup driver: {e}", "ERROR")
            raise

    def wait_for_login(self, album_url, timeout=180):
        self.log("Please log in to Facebook in the browser window. Complete any additional verification if required...")
        self.driver.get("https://www.facebook.com/login")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.stop_requested:
                return False
            current_url = self.driver.current_url.lower()
            if 'login' not in current_url and 'checkpoint' not in current_url and 'two_step_verification' not in current_url:
                self.log("Initial login or verification detected, navigating to album...")
                time.sleep(5)
                self.driver.get(album_url)
                time.sleep(3)
                current_url = self.driver.current_url.lower()
                if 'login' not in current_url and 'checkpoint' not in current_url and 'two_step_verification' not in current_url:
                    self.log("Full login confirmed, proceeding to album...")
                    return True
                else:
                    self.log("Additional verification required, please complete it...")
            time.sleep(1)
        
        self.log("Login timeout. Please ensure you completed all login steps and two-step verification.", "ERROR")
        return False

    def remove_invalid_characters(self, title):
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            title = title.replace(char, '_')
        return title.strip()

    def create_folder(self, main_folder, album_title):
        folder_path = os.path.normpath(os.path.join(main_folder, album_title))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path

    def save_urls_to_file(self, urls, file_path):
        try:
            file_path = os.path.normpath(file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(urls, f)
            self.log(f"Saved {len(urls)} URLs to {file_path}")
        except Exception as e:
            self.log(f"Failed to save URLs to file: {e}", "ERROR")

    def load_urls_from_file(self, file_path):
        try:
            file_path = os.path.normpath(file_path)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    urls = json.load(f)
                self.log(f"Loaded {len(urls)} URLs from {file_path}")
                return urls
            return []
        except Exception as e:
            self.log(f"Failed to load URLs from file: {e}", "ERROR")
            return []

    def select_first_media(self, album_url):
        try:
            album_id = parse_qs(urlparse(album_url).query).get('set', [''])[0]
            selectors = [
                "a[href*='/photo/'] img",
                "a[href*='/videos/'] video",
                "div[role='img'] img",
                "[data-pagelet*='Photo'] img",
                "img[src*='scontent']",
                "img[src*='fbcdn']",
                "video[src*='fbcdn']"
            ]
            for selector in selectors:
                try:
                    media_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in media_elements:
                        if element.is_displayed():
                            width = element.get_attribute('width') or element.get_attribute('naturalWidth') or '100'
                            height = element.get_attribute('height') or element.get_attribute('naturalHeight') or '100'
                            if int(width) >= 100 and int(height) >= 100:
                                href = element.find_element(By.XPATH, "./ancestor::a").get_attribute('href') if element.find_elements(By.XPATH, "./ancestor::a") else ''
                                if href and (album_id in href or '/videos/' in href):
                                    self.driver.execute_script("arguments[0].click();", element)
                                    self.log("Selected first media (image or video)")
                                    time.sleep(self.delay_map[self.speed]["grab"])
                                    return True
                except:
                    continue
            self.log("Could not find first media", "ERROR")
            return False
        except Exception as e:
            self.log(f"Error selecting first media: {e}", "ERROR")
            return False

    def get_album_title(self):
        title_selectors = [
            "h1",
            "[data-pagelet='MediaViewerPhoto'] h1",
            "[role='main'] h1",
            "div[dir='auto'] h1",
            "span[dir='auto']"
        ]
        
        for selector in title_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.get_attribute('textContent').strip()
                    if text and 3 < len(text) < 100:
                        self.log(f"Found album title: {text}")
                        return text
            except:
                continue
        
        fallback_title = f"Facebook_Album_{int(time.time())}"
        self.log(f"Could not find album title, using: {fallback_title}", "WARNING")
        return fallback_title

    def get_media_url(self):
        try:
            current_url = self.driver.current_url
            media_type = 'video' if '/videos/' in current_url else 'image'
            
            if media_type == 'image':
                try:
                    image_selectors = [
                        "img[data-visualcompletion='media-vc-image']",
                        "img[src*='scontent']",
                        "img[src*='fbcdn']"
                    ]
                    for selector in image_selectors:
                        image = self.driver.find_element(By.CSS_SELECTOR, selector)
                        image_url = image.get_attribute('src')
                        if image_url and ('scontent' in image_url or 'fbcdn' in image_url):
                            self.log(f"Found image URL: {image_url}")
                            return image_url, media_type, current_url
                except:
                    pass
            else:
                try:
                    video_selectors = [
                        "video[src*='fbcdn']",
                        "video[data-sigil='inline-video']",
                        "video[src*='video-ak']",
                        "[data-video-id] video"
                    ]
                    for selector in video_selectors:
                        video = self.driver.find_element(By.CSS_SELECTOR, selector)
                        video_url = video.get_attribute('src')
                        if video_url and ('fbcdn' in video_url or 'video-ak' in video_url):
                            self.log(f"Found video URL: {video_url}")
                            return video_url, media_type, current_url
                except:
                    try:
                        self.driver.execute_script("document.querySelector('video').play();")
                        time.sleep(self.delay_map[self.speed]["grab"])
                        video = self.driver.find_element(By.CSS_SELECTOR, "video")
                        video_url = video.get_attribute('src')
                        if video_url:
                            self.log(f"Found video URL after playback attempt: {video_url}")
                            return video_url, media_type, current_url
                    except:
                        pass
            
            self.log(f"Invalid or missing media URL for {current_url}", "ERROR")
            return None, None, None
        except Exception as e:
            self.log(f"Failed to get media URL for {self.driver.current_url}: {e}", "ERROR")
            return None, None, None

    def navigate_to_media(self, target_url):
        try:
            self.driver.get(target_url)
            time.sleep(self.delay_map[self.speed]["grab"])
            if 'login' in self.driver.current_url.lower() or 'checkpoint' in self.driver.current_url.lower() or 'two_step_verification' in self.driver.current_url.lower():
                self.log("Login or verification required after navigating to media URL", "ERROR")
                return False
            self.log(f"Navigated to media URL: {target_url}")
            return True
        except Exception as e:
            self.log(f"Failed to navigate to media URL: {e}", "ERROR")
            return False

    def collect_media_urls(self, album_url, max_media=2000, url_file_path=None, resume_url=None):
        media_urls = self.load_urls_from_file(url_file_path) if url_file_path else []
        current_media = len(media_urls)
        album_id = parse_qs(urlparse(album_url).query).get('set', [''])[0]
        max_stuck_attempts = 5
        stuck_count = 0
        last_url_count = len(media_urls)
        
        self.log(f"Collecting up to {max_media} media URLs (images and videos)...")
        self.update_progress(current_media, max_media, "Collecting media URLs...")
        
        if resume_url:
            self.log(f"Resuming from URL: {resume_url}")
            if not self.navigate_to_media(resume_url):
                self.log("Failed to resume from last URL, starting from album", "WARNING")
                if not self.select_first_media(album_url):
                    if media_urls and url_file_path:
                        self.save_urls_to_file(media_urls, url_file_path)
                    return media_urls
        elif not self.select_first_media(album_url):
            if media_urls and url_file_path:
                self.save_urls_to_file(media_urls, url_file_path)
            return media_urls
        
        while current_media < max_media and not self.stop_requested:
            try:
                media_url, media_type, original_url = self.get_media_url()
                if media_url and media_url not in [url for url, _, _ in media_urls] and original_url not in [o_url for _, _, o_url in media_urls]:
                    media_urls.append((media_url, media_type, original_url))
                    self.log(f"Collected {media_type} URL {len(media_urls)}/{max_media}: {media_url}")
                    self.update_progress(len(media_urls), max_media, f"Collected {len(media_urls)} URLs")
                    if url_file_path:
                        self.save_urls_to_file(media_urls, url_file_path)
                    stuck_count = 0
                else:
                    if media_url and original_url in [o_url for _, _, o_url in media_urls]:
                        self.log(f"Skipped duplicate media URL: {original_url}", "INFO")
                    stuck_count += 1
                
                if stuck_count >= max_stuck_attempts:
                    self.log(f"Stuck at {len(media_urls)} URLs, reloading page...", "WARNING")
                    self.driver.refresh()
                    time.sleep(self.delay_map[self.speed]["grab"])
                    stuck_count = 0
                    if resume_url and not self.navigate_to_media(resume_url):
                        if not self.select_first_media(album_url):
                            self.log("Failed to reselect first media after reload", "ERROR")
                            break
                    elif not self.select_first_media(album_url):
                        self.log("Failed to reselect first media after reload", "ERROR")
                        break
                
                if len(media_urls) == last_url_count:
                    stuck_count += 1
                else:
                    last_url_count = len(media_urls)
                
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.RIGHT)
                    time.sleep(self.delay_map[self.speed]["grab"])
                    
                    media_elements = self.driver.find_elements(By.CSS_SELECTOR, "img[data-visualcompletion='media-vc-image'], video[src*='fbcdn'], video[data-sigil='inline-video'], video[src*='video-ak']")
                    if not media_elements:
                        self.log("No media elements found, attempting to detect end of album...", "WARNING")
                        time.sleep(self.delay_map[self.speed]["grab"])
                        if not self.driver.find_elements(By.CSS_SELECTOR, "img[data-visualcompletion='media-vc-image'], video[src*='fbcdn'], video[data-sigil='inline-video'], video[src*='video-ak']"):
                            self.log("Reached end of album", "INFO")
                            break
                except:
                    self.log("Failed to navigate to next media, retrying...", "WARNING")
                    stuck_count += 1
                
                current_media += 1
                
            except Exception as e:
                self.log(f"Error during URL collection: {e}", "WARNING")
                stuck_count += 1
                if stuck_count >= max_stuck_attempts:
                    self.log("Too many errors, stopping URL collection", "ERROR")
                    break
                self.driver.refresh()
                time.sleep(self.delay_map[self.speed]["grab"])
        
        if url_file_path and media_urls:
            self.save_urls_to_file(media_urls, url_file_path)
        self.log(f"Finished collecting {len(media_urls)} media URLs")
        return media_urls

    def download_media_from_url(self, media_url, file_path, media_type):
        try:
            file_path = os.path.normpath(file_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(media_url, headers=headers, stream=True)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                self.log(f"Successfully saved {media_type}: {os.path.basename(file_path)}")
                return True
            else:
                self.log(f"Failed to download {media_type} from URL: Status {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Failed to download {media_type}: {e}", "ERROR")
            return False

    def find_resume_index(self, media_urls, main_folder, album_folder):
        folder_path = os.path.normpath(os.path.join(main_folder, album_folder))
        last_file = 0
        for i, (media_url, media_type, original_url) in enumerate(media_urls, 1):
            file_ext = 'mp4' if media_type == 'video' else 'jpg'
            file_path = os.path.normpath(os.path.join(folder_path, f"{i:03d}.{file_ext}"))
            if not os.path.exists(file_path):
                return i - 1
            last_file = i
        return last_file

    def download_media(self, media_urls, main_folder, album_folder, max_media=2000):
        resume_index = self.find_resume_index(media_urls, main_folder, album_folder)
        if resume_index > 0:
            self.log(f"Resuming from media {resume_index + 1}/{len(media_urls)}")
        
        successful_downloads = resume_index
        total_media = min(len(media_urls), max_media)
        
        self.log(f"Starting download of {total_media} media items")
        self.update_progress(resume_index, total_media, "Starting download...")
        
        folder_path = os.path.normpath(os.path.join(main_folder, album_folder))
        
        for i, (media_url, media_type, original_url) in enumerate(media_urls[resume_index:], resume_index + 1):
            if self.stop_requested:
                self.log("Download stopped by user", "WARNING")
                break
                
            file_ext = 'mp4' if media_type == 'video' else 'jpg'
            file_name = f"{i:03d}.{file_ext}"
            file_path = os.path.normpath(os.path.join(folder_path, file_name))
            
            if os.path.exists(file_path):
                self.log(f"Skipping {file_name}, already exists")
                successful_downloads += 1
                self.update_progress(i, total_media, f"Skipped {file_name}")
                continue
            
            self.log(f"Saving {media_type} {i}/{total_media}: {file_name} from {media_url}")
            self.update_progress(i-1, total_media, f"Saving {file_name}")
            
            if self.download_media_from_url(media_url, file_path, media_type):
                successful_downloads += 1
            else:
                self.log(f"Failed to save {media_type} {i}/{total_media}", "WARNING")
            
            time.sleep(self.delay_map[self.speed]["download"])
        
        self.log(f"Download completed: {successful_downloads}/{total_media} media items saved")
        self.update_progress(total_media, total_media, "Download completed")
        return successful_downloads

    def grab_links_only(self, album_url, main_folder, album_title, max_media=2000):
        try:
            self.log(f"Starting to grab links for album: {album_url}")
            self.update_progress(0, 100, "Initializing browser...")
            
            self.setup_driver()
            if self.stop_requested:
                return False
            
            self.update_progress(10, 100, "Waiting for login...")
            if not self.wait_for_login(album_url):
                return False
            
            if self.stop_requested:
                return False
            
            current_url = self.driver.current_url
            if 'login' in current_url.lower() or 'checkpoint' in current_url.lower() or 'two_step_verification' in current_url.lower():
                self.log("Still on login or verification page after timeout.", "ERROR")
                return False
            
            folder_path = self.create_folder(main_folder, album_title)
            url_file_path = os.path.normpath(os.path.join(folder_path, "media_urls.json"))
            
            self.update_progress(30, 100, "Collecting media URLs...")
            media_urls = self.collect_media_urls(album_url, max_media, url_file_path)
            if media_urls:
                self.log(f"Successfully saved {len(media_urls)} URLs")
                self.update_progress(100, 100, "URL collection completed!")
                return True
            else:
                self.log("No media URLs collected", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error during link grabbing: {e}", "ERROR")
            return False
        finally:
            self.close()

    def resume_grab_links(self, album_url, json_file_path, max_media=2000):
        try:
            self.log(f"Resuming link grabbing for album: {album_url}")
            self.update_progress(0, 100, "Initializing browser...")
            
            self.setup_driver()
            if self.stop_requested:
                return False
            
            self.update_progress(10, 100, "Waiting for login...")
            if not self.wait_for_login(album_url):
                return False
            
            if self.stop_requested:
                return False
            
            current_url = self.driver.current_url
            if 'login' in current_url.lower() or 'checkpoint' in current_url.lower() or 'two_step_verification' in current_url.lower():
                self.log("Still on login or verification page after timeout.", "ERROR")
                return False
            
            media_urls = self.load_urls_from_file(json_file_path)
            
            if not media_urls:
                self.log("No URLs found in JSON file to resume from", "ERROR")
                return False
            
            last_url = media_urls[-1][2]  # Get the last original URL
            self.update_progress(30, 100, "Resuming media URL collection...")
            media_urls = self.collect_media_urls(album_url, max_media, json_file_path, resume_url=last_url)
            if media_urls:
                self.log(f"Successfully saved {len(media_urls)} URLs")
                self.update_progress(100, 100, "URL collection completed!")
                return True
            else:
                self.log("No additional URLs collected", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error during resume link grabbing: {e}", "ERROR")
            return False
        finally:
            self.close()

    def download_from_json(self, json_file_path, main_folder, max_media=2000):
        try:
            media_urls = self.load_urls_from_file(json_file_path)
            if not media_urls:
                self.log("No URLs found in JSON file", "ERROR")
                return False
            
            # Extract album_title from the JSON file's parent directory
            album_title = os.path.basename(os.path.dirname(json_file_path))
            if not album_title:
                album_title = self.remove_invalid_characters(f"Album_{int(time.time())}")
                self.log(f"Could not determine album title from JSON path, using: {album_title}", "WARNING")
            
            self.update_progress(90, 100, "Starting media downloads...")
            successful_downloads = self.download_media(media_urls, main_folder, album_title, max_media)
            
            self.log(f"Download completed. Saved {successful_downloads} media items")
            self.update_progress(100, 100, "Download completed!")
            return successful_downloads > 0
            
        except Exception as e:
            self.log(f"Error during download from JSON: {e}", "ERROR")
            return False

    def stop_scraping(self):
        self.stop_requested = True
        self.log("Stop requested by user", "INFO")

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                self.log("Browser closed successfully")
            except Exception as e:
                self.log(f"Error closing browser: {e}", "ERROR")
            self.driver = None

    def scrape_album(self, album_url, main_folder="downloaded_albums", max_media=2000):
        try:
            self.log(f"Starting scrape of album: {album_url}")
            self.update_progress(0, 100, "Initializing browser...")
            
            self.setup_driver()
            if self.stop_requested:
                return False
            
            self.update_progress(10, 100, "Waiting for login...")
            if not self.wait_for_login(album_url):
                return False
            
            if self.stop_requested:
                return False
            
            current_url = self.driver.current_url
            if 'login' in current_url.lower() or 'checkpoint' in current_url.lower() or 'two_step_verification' in current_url.lower():
                self.log("Still on login or verification page after timeout.", "ERROR")
                return False
            
            self.update_progress(20, 100, "Extracting album information...")
            album_title = self.get_album_title()
            album_title = self.remove_invalid_characters(album_title)
            
            folder_path = self.create_folder(main_folder, album_title)
            url_file_path = os.path.normpath(os.path.join(folder_path, "media_urls.json"))
            
            self.update_progress(30, 100, "Collecting media URLs...")
            media_urls = self.collect_media_urls(album_url, max_media, url_file_path)
            if not media_urls:
                self.log("No media URLs collected", "ERROR")
                return False
            
            if self.stop_requested:
                return False
            
            self.update_progress(90, 100, "Starting media downloads...")
            successful_downloads = self.download_media(media_urls, main_folder, album_title, max_media)
            
            self.log(f"Scraping completed. Saved {successful_downloads} media items to {folder_path}")
            self.update_progress(100, 100, "Scraping completed!")
            return successful_downloads > 0
            
        except Exception as e:
            self.log(f"Error during scraping: {e}", "ERROR")
            return False
        finally:
            self.close()

class ModernButton(tk.Frame):
    def __init__(self, parent, text, command=None, bg_color="#FF1493", hover_color="#FF69B4", text_color="white", **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)
        
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.animation_id = None
        
        self.button = tk.Label(self, text=text, bg=bg_color, fg=text_color, 
                              font=('Segoe UI', 10, 'bold'), relief='flat',
                              padx=20, pady=8, cursor='hand2')
        self.button.pack(fill='both', expand=True)
        
        self.button.bind('<Button-1>', self._on_click)
        self.button.bind('<Enter>', self._on_enter)
        self.button.bind('<Leave>', self._on_leave)
        
    def _on_click(self, event):
        if self.command:
            self.command()
    
    def _on_enter(self, event):
        self.is_hovered = True
        self._animate_color(self.bg_color, self.hover_color)
    
    def _on_leave(self, event):
        self.is_hovered = False
        self._animate_color(self.hover_color, self.bg_color)
    
    def _animate_color(self, start_color, end_color):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        # Simple color animation
        steps = 10
        start_rgb = self._hex_to_rgb(start_color)
        end_rgb = self._hex_to_rgb(end_color)
        
        def animate_step(step):
            if step <= steps:
                ratio = step / steps
                current_rgb = [
                    int(start_rgb[i] + (end_rgb[i] - start_rgb[i]) * ratio)
                    for i in range(3)
                ]
                current_color = self._rgb_to_hex(current_rgb)
                self.button.config(bg=current_color)
                self.animation_id = self.after(20, lambda: animate_step(step + 1))
        
        animate_step(0)
    
    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def config_state(self, state):
        if state == "disabled":
            self.button.config(bg="#333333", fg="#666666", cursor='')
            self.button.unbind('<Button-1>')
            self.button.unbind('<Enter>')
            self.button.unbind('<Leave>')
        else:
            self.button.config(bg=self.bg_color, fg=self.text_color, cursor='hand2')
            self.button.bind('<Button-1>', self._on_click)
            self.button.bind('<Enter>', self._on_enter)
            self.button.bind('<Leave>', self._on_leave)

class AnimatedProgressBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1a1a1a', **kwargs)
        
        self.canvas = tk.Canvas(self, height=20, bg='#2a2a2a', highlightthickness=0)
        self.canvas.pack(fill='x', padx=5, pady=5)
        
        self.progress = 0
        self.animation_id = None
        
        self.bind('<Configure>', self._on_resize)
    
    def _on_resize(self, event):
        self.update_display()
    
    def set_progress(self, value):
        target = max(0, min(100, value))
        self.animate_to(target)
    
    def animate_to(self, target):
        if self.animation_id:
            self.after_cancel(self.animation_id)
        
        def animate_step():
            diff = target - self.progress
            if abs(diff) < 0.5:
                self.progress = target
                self.update_display()
                return
            
            self.progress += diff * 0.1
            self.update_display()
            self.animation_id = self.after(16, animate_step)
        
        animate_step()
    
    def update_display(self):
        self.canvas.delete('all')
        if self.canvas.winfo_width() <= 1:
            return
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Background
        self.canvas.create_rectangle(2, 2, width-2, height-2, fill='#333333', outline='#555555')
        
        # Progress fill with gradient effect
        progress_width = (width - 4) * (self.progress / 100)
        if progress_width > 0:
            # Create gradient effect
            for i in range(int(progress_width)):
                ratio = i / max(1, progress_width)
                r = int(255 * (1 - ratio) + 255 * ratio)
                g = int(20 * (1 - ratio) + 105 * ratio)
                b = int(147 * (1 - ratio) + 180 * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                
                self.canvas.create_line(2 + i, 2, 2 + i, height-2, fill=color, width=1)

class FacebookScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Album Scraper - Modern Edition")
        self.root.geometry("900x600")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(True, True)
        
        # Configure modern style
        self.setup_styles()
        
        self.scraper = None
        self.scraping_thread = None
        self.is_scraping = False
        
        # Show warning popup before main GUI
        self.show_warning_popup()
        
        self.setup_gui()
        self.animate_startup()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Modern.TFrame', background='#1a1a1a', relief='flat')
        style.configure('Modern.TLabel', background='#1a1a1a', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Modern.TEntry', fieldbackground='#2a2a2a', bordercolor='#FF1493', 
                       insertcolor='#ffffff', foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Modern.TCombobox', fieldbackground='#2a2a2a', bordercolor='#FF1493',
                       foreground='#ffffff', font=('Segoe UI', 10))
        style.configure('Modern.TCheckbutton', background='#1a1a1a', foreground='#ffffff',
                       focuscolor='#FF1493', font=('Segoe UI', 10))
        
        # Map hover effects
        style.map('Modern.TEntry', focuscolor=[('!focus', '#FF1493')])
        style.map('Modern.TCombobox', focuscolor=[('!focus', '#FF1493')])
        
    def show_warning_popup(self):
        warning_window = tk.Toplevel(self.root)
        warning_window.title("⚠️ IMPORTANT WARNING")
        warning_window.geometry("400x250")
        warning_window.configure(bg='#1a1a1a')
        warning_window.resizable(False, False)
        warning_window.transient(self.root)
        warning_window.grab_set()
        
        # Center the warning window
        warning_window.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (250 // 2)
        warning_window.geometry(f"400x250+{x}+{y}")
        
        warning_frame = tk.Frame(warning_window, bg='#1a1a1a', relief='solid', bd=1)
        warning_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        warning_header = tk.Frame(warning_frame, bg='#FF4444')
        warning_header.pack(fill='x')
        
        warning_title = tk.Label(warning_header, text="⚠️ IMPORTANT WARNING", 
                               bg='#FF4444', fg='white', 
                               font=('Segoe UI', 12, 'bold'))
        warning_title.pack(pady=5)
        
        warning_content = tk.Frame(warning_frame, bg='#1a1a1a')
        warning_content.pack(fill='both', expand=True, padx=10, pady=10)
        
        warning_text = ("This tool is for educational purposes only!\n\n"
                       "Please ensure you have permission to download content and\n"
                       "comply with Facebook's Terms of Service and applicable laws.\n\n"
                       "By continuing, you acknowledge that you understand and agree\n"
                       "to use this tool responsibly.")
        
        warning_label = tk.Label(warning_content, text=warning_text, 
                               bg='#1a1a1a', fg='#ffaaaa', 
                               font=('Segoe UI', 10), justify='center')
        warning_label.pack(expand=True)
        
        button_frame = tk.Frame(warning_frame, bg='#1a1a1a')
        button_frame.pack(fill='x', pady=10)
        
        accept_button = ModernButton(button_frame, text="I Understand, Proceed", 
                                  command=warning_window.destroy,
                                  bg_color="#FF1493", hover_color="#FF69B4")
        accept_button.pack(pady=5)
        
        # Prevent main window interaction until warning is dismissed
        self.root.wait_window(warning_window)
    
    def setup_gui(self):
        # Main container with paned window for resizable columns
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg='#0a0a0a', sashwidth=5, sashrelief='raised')
        self.paned_window.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left column for header, settings, buttons, and progress
        left_column = tk.Frame(self.paned_window, bg='#0a0a0a', width=400)
        self.paned_window.add(left_column, minsize=300, width=400)
        
        # Right column for log
        right_column = tk.Frame(self.paned_window, bg='#0a0a0a')
        self.paned_window.add(right_column, minsize=300)
        
        # Header
        self.setup_header(left_column)
        
        # Settings section
        self.setup_settings(left_column)
        
        # Action buttons
        self.setup_buttons(left_column)
        
        # Progress section
        self.setup_progress(left_column)
        
        # Log section
        self.setup_log(right_column)
    
    def setup_header(self, parent):
        header_frame = tk.Frame(parent, bg='#0a0a0a')
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Animated title
        self.title_label = tk.Label(header_frame, text="FACEBOOK ALBUM SCRAPER", 
                                   bg='#0a0a0a', fg='#FF1493', 
                                   font=('Segoe UI', 18, 'bold'), cursor='hand2')
        self.title_label.pack()
        
        subtitle = tk.Label(header_frame, text="Modern Edition - Extract with Style", 
                           bg='#0a0a0a', fg='#FF69B4', 
                           font=('Segoe UI', 10, 'italic'))
        subtitle.pack(pady=(2, 0))
        
        # Animated underline
        self.underline_canvas = tk.Canvas(header_frame, height=2, bg='#0a0a0a', highlightthickness=0)
        self.underline_canvas.pack(fill='x', pady=(5, 0))
        
    def setup_settings(self, parent):
        settings_frame = tk.Frame(parent, bg='#1a1a1a', relief='solid', bd=1)
        settings_frame.pack(fill='x', pady=(0, 10))
        
        # Header
        settings_header = tk.Frame(settings_frame, bg='#FF1493')
        settings_header.pack(fill='x')
        
        settings_title = tk.Label(settings_header, text="⚙️ CONFIGURATION", 
                                bg='#FF1493', fg='white', 
                                font=('Segoe UI', 10, 'bold'))
        settings_title.pack(pady=5)
        
        # Content
        settings_content = tk.Frame(settings_frame, bg='#1a1a1a')
        settings_content.pack(fill='both', expand=True, padx=10, pady=10)
        
        # URL input
        url_frame = tk.Frame(settings_content, bg='#1a1a1a')
        url_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(url_frame, text="Facebook Album URL:", 
                bg='#1a1a1a', fg='#ffffff', 
                font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.url_var = tk.StringVar()
        url_entry = tk.Entry(url_frame, textvariable=self.url_var, 
                           bg='#2a2a2a', fg='#ffffff', insertbackground='#FF1493',
                           font=('Segoe UI', 9), relief='flat', bd=3)
        url_entry.pack(fill='x', pady=(3, 0), ipady=6)
        
        # Folder input
        folder_frame = tk.Frame(settings_content, bg='#1a1a1a')
        folder_frame.pack(fill='x', pady=(0, 8))
        
        tk.Label(folder_frame, text="Download Folder:", 
                bg='#1a1a1a', fg='#ffffff', 
                font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        folder_input_frame = tk.Frame(folder_frame, bg='#1a1a1a')
        folder_input_frame.pack(fill='x', pady=(3, 0))
        
        self.folder_var = tk.StringVar(value="downloaded_albums")
        folder_entry = tk.Entry(folder_input_frame, textvariable=self.folder_var,
                              bg='#2a2a2a', fg='#ffffff', insertbackground='#FF1493',
                              font=('Segoe UI', 9), relief='flat', bd=3)
        folder_entry.pack(side='left', fill='x', expand=True, ipady=6)
        
        browse_btn = ModernButton(folder_input_frame, text="Browse", 
                                command=self.browse_folder, width=60,
                                bg_color="#FF1493", hover_color="#FF69B4")
        browse_btn.pack(side='right', padx=(5, 0))
        
        # Settings row
        settings_row = tk.Frame(settings_content, bg='#1a1a1a')
        settings_row.pack(fill='x', pady=(0, 8))
        
        # Media count
        count_frame = tk.Frame(settings_row, bg='#1a1a1a')
        count_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        tk.Label(count_frame, text="Media Items:", 
                bg='#1a1a1a', fg='#ffffff', 
                font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.media_count_var = tk.StringVar(value="2000")
        count_entry = tk.Entry(count_frame, textvariable=self.media_count_var,
                             bg='#2a2a2a', fg='#ffffff', insertbackground='#FF1493',
                             font=('Segoe UI', 9), relief='flat', bd=3, width=10)
        count_entry.pack(anchor='w', pady=(3, 0), ipady=6)
        
        # Speed
        speed_frame = tk.Frame(settings_row, bg='#1a1a1a')
        speed_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(speed_frame, text="Speed:", 
                bg='#1a1a1a', fg='#ffffff', 
                font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        
        self.speed_var = tk.StringVar(value="Medium")
        speed_frame_inner = tk.Frame(speed_frame, bg='#2a2a2a')
        speed_frame_inner.pack(anchor='w', pady=(3, 0))
        
        for i, speed in enumerate(["Slow", "Medium", "Fast"]):
            color = "#FF1493" if speed == "Medium" else "#666666"
            btn = tk.Radiobutton(speed_frame_inner, text=speed, variable=self.speed_var, 
                               value=speed, bg='#2a2a2a', fg=color, 
                               selectcolor='#FF1493', activebackground='#2a2a2a',
                               font=('Segoe UI', 8), relief='flat')
            btn.pack(side='left', padx=(0, 10))
        
        # Options
        options_frame = tk.Frame(settings_content, bg='#1a1a1a')
        options_frame.pack(fill='x')
        
        self.headless_var = tk.BooleanVar()
        headless_check = tk.Checkbutton(options_frame, text="Run in headless mode (hide browser)",
                                      variable=self.headless_var, bg='#1a1a1a', fg='#ffffff',
                                      selectcolor='#FF1493', activebackground='#1a1a1a',
                                      font=('Segoe UI', 9), relief='flat')
        headless_check.pack(anchor='w')
    
    def setup_buttons(self, parent):
        button_frame = tk.Frame(parent, bg='#0a0a0a')
        button_frame.pack(fill='x', pady=(0, 10))
        
        # First row of buttons
        button_row1 = tk.Frame(button_frame, bg='#0a0a0a')
        button_row1.pack(fill='x')
        
        self.start_button = ModernButton(button_row1, text="🚀 START SCRAPING", 
                                       command=self.start_scraping, 
                                       bg_color="#FF1493", hover_color="#FF69B4")
        self.start_button.pack(side='left', padx=(0, 5), pady=(0, 5), fill='y')
        
        self.grab_button = ModernButton(button_row1, text="🔗 GRAB LINKS", 
                                      command=self.grab_links,
                                      bg_color="#9932CC", hover_color="#BA55D3")
        self.grab_button.pack(side='left', padx=(0, 5), pady=(0, 5), fill='y')
        
        self.resume_button = ModernButton(button_row1, text="🔄 RESUME GRAB", 
                                        command=self.resume_grab_links,
                                        bg_color="#FF6347", hover_color="#FF7F50")
        self.resume_button.pack(side='left', padx=(0, 5), pady=(0, 5), fill='y')
        
        # Second row of buttons
        button_row2 = tk.Frame(button_frame, bg='#0a0a0a')
        button_row2.pack(fill='x')
        
        self.download_button = ModernButton(button_row2, text="📥 DOWNLOAD JSON", 
                                          command=self.download_from_json,
                                          bg_color="#32CD32", hover_color="#90EE90")
        self.download_button.pack(side='left', padx=(0, 5), pady=(0, 5), fill='y')
        
        self.stop_button = ModernButton(button_row2, text="⏹️ STOP", 
                                      command=self.stop_scraping,
                                      bg_color="#DC143C", hover_color="#F08080")
        self.stop_button.pack(side='left', padx=(0, 5), pady=(0, 5), fill='y')
        self.stop_button.config_state("disabled")
        
        self.clear_button = ModernButton(button_row2, text="🗑️ CLEAR LOG", 
                                       command=self.clear_log,
                                       bg_color="#696969", hover_color="#808080")
        self.clear_button.pack(side='left', padx=(0, 5), pady=(0, 5), fill='y')
    
    def setup_log(self, parent):
        log_frame = tk.Frame(parent, bg='#1a1a1a', relief='solid', bd=1)
        log_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Header
        log_header = tk.Frame(log_frame, bg='#4169E1')
        log_header.pack(fill='x')
        
        log_title = tk.Label(log_header, text="📋 ACTIVITY LOG", 
                           bg='#4169E1', fg='white', 
                           font=('Segoe UI', 10, 'bold'))
        log_title.pack(pady=5)
        
        # Log content
        log_content = tk.Frame(log_frame, bg='#0f0f0f')
        log_content.pack(fill='both', expand=True, padx=1, pady=1)
        
        self.log_text = scrolledtext.ScrolledText(log_content, height=10, 
                                                bg='#0f0f0f', fg='#00ff00',
                                                insertbackground='#FF1493',
                                                font=('Consolas', 8),
                                                relief='flat', bd=0)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configure text tags for colored output
        self.log_text.tag_config("INFO", foreground="#00ff00")
        self.log_text.tag_config("WARNING", foreground="#ffaa00")
        self.log_text.tag_config("ERROR", foreground="#ff4444")
        self.log_text.tag_config("SUCCESS", foreground="#ff69b4")
    
    def setup_progress(self, parent):
        progress_frame = tk.Frame(parent, bg='#1a1a1a', relief='solid', bd=1)
        progress_frame.pack(fill='x')
        
        # Header
        progress_header = tk.Frame(progress_frame, bg='#FF1493')
        progress_header.pack(fill='x')
        
        progress_title = tk.Label(progress_header, text="📊 PROGRESS", 
                                bg='#FF1493', fg='white', 
                                font=('Segoe UI', 10, 'bold'))
        progress_title.pack(pady=5)
        
        # Progress content
        progress_content = tk.Frame(progress_frame, bg='#1a1a1a')
        progress_content.pack(fill='x', padx=10, pady=10)
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        self.progress_label = tk.Label(progress_content, textvariable=self.progress_var,
                                     bg='#1a1a1a', fg='#ffffff', 
                                     font=('Segoe UI', 9))
        self.progress_label.pack(anchor='w')
        
        self.progress_bar = AnimatedProgressBar(progress_content)
        self.progress_bar.pack(fill='x', pady=(5, 0))
        
    def animate_startup(self):
        # Animate the underline
        def animate_underline():
            width = self.underline_canvas.winfo_width()
            if width > 1:
                self.underline_canvas.delete('all')
                # Create animated gradient line
                for i in range(0, width, 2):
                    ratio = i / width
                    r = int(255 * ratio)
                    g = int(20 + (105 * ratio))
                    b = int(147 + (33 * ratio))
                    color = f"#{r:02x}{g:02x}{b:02x}"
                    self.underline_canvas.create_line(i, 1, i+1, 1, fill=color, width=2)
        
        self.root.after(100, animate_underline)
        
        # Animate title color
        def animate_title():
            colors = ['#FF1493', '#FF69B4', '#FF1493', '#DA70D6', '#FF1493']
            for i, color in enumerate(colors):
                self.root.after(i * 500, lambda c=color: self.title_label.config(fg=c))
        
        animate_title()
    
    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
    
    def select_json_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=self.folder_var.get(),
            title="Select JSON File",
            filetypes=[("JSON files", "*.json")]
        )
        return file_path
    
    def log_message(self, message):
        # Determine message type and color
        if "[ERROR]" in message:
            tag = "ERROR"
        elif "[WARNING]" in message:
            tag = "WARNING" 
        elif "✅" in message or "completed successfully" in message:
            tag = "SUCCESS"
        else:
            tag = "INFO"
        
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current, total, message=""):
        if total > 0:
            progress = (current / total) * 100
            self.progress_bar.set_progress(progress)
        
        if message:
            self.progress_var.set(f"{message} ({current}/{total})")
        else:
            self.progress_var.set(f"Progress: {current}/{total}")
        
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log_message("📋 Log cleared - Ready for new session")
    
    def validate_inputs(self, require_url=True):
        url = self.url_var.get().strip()
        folder = self.folder_var.get().strip()
        media_count = self.media_count_var.get().strip()
        speed = self.speed_var.get().strip()
        
        if require_url and not url:
            messagebox.showerror("Error", "Please enter a Facebook album URL")
            return False
        if require_url and not url.startswith(('http://', 'https://')):
            messagebox.showerror("Error", "Please enter a valid URL starting with http:// or https://")
            return False
        if not folder:
            messagebox.showerror("Error", "Please specify a download folder")
            return False
        if speed not in ["Slow", "Medium", "Fast"]:
            messagebox.showerror("Error", "Please select a valid speed (Slow, Medium, Fast)")
            return False
        try:
            max_media = int(media_count)
            if max_media <= 0:
                raise ValueError
            return max_media
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for media count")
            return False
    
    def start_scraping(self):
        max_media = self.validate_inputs()
        if not max_media:
            return
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
        
        # Custom confirmation dialog
        result = messagebox.askyesno("🚀 Confirm Scraping", 
                                   "Ready to launch the scraping mission?\n\n"
                                   "Please ensure you have permission to download "
                                   "the content and comply with Facebook's Terms of Service.\n\n"
                                   "Let's go! 🎯")
        if not result:
            return
        
        self.set_scraping_state(True)
        self.log_message("🚀 Starting scraping mission...")
        self.progress_bar.set_progress(0)
        self.progress_var.set("Initializing...")
        
        self.scraping_thread = threading.Thread(
            target=self.run_scraping, 
            args=(max_media,), 
            daemon=True
        )
        self.scraping_thread.start()
    
    def grab_links(self):
        max_media = self.validate_inputs()
        if not max_media:
            return
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
        
        result = messagebox.askyesno("🔗 Confirm Link Grabbing", 
                                   "Ready to grab those links?\n\n"
                                   "This will collect media URLs without downloading.\n"
                                   "Perfect for batch processing later! 📎")
        if not result:
            return
        
        self.set_scraping_state(True)
        self.log_message("🔗 Starting link collection mission...")
        self.progress_bar.set_progress(0)
        self.progress_var.set("Initializing...")
        
        self.scraping_thread = threading.Thread(
            target=self.run_grab_links, 
            args=(max_media,), 
            daemon=True
        )
        self.scraping_thread.start()
    
    def resume_grab_links(self):
        max_media = self.validate_inputs()
        if not max_media:
            return
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
        
        json_file_path = self.select_json_file()
        if not json_file_path:
            messagebox.showerror("Error", "No JSON file selected")
            return
        
        result = messagebox.askyesno("🔄 Confirm Resume", 
                                   "Ready to resume link grabbing?\n\n"
                                   "This will continue from where you left off.\n"
                                   "Smart and efficient! 🧠")
        if not result:
            return
        
        self.set_scraping_state(True)
        self.log_message("🔄 Resuming link collection mission...")
        self.progress_bar.set_progress(0)
        self.progress_var.set("Initializing...")
        
        self.scraping_thread = threading.Thread(
            target=self.run_resume_grab_links, 
            args=(max_media, json_file_path), 
            daemon=True
        )
        self.scraping_thread.start()
    
    def download_from_json(self):
        max_media = self.validate_inputs(require_url=False)
        if not max_media:
            return
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
        
        json_file_path = self.select_json_file()
        if not json_file_path:
            messagebox.showerror("Error", "No JSON file selected")
            return
        
        result = messagebox.askyesno("📥 Confirm Download", 
                                   "Ready to download from JSON?\n\n"
                                   "This will download all media from your saved links.\n"
                                   "Time to collect the treasures! 💎")
        if not result:
            return
        
        self.set_scraping_state(True)
        self.log_message("📥 Starting download from JSON...")
        self.progress_bar.set_progress(0)
        self.progress_var.set("Initializing...")
        
        self.scraping_thread = threading.Thread(
            target=self.run_download_from_json, 
            args=(max_media, json_file_path), 
            daemon=True
        )
        self.scraping_thread.start()
    
    def stop_scraping(self):
        if self.scraper:
            self.scraper.stop_scraping()
            self.log_message("⏹️ Stop signal sent...")
    
    def set_scraping_state(self, is_scraping):
        self.is_scraping = is_scraping
        
        if is_scraping:
            self.start_button.config_state("disabled")
            self.grab_button.config_state("disabled")
            self.resume_button.config_state("disabled")
            self.download_button.config_state("disabled")
            self.stop_button.config_state("normal")
            self.clear_button.config_state("disabled")
        else:
            self.start_button.config_state("normal")
            self.grab_button.config_state("normal")
            self.resume_button.config_state("normal")
            self.download_button.config_state("normal")
            self.stop_button.config_state("disabled")
            self.clear_button.config_state("normal")
            self.progress_var.set("Ready for next mission...")
    
    def run_scraping(self, max_media):
        try:
            self.scraper = FacebookAlbumScraper(
                headless=self.headless_var.get(),
                progress_callback=self.update_progress,
                log_callback=self.log_message,
                speed=self.speed_var.get()
            )
            
            url = self.url_var.get().strip()
            folder = self.folder_var.get().strip()
            
            success = self.scraper.scrape_album(url, folder, max_media)
            
            if success:
                self.log_message("✅ Mission accomplished! Scraping completed successfully! 🎉")
                messagebox.showinfo("🎉 Success!", f"Mission completed successfully!\n\nMedia saved to: {folder}\n\nYou're awesome! 🌟")
            else:
                self.log_message("❌ Mission failed. Check the logs for details.")
                messagebox.showerror("💥 Mission Failed", "Something went wrong during scraping.\nCheck the activity log for details.")
                
        except Exception as e:
            self.log_message(f"💥 Unexpected error: {e}")
            messagebox.showerror("💥 System Error", f"Unexpected error occurred:\n{e}")
        finally:
            if self.scraper:
                self.scraper.close()
                self.scraper = None
            self.set_scraping_state(False)
    
    def run_grab_links(self, max_media):
        try:
            self.scraper = FacebookAlbumScraper(
                headless=self.headless_var.get(),
                progress_callback=self.update_progress,
                log_callback=self.log_message,
                speed=self.speed_var.get()
            )
            
            url = self.url_var.get().strip()
            folder = self.folder_var.get().strip()
            album_title = self.remove_invalid_characters(f"Album_{int(time.time())}")
            
            success = self.scraper.grab_links_only(url, folder, album_title, max_media)
            
            if success:
                self.log_message("✅ Link collection mission accomplished! 🔗")
                messagebox.showinfo("🔗 Links Collected!", f"Links successfully saved to:\n{folder}/{album_title}/media_urls.json\n\nReady for download! 📥")
            else:
                self.log_message("❌ Link collection failed. Check the logs for details.")
                messagebox.showerror("💥 Collection Failed", "Link grabbing failed.\nCheck the activity log for details.")
                
        except Exception as e:
            self.log_message(f"💥 Unexpected error: {e}")
            messagebox.showerror("💥 System Error", f"Unexpected error occurred:\n{e}")
        finally:
            if self.scraper:
                self.scraper.close()
                self.scraper = None
            self.set_scraping_state(False)
    
    def run_resume_grab_links(self, max_media, json_file_path):
        try:
            self.scraper = FacebookAlbumScraper(
                headless=self.headless_var.get(),
                progress_callback=self.update_progress,
                log_callback=self.log_message,
                speed=self.speed_var.get()
            )
            
            url = self.url_var.get().strip()
            
            success = self.scraper.resume_grab_links(url, json_file_path, max_media)
            
            if success:
                self.log_message("✅ Resume mission accomplished! 🔄")
                messagebox.showinfo("🔄 Resume Complete!", f"Successfully resumed and updated:\n{json_file_path}\n\nContinuation perfected! ⚡")
            else:
                self.log_message("❌ Resume mission failed. Check the logs for details.")
                messagebox.showerror("💥 Resume Failed", "Resume link grabbing failed.\nCheck the activity log for details.")
                
        except Exception as e:
            self.log_message(f"💥 Unexpected error: {e}")
            messagebox.showerror("💥 System Error", f"Unexpected error occurred:\n{e}")
        finally:
            if self.scraper:
                self.scraper.close()
                self.scraper = None
            self.set_scraping_state(False)
    
    def run_download_from_json(self, max_media, json_file_path):
        try:
            self.scraper = FacebookAlbumScraper(
                headless=self.headless_var.get(),
                progress_callback=self.update_progress,
                log_callback=self.log_message,
                speed=self.speed_var.get()
            )
            
            folder = self.folder_var.get().strip()
            
            success = self.scraper.download_from_json(json_file_path, folder, max_media)
            
            if success:
                album_title = os.path.basename(os.path.dirname(json_file_path))
                if not album_title:
                    album_title = f"Album_{int(time.time())}"
                self.log_message("✅ Download mission accomplished! 📥")
                messagebox.showinfo("📥 Download Complete!", f"All media successfully downloaded!\n\nSaved to: {folder}/{album_title}\n\nCollection complete! 🎊")
            else:
                self.log_message("❌ Download mission failed. Check the logs for details.")
                messagebox.showerror("💥 Download Failed", "JSON download failed.\nCheck the activity log for details.")
                
        except Exception as e:
            self.log_message(f"💥 Unexpected error: {e}")
            messagebox.showerror("💥 System Error", f"Unexpected error occurred:\n{e}")
        finally:
            if self.scraper:
                self.scraper.close()
                self.scraper = None
            self.set_scraping_state(False)
    
    def remove_invalid_characters(self, title):
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            title = title.replace(char, '_')
        return title.strip()

    def on_closing(self):
        if self.is_scraping:
            result = messagebox.askyesno("🚪 Confirm Exit", 
                                       "A mission is currently in progress!\n\n"
                                       "Do you want to abort and exit?\n"
                                       "⚠️ Progress may be lost!")
            if result:
                if self.scraper:
                    self.scraper.stop_scraping()
                self.root.destroy()
        else:
            # Goodbye animation
            self.title_label.config(text="GOODBYE! 👋", fg="#FF69B4")
            self.root.after(500, self.root.destroy)

def main():
    root = tk.Tk()
    
    # Set window icon and properties
    try:
        # Try to set a modern icon if available
        root.iconbitmap(default="")  # You can add an .ico file path here
    except:
        pass
    
    # Configure the root window
    root.configure(bg='#0a0a0a')
    
    # Create the modern GUI
    app = FacebookScraperGUI(root)
    
    # Set up proper window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Start the GUI
    root.mainloop()

if __name__ == "__main__":
    main()