"""
Copyright (c) 2021, Gwavitie
All rights reserved.

This source code is licensed under the BSD-style license found in the
LICENSE file in the root directory of this source tree.
"""
import mouse
import keyboard
import time
import os.path
from os import path
import glob
import sys
import math
from math import sqrt


def read_config():
    def parse_config(conf):
        parsed_conf = {}
        for line in conf.split('\n'):
            if line.strip() != '' and not line.strip().startswith('#'):
                ops = line.split('=')
                if len(ops) == 1:
                    key, value = ops[0], ''
                else:
                    key, value = ops[0], "=".join(ops[1:])
                parsed_conf[key.strip()] = value.strip()
        return parsed_conf

    config_filepath = False
    game_folder = 'C:/Users/{}/AppData/Local/osu!'.format(os.environ.get('USERNAME'))  # noq

    while not os.path.isdir(game_folder):
        print('osu!\'s game directory was not found, please manually enter the path.')  # noqa
        game_folder = input('Path to osu! game folder: ')

    for file in os.listdir(game_folder):
        if file.startswith('osu!.') and file.endswith('.cfg') and len(file.split('.')) > 2:
            config_filepath = os.path.join(
                game_folder, file).replace('\\', '/')

    if config_filepath == False:
        return {}

    with open(config_filepath, 'r', encoding="utf8") as f:
        config_file = parse_config(f.read())  # noqa
    return config_file


config = read_config()

movements = []
time_points = []
beat_lengths = []
slider_points = []
resolution_offsets = {
    (1920, 1080): (-170.6666666666666666666667, -56)
}
songs_dir = ''
resolution = int(config['Width']), int(config['Height'])

if config['Fullscreen'] == '1':
    resolution = int(config['WidthFullscreen']), int(config['HeightFullscreen'])

if resolution not in resolution_offsets:
    print('The resolution osu is running at is not currently supported by this program.')  # noqa
    sys.exit(1)

offset_x, offset_y = resolution_offsets[resolution]
framerate = int(config['CustomFrameLimit'])


def setSongsFolder():
    global songs_dir
    if songs_dir != '':
        return
    if os.path.isdir('C:/Users/{}/AppData/Local/osu!/Songs'.format(os.environ.get('USERNAME'))):
        songs_dir = 'C:/Users/{}/AppData/Local/osu!/Songs'.format(os.environ.get('USERNAME'))
    else:
        user_input = input('Enter the path to the folder named "Songs" inside your osu! game directory: ')  # noqa
        while not os.path.isdir(user_input):
            print('Please enter a valid path.')
            user_input = input('Enter the path to the folder named "Songs" inside your osu! game directory: ')  # noqa
        songs_dir = user_input.replace('\\', '/')


setSongsFolder()


def search():
    # ===================================
    # reset previous calculations
    global movements
    global time_points
    global beat_lengths
    global slider_points
    movements = []
    time_points = []
    beat_lengths = []
    slider_points = []
    # ===================================

    songs_dir_glob = songs_dir + ('*' if songs_dir[-1] == '/' else '/*')
    beatmap = input("Enter Beatmap Name: ").strip()
    songs = glob.glob(songs_dir_glob, recursive=True)

    for song in songs:
        if beatmap.lower() in song.lower():
            beatmap = song

    versions = [os.path.join(beatmap, x)
                for x in os.listdir(beatmap) if '.osu' in x]

    for num in range(len(versions)):
        diff = path.split(versions[num])
        print("{}: {}".format(num+1, diff[-1]))

    beatmap = input("Select Difficulty: ").strip()
    beatmap = versions[int(beatmap)-1]

    osu_file = (open(beatmap, encoding="utf8")).read()
    slider_multiplier = ""

    for char in osu_file[osu_file.find("SliderMultiplier:") + len("SliderMultiplier:"):]:
        if not char == "\n":
            slider_multiplier += char
        else:
            break

    slider_multiplier = float(slider_multiplier)
    hit_objects = osu_file[osu_file.find("[HitObjects]") + len("[HitObjects]") + 1:]  # noqa

    while hit_objects[-1] == "\n":
        hit_objects = hit_objects[:-1]

    hit_objects = hit_objects.split("\n")
    timing_points = osu_file[osu_file.find("[TimingPoints]") + len("[TimingPoints]") + 1:osu_file.find("[Colours]")]  # noqa

    if timing_points.count("[HitObjects]") == 1:
        timing_points = timing_points[:timing_points.find("[HitObjects]")]

    while timing_points[-1] == "\n":
        timing_points = timing_points[:-1]

    timing_points = timing_points.split("\n")

    for line in timing_points:
        info = line.split(",")

        if int(info[6]) == 1:
            beat_lengths.append([float(info[0])/1000, float(info[1])/1000])
            standard_length = float(info[1])/1000
        else:
            multiplier = (float(info[1][1:])/100)
            beat_lengths.append([float(info[0])/1000, standard_length*multiplier])  # noqa

    for line in hit_objects:
        if "|" in line:
            slider(line, slider_multiplier)
        else:
            diff = line.split(",")
            if len(diff) <= 6:
                circle(line)
            else:
                spinner(line)

    temp_movements = []
    temp_time_points = []

    for num in range(len(movements)-1):
        if (len(movements[num]) == 3 and movements[num][2] == 0) or (len(movements[num]) == 3 and movements[num][2] == 3):
            frames = abs(int(round((time_points[num+1] - time_points[num])*framerate, 0)))  # noqa

            if frames != 0:
                change_x = (movements[num+1][0] - movements[num][0])/frames
                change_y = (movements[num+1][1] - movements[num][1])/frames
                change_time = abs((time_points[num+1] - time_points[num])/frames)  # noqa
                next_index = len(temp_movements)

                for add_num in range(frames, 0, -1):
                    temp_movements.append([[movements[num][0]+change_x*add_num, movements[num][1]+change_y*add_num], num+next_index+1])  # noqa
                    temp_time_points.append([time_points[num]+change_time*add_num, num+next_index+1])  # noqa

    for num in range(len(temp_movements)):
        movements.insert(temp_movements[num][1], temp_movements[num][0])
        time_points.insert(temp_time_points[num][1], temp_time_points[num][0])

    offset = time_points[0]

    for num in range(len(time_points)):
        time_points[num] = time_points[num]-offset

    print("calculations finished")


