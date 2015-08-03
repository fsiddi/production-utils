#!/usr/bin/env python3
import os
import multiprocessing
import subprocess as sp
from tempfile import mkdtemp
from shutil import rmtree
from operator import floordiv


FFMPEG_BIN = "ffmpeg" # on Linux and Mac OS
CONVERT_BIN = "convert" # on Linux and Mac OS
RES_MOSAIC = '2048x858'
RES_TILE = '204x85'
TILE_SCALE = 6
TRIM_START = 600
TRIM_END = 14765
FILE_PATH = '/render/_mp4/png/'

processes_list_index_len = multiprocessing.cpu_count()
processes_list = []
for x in range(processes_list_index_len):
    processes_list.append([])

def parse_resolution(resolution):
    res_x, res_y = resolution.split('x')
    return [int(res_x), int(res_y)]

res_mosaic = parse_resolution(RES_MOSAIC)

if RES_TILE:
    res_tile = parse_resolution(RES_TILE)
if TILE_SCALE:
    tile_res_x = res_mosaic[0] / TILE_SCALE
    tile_res_y = res_mosaic[1] / TILE_SCALE
    res_tile = (tile_res_x, tile_res_y)

count_x, count_y = map(floordiv, res_mosaic, res_tile)
tiles_count = (count_x + 1) * (count_y + 1)

temp_tiles = mkdtemp()

if os.path.isfile(FILE_PATH):
    print ('is movie')
elif os.path.isdir(FILE_PATH):
    subprocess_list = []
    for root, dirs, files in os.walk(FILE_PATH):
        files.sort()
        if TRIM_END > 0 or TRIM_START > 0:
            # For removing film credits for example
            files = files[TRIM_START:TRIM_END]
        dir_files_count = len(files)
        samples = int(dir_files_count / tiles_count)
        frames_list = []
        if samples > 0:
            # Pick every other n file (according tothe sample count)
            files = files[::samples]
            # Otherwise we keep the list intact

        processes_list_index = 0
        for f in files:
            file_in = os.path.join(root, f)
            file_out = os.path.join(temp_tiles, f)
            command = [
                FFMPEG_BIN,
                '-i', file_in,
                '-loglevel', 'panic',
                '-vf',
                'scale={0}:{1}'.format(res_tile[0], res_tile[1]),
                file_out]

            # Place the command in one of the lists
            # processes_list[processes_list_index].append(command)
            # if processes_list_index >= processes_list_index_len - 1:
            #     processes_list_index = 0
            # else:
            #     processes_list_index += 1


            pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)
            subprocess_list.append(pipe)

    exit_codes = [p.wait() for p in subprocess_list]

    subprocess_list = []
    index = 0
    files_index = 1
    files_len = len(files)
    row = ['(']
    for f in files:
        file_in = os.path.join(temp_tiles, f)
        if index > count_x:
            row.append('+append')
            row.append(')')
            if files_index != files_len:
                row.append('(')
                row.append(file_in)
            index = 1
        else:
            row.append(file_in)
            if files_index == files_len:
                row.append('+append')
                row.append(')')
            index += 1
        files_index += 1

    row.extend(['-background', 'none', '-append', 'oo.png'])

    command = [CONVERT_BIN,
        ]
    command.extend(row)
    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10**8)
    subprocess_list.append(pipe)

exit_codes = [p.wait() for p in subprocess_list]
rmtree(temp_tiles)

print ("Done!")

