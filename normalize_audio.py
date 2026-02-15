#!/usr/bin/env python3
"""
Audio Normalization Script
Normalizes all audio files in sounds/ directory to consistent volume levels.
Uses FFmpeg's loudnorm filter (EBU R128 standard) for perceived loudness normalization.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SOUNDS_DIR = SCRIPT_DIR / "sounds"
TEMP_DIR = Path("/tmp/lacrosse_normalize")

# Loudness normalization targets (EBU R128 standard)
TARGET_I = -16.0  # Integrated loudness target (LUFS)
TARGET_LRA = 11.0  # Loudness range target
TARGET_TP = -1.5   # True peak target (dBTP)

def normalize_file(input_path, output_path):
    """
    Normalize audio file using FFmpeg's loudnorm filter (two-pass).

    Two-pass process:
    1. First pass: Analyze audio and get loudness measurements
    2. Second pass: Apply normalization with measured values
    """

    # First pass: measure loudness
    measure_cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-af', f'loudnorm=I={TARGET_I}:LRA={TARGET_LRA}:TP={TARGET_TP}:print_format=json',
        '-f', 'null',
        '-'
    ]

    result = subprocess.run(measure_cmd, capture_output=True, text=True)

    # Parse the JSON output from stderr
    output_lines = result.stderr.split('\n')
    measurements = {}
    in_json = False

    for line in output_lines:
        if '{' in line:
            in_json = True
        if in_json:
            if 'input_i' in line:
                measurements['input_i'] = line.split(':')[1].strip().rstrip(',').strip('"')
            elif 'input_lra' in line:
                measurements['input_lra'] = line.split(':')[1].strip().rstrip(',').strip('"')
            elif 'input_tp' in line:
                measurements['input_tp'] = line.split(':')[1].strip().rstrip(',').strip('"')
            elif 'input_thresh' in line:
                measurements['input_thresh'] = line.split(':')[1].strip().rstrip(',').strip('"')
            elif 'target_offset' in line:
                measurements['target_offset'] = line.split(':')[1].strip().rstrip(',').strip('"')

    # Second pass: apply normalization with measured values
    if measurements:
        normalize_cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-af', (f'loudnorm=I={TARGET_I}:LRA={TARGET_LRA}:TP={TARGET_TP}:'
                   f'measured_I={measurements["input_i"]}:'
                   f'measured_LRA={measurements["input_lra"]}:'
                   f'measured_TP={measurements["input_tp"]}:'
                   f'measured_thresh={measurements["input_thresh"]}:'
                   f'offset={measurements["target_offset"]}:'
                   f'linear=true:print_format=summary'),
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-y',
            str(output_path)
        ]
    else:
        # Fallback: single-pass normalization if measurements failed
        normalize_cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-af', f'loudnorm=I={TARGET_I}:LRA={TARGET_LRA}:TP={TARGET_TP}',
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-y',
            str(output_path)
        ]

    result = subprocess.run(normalize_cmd, capture_output=True, text=True)

    return result.returncode == 0

def main():
    print("Lacrosse Goal Songs - Audio Normalization")
    print("=" * 60)
    print(f"Target: {TARGET_I} LUFS (EBU R128 standard)")
    print("=" * 60)

    if not SOUNDS_DIR.exists():
        print(f"✗ Error: {SOUNDS_DIR} not found")
        return

    # Get all webm files
    audio_files = list(SOUNDS_DIR.glob('*.webm'))

    if not audio_files:
        print("✗ No .webm files found in sounds/ directory")
        return

    print(f"\nFound {len(audio_files)} audio file(s)")
    print()

    # Create temp directory
    TEMP_DIR.mkdir(exist_ok=True)

    # Process each file
    success_count = 0
    failed_files = []

    for i, audio_file in enumerate(audio_files, 1):
        filename = audio_file.name
        print(f"[{i}/{len(audio_files)}] Processing {filename}...", end=" ")

        temp_output = TEMP_DIR / filename

        try:
            if normalize_file(audio_file, temp_output):
                # Replace original with normalized version
                temp_output.replace(audio_file)
                print("✓")
                success_count += 1
            else:
                print("✗ Failed")
                failed_files.append(filename)
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            failed_files.append(filename)

    # Cleanup
    if TEMP_DIR.exists():
        for f in TEMP_DIR.glob('*'):
            f.unlink()
        TEMP_DIR.rmdir()

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(audio_files)}")
    print(f"Normalized: {success_count}")
    print(f"Failed: {len(failed_files)}")

    if failed_files:
        print("\nFailed files:")
        for f in failed_files:
            print(f"  • {f}")

    print()
    print("✓ Audio normalization complete!")
    print("  All clips now have consistent volume levels.")

if __name__ == '__main__':
    main()