def slider(line, slider_multiplier):
    slider_points = []
    points = line.split("|")

    while points[-1].count(",") <= 1:
        del points[-1]

    if len(points) > 1:
        if len(points[-1]) == 1:
            points = points[:-1]

        info = points[0].split(",")
        slider_points.append([(int(info[0]) - offset_x)*2.25, (int(info[1]) - offset_y)*2.25])  # noqa
        compare_time = int(info[2])/1000
        info = points[-1].split(",")
        length = float(info[2])
        slides = int(info[1])

        for beat_length in beat_lengths:
            if round(beat_length[0], 3) <= compare_time:
                current_beat_length = beat_length[1]

        add_time = length/(slider_multiplier*100)*current_beat_length
        frames = int(round((add_time*framerate), 0))
        change_time = ((add_time)/frames)

        if len(points) > 2:
            count = 1

            for point in points[1:-1]:
                info = point.split(":")
                slider_points.append([(int(info[0]) - offset_x)*2.25, (int(info[1]) - offset_y)*2.25])  # noqa
                count += 1

        info = points[-1].split(",")
        info = info[0].split(":")
        slider_points.append([(int(info[0]) - offset_x)*2.25, (int(info[1]) - offset_y)*2.25])  # noqa

        if "B" in line:
            for frame in range(frames+1):
                bezier(slider_points, frames, frame)
                time_points.append(compare_time+frame*change_time)

        elif "L" in line:
            part = add_time/(len(slider_points)-1)
            index = len(movements)
            point_length = (len(slider_points))

            for num in range(len(slider_points)):
                movements.append(slider_points[num])
                time_points.append(compare_time+(part*num))

            linear(index, point_length)

        elif "P" in line:
            for frame in range(frames+1):
                bezier(slider_points, frames, frame)
                time_points.append(compare_time+frame*change_time)

        elif "C" in line:
            catmull(line)

        movement_length = frames+1

        if slides > 1:
            repeat(slides, movement_length, add_time)

        movements[-1*(movement_length)*slides+(slides-1)].append(1)
        movements[-1].append(0)


def bezier(point_list, times, t):
    new_list = []
    if len(point_list) > 1:
        for num in range(len(point_list)-1):
            x = (1-((1/times)*t)) * \
                point_list[num][0]+((1/times)*t)*point_list[num+1][0]
            y = (1-((1/times)*t)) * \
                point_list[num][1]+((1/times)*t)*point_list[num+1][1]
            new_list.append([x, y])
        return bezier(new_list, times, t)

    else:
        movements.append(point_list[0])


def linear(index, point_length):
    temp_movements = []
    temp_time_points = []

    for num in range(index, index+point_length-1):
        frames = abs(int(round((time_points[num+1] - time_points[num])*framerate, 0)))  # noqa

        if frames != 0:
            change_x = (movements[num+1][0] - movements[num][0])/frames
            change_y = (movements[num+1][1] - movements[num][1])/frames
            change_time = abs((time_points[num+1] - time_points[num])/frames)
            next_index = len(temp_movements)

            for add_num in range(frames, 0, -1):
                temp_movements.append([[movements[num][0]+change_x*add_num, movements[num][1]+change_y*add_num], num+next_index+1])  # noqa
                temp_time_points.append([time_points[num]+change_time*add_num, num+next_index+1])  # noqa

    for num in range(len(temp_movements)):
        movements.insert(temp_movements[num][1], temp_movements[num][0])
        time_points.insert(temp_time_points[num][1], temp_time_points[num][0])


def perfect_circle(point_list, times):
    pass


def catmull(line):
    pass


def circle(line):
    info = line.split(",")
    movements.append([(int(info[0]) - offset_x)*2.25,
                     (int(info[1]) - offset_y)*2.25, 3])
    time_points.append(int(info[2])/1000)


def spinner(line):
    pass


def repeat(slides, movement_length, add_time):
    for slide in range(slides-1):
        slider_movements = []

        for movement in movements[-(movement_length):len(movements)-1]:
            unlink = movement[:]
            slider_movements.append(unlink)

        slider_movements.reverse()

        for point in time_points[-(movement_length-1):len(time_points)]:
            time_points.append(point+add_time)

        for movement in slider_movements:
            movements.append(movement)


def play():
    keyboard.wait('q')
    start = time.perf_counter()

    for num in range(len(movements)):
        while time_points[num] > (time.perf_counter()-start):
            pass

        if len(movements[num]) == 3:
            if movements[num][2] == 3:
                mouse.move(movements[num][0], movements[num][1], duration=0)
                mouse.click(button='left')

            if movements[num][2] == 1:
                mouse.move(movements[num][0], movements[num][1], duration=0)
                mouse.press(button='left')

            if movements[num][2] == 0:
                mouse.move(movements[num][0], movements[num][1], duration=0)
                mouse.release(button='left')
        else:
            mouse.move(movements[num][0], movements[num][1], duration=0)

        if keyboard.is_pressed('esc'):
            break
