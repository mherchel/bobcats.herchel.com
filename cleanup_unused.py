#!/usr/bin/env python3
"""
Cleanup script to remove unused audio files from the sounds/ directory.
Compares audio files against sounds.json to find orphaned files.
"""

import json
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SOUNDS_DIR = SCRIPT_DIR / "sounds"
SOUNDS_JSON_PATH = SCRIPT_DIR / "sounds.json"

def main():
    print("Lacrosse Goal Songs - Cleanup Unused Audio Files")
    print("=" * 60)

    # Load sounds.json to get list of active files
    if not SOUNDS_JSON_PATH.exists():
        print(f"✗ Error: {SOUNDS_JSON_PATH} not found")
        print("  Run process_songs.py first to generate sounds.json")
        return

    with open(str(SOUNDS_JSON_PATH), 'r', encoding='utf-8') as f:
        sounds_data = json.load(f)

    # Get list of active audio files
    active_files = set()
    for entry in sounds_data:
        audio_file = entry['audioFile'] + '.webm'
        active_files.add(audio_file)

    print(f"\n✓ Found {len(active_files)} active audio files in sounds.json")

    # Get list of actual files in sounds/ directory
    if not SOUNDS_DIR.exists():
        print(f"✗ Error: {SOUNDS_DIR} not found")
        return

    actual_files = set()
    for file in SOUNDS_DIR.glob('*.webm'):
        actual_files.add(file.name)

    print(f"✓ Found {len(actual_files)} .webm files in sounds/ directory")

    # Find unused files
    unused_files = actual_files - active_files

    if not unused_files:
        print("\n✓ No unused files found. All audio files are referenced in sounds.json")
        return

    print(f"\n⚠ Found {len(unused_files)} unused audio file(s):")
    print()

    total_size = 0
    for filename in sorted(unused_files):
        filepath = SOUNDS_DIR / filename
        size = filepath.stat().st_size
        total_size += size
        size_kb = size / 1024
        print(f"  • {filename} ({size_kb:.1f} KB)")

    print()
    print(f"Total size: {total_size / 1024 / 1024:.2f} MB")
    print()

    # Ask for confirmation
    response = input("Delete these files? (yes/no): ").strip().lower()

    if response in ('yes', 'y'):
        print()
        for filename in unused_files:
            filepath = SOUNDS_DIR / filename
            filepath.unlink()
            print(f"  ✓ Deleted: {filename}")

        print()
        print(f"✓ Removed {len(unused_files)} unused audio file(s)")
        print(f"✓ Freed {total_size / 1024 / 1024:.2f} MB of disk space")
    else:
        print("\n✓ No files deleted")

if __name__ == '__main__':
    main()
