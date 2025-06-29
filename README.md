# StuyTown Apartment Scraper

A Python scraper that monitors StuyTown's website for new apartment listings and sends email and optional sound notifications when new apartments become available.

## Features

- 🔍 Monitors StuyTown website for 1-2 bedroom apartments
- 📧 Email notifications to multiple recipients  
- 🔊 Optional sound notifications to wake you up
- 💾 JSON persistence of seen apartments using address as unique key
- 🔄 Automatic scrolling to load all dynamic content
- 🔗 Individual apartment URL extraction from listing details
- ⚙️ Three operation modes: monitoring, initial setup, notification testing

## How It Works

### Core Architecture

The scraper uses **Selenium WebDriver** to handle StuyTown's dynamic JavaScript-rendered content. Here's the general flow:

1. **Driver Setup**: Initializes headless Chrome with optimized options
2. **Page Loading**: Navigates to StuyTown search URL with 1-2 bedroom filter
3. **Content Discovery**: Scrolls through entire page to trigger lazy-loading of all apartments
4. **Data Extraction**: Uses CSS selectors to extract apartment details from each listing container
5. **Change Detection**: Compares current listings against stored apartments using address as unique identifier
6. **Notifications**: Sends email alerts and optional sound notifications for any newly discovered apartments
7. **Persistence**: Updates JSON file with current apartment state

### Data Flow

```
Load Page → Scroll to Load All → Extract Apartments → Compare with Known → Send Notifications → Save State → Wait → Repeat
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install ChromeDriver

**On macOS with Homebrew:**
```bash
brew install chromedriver
```

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver
```

**Manual Installation:**
- Download from: https://chromedriver.chromium.org/
- Place in your PATH or same directory as script

### 3. Configure Email Settings

Copy the configuration template and update with your settings:

```bash
cp config.example.py config.py
```

Edit `config.py` with your email details:

```python
EMAIL_FROM = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use Gmail App Password
EMAIL_TO = [
    "recipient1@gmail.com", 
    "recipient2@gmail.com"
]  # List of recipients
```

**Gmail App Password Setup:**
1. Enable 2-Factor Authentication on your Gmail account
2. Go to Google Account Settings → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this password in config.py (not your regular Gmail password)

**Note:** The `config.py` file is gitignored to keep your credentials secure.

## Operation Modes

The scraper has three distinct operation modes:

### 1. Normal Monitoring Mode (Default)
Continuously monitors for new apartments and sends notifications:
```bash
python main.py
```
- Checks every 30 seconds (configurable via `CHECK_INTERVAL`)
- Compares current listings against known apartments
- Sends email notifications for new discoveries
- Updates apartments.json with current state
- Runs indefinitely until stopped with Ctrl+C

**With Sound Notifications:**
```bash
python main.py --sound
```
- Same as above but also plays notification sounds when new apartments are found
- Designed to wake you up - plays system sounds on macOS/Linux/Windows

### 2. Initial Setup Mode
Saves current apartments without sending notifications:
```bash
python main.py --save-apartments
```
- **Use this first** to establish a baseline of existing apartments
- Prevents getting notified about apartments that were already available
- Extracts all current listings and saves to apartments.json
- Exits after completion

### 3. Notification Test Mode  
Sends a test notification to verify configuration:
```bash
python main.py --test-notification
```
- Sends test email to all recipients in `EMAIL_TO` list
- Verifies SMTP settings and Gmail App Password
- If using `--sound` flag, also tests sound notification
- Exits after sending test notification

**Test with Sound:**
```bash
python main.py --test-notification --sound
```

## Usage Workflow

### Recommended First-Time Setup

1. **Initial Baseline** (prevents false notifications):
   ```bash
   python main.py --save-apartments
   ```

2. **Test Notification Configuration**:
   ```bash
   python main.py --test-notification
   ```

3. **Test with Sound** (optional):
   ```bash
   python main.py --test-notification --sound
   ```

4. **Start Monitoring**:
   ```bash
   python main.py --sound  # With sound to wake you up
   # OR
   python main.py          # Email only
   ```

5. **Stop with Ctrl+C** when needed

## Configuration

### Modify Check Interval
Change `CHECK_INTERVAL` in `main.py` (default: 30 seconds):
```python
CHECK_INTERVAL = 60  # Check every 60 seconds
```

### Add More Recipients
Edit the `EMAIL_TO` list in `main.py`:
```python
EMAIL_TO = [
    "person1@gmail.com",
    "person2@gmail.com", 
    "person3@gmail.com"
]
```

### Customize Search Parameters
The URL in `STUYTOWN_URL` can be modified to change search criteria:
- Current: 1-2 bedrooms, sorted by low price
- Modify the URL parameters as needed

## Files Generated

- `apartments.json` - Stores seen apartments for persistence (address used as unique key)
- Console logs - Detailed operation logs with timestamps

## Data Structure

Each apartment in `apartments.json` contains:
```json
{
  "address": "20 Avenue C, Apt 12A",
  "price": "$3,200/month",
  "bedrooms": "1 Bedroom, 1 Bathroom",
  "availability": "Available Now",
  "discovered_at": "2024-01-15T14:30:22.123456",
  "url": "https://www.stuytown.com/nyc-apartments-for-rent/unit/?unitSpk=..."
}
```
