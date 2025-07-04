# Setup Guide for Pocket Export & Analyzer

This guide walks you through setting up the Pocket Export & Analyzer tool, including obtaining API credentials and configuring your environment.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [API Credentials Setup](#api-credentials-setup)
4. [Environment Configuration](#environment-configuration)
5. [Testing Your Setup](#testing-your-setup)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher**
- **A Pocket account** (create one at [getpocket.com](https://getpocket.com) if needed)
- **Git** (for cloning the repository)
- **pip** (Python package installer)

### Verify Python Installation
```bash
python --version
# Should show Python 3.8 or higher
```

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/pocketexportanalysis.git
cd pocketexportanalysis
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
python pocket_export.py --help
```

You should see the help output with available commands.

---

## API Credentials Setup

**⚠️ Important**: This tool requires Pocket API credentials to function. Follow these steps carefully.

### Step 1: Create a Pocket Developer Application

1. **Go to the Pocket Developer Portal**
   - Visit: [getpocket.com/developer/apps/new](https://getpocket.com/developer/apps/new)
   - Log in with your Pocket account

2. **Fill in Application Details**
   - **Application Name**: `Pocket Export & Analyzer` (or your preferred name)
   - **Platform**: Select "Desktop" or "Web"
   - **Description**: "CLI tool for exporting Pocket articles before API shutdown"

3. **Set Permissions**
   - ✅ **Read**: Required for exporting articles
   - ❌ **Write**: Not needed for export functionality
   - ❌ **Delete**: Not needed for export functionality

4. **Configure Redirect URI**
   - **Format**: `pocketapp[YOUR_APP_ID]:authorizationFinished`
   - **Example**: If your app ID is 1234, use: `pocketapp1234:authorizationFinished`
   - **Note**: The app ID is the first part of your consumer key (before the hyphen)

5. **Complete Registration**
   - Review your settings
   - Accept the terms of service
   - Click "Create Application"

6. **Save Your Credentials**
   - **Consumer Key**: Copy this immediately (format: `1234-abcd1234abcd1234abcd1234`)
   - **App ID**: The first part of your consumer key (e.g., `1234`)

### Step 2: Get Your Access Token

**Current Method (Manual Setup)**:

1. **Add your consumer key to `.env`**:
   ```bash
   # Edit .env file
   POCKET_CONSUMER_KEY=your_actual_consumer_key_here
   ```

2. **Test authentication**:
   ```bash
   python pocket_export.py --test-auth
   ```

3. **Complete OAuth flow**:
   - The tool will provide a URL to visit
   - Authorize your application in the browser
   - Copy the access token from the response
   - Add it to your `.env` file

4. **Verify setup**:
   ```bash
   python pocket_export.py --test-auth
   ```

**Automated Setup** (coming soon):
```bash
python pocket_export.py --auth-setup
```

**Detailed Manual Instructions**:
For step-by-step OAuth flow instructions, see `docs/reference/pocket_api/setup_guide.md`.

---

## Environment Configuration

### Option 1: Environment File (Recommended)

1. **Create Environment File**
   ```bash
   cp env.example .env
   ```

2. **Edit the .env File**
   ```bash
   # Pocket API Configuration
   POCKET_CONSUMER_KEY=your_consumer_key_here
   POCKET_ACCESS_TOKEN=your_access_token_here
   
   # Optional: App ID (auto-detected from consumer key)
   POCKET_APP_ID=your_app_id_here
   ```

3. **Replace the placeholder values** with your actual credentials

### Option 2: Environment Variables

Set environment variables directly:

```bash
export POCKET_CONSUMER_KEY="your_consumer_key_here"
export POCKET_ACCESS_TOKEN="your_access_token_here"
```

### Option 3: Direct Input

The tool will prompt for credentials if not found in environment variables.

---

## Testing Your Setup

### 1. Test Authentication
```bash
python pocket_export.py --test-auth
```

**Expected Output**:
```
INFO - Setting up Pocket API authentication...
INFO - API credentials loaded successfully
INFO - API credentials validated successfully
INFO - Authentication setup completed successfully
INFO - Authentication successful. Ready for data extraction.
```

### 2. Test Data Fetching
```bash
# Fetch a small number of articles to test
python pocket_export.py --fetch --count 5
```

**Expected Output**:
```
INFO - Starting Pocket Export Tool...
INFO - Setting up Pocket API authentication...
INFO - Authentication successful. Ready for data extraction.
INFO - Starting data fetch operation...
INFO - Starting article fetch (detail_type: complete, state: all)
INFO - Fetching batch: offset=0, count=5
INFO - Fetched article 1: [Article Title]
INFO - Fetched article 2: [Article Title]
...
INFO - Data fetch completed. Total articles fetched: 5
```

### 3. Test Different States
```bash
# Test unread articles only
python pocket_export.py --fetch --count 3 --state unread

# Test archived articles only
python pocket_export.py --fetch --count 3 --state archive
```

### 4. Test Enhanced Export (Recommended)
```bash
# Test with limited data first
python enhanced_incremental_export.py --max-articles 50

# Test resume functionality
python enhanced_incremental_export.py --resume-from 25
```

## 🔧 Enhanced Export Features

### **Resume Functionality**
If your export is interrupted, you can resume from where it left off:

```bash
# Find the last processed offset from logs
grep "Batch.*completed" export_logs.txt | tail -1

# Resume from that offset
python enhanced_incremental_export.py --resume-from 12512
```

### **Export Logging**
All exports automatically log to `export_logs.txt`:
```bash
# Monitor progress in real-time
tail -f export_logs.txt

# Check for errors
grep "ERROR" export_logs.txt

# View recent progress
grep "Batch" export_logs.txt | tail -10
```

### **Sample Exports**
Test your setup with limited data:
```bash
# Export only 50 articles for testing
python enhanced_incremental_export.py --max-articles 50

# Export only 10 articles for quick validation
python enhanced_incremental_export.py --max-articles 10
```

## 🚀 Production Export

Once testing is successful, run your full export:

```bash
# Recommended: Enhanced export with all safety features
python enhanced_incremental_export.py

# Monitor progress
tail -f export_logs.txt
```

**Features included:**
- ✅ **Automatic rate limiting** with progressive delays
- ✅ **Error recovery** with exponential backoff
- ✅ **Data safety** - saves after each batch
- ✅ **Resume capability** for interrupted exports
- ✅ **Detailed logging** for troubleshooting
- ✅ **Extra breaks** every 20 batches to avoid rate limits

## 📊 Real-World Performance (16K+ Articles)

Based on our experience exporting **16,291 articles**:

### **Performance Metrics**
- **Export Time**: ~45-60 minutes (with rate limiting)
- **Raw Data Size**: ~40MB (16,291 articles)
- **Parsed Data Size**: ~25MB (processed data)
- **Memory Usage**: ~200MB peak (streamed to disk)
- **Network Transfer**: ~50MB total
- **Batches**: ~60 batches of 272 articles each

### **Rate Limiting Strategy**
- **Progressive delays**: 2-8 seconds between batches
- **Extra breaks**: 10-second pause every 20 batches
- **Error recovery**: Exponential backoff on failures
- **Resume capability**: Continue from any offset

### **Large Archive Considerations**
- **Time Investment**: Plan for 45-90 minutes for very large archives
- **Network Stability**: Use stable connection (wired preferred)
- **Storage Space**: Ensure 100MB+ free space for raw + parsed data
- **Monitoring**: Watch `export_logs.txt` for progress and issues
- **Resume Ready**: Don't worry about interruptions - resume capability built-in

### **Performance Tips for Large Exports**
- **Test first**: Use `--max-articles 100` to validate setup
- **Monitor logs**: `tail -f export_logs.txt` for real-time progress
- **Check space**: Ensure adequate disk space before starting
- **Stable connection**: Use wired connection if possible
- **Patience**: Rate limiting is intentional to avoid API issues

---
## Troubleshooting

### Common Issues

#### 1. "Invalid consumer key" Error
**Symptoms**: `ERROR - Invalid API credentials - please check your consumer_key and access_token`

**Solutions**:
- Verify your consumer key format: `1234-abcd1234abcd1234abcd1234`
- Check for extra spaces or characters
- Ensure you're using the correct key for your platform

#### 2. "Missing consumer key" Error
**Symptoms**: `ERROR - POCKET_CONSUMER_KEY environment variable is required`

**Solutions**:
- Check that your `.env` file exists and contains the consumer key
- Verify environment variable names are correct
- Try setting variables directly: `export POCKET_CONSUMER_KEY="your_key"`

#### 3. "Authentication failed" Error
**Symptoms**: `ERROR - Failed to validate API credentials`

**Solutions**:
- Run `python pocket_export.py --auth-setup` to refresh your access token
- Check that your Pocket account is active
- Verify your app has the correct permissions

#### 4. "Rate limit exceeded" Error
**Symptoms**: `WARNING - Rate limit exceeded. Waiting 5 seconds...`

**Solutions**:
- Wait a few minutes before trying again
- The tool automatically handles rate limiting
- Consider reducing batch sizes if you have many articles

#### 5. Network/Connection Errors
**Symptoms**: `ERROR - Network error during API request`

**Solutions**:
- Check your internet connection
- Verify you can access `getpocket.com`
- Try again in a few minutes

#### 6. Large Export Taking Too Long
**Symptoms**: Export seems to be taking forever, no progress updates

**Solutions**:
- **Normal behavior**: 16K articles took ~45-60 minutes
- **Rate limiting**: Intentional delays to avoid API issues
- **Monitor progress**: Check `export_logs.txt` for batch completion
- **Resume capability**: Can safely interrupt and resume

### Getting Help

If you're still having issues:

1. **Check the logs**: Run with `--verbose` for detailed output
   ```bash
   python pocket_export.py --fetch --verbose
   ```

2. **Review API documentation**: See `docs/reference/pocket_api/`

3. **Check Pocket's status**: Visit [getpocket.com/developer](https://getpocket.com/developer)

4. **Create an issue**: Report bugs on the project's GitHub page

---

## Security Best Practices

### 1. Protect Your Credentials
- **Never commit credentials to version control**
- **Use `.env` files** (already in `.gitignore`)
- **Don't share your consumer key publicly**
- **Rotate credentials if compromised**

### 2. Environment Security
```bash
# Set proper file permissions
chmod 600 .env

# Use environment variables in production
export POCKET_CONSUMER_KEY="your_key"
export POCKET_ACCESS_TOKEN="your_token"
```

### 3. Network Security
- **Use HTTPS** (enforced by the tool)
- **Run on trusted networks**
- **Don't use public Wi-Fi for credential setup**

### 4. Data Privacy
- **All processing happens locally**
- **No data is sent to external services**
- **Your reading data stays private**

---

## Next Steps

Once your setup is working:

1. **Test with sample export**: `python enhanced_incremental_export.py --max-articles 50`
2. **Run full export**: `python enhanced_incremental_export.py`
3. **Monitor progress**: `tail -f export_logs.txt`
4. **Explore the output**: Check the generated files in `raw_data/` and `parsed_data/`
5. **Validate your data**: Use the validation tools to ensure data integrity
6. **Prepare for Phase 2**: The web analyzer (coming soon)

---

## Support

- **Documentation**: Check `docs/` directory for detailed guides
- **Issues**: Report bugs on GitHub
- **Questions**: Open a discussion on GitHub

---

*Last updated: July 2, 2025* 