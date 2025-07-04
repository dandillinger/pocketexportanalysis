# Pocket Archive & Analyzer

A tool for extracting, preserving, and analyzing Pocket archives before the API shutdown. This project consists of two main components:

1. **Pocket Export Tool** - A CLI utility for extracting data from Pocket's API
2. **Pocket Analyzer** - A web-based tool for analyzing and enriching archived content

## 🎯 Purpose

This project helps preserve Pocket archives by extracting all saved articles and transforming them into a structured, searchable knowledge corpus. With Pocket's API shutting down, this tool ensures your reading history and saved content remain accessible and useful.

## 🧱 Components

### Pocket Export Tool (CLI)
- Extracts all saved and archived articles from Pocket's API (pure extraction only)
- Stores data in structured JSON format without any enrichment
- Handles OAuth authentication
- Creates both raw and parsed data outputs
- Real-time progress updates during large exports
- No analysis, tag generation, or additional metadata

### Pocket Analyzer (Web App)
- Analyzes and enriches archived content
- Provides tag generation and quality assessment
- Offers behavioral analytics and usage insights
- Exports data in multiple formats (JSONL, Markdown, CSV)

## 🧩 Data Model

### Phase 1: Export Tool (Pure Extraction)
Each article contains only what Pocket provides:
- Basic metadata (URL, title, excerpt, word count)
- User tags (as assigned in Pocket)
- Timestamps and reading status
- No generated tags, quality assessments, or analytics

### Phase 2: Analyzer Tool (Enhanced)
Additional fields added by the analyzer:
- Generated tags with confidence scores
- Quality assessments of existing tags
- Behavioral analytics and insights

## 📤 Output Formats

- **JSONL**: For AI corpus and semantic search
- **Markdown**: For personal notes and Obsidian vaults
- **CSV**: For lightweight spreadsheet review
- **HTML**: Raw backup format

## 📦 Output Files

When you run the export tool, two main files are created:

- `raw_data/pocket_export_raw.json`: Contains the complete list of raw API article responses as returned by Pocket. This is your full, original backup.
- `parsed_data/articles.jsonl`: Contains one parsed article per line in JSONL format, using the structured data model described above. This is ready for analysis or import into other tools.

After export, the tool prints file size and article count summaries for both files. All output directories are created automatically if they do not exist. File write errors are handled gracefully and reported in the CLI output.

## 🛠 Development

