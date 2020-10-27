#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import argparse
import json
import ntpath
import os
from google.cloud import storage
from google.cloud.speech_v1p1beta1 import types, SpeechClient


class Transcriber:
    def __init__(self, gs_bucket, gs_dir):
        self.gs_bucket = gs_bucket
        self.gs_dir = gs_dir
        self.client = SpeechClient()
        self.bucket = storage.Client().get_bucket(gs_bucket)

    def translate_with_timestamps(self, gs_uri, encoding, mode, hint):
        audio = types.RecognitionAudio(uri=gs_uri)
        config = types.RecognitionConfig(
            encoding=encoding,
            language_code=mode,
            enable_word_time_offsets=True,
            speech_contexts=[types.SpeechContext(phrases=hint)],
            enable_word_confidence=True
        )
        operation = self.client.long_running_recognize(config=config, audio=audio)
        results = []
        for result in operation.result().results:
            alternatives = result.alternatives
            if not alternatives:
                continue
            alternative = alternatives[0]
            results.append([alternative.transcript, alternative.confidence])
            for word_info in alternative.words:
                word = word_info.word
                start_time = word_info.start_time.seconds + word_info.start_time.microseconds * 1e-6
                end_time = word_info.end_time.seconds + word_info.end_time.microseconds * 1e-6
                confidence = word_info.confidence
                results.append([word, start_time, end_time, confidence])
        return results

    def upload_to_gcs(self, audio_path):
        audio_filename = ntpath.basename(audio_path)
        gs_path = os.path.join(self.gs_dir, audio_filename)
        self.bucket.blob(gs_path).upload_from_filename(audio_path)
        return self.generate_uri(gs_path)

    def delete_from_gcs(self, audio_filename):
        gs_path = os.path.join(self.gs_dir, audio_filename)
        self.bucket.delete_blob(gs_path)

    def generate_uri(self, gs_path):
        return 'gs://' + os.path.join(self.gs_bucket, gs_path)


def extract_transcript(audio_dir, key_file, gs_bucket, trans_dir='transcripts', mode='en-US', audio_type='flac',
                       gs_dir='audios', threshold=0.85, hint=None, replace=False):
    '''
    How to use this function: 
    1. Go to GCP
    2. Enable Speech-to-Text API
    3. Go to APIs & Admin - Credentials and create a new credential for a new service account
    4. Create a new key for the service account and download the key
    5. Place the key under the directory where you call this function
    '''
    trans_type = 'json'
    if not os.path.isdir(trans_dir):
        os.makedirs(trans_dir)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_file
    transcriber = Transcriber(gs_bucket, gs_dir)
    with open(os.path.join(trans_dir, 'error_log.txt'), 'w') as f_log:
        # Iterate through the list of files in the specified audio directory
        for audio_filename in os.listdir(audio_dir):
            # Create path by putting the audio directory and audio file name
            audio_path = os.path.join(audio_dir, audio_filename)
            # If the audio file does not end in the proper format or if the given path is not a true file, then skip to the next audio file
            if not (audio_filename.endswith('.' + audio_type) and os.path.isfile(audio_path)):
                continue
            # Return the highest index of the dot
            dot_pos = audio_filename.rfind('.')
            # Note: The trans_type is set to json above
            transcript_filename = audio_filename[:dot_pos] + '.' + trans_type
            transcript_path = os.path.join(trans_dir, transcript_filename)
            # If we already have created a transcript of the same name then go on to the next audio file
            if not replace and os.path.isfile(transcript_path):
                continue

            print('===> Start uploding file: ' + audio_filename)
            gs_uri = transcriber.upload_to_gcs(audio_path)
            print('===> Finish uploading file: ' + audio_filename)
            try:
                transcriber_results = transcriber.translate_with_timestamps(gs_uri, audio_type.upper(), mode, hint)
                result = []
                skip = False
                for item in transcriber_results:
                    if len(item) == 2:
                        trans, confidence = item
                        if confidence < threshold:
                            print('===> Confidence value too low, dropping this transcript')
                            skip = True
                            continue
                        if skip:
                            skip = False
                        result.append({'transcript': trans, 'confidence': confidence, 'words': []})
                        print('--------------------------- transcript ---------------------------')
                        print(trans)
                        print('--------------------------- confidence ---------------------------')
                        print(confidence)
                    elif not skip:
                        word, start_time, end_time, confidence = item
                        result[-1]['words'].append(
                            {'word': word, 'start': start_time, 'end': end_time, 'confidence': confidence})
                    with open(transcript_path, 'w') as f:
                        json.dump(result, f)
            except Exception as e:
                print('===> Error: writing log...')
                f_log.write(audio_filename + str(e) + '\n')
            print('===> Delete file: ' + audio_filename)
            transcriber.delete_from_gcs(audio_filename)


def main():
    parser = argparse.ArgumentParser(description='Extract transcripts from audios')
    parser.add_argument('input', help='directory of audios to process')
    parser.add_argument('key', help='key file for google cloud api')
    parser.add_argument('gs_bucket', type=str, help='google cloud storage bucket')
    parser.add_argument('-o', '--output', default='transcripts', help='directory of transcripts to output')
    parser.add_argument('-l', '--language', default='en-US', help='language of audios')
    parser.add_argument('-f', '--audio-format', default='flac', help='audios format')
    parser.add_argument('-d', '--gs-dir', type=str, default='audios',
                        help='google cloud storage directory for audio files')
    parser.add_argument('-s', '--threshold', type=float, default=0.85,
                        help='threshold for dropping unconfident transcripts')
    parser.add_argument('-t', '--hint', nargs='*', help='hint words for speech recognition')
    parser.add_argument('-r', '--replace', action='store_true', help='whether to replace existing results')
    args = parser.parse_args()
    mode = 'cmn-Hans-CN' if args.language[0].lower() == 'c' else 'en-US'
    hint = args.hint if args.hint else []
    extract_transcript(args.input, args.key, args.gs_bucket, args.output, mode, args.audio_format, args.gs_dir,
                       args.threshold, hint, args.replace)


if __name__ == '__main__':
    main()
