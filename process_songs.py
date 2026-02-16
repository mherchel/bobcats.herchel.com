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
CSV_PATH = SCRIPT_DIR / "Goal Songs.csv"
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
    """Parse CSV and return list of all player rows (with and without songs)"""
    players = []

    with open(str(CSV_PATH), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header

        for row in reader:
            if len(row) < 3:
                continue

            name = row[0].strip()
            player_num = row[1].strip()
            team = row[2].strip()

            # Skip if essential fields are missing
            if not all([name, player_num, team]):
                continue

            # Get optional song fields (may be empty)
            artist = row[3].strip() if len(row) > 3 else ''
            song_title = row[4].strip() if len(row) > 4 else ''
            start_time = row[5].strip() if len(row) > 5 else ''
            end_time = row[6].strip() if len(row) > 6 else ''
            youtube_link = row[7].strip() if len(row) > 7 else ''

            # Check if player has a song
            has_song = all([song_title, start_time, end_time, youtube_link])

            players.append({
                'name': name,
                'player_num': player_num,
                'team': team,
                'song_title': song_title,
                'artist': artist,
                'start_time': start_time,
                'end_time': end_time,
                'youtube_link': youtube_link,
                'has_song': has_song
            })

    return players

def download_and_trim_song(song, index, total):
    """Download song from YouTube and trim it"""
    print(f"\n[{index}/{total}] Processing {song['name']} - Player #{song['player_num']}")

    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Use direct YouTube link
    youtube_url = song['youtube_link']
    print(f"  Downloading from: {youtube_url}")
    print(f"  Song: {song['song_title']} by {song['artist']}")

    # Generate output filename
    team_normalized = normalize_team_name(song['team'])
    output_filename = f"player{song['player_num']}_{team_normalized}.webm"
    output_path = SOUNDS_DIR / output_filename

    # Remove existing file to force regeneration
    if os.path.exists(output_path):
        print(f"  Removing existing file to regenerate...")
        os.remove(output_path)

    # Download with yt-dlp
    temp_download = TEMP_DIR / f"temp_{index}.webm"

    try:
        # Download audio
        print(f"  Downloading...")
        download_cmd = [
            'yt-dlp',
            youtube_url,
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

def generate_sounds_json(players, successful_files):
    """Generate sounds.json from all players (with and without songs)"""
    sounds_data = []
    varsity_data = []
    jv_data = []

    for player in players:
        team_normalized = normalize_team_name(player['team'])
        audio_file = f"player{player['player_num']}_{team_normalized}"

        # Format team name for display
        team_display = player['team'].strip()
        team_lower = team_display.lower()

        if 'goalie' in team_lower:
            team_display = 'Goalie'

        # Create entry for player
        main_entry = {
            'keycode': None,
            'letter': f"{player['player_num']} {team_display}",
            'label': player['name'],
        }

        team_entry = {
            'keycode': None,
            'letter': player['player_num'],
            'label': player['name'],
        }

        # Add audioFile if player has a song and it was successfully created
        if player['has_song'] and audio_file in successful_files:
            main_entry['audioFile'] = audio_file
            team_entry['audioFile'] = audio_file
        else:
            # Mark as disabled if no song
            main_entry['disabled'] = True
            team_entry['disabled'] = True

        # Add to main sounds.json
        sounds_data.append(main_entry)

        # Add to team-specific JSON
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

    enabled_count = len([p for p in players if p['has_song'] and f"player{p['player_num']}_{normalize_team_name(p['team'])}" in successful_files])
    disabled_count = len([p for p in players if not p['has_song']])

    print(f"\n✓ Generated sounds.json with {len(sounds_data)} entries ({enabled_count} enabled, {disabled_count} disabled)")
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
    players = parse_csv()
    players_with_songs = [p for p in players if p['has_song']]
    players_without_songs = [p for p in players if not p['has_song']]

    print(f"Found {len(players)} total players")
    print(f"  - {len(players_with_songs)} with songs")
    print(f"  - {len(players_without_songs)} without songs (will be disabled)")

    # Process each song
    successful_files = []
    failed_songs = []

    for i, player in enumerate(players_with_songs, 1):
        audio_file, success = download_and_trim_song(player, i, len(players_with_songs))
        if success and audio_file:
            successful_files.append(audio_file)
        else:
            failed_songs.append(player)

    # Generate sounds.json (includes all players)
    generate_sounds_json(players, successful_files)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total players: {len(players)}")
    print(f"Players with songs: {len(players_with_songs)}")
    print(f"  - Successful downloads: {len(successful_files)}")
    print(f"  - Failed downloads: {len(failed_songs)}")
    print(f"Players without songs (disabled): {len(players_without_songs)}")

    if failed_songs:
        print("\nFailed song downloads:")
        for player in failed_songs:
            print(f"  - {player['name']} (#{player['player_num']}) - {player['song_title']}")

    if players_without_songs:
        print("\nPlayers without songs (buttons will be disabled):")
        for player in players_without_songs:
            print(f"  - {player['name']} (#{player['player_num']})")

    print("\nNext steps:")
    print("1. Test the web app to verify disabled buttons work correctly")
    print("2. Check that all songs play correctly")
    print("3. Verify timestamps are correct")

if __name__ == '__main__':
    main()
