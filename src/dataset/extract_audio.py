#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import argparse
import os
import subprocess


def extract_audio(video_dir, audio_dir='audios', audio_type='flac', audio_channel=1,
                  replace=False):
    if not os.path.isdir(audio_dir):
        os.makedirs(audio_dir)
    video_list = os.listdir(video_dir)
    for video_filename in video_list:
        video_path = os.path.join(video_dir, video_filename)
        if not os.path.isfile(video_path):
            continue
        dot_pos = video_filename.rfind('.')
        audio_filename = (video_filename[:dot_pos] if dot_pos != -1 else video_filename) + '.' + audio_type
        audio_path = os.path.join(audio_dir, audio_filename)
        if not replace and os.path.isfile(audio_path):
            continue
        # https://ffmpeg.org/ffmpeg.html
        subprocess.call(['ffmpeg', '-y', '-i', video_path, '-f', audio_type, '-ac',
                         str(audio_channel), '-vn', audio_path])


def main():
    parser = argparse.ArgumentParser(description='Extract audios from videos')
    parser.add_argument('input', help='directory of videos to process')
    parser.add_argument('-o', '--output', default='audios', help='directory of audios to output')
    parser.add_argument('-f', '--audio-format', default='flac', help='output audios format')
    parser.add_argument('-c', '--audio-channel', type=int, default=1, help='default is mono channel')
    parser.add_argument('-r', '--replace', action='store_true', help='whether to replace existing results')
    args = parser.parse_args()
    extract_audio(args.input, args.output, args.audio_format, args.audio_channel, args.replace)


if __name__ == '__main__':
    main()
