#!/usr/bin/env python3
"""
Lacrosse Goal Songs Processor
Parses CSV, downloads YouTube songs, trims them, and generates sounds.json
"""

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Configuration - paths relative to script location
SCRIPT_DIR = Path(__file__).parent.resolve()
CSV_PATH = SCRIPT_DIR / "Lacrosse Goal songs (1).csv"
SOUNDS_DIR = SCRIPT_DIR / "sounds"
SOUNDS_JSON_PATH = SCRIPT_DIR / "sounds.json"
TEMP_DIR = Path("/tmp/lacrosse_songs")

def parse_time_to_seconds(time_str):
    """Convert time string like '1:28' or '0:04' to seconds"""
    parts = time_str.split(':')
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + int(seconds)
    return 0

def normalize_team_name(team):
    """Normalize team name for filename"""
    team = team.strip().lower()
    if 'jv goalie' in team:
        return 'jv_goalie'
    elif 'var goalie' in team:
        return 'var_goalie'
    elif 'jv' in team:
        return 'jv'
    elif 'var' in team:
        return 'var'
    return team.replace(' ', '_')

def parse_csv():
    """Parse CSV and return list of complete rows"""
    songs = []

    with open(str(CSV_PATH), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if len(row) < 7:
                continue

            name = row[0].strip()
            player_num = row[1].strip()
            team = row[2].strip()
            song_title = row[3].strip()
            artist = row[4].strip()
            start_time = row[5].strip()
            end_time = row[6].strip()

            # Skip if any required field is missing
            if not all([name, player_num, team, song_title, start_time, end_time]):
                continue

            # Handle Row 21 (Farrah Arledge) - use first song only
            songs.append({
                'name': name,
                'player_num': player_num,
                'team': team,
                'song_title': song_title,
                'artist': artist,
                'start_time': start_time,
                'end_time': end_time
            })

    return songs

def download_and_trim_song(song, index, total):
    """Download song from YouTube and trim it"""
    print(f"\n[{index}/{total}] Processing {song['name']} - Player #{song['player_num']}")

    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Construct search query
    query = f"{song['artist']} {song['song_title']}" if song['artist'] else song['song_title']
    print(f"  Searching: {query}")

    # Generate output filename
    team_normalized = normalize_team_name(song['team'])
    output_filename = f"player{song['player_num']}_{team_normalized}.webm"
    output_path = SOUNDS_DIR / output_filename

    # Skip if already exists
    if os.path.exists(output_path):
        print(f"  ✓ Already exists: {output_filename}")
        return output_filename.replace('.webm', ''), True

    # Download with yt-dlp
    temp_download = TEMP_DIR / f"temp_{index}.webm"

    try:
        # Download audio
        print(f"  Downloading...")
        download_cmd = [
            'yt-dlp',
            f'ytsearch1:{query}',
            '-f', 'bestaudio',
            '-o', str(temp_download),
            '--no-playlist',
            '--quiet',
            '--no-warnings'
        ]

        result = subprocess.run(download_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ✗ Download failed: {result.stderr}")
            return None, False

        # Find the downloaded file (yt-dlp may add extension)
        temp_files = [f for f in os.listdir(str(TEMP_DIR)) if f.startswith(f"temp_{index}")]
        if not temp_files:
            print(f"  ✗ Download failed: File not created")
            return None, False

        # Use the first matching file
        actual_download = TEMP_DIR / temp_files[0]

        # Trim with FFmpeg, convert to webm, and normalize audio
        print(f"  Trimming {song['start_time']} to {song['end_time']} and normalizing...")
        start_seconds = parse_time_to_seconds(song['start_time'])
        end_seconds = parse_time_to_seconds(song['end_time'])

        # Use loudnorm filter for consistent volume across all clips (EBU R128 standard)
        trim_cmd = [
            'ffmpeg',
            '-i', str(actual_download),
            '-ss', str(start_seconds),
            '-to', str(end_seconds),
            '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5',  # Normalize to -16 LUFS
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-y',
            str(output_path),
            '-loglevel', 'error'
        ]

        result = subprocess.run(trim_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ✗ Trim failed: {result.stderr}")
            # Clean up temp file
            if os.path.exists(actual_download):
                os.remove(actual_download)
            return None, False

        # Verify output file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"  ✓ Success: {output_filename}")
            # Clean up temp file
            if os.path.exists(actual_download):
                os.remove(actual_download)
            return output_filename.replace('.webm', ''), True
        else:
            print(f"  ✗ Trim failed: Output file invalid")
            return None, False

    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return None, False

def generate_sounds_json(songs, successful_files):
    """Generate sounds.json from processed songs"""
    sounds_data = []
    varsity_data = []
    jv_data = []

    for song in songs:
        team_normalized = normalize_team_name(song['team'])
        audio_file = f"player{song['player_num']}_{team_normalized}"

        # Only include if file was successfully created
        if audio_file in successful_files:
            # Format team name for display
            team_display = song['team'].strip()
            team_lower = team_display.lower()

            if 'goalie' in team_lower:
                team_display = 'Goalie'

            # Add to main sounds.json
            sounds_data.append({
                'keycode': None,
                'letter': f"{song['player_num']} {team_display}",
                'label': song['name'],
                'audioFile': audio_file
            })

            # Add to team-specific JSON (without team in letter)
            team_entry = {
                'keycode': None,
                'letter': song['player_num'],
                'label': song['name'],
                'audioFile': audio_file
            }

            if 'var' in team_lower:
                varsity_data.append(team_entry)
            elif 'jv' in team_lower:
                jv_data.append(team_entry)

    # Write to sounds.json
    with open(str(SOUNDS_JSON_PATH), 'w', encoding='utf-8') as f:
        json.dump(sounds_data, f, indent=2)

    # Write to sounds_varsity.json
    varsity_path = SCRIPT_DIR / 'sounds_varsity.json'
    with open(str(varsity_path), 'w', encoding='utf-8') as f:
        json.dump(sorted(varsity_data, key=lambda x: int(x['letter'])), f, indent=2)

    # Write to sounds_jv.json
    jv_path = SCRIPT_DIR / 'sounds_jv.json'
    with open(str(jv_path), 'w', encoding='utf-8') as f:
        json.dump(sorted(jv_data, key=lambda x: int(x['letter'])), f, indent=2)

    print(f"\n✓ Generated sounds.json with {len(sounds_data)} entries")
    print(f"✓ Generated sounds_varsity.json with {len(varsity_data)} entries")
    print(f"✓ Generated sounds_jv.json with {len(jv_data)} entries")

def check_dependencies():
    """Check if required tools are installed"""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: yt-dlp is not installed. Install with: pip install yt-dlp")
        return False

    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed. Install with: brew install ffmpeg")
        return False

    return True

def main():
    print("Lacrosse Goal Songs Processor")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Create sounds directory if it doesn't exist
    SOUNDS_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

    # Parse CSV
    print("\nParsing CSV...")
    songs = parse_csv()
    print(f"Found {len(songs)} complete song entries")

    # Process each song
    successful_files = []
    failed_songs = []

    for i, song in enumerate(songs, 1):
        audio_file, success = download_and_trim_song(song, i, len(songs))
        if success and audio_file:
            successful_files.append(audio_file)
        else:
            failed_songs.append(song)

    # Generate sounds.json
    generate_sounds_json(songs, successful_files)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total songs: {len(songs)}")
    print(f"Successful: {len(successful_files)}")
    print(f"Failed: {len(failed_songs)}")

    if failed_songs:
        print("\nFailed songs:")
        for song in failed_songs:
            print(f"  - {song['name']} (#{song['player_num']}) - {song['song_title']}")

    print("\nNext steps:")
    print("1. Update app.js to use .webm extension")
    print("2. Run 'gulp build' in the sillysounds directory")
    print("3. Update index.html title")
    print("4. Test the web app")

if __name__ == '__main__':
    main()
