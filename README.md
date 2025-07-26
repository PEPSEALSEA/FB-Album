# 🎯 FB - Album

## ⚠️ Important Notice

**This tool is for educational purposes only.** Please ensure you have permission to download content and comply with FB's Terms of Service and applicable laws. Always respect privacy and copyright.

## ✨ Features

- **Modern GUI** with animated black/pink theme
- **Smart scraping** with automatic detection of images and videos
- **Resume functionality** to continue interrupted downloads
- **JSON export/import** for batch processing
- **Speed control** (Slow/Medium/Fast)
- **Headless mode** support
- **Progress tracking** with animated progress bars
- **Real-time logging** with colored output

## 🔧 Installation

### Prerequisites

Make sure you have Python 3.7+ installed on your system.

### Required Dependencies

Install all required packages using pip:

```bash
pip install tkinter selenium requests webdriver-manager
```

### Chrome Browser

This tool requires Google Chrome browser to be installed on your system. The Chrome WebDriver will be automatically downloaded and managed.

## 🚀 Usage

### 1. Basic Usage

1. **Run the application:**
   ```bash
   python FB-Album V.X.X.py
   ```

2. **Configure settings:**
   - Enter the FB album URL
   - Set download folder path
   - Choose number of media items to download
   - Select speed (Slow/Medium/Fast)
   - Toggle headless mode if needed

3. **Start scraping:**
   - Click "🚀 START SCRAPING" for complete download
   - Or use advanced features below

### 2. Advanced Features

#### 🔗 Grab Links Only
- Click "🔗 GRAB LINKS" to collect URLs without downloading
- Saves URLs to `media_urls.json` file
- Perfect for batch processing later

#### 🔄 Resume Link Grabbing
- Click "🔄 RESUME GRAB" to continue from where you left off
- Select existing JSON file to resume collection

#### 📥 Download from JSON
- Click "📥 DOWNLOAD JSON" to download media from saved URLs
- Select JSON file containing media URLs
- Downloads all media without re-scraping

### 3. Login Process

1. The browser will open automatically
2. Log in to your FB account
3. Complete any two-factor authentication if required
4. The tool will automatically proceed once logged in

## 📁 File Structure

After scraping, your files will be organized as:

```
downloaded_albums/
└── Album_Name/
    ├── media_urls.json    # Contains all media URLs
    ├── 001.jpg           # Downloaded images
    ├── 002.mp4           # Downloaded videos
    ├── 003.jpg
    └── ...
```

## 🌐 JSON Viewer & Fast Download

After getting the `media_urls.json` file, you can use our online tool for better management:

### 🔗 [JSON Array Editor](https://pepsealsea.github.io/JSON-Array-Editor/)

**Features:**
- **Preview all images** in a beautiful gallery
- **Fast batch download** with optimized speed
- **Filter and sort** media items
- **Edit JSON arrays** directly in browser
- **Export selected items** only

**How to use:**
1. Open [https://pepsealsea.github.io/JSON-Array-Editor/](https://pepsealsea.github.io/JSON-Array-Editor/)
2. Upload your `media_urls.json` file
3. Preview all images in gallery view
4. Select items you want to download
5. Download with optimized batch processing

This web tool is especially useful for:
- **Large albums** with hundreds of images
- **Selective downloading** of specific items
- **Faster download speeds** with parallel processing
- **Better organization** and preview capabilities

## 🛠️ Troubleshooting

### Common Issues

1. **Chrome driver issues:**
   - The tool automatically downloads the correct Chrome driver
   - Make sure Chrome browser is installed and updated

2. **Login problems:**
   - Disable 2FA temporarily if possible
   - Try logging in manually first in Chrome
   - Clear browser cache and cookies

3. **Slow performance:**
   - Use "Fast" speed setting
   - Enable headless mode
   - Close other browser instances

4. **Network errors:**
   - Check internet connection
   - Try different speed settings
   - Resume using JSON files if interrupted

### Speed Settings

- **Slow:** 1.0s grab delay, 0.5s download delay (most stable)
- **Medium:** 0.5s grab delay, 0.3s download delay (balanced)
- **Fast:** 0.2s grab delay, 0.1s download delay (fastest, may trigger rate limits)

## 📜 License

This project is provided for educational purposes only. Users are responsible for complying with FB's Terms of Service and applicable laws.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review the activity log for error details
3. Try using the JSON workflow for better reliability
4. Use the online JSON editor for enhanced functionality
5. Contact us : [Discord](https://discord.gg/FbHAVFAYBG)

---

**Remember:** Always respect privacy, copyright, and terms of service when using this tool. Happy scraping! 🎉
