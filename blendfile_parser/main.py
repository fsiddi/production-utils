#!/usr/bin/env python

import os
import blendfile
import argparse

def query_main_scene(filepath, callbacks):
    """Return the equivalent to bpy.context.scene"""
    with blendfile.open_blend(filepath) as blend:
        # There is no bpy.context.scene, we get it from the main window
        window_manager = [block for block in blend.blocks if block.code == b'WM'][0]
        window = window_manager.get_pointer(b'winactive')
        screen = window.get_pointer(b'screen')
        scene = screen.get_pointer(b'scene')

        output = []
        for callback in callbacks:
            output.append(callback(scene))
        return output

def get_frames(filepath):
    def get_frame_start(scene):
        return scene.get((b'r', b'sfra'))

    def get_frame_end(scene):
        return scene.get((b'r', b'efra'))

    def get_frame_current(scene):
        return scene.get((b'r', b'cfra'))

    return query_main_scene(filepath, [
        get_frame_start,
        get_frame_end,
        get_frame_current,
        ])

    print(frame_start)

parser = argparse.ArgumentParser(description='Parse file')
parser.add_argument('files', metavar='N', type=str, nargs='+',
                    help='Blendfiles')
args = parser.parse_args()

for f in args.files:
    print(f)
    start, end, current = get_frames(f)
    print('Start frame: {}'.format(start))
    print('End frame: {}'.format(end))
    print('Current frame: {}'.format(current))
