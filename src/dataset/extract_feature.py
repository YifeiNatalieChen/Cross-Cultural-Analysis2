#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import argparse
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
from tqdm import tqdm
from tensorflow import keras


# tf.config.experimental.set_memory_growth(tf.config.experimental.list_physical_devices('GPU')[0], True)

IMAGE_PAIR_BATCH_SIZE = 128


class Extractor:
    def __init__(self):
        vgg19 = keras.applications.vgg19.VGG19()
        self.model = keras.models.Sequential()
        for layer in vgg19.layers[:-1]:
            self.model.add(layer)

    def extract_features(self, frames):
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
        features = list(extractor.extract_features(frames))
        for k, feature, text in zip(batch_keys, features, texts):
            result[k] = (feature, text)
        del images, frames
    return result


def extract_feature(input_dir, output_path='output'):
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f'No such file or directory: {input_dir}')
    output_dir = os.path.dirname(output_path)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    open(output_path, 'wb').close()

    extractor = Extractor()
    for image_pair_filename in os.listdir(input_dir):
        image_pair_path = os.path.join(input_dir, image_pair_filename)
        with open(image_pair_path, 'rb') as f:
            image_text_pairs = pickle.load(f)
        if len(image_text_pairs) > 0:
            print("Start extracting features: " + image_pair_filename)
            result = get_image_features(image_text_pairs, extractor)
            feature_path = os.path.join(output_path, image_pair_filename)
            with open(feature_path, 'ab') as f:
                pickle.dump(result, f)
            del result


def main():
    print('Extracting Features')
    print('------------------------')
    parser = argparse.ArgumentParser(
        description='Extract features from image and text pairs')
    parser.add_argument('input', help='directory of pairs data files')
    parser.add_argument('-o', '--output', default='output', help='path to output data file')
    args = parser.parse_args()
    extract_feature(args.input, args.output)


if __name__ == '__main__':
    main()
