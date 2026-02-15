# Lacrosse Goal Songs Soundboard

A web-based soundboard for playing lacrosse team goal songs. Each player has a custom song clip that plays when scoring.

## 🚀 Quick Start

### View the Soundboard

```bash
# Start the local server
python3 serve.py

# Open in browser:
# http://localhost:8080
```

### Update Songs

1. Edit `Lacrosse Goal songs (1).csv` with new player/song data
2. Run the processing script:

```bash
python3 process_songs.py
```

3. Refresh your browser to see changes

## 📋 Requirements

- Python 3
- yt-dlp: `pip install yt-dlp`
- ffmpeg: `brew install ffmpeg` (macOS)

## 📁 Project Structure

```
sillysounds/
├── index.html              # Landing page
├── varsity.html            # Varsity team page
├── jv.html                 # JV team page
├── styles.css              # All styles
├── src/app.js             # JavaScript application
├── sounds/                 # Audio files (.webm)
├── sounds.json            # All players data
├── sounds_varsity.json    # Varsity players
├── sounds_jv.json         # JV players
└── Lacrosse Goal songs (1).csv  # Source data
```

## 🛠 Scripts

### `process_songs.py`
Downloads songs from YouTube, trims them to specified times, and generates JSON files.

```bash
python3 process_songs.py
```

**What it does:**
- Parses the CSV file
- Searches YouTube for each song
- Downloads and converts to WebM format
- Trims to specified start/end times
- Generates sounds.json, sounds_varsity.json, sounds_jv.json

### `serve.py`
Starts a local web server for testing.

```bash
python3 serve.py
```

Opens on http://localhost:8080

### `cleanup_unused.py`
Removes audio files that are no longer referenced in sounds.json.

```bash
python3 cleanup_unused.py
```

Useful after removing players or changing songs.

## 📝 CSV Format

Required columns:
- **Name**: Player name
- **Player #**: Jersey number
- **Var, JV, Goalie**: Team designation
- **Song Title**: Name of the song
- **Artist**: Artist name (optional but recommended)
- **Start Time**: Trim start (format: M:SS or MM:SS)
- **End Time**: Trim end (format: M:SS or MM:SS)

Example:
```csv
Name,Player #,"Var, JV, Goalie",Song Title,Artist,Start Time,End Time
Aarna Patel,20,JV,White Iverson,Post Malone,1:28,1:50
```

## 🎵 Features

- **Team-specific pages**: Separate soundboards for Varsity and JV
- **One-click playback**: Click player button to play their goal song
- **National Anthem button**: Special button for the US national anthem on both pages
- **Auto-stop**: New song stops currently playing song
- **Stop button**: Appears when song is playing, allows early stop
- **Gradient backgrounds**: Pink for Varsity, blue for JV
- **Responsive design**: Works on desktop and mobile

## 🔧 Common Tasks

### Add a New Player
1. Add row to CSV with all required fields
2. Run `python3 process_songs.py`
3. New player appears automatically

### Change a Player's Song
1. Update song/artist/times in CSV
2. Run `python3 process_songs.py`
3. Old file is overwritten

### Remove a Player
1. Delete row from CSV or clear required fields
2. Run `python3 process_songs.py`
3. Run `python3 cleanup_unused.py` to delete old audio file

### Adjust Trim Times
1. Edit Start Time/End Time in CSV
2. Run `python3 process_songs.py`
3. Audio file is re-downloaded and re-trimmed

## 📚 Documentation

For detailed documentation, see:
- **[agents.md](agents.md)** - Complete technical documentation for AI agents and developers
- Includes troubleshooting, architecture notes, and future enhancements

## 🌐 Browser Support

Works on all modern browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari

## 📊 Current Stats

- **Total players**: 35
- **Varsity players**: 21
- **JV players**: 14
- **Audio format**: WebM (Opus codec, 128kbps)
- **Average clip length**: 15-20 seconds

## 🚀 Deployment

To deploy to production:
1. Upload all files to web server
2. Ensure .webm MIME types are configured
3. Enable gzip compression for JSON files
4. Add cache headers for audio files

**Recommended hosting:**
- GitHub Pages
- Netlify
- Vercel
- AWS S3 + CloudFront

## 📄 License

This project is for the lacrosse team's use.

---

**Last Updated**: 2026-02-15