This project is built with:
- **Python** for the CLI export tool
- **Web technologies** for the analyzer interface
- **Structured data formats** for long-term preservation

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Pocket account (create one at [getpocket.com](https://getpocket.com) if needed)

### Installation
1. **Clone this repository**
   ```bash
   git clone https://github.com/yourusername/pocketexportanalysis.git
   cd pocketexportanalysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Pocket API credentials** (required for data extraction)
   ```bash
   # Create environment file
   cp env.example .env
   # Edit .env with your credentials (see API Setup section below)
   ```

4. **Test the installation**
   ```bash
   python pocket_export.py --help
   ```

## 📊 Export Tool Selection Guide

Choose the right export tool based on your needs:

### **Enhanced Export** (Recommended for most users)
```bash
python enhanced_incremental_export.py
```
**Best for:**
- ✅ **Large archives** (1000+ articles) - **Proven with 16K+ articles**
- ✅ **Unstable connections** or frequent timeouts
- ✅ **Rate limit concerns** (Pocket API limits)
- ✅ **Production use** with reliability requirements
- ✅ **Long-running exports** that need to survive interruptions
- ✅ **Resuming interrupted exports** with `--resume-from`

**Features:**
- Progressive delays with jitter to avoid rate limits
- Automatic error recovery with exponential backoff
- Data saved after each batch (no data loss on interruption)
- Extra breaks every 20 batches
- Detailed progress reporting
- **Resume functionality** for interrupted exports
- **Export logging** to `export_logs.txt` file
- **Sample exports** with `--max-articles` for testing

**Real-World Performance:**
- **16,291 articles**: ~40MB raw data, ~45-60 minutes export time
- **Memory efficient**: ~200MB peak usage, streams to disk
- **Reliable**: Handles network interruptions and rate limits gracefully

**Options:**
- `--max-articles N`: Export only first N articles (for testing)
- `--resume-from OFFSET`: Resume from specific offset after interruption
- `--help`: Show all available options

### **Incremental Export** (Good for medium archives)
```bash
python incremental_export.py
```
**Best for:**
- ✅ **Medium archives** (100-1000 articles)
- ✅ **Stable connections** with occasional timeouts
- ✅ **Users who want data safety** but simpler logic
- ✅ **Testing exports** before running enhanced version

**Features:**
- Saves data after each batch
- Basic rate limiting
- Simple error handling
- Good for reliable networks

### **Standard Export** (Simple, fast)
```bash
python pocket_export.py
```
**Best for:**
- ✅ **Small archives** (<100 articles)
- ✅ **Fast testing** and validation
- ✅ **Stable, fast connections**
- ✅ **Simple use cases** with minimal complexity

**Features:**
- Fastest export method
- Basic progress reporting
- Saves data at the end only
- Minimal rate limiting

### **Sample Export** (Testing and validation)
```bash
python enhanced_incremental_export.py --max-articles 50
```
**Best for:**
- ✅ **Testing your setup** before full export
- ✅ **Validating credentials** and connectivity
- ✅ **Quick data preview**
- ✅ **Development and debugging**

**Features:**
- Limited to specified number of articles
- Uses enhanced export logic for reliability
- Perfect for testing and validation

### **Recommendations by Archive Size:**

| Archive Size | Recommended Tool | Reasoning |
|--------------|------------------|-----------|
| **< 100 articles** | `pocket_export.py` | Fast and simple, no complexity needed |
| **100-500 articles** | `incremental_export.py` | Good balance of safety and speed |
| **500-2000 articles** | `enhanced_incremental_export.py` | Reliable for medium-large archives |
| **2000+ articles** | `enhanced_incremental_export.py` | Essential for large archives, handles rate limits |
| **Testing/Validation** | `enhanced_incremental_export.py --max-articles 50` | Safe testing with limited data |

### **Large Archive Considerations (10K+ Articles)**

**Based on our 16K+ article export experience:**

- **Time Investment**: Plan for 45-90 minutes for very large archives
- **Network Stability**: Use stable connection (wired preferred)
- **Storage Space**: Ensure 100MB+ free space for raw + parsed data
- **Monitoring**: Watch `export_logs.txt` for progress and issues
- **Resume Ready**: Don't worry about interruptions - resume capability built-in

**Performance Tips for Large Exports:**
- **Test first**: Use `--max-articles 100` to validate setup
- **Monitor logs**: `tail -f export_logs.txt` for real-time progress
- **Check space**: Ensure adequate disk space before starting
- **Stable connection**: Use wired connection if possible
- **Patience**: Rate limiting is intentional to avoid API issues

### **Network Considerations:**
- **Fast, stable connection**: Any tool works well
- **Slow or unstable connection**: Use enhanced export
- **Frequent timeouts**: Enhanced export with automatic retries
- **Rate limit issues**: Enhanced export with progressive delays

## 🔧 Troubleshooting & Logging

### **Export Logs**
All export operations automatically log to `export_logs.txt`:
```bash
# View recent logs
tail -f export_logs.txt

# Search for errors
grep "ERROR" export_logs.txt

# Check export progress
grep "Batch" export_logs.txt | tail -10
```

### **Common Issues & Solutions**

**Export Interrupted?**
```bash
# Find the last processed offset
grep "Batch.*completed" export_logs.txt | tail -1

# Resume from that offset
python enhanced_incremental_export.py --resume-from 12512
```

**Rate Limited?**
- Enhanced export automatically handles this with progressive delays
- Check logs for rate limit messages
- Wait 5-10 minutes before retrying

**Authentication Issues?**
```bash
# Test credentials
python -c "from dotenv import load_dotenv; load_dotenv(); from pocket_export import setup_authentication; print('✅ Auth OK' if setup_authentication() else '❌ Auth failed')"

# Check .env file format
cat .env
```

**Memory Issues with Large Exports?**
- Use enhanced export (streams data to disk)
- Consider using `--max-articles` for testing first
- Check available disk space

**Large Export Taking Too Long?**
- **Normal behavior**: 16K articles took ~45-60 minutes
- **Rate limiting**: Intentional to avoid API issues
- **Monitor progress**: Check `export_logs.txt` for batch completion
- **Resume capability**: Can safely interrupt and resume
- **Common stopping point**: Around batch 60-70 due to rate limits
- **Resume experience**: Successfully resumed from batch 64 to completion

**Disk Space Issues?**
- **Raw data**: ~40MB for 16K articles
- **Parsed data**: ~25MB for 16K articles
- **Total space needed**: ~100MB for large archives
- **Check space**: `df -h` before starting large exports

### **Performance Tips**
- **Test first**: Use `--max-articles 50` before full export
- **Stable connection**: Use wired connection if possible
- **Monitor logs**: Watch `export_logs.txt` for progress
- **Resume capability**: Don't worry about interruptions
- **Large exports**: Plan for 45-90 minutes for 10K+ articles

## 🔑 API Setup (Required)

**⚠️ Important**: You need Pocket API credentials to use this tool. Follow these steps:

### Step 1: Get Pocket API Credentials
1. Go to [getpocket.com/developer/apps/new](https://getpocket.com/developer/apps/new)
2. Log in with your Pocket account
3. Create a new application:
   - **Name**: `Pocket Export & Analyzer` (or your preferred name)
   - **Platform**: Choose "Desktop" or "Web"
   - **Permissions**: Select "Read" (required for export)
   - **Redirect URI**: `pocketapp[YOUR_APP_ID]:authorizationFinished` (replace `[YOUR_APP_ID]` with your app ID)
4. Copy your **Consumer Key** (looks like `1234-abcd1234abcd1234abcd1234`)

### Step 2: Get Access Token

**Current Method (Manual Setup)**:

1. **Add your consumer key to `.env`**:
   ```bash
   # Edit .env file
   POCKET_CONSUMER_KEY=your_actual_consumer_key_here
   ```

2. **Test authentication**:
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); from pocket_export import setup_authentication; print('✅ Auth OK' if setup_authentication() else '❌ Auth failed')"
   ```

3. **Complete OAuth flow** (if needed):
   - Follow Pocket's OAuth documentation
   - Add your access token to `.env` file
   - Test again with the command above

4. **Verify setup**:
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); from pocket_export import setup_authentication; print('✅ Auth OK' if setup_authentication() else '❌ Auth failed')"
   ```

**Note**: The current version uses manual OAuth setup. Automated setup will be available in future versions.

### Step 3: Verify Setup
```bash
# Test your credentials
python -c "from dotenv import load_dotenv; load_dotenv(); from pocket_export import setup_authentication; print('✅ Auth OK' if setup_authentication() else '❌ Auth failed')"

# If successful, you're ready to export data!
python enhanced_incremental_export.py --max-articles 5
```

### Troubleshooting
- **"Invalid consumer key"**: Check your consumer key format
- **"Authentication failed"**: Run `--auth-setup` again
- **"Rate limit exceeded"**: Wait a few minutes and try again

**📖 For detailed setup instructions, see [SETUP.md](SETUP.md)**

## 🚀 Quick Start

**Test your setup first:**
```bash
# Test authentication (loads credentials from .env)
python -c "from dotenv import load_dotenv; load_dotenv(); from pocket_export import setup_authentication; print('✅ Auth OK' if setup_authentication() else '❌ Auth failed')"

# RECOMMENDED: Enhanced export (best for most users)
python enhanced_incremental_export.py

# For testing with limited data first
python enhanced_incremental_export.py --max-articles 50

# Resume interrupted export from specific offset
python enhanced_incremental_export.py --resume-from 12512

# Alternative options (see Export Tool Selection Guide below):
# Standard export (simple, fast): python pocket_export.py
# Incremental export (medium archives): python incremental_export.py

# View help
python enhanced_incremental_export.py --help
```

**💡 Tip**: Start with a sample export (`--max-articles 50`) to test your setup, then run the full enhanced export for your complete archive.

**📝 Logging**: All export progress and errors are automatically logged to `export_logs.txt` for troubleshooting.

## 📊 Real-World Performance (16K+ Articles)

Based on our experience exporting **16,291 articles**:

### **File Sizes & Performance**
- **Raw JSON**: ~40MB (16,291 articles)
- **Parsed JSONL**: ~25MB (processed data)
- **Export Time**: ~45-60 minutes (with rate limiting)
- **Memory Usage**: ~200MB peak (streamed to disk)
- **Network**: ~50MB total transfer

### **Real-World Export Experience**
- **Initial export**: Stopped at batch 64 (rate limiting)
- **Resume successful**: Continued from batch 64 to completion
- **Total batches**: ~60 batches of 272 articles each
- **Rate limiting**: Hit limits around batch 60-70 (common)
- **Resume capability**: Proven to work seamlessly

### **Rate Limiting Strategy**
- **Progressive delays**: 2-8 seconds between batches
- **Extra breaks**: 10-second pause every 20 batches
- **Error recovery**: Exponential backoff on failures
- **Resume capability**: Continue from any offset

### **Data Safety Features**
- ✅ **Batch-by-batch saving** (no data loss on interruption)
- ✅ **Automatic resume** from last successful batch
- ✅ **Detailed logging** for troubleshooting
- ✅ **Memory efficient** (streams to disk)

## 📄 Documentation

- **Setup Guide**: [SETUP.md](SETUP.md) - Complete setup instructions
- **API Reference**: `docs/reference/pocket_api/` - Pocket API documentation
- **Example Outputs**: `docs/reference/export_outputs/` - Sample data structures
- **Planning**: `docs/planning/` - Project architecture and user stories (private)

## 🔐 Privacy

This tool is designed for personal use and data preservation. All processing happens locally or in controlled environments to maintain privacy of your reading data.

## 🗂️ Parsed Article Data Structure

Articles are parsed into a consistent structure for storage and analysis. The main fields are:

- `item_id` (str): Unique Pocket article ID
- `resolved_url` (str, optional): Final URL after redirects
- `resolved_title` (str, optional): Article title
- `excerpt` (str, optional): Article summary/excerpt
- `tags` (dict, optional): User tags (empty dict if none)
- `status` (str, optional): Pocket status code
- `time_added` (str, optional): ISO 8601 timestamp (e.g., `2024-01-15T09:15:00Z`)
- `word_count` (int, optional): Word count
- `original` (dict): All original fields from the Pocket API for auditing

**Parsing details:**
- Missing/null fields are handled gracefully
- Timestamps are normalized to ISO 8601 format
- Tags are always a dictionary (empty if missing)
- All original fields are preserved in the `original` attribute
- See `data_parser.py` for implementation details

---

*Built to preserve digital reading history before Pocket's API shutdown.*