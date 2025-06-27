# StuyTown Apartment Scraper

A Python scraper that monitors StuyTown's website for new apartment listings and sends email notifications when new apartments become available.

## Features

- 🔍 Monitors StuyTown website for 1-2 bedroom apartments
- 📧 Email notifications to multiple recipients  
- 💾 JSON persistence of seen apartments using address as unique key
- 📊 Comprehensive logging with timestamp tracking
- 🔄 Automatic scrolling to load all dynamic content
- 🔗 Individual apartment URL extraction from listing details
- ⚙️ Three operation modes: monitoring, initial setup, email testing
- ✅ Data validation to skip incomplete listings

## How It Works

### Core Architecture

The scraper uses **Selenium WebDriver** to handle StuyTown's dynamic JavaScript-rendered content. Here's the general flow:

1. **Driver Setup**: Initializes headless Chrome with optimized options
2. **Page Loading**: Navigates to StuyTown search URL with 1-2 bedroom filter
3. **Content Discovery**: Scrolls through entire page to trigger lazy-loading of all apartments
4. **Data Extraction**: Uses CSS selectors to extract apartment details from each listing container
5. **Change Detection**: Compares current listings against stored apartments using address as unique identifier
6. **Notifications**: Sends email alerts for any newly discovered apartments
7. **Persistence**: Updates JSON file with current apartment state

### CSS Selectors Used

The scraper targets these specific CSS classes on StuyTown's website:
- `.bG_cM` - Main apartment listing containers
- `.bG_2` - Bedroom/bathroom information  
- `.bG_cQ` - Full apartment address (used as unique key)
- `.bG_bz` - Availability status
- `.bG_jY` - Rental price
- `.bG_ct` - Details link for individual apartment URL

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

### 2. Initial Setup Mode
Saves current apartments without sending notifications:
```bash
python main.py --save-apartments
```
- **Use this first** to establish a baseline of existing apartments
- Prevents getting notified about apartments that were already available
- Extracts all current listings and saves to apartments.json
- Exits after completion

### 3. Email Test Mode  
Sends a test email to verify configuration:
```bash
python main.py --test-email
```
- Sends test email to all recipients in `EMAIL_TO` list
- Verifies SMTP settings and Gmail App Password
- Exits after sending test email

## Usage Workflow

### Recommended First-Time Setup

1. **Initial Baseline** (prevents false notifications):
   ```bash
   python main.py --save-apartments
   ```

2. **Test Email Configuration**:
   ```bash
   python main.py --test-email
   ```

3. **Start Monitoring**:
   ```bash
   python main.py
   ```

4. **Stop with Ctrl+C** when needed

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

## Technical Details

### Text Extraction Method
Uses `get_attribute('textContent')` instead of `.text` for reliable text extraction from dynamically loaded elements.

### Scrolling Algorithm
Implements intelligent scrolling that:
- Detects when page height stops changing
- Has safety limit (50 scrolls max)
- Waits 2 seconds between scrolls for content loading

### Data Validation
Skips apartments missing required fields (address or price) to ensure data quality.