# Lacrosse Goal Songs Soundboard - Agent Documentation

## Project Overview

This is a web-based soundboard for playing lacrosse team goal songs. Each player has a specific song clip that plays when their button is clicked. The soundboard is split into two separate pages: one for Varsity team and one for JV team.

## Technology Stack

- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Audio Format**: WebM with Opus codec
- **Build Process**: None (direct source execution)
- **Audio Processing**: Python script using yt-dlp and FFmpeg

## File Structure

```
sillysounds/
├── index.html              # Landing page with team selection
├── varsity.html            # Varsity team soundboard
├── jv.html                 # JV team soundboard
├── styles.css              # All CSS styles (consolidated)
├── src/
│   └── app.js             # Main JavaScript application
├── sounds/                 # Audio files directory
│   ├── player0_var.webm
│   ├── player4_jv.webm
│   └── ...                # 35 total WebM files
├── sounds.json            # Complete player data (all teams)
├── sounds_varsity.json    # Varsity players only (21 players)
├── sounds_jv.json         # JV players only (14 players)
├── Lacrosse Goal songs (1).csv # Source data with player/song info
├── process_songs.py       # Main script: downloads & processes songs
├── serve.py               # Development server for local testing
├── cleanup_unused.py      # Utility: removes orphaned audio files
├── README.md              # Quick start guide
└── agents.md              # This file: detailed documentation
```

## CSV Data Format

The CSV file (`Lacrosse Goal songs.csv`) contains player information with the following columns:

- Column 0: Name (player name)
- Column 1: Player # (jersey number)
- Column 2: Var, JV, Goalie (team designation)
- Column 3: Song Title
- Column 4: Artist
- Column 5: Start Time (format: M:SS or MM:SS)
- Column 6: End Time (format: M:SS or MM:SS)

**Important**: Rows missing any required field are automatically skipped during processing.

## Available Scripts

### process_songs.py
**Purpose**: Downloads songs from YouTube, trims them, normalizes audio, and generates JSON files.

**Usage**:
```bash
cd /path/to/sillysounds
python3 process_songs.py
```

**Features**:
- Uses relative paths (portable)
- Skips existing files (fast re-runs)
- Trims songs to specified time ranges
- **Normalizes audio to -16 LUFS** (consistent volume across all clips)
- Generates all three JSON files
- Shows progress and summary
- Handles failures gracefully

**Audio Processing**:
- Downloads best audio quality from YouTube
- Trims to exact start/end times from CSV
- Applies loudnorm filter (EBU R128 standard) for consistent loudness
- Converts to WebM format with Opus codec (128kbps)

### serve.py
**Purpose**: Starts a local web server for testing.

**Usage**:
```bash
cd /path/to/sillysounds
python3 serve.py
```

Opens at http://localhost:8080

**Features**:
- Proper MIME types for WebM
- CORS headers for local testing
- Shows all available pages
- Press Ctrl+C to stop

### cleanup_unused.py
**Purpose**: Removes audio files not referenced in sounds.json.

**Usage**:
```bash
cd /path/to/sillysounds
python3 cleanup_unused.py
```

**Features**:
- Safe: asks for confirmation before deleting
- Shows file sizes and total space to free
- Compares sounds/ directory against sounds.json
- Useful after removing players or changing songs

### normalize_audio.py
**Purpose**: Normalizes all existing audio files to consistent volume levels.

**Usage**:
```bash
cd /path/to/sillysounds
python3 normalize_audio.py
```

**Features**:
- Two-pass loudness normalization (EBU R128 standard)
- Normalizes to -16 LUFS (perceived loudness)
- Processes all .webm files in sounds/ directory
- Shows progress for each file
- Safe: creates temp files before replacing originals

**When to use**:
- After manually adding audio files
- If some clips are noticeably louder/quieter than others
- Not needed if using process_songs.py (it normalizes automatically)

## How to Update Songs

### 1. Update the CSV File

Edit `Lacrosse Goal songs.csv` with new player information:
- Add new players as new rows
- Update existing player song choices
- Change start/end times for trimming
- Remove rows for players who left the team (just delete or clear required fields)

### 2. Run the Processing Script

```bash
python3 process_songs.py
```

**What the script does:**
1. Parses the CSV and identifies complete rows (28 in current dataset)
2. Searches YouTube for each song using yt-dlp
3. Downloads the best audio quality
4. Trims each song to the specified time range using FFmpeg
5. Converts to WebM format with Opus codec
6. Generates three JSON files: sounds.json, sounds_varsity.json, sounds_jv.json
7. Saves audio files to `sounds/` directory with naming: `player{number}_{team}.webm`

**Requirements:**
- Python 3
- yt-dlp: `pip install yt-dlp`
- FFmpeg: `brew install ffmpeg` (macOS) or equivalent

### 3. Verify the Results

The script will output a summary showing:
- Total songs processed
- Number of successful downloads
- List of any failed songs

Check the `sounds/` directory to verify audio files were created.

### 4. Test in Browser

Open the pages in a browser and test:
- http://127.0.0.1:8080/index.html (landing page)
- http://127.0.0.1:8080/varsity.html (15 Varsity players)
- http://127.0.0.1:8080/jv.html (13 JV players)

## Audio File Naming Convention

Format: `player{number}_{team}.webm`

Examples:
- `player20_jv.webm` - Player #20 on JV team
- `player4_var.webm` - Player #4 on Varsity team
- `player0_var.webm` - Player #0 on Varsity team

**Team suffixes:**
- `var` - Varsity
- `jv` - JV
- `var_goalie` - Varsity Goalie
- `jv_goalie` - JV Goalie

## JSON Data Structure

Each JSON file contains an array of player objects:

```json
{
  "keycode": null,
  "letter": "20",          // Player number (team designation removed for team-specific pages)
  "label": "Aarna Patel",  // Player name
  "audioFile": "player20_jv" // Filename without extension
}
```

- `sounds.json` - All players with team in "letter" field (e.g., "20 JV")
- `sounds_varsity.json` - Varsity only, just number in "letter" field (e.g., "20")
- `sounds_jv.json` - JV only, just number in "letter" field (e.g., "20")

## Common Tasks

### Adding a New Player

1. Add a new row to the CSV with all required fields
2. Run `python3 process_songs.py`
3. The new player will automatically appear on the appropriate team page

### Changing a Player's Song

1. Update the song title, artist, and/or trim times in the CSV
2. Delete the old audio file from `sounds/` directory (optional, script will overwrite)
3. Run `python3 process_songs.py`

### Removing a Player

**Option 1**: Delete the entire row from the CSV
**Option 2**: Clear required fields (song title, start time, end time) so the row is skipped

Then run `python3 process_songs.py` to regenerate the JSON files.

The old audio file will remain in `sounds/` but won't be referenced. You can manually delete it if desired.

### Adjusting Song Trim Times

1. Open the CSV and modify the Start Time and/or End Time columns
2. Run `python3 process_songs.py`
3. The script will re-download and trim with the new times

**Tip**: Use format M:SS or MM:SS (e.g., "1:28", "0:04", "2:45")

### Clearing All Songs and Starting Fresh

```bash
# Delete all audio files
rm sounds/player*.webm

# Run the script to regenerate everything
python3 process_songs.py
```

## Web Application Features

### Landing Page (index.html)
- Displays team selection with two large buttons
- Shows bobcat mascot logo
- Links to varsity.html and jv.html

### Team Pages (varsity.html, jv.html)
- Display player buttons with number and name
- Click to play goal song clip
- Special "National Anthem" button at bottom (patriotic red/white/blue styling)
- Fixed header with team name and back link
- Gradient background (pink for Varsity, blue for JV)
- Stop button appears when song is playing

### Audio Playback Behavior
- Only one song plays at a time (clicking new button stops current song)
- Stop button appears at bottom when song plays
- Stop button disappears when song ends or is manually stopped
- Visual feedback: buttons briefly scale up when clicked

### Keyboard Support
- Keyboard shortcuts are defined in JSON but currently set to `null`
- Can be enabled by adding keycode values to the JSON files

## Troubleshooting

### Song Download Fails
- **Issue**: YouTube video not found or unavailable
- **Solution**: Edit CSV with more specific search terms (artist + song title), or try different video

### Trim Points Incorrect
- **Issue**: Song doesn't start/end where expected
- **Solution**: Adjust start/end times in CSV. Times are in seconds from beginning of video.

