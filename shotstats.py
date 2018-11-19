#!/usr/bin/env python3

import argparse
import csv
import datetime
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


parser = argparse.ArgumentParser(description='Generate shots stats.')
parser.add_argument('-i', '--in_path', help='Input path', required=True)
parser.add_argument('-o', '--output_file', help='Output file path', default='out_grid.png')
parser.add_argument('-y', '--skip_confirmation', help='Skip confirmation', action='store_true')
parser.add_argument('-f', '--framerate', help='Framerate', default=24)
parser.add_argument('--memory_unit', default='G')
parser.add_argument('--render_time_unit', help='How display render time', default='m')
args = parser.parse_args()


def which(command):
    """Check if command is available and return its path."""
    command_path = shutil.which(command)
    if command_path is None:
        print(f'{command} is required to run this script it, but it was not found.')
        sys.exit()
    return command_path


toolset = {
    'ffmpeg': os.environ.get('FFMPEG_BIN', 'ffmpeg'),
    'ffprobe': os.environ.get('FFPROBE_BIN', 'ffprobe'),
    'exrheader': os.environ.get('EXRHEADER_BIN', 'exrheader'),
    'gnuplot': os.environ.get('GNUPLOT_BIN', 'gnuplot'),
    'identify': os.environ.get('IDENTIFY_BIN', 'identify'),
}

# Get render time and memory from frames

# If exr, use exrheader (we will also need jpeg previews later)


def parse_metadata(s):
    result = re.search('"(.*)"', s)
    return result.group(1)


def parse_memory(s):
    """Get the amount of memory used.

    We strip the last char, and assume it's M. The we cast to float.
    """
    s = parse_metadata(s)
    memory_in_mb = float(s[:-1])
    if args.memory_unit == 'G':
        m = memory_in_mb / 1024
    else:
        m = memory_in_mb
    return m


def parse_render_time(s):
    """Get the render time in seconds."""
    s = parse_metadata(s)
    time_array = s.split(':')
    if len(time_array) < 2:  # Only seconds
        time_in_seconds = float(s)
    elif len(time_array) < 3:  # Minutes and seconds
        time_in_seconds = int(time_array[0]) * 60 + float(time_array[1])
    elif len(time_array) < 4:  # Hours, minutes and seconds
        time_in_seconds = int(time_array[0]) * 3600 + int(time_array[1]) * 60 + float(time_array[2])
    else:
        time_in_seconds = float(0)

    if args.render_time_unit == 'm':
        t = time_in_seconds / 60
    else:
        t = time_in_seconds
    return t


def parse_frame_number(s):
    """Get the frame number."""
    s = parse_metadata(s)
    return int(s)


def parse_exr_frames(frames_list):
    """Parse EXR frames using the exrheader command."""
    frames_stats = []
    for frame in frames_list:
        exrheader_command = [
            toolset['exrheader'],
            frame
        ]
        p = subprocess.Popen(exrheader_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        lines = iter(out.decode('utf-8').splitlines())
        frame_stats = {'name': frame.stem}
        for line in lines:
            if line.startswith('Memory'):
                frame_stats['memory_in_mb'] = parse_memory(line)
            elif line.startswith('RenderTime'):
                frame_stats['render_time_in_s'] = parse_render_time(line)
            elif line.startswith('Frame'):
                frame_stats['frame_number'] = parse_frame_number(line)
        frames_stats.append(frame_stats)

    return frames_stats

# If png use identify -verbose

# Get current directory
cwd = Path(os.getcwd())

# Get absolute path of input dir (if relative it will be combined with cwd)
in_dir_absolute_path = cwd.joinpath(args.in_path)

# Look for exr files
frames = sorted(in_dir_absolute_path.glob('*.exr'))
if frames:
    stats = parse_exr_frames(frames)
    with open('frames_stats.csv', 'w', newline='') as csvfile:
        fieldnames = ['frame_number', 'name', 'memory_in_mb', 'render_time_in_s']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()
        for s in stats:
            writer.writerow(s)
        print('frames_stats.csv is ready.')
else:
    # TODO(fsiddi) Handle PNG images
    print('No images found.')
    sys.exit()

# TODO(fsiddi) Get frame resolution

# Make chart with memory usage and render time, using the size of frame

gnuplot_command = [
    'gnuplot',
    '-c',
    'gnuplot_chart.tpl',
]

subprocess.call(gnuplot_command)


# Combine the chart with images sequence and overlay the playhead


# For instance if you've got a 3 minutes song and a video width of 1280:
#
# 3 minutes = 3x60 = 180 seconds.
# "Width of your video / Duration of your video" = 1280 / 180 = 7.11 pixels / second.
# 7.11 is the value to use instead of 5 in -W+(t)*5,.


# ffmpeg -i extract/2018_11_09_002-spring.mov -i chart.png -i playhead.png -filter_complex "overlay, overlay=x='if(gte(t,0), -w+(t)*4.87, NAN)':y=0" output.mp4

# ffmpeg -framerate 24 -i extract/frames/%03d.jpg -i chart.png -i playhead.png -filter_complex "overlay, overlay=x='if(gte(t,0), -w+(t)*364.1, NAN)':y=0" output.mp4

pixel_per_second = 2048 / (len(frames) / args.framerate)

overlay_string = f"overlay, overlay=x='if(gte(t,0), -w+(t)*{pixel_per_second}, NAN)':y=0"

# Get the number of the first frame of the sequence
start_number = stats[0]['frame_number']

ffmpeg_command = [
    'ffmpeg',
    '-framerate',
    f'{args.framerate}',
    '-start_number',
    f'{start_number}',
    '-i',
    f'{args.in_path}%6d.jpg',  # TODO(fsiddi) also support PNG extension
    '-i',
    'chart.png',
    '-i',
    'playhead.png',
    '-filter_complex',
    f'{overlay_string}',
    f'{in_dir_absolute_path.name}-{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.mp4'
]

subprocess.call(ffmpeg_command)