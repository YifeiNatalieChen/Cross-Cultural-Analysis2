#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import argparse
import cv2
import json
import matplotlib.pyplot as plt
import os
import pickle
from tqdm import tqdm


def extract_frame(trans_path, video_dir, frame_dir='output', data_dir='data'):
    frame_type = 'png'
    with open(trans_path) as f:
        trans_info = json.load(f)
    if not os.path.isdir(frame_dir):
        os.makedirs(frame_dir)
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    for video_filename in os.listdir(video_dir):
        image_text_pairs = {}
        video_path = os.path.join(video_dir, video_filename)
        if not os.path.isfile(video_path):
            continue
        dot_pos = video_filename.rfind('.')
        vid = video_filename[:dot_pos] if dot_pos != -1 else video_filename
        if vid not in trans_info:
            continue
        print('Now processing: ' + video_filename)
        capture = cv2.VideoCapture(video_path)

        for ms, text in tqdm(trans_info[vid]):
            capture.set(cv2.CAP_PROP_POS_MSEC, ms)
            ms = capture.get(cv2.CAP_PROP_POS_MSEC)
            frame = capture.read()[1]
            cleaned_word = ''.join(
                c.lower() if c.isalnum() else '-' for c in text)
            frame_filename = '_'.join([vid, str(round(ms)), cleaned_word]) + \
                             '.' + frame_type
            frame_path = os.path.join(frame_dir, frame_filename)
            plt.imsave(frame_path, frame)
            image_text_pairs[vid, round(ms)] = frame_path, text
        capture.release()

        image_text_pairs_path = os.path.join(data_dir, video_filename.split('.')[0])
        with open(image_text_pairs_path, 'wb') as f:
            pickle.dump(image_text_pairs, f)


def main():
    print('Extracting Frames')
    print('------------------------')
    parser = argparse.ArgumentParser(
        description='Extract frames from processed transcript and videos')
    parser.add_argument('input', help='path of processed transcript file')
    parser.add_argument('video_dir', help='directory of videos to process')
    parser.add_argument('-o', '--output', help='directory of frames to output')
    parser.add_argument('-d', '--data', default='data', help='path of output data')
    args = parser.parse_args()
    extract_frame(args.input, args.video_dir,
                  args.output, args.data)


if __name__ == '__main__':
    main()