### Audio File Size Too Large
- **Issue**: Files are larger than expected
- **Solution**: The script uses 128kbps Opus codec. This is a good balance. For smaller files, edit `process_songs.py` and change `-b:a 128k` to `-b:a 96k`.

### Script Hangs on Download
- **Issue**: yt-dlp taking a long time
- **Solution**: Check internet connection. Some videos may be slow. The script processes sequentially to avoid rate limiting.

### Player Button Doesn't Appear
- **Issue**: New player not showing on page
- **Solution**:
  1. Verify CSV has all required fields
  2. Check that JSON file was regenerated
  3. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)
  4. Check browser console for errors

## Technical Notes

### Why WebM?
- Modern browser support (all current browsers)
- Good compression (smaller files than MP3)
- Opus codec provides excellent audio quality at low bitrates
- Open format, no licensing issues

### Why No Build Step?
- Originally used Gulp for IE11 compatibility with Babel transpilation
- Modern browsers support ES6+ natively (const, let, arrow functions, etc.)
- Removed build complexity for easier maintenance
- Direct source execution is faster for development

### Audio Preloading
The app preloads all audio files on page load for instant playback. This means:
- Initial page load downloads all audio files
- Subsequent button clicks play instantly
- Total download: ~8-12MB per team page

### Browser Compatibility
Tested and working on:
- Chrome/Edge (Chromium) - Latest
- Firefox - Latest
- Safari - Latest

**Note**: IE11 is NOT supported (no longer receives security updates from Microsoft).

## Python Script Details

### Script Configuration
The script uses **relative paths** based on its location:

```python
SCRIPT_DIR = Path(__file__).parent.resolve()
CSV_PATH = SCRIPT_DIR / "Lacrosse Goal songs (1).csv"
SOUNDS_DIR = SCRIPT_DIR / "sounds"
SOUNDS_JSON_PATH = SCRIPT_DIR / "sounds.json"
TEMP_DIR = Path("/tmp/lacrosse_songs")
```

**Portable**: Works from any location, no need to update paths.

### Script Functions

- `parse_csv()` - Reads CSV and returns list of valid song entries
- `parse_time_to_seconds()` - Converts "M:SS" to integer seconds
- `normalize_team_name()` - Converts "Var" to "var", "JV Goalie" to "jv_goalie", etc.
- `download_and_trim_song()` - Downloads from YouTube and trims with FFmpeg
- `generate_sounds_json()` - Creates the three JSON files
- `check_dependencies()` - Verifies yt-dlp and ffmpeg are installed

### Error Handling
The script continues processing even if individual songs fail. At the end, it shows:
- Summary of successful vs failed songs
- List of failed songs with player names

### Download Strategy
- Sequential downloads (not parallel) to avoid YouTube rate limiting
- Uses `ytsearch1:` prefix to get first search result
- Downloads to `/tmp/lacrosse_songs/` first, then moves to final location
- Cleans up temp files after processing

## Future Enhancements

Potential improvements to consider:

1. **Admin Interface**: Web form to edit player/song data instead of CSV
2. **Multiple Song Choices**: Let players have 2-3 song options
3. **Volume Control**: Add slider to adjust playback volume
4. **Playlist Mode**: Shuffle and play all songs
5. **Search/Filter**: Find player by name or number
6. **Mobile Optimization**: Better touch targets for mobile devices
7. **Song Preview**: Show song title/artist when hovering over button
8. **Keyboard Shortcuts**: Enable keyboard number pad for quick access
9. **Analytics**: Track which songs are played most often
10. **Cloud Storage**: Store audio files on CDN for faster loading

## Deployment

To deploy to production:

1. Upload all files to web server
2. Ensure proper MIME types are set for .webm files
3. Consider enabling gzip compression for JSON files
4. Add cache headers for audio files (they don't change often)
5. Test on target devices/browsers

**Static Hosting Options:**
- GitHub Pages
- Netlify
- Vercel
- AWS S3 + CloudFront

## Contact & Maintenance

When modifying this project:
- Test changes locally before deploying
- Keep CSV file backed up (it's the source of truth)
- Document any changes to the Python script
- Verify audio quality after processing changes
- Test on multiple browsers after updates

---

Last Updated: 2026-02-15
