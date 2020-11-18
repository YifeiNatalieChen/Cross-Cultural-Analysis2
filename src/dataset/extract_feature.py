#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import argparse
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
import warnings
import tensorflow as tf
from tqdm import tqdm
from tensorflow import keras


#tf.config.experimental.set_memory_growth(tf.config.experimental.list_physical_devices('GPU')[0], True)

IMAGE_PAIR_BATCH_SIZE = 128


class Extractor:
    def __init__(self):
        vgg19 = keras.applications.vgg19.VGG19()
        self.model = keras.models.Sequential()
        for layer in vgg19.layers[:-1]:
            self.model.add(layer)

    def extract_frames(self, frames):
        features = self.model.predict(frames, batch_size=16)
        return features


def get_image_features(image_text_pairs, extractor):
    shape = (224, 224)
    keys = list(image_text_pairs.keys())
    result = {}

    # Process image pairs in batch
    for i in tqdm(range(len(keys)//IMAGE_PAIR_BATCH_SIZE+1)):
        # Load the batch of keys and images
        images = {}
        if (i+1)*IMAGE_PAIR_BATCH_SIZE < len(keys):
            batch_keys = keys[i *
                              IMAGE_PAIR_BATCH_SIZE:(i+1)*IMAGE_PAIR_BATCH_SIZE]
        else:
            batch_keys = keys[i*IMAGE_PAIR_BATCH_SIZE:]
        for key in batch_keys:
            frame = plt.imread(image_text_pairs[key][0])
            if frame.shape[-1] > 3:
                frame = frame.T[:3].T
            frame *= 255
            images[key] = frame

        # Extract features
        frames = (np.stack([cv2.resize(images[k], shape)
                            for k in batch_keys]) / 255).astype(np.float32)
        texts = [image_text_pairs[k][1] for k in batch_keys]
        features = list(extractor.extract_frames(frames))
        for k, feature, text in zip(batch_keys, features, texts):
            result[k] = (feature, text)
        del images, frames
    return result


def extract_feature(input_frames, output_dir='output', input_frame_dir="input"):
    frame_type = 'png'
    if not os.path.exists(input_frames):
        raise FileNotFoundError(f'No such file or directory: {input_frames}')
    if not os.path.isdir(input_frames):
        # The new version fo extract_frame generate separate image pair files for each video
        # This might require some work to adapt to the new version of extract_frames
        warnings.warn(
            'This might require some work to adapt to the new version of extract_frames')
        image_text_pairs = {}
        for frame_filename in os.listdir(input_frames):
            if not frame_filename.endswith('.' + frame_type):
                continue
            dot_pos = frame_filename.rfind('.')
            frame_filename_without_postfix = frame_filename[:dot_pos]
            info = frame_filename_without_postfix.split('_')
            if len(info) == 1:
                vid = info
                ms = '0'
                text = ''
            elif len(info) == 2:
                vid, ms = info
                text = ''
            elif len(info) == 3:
                vid, ms, text = info
            else:
                continue
            ms = int(ms)
            frame_path = os.path.join(input_frames, frame_filename)
            frame = plt.imread(frame_path)
            if frame.shape[-1] > 3:
                frame = frame.T[:3].T
            frame *= 255
            image_text_pairs[(vid, ms)] = frame, text

    extractor = Extractor()
    for image_pair_filename in os.listdir(input_frames):
        image_pair_path = os.path.join(input_frames, image_pair_filename)
        with open(image_pair_path, 'rb') as f:
            image_text_pairs = pickle.load(f)
        if len(image_text_pairs) > 0:
            print("Start extracting features: " + image_pair_filename)
            result = get_image_features(image_text_pairs, extractor)
            # Save to output
            if not os.path.isdir(output_dir):
                os.makedirs(output_dir)
            with open(output_dir + "/" + image_pair_filename, 'wb') as f:
                pickle.dump(result, f)
            del result
    return True


def main():
    print('We are now in Extract Feature')
    print('------------------------')
    parser = argparse.ArgumentParser(
        description='Extract features from image and text pairs')
    parser.add_argument(
        'input', help='directory of frames or path to pairs data file')
    parser.add_argument('-o', '--output', default='output',
                        help='path to output data file')
    args = parser.parse_args()
    extract_feature(args.input, args.output)


if __name__ == '__main__':
    main()
