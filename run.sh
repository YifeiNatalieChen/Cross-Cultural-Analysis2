#!/usr/bin/env bash
src="$(dirname $0)/src"
results="$(dirname $0)/results"

echo "##############################################"
echo "get video metadata"
echo "##############################################"
# python3 $src/spidering/get_metadata.py "AlphaGo" -n 5 -o $results/AlphaGo/chinese/video_metadata -s bilibili qq iqiyi
# python3 $src/spidering/get_metadata.py "AlphaGo" -n 5 -o $results/AlphaGo/english/video_metadata -s youtube -k key.txt

echo "##############################################"
echo "download videos"
echo "##############################################"
# python3 $src/spidering/download.py $results/AlphaGo/chinese/video_metadata/metadata -ao $results/AlphaGo/chinese/audios -vo $results/AlphaGo/chinese/videos -s bilibili qq iqiyi
# python3 $src/spidering/download.py $results/AlphaGo/english/video_metadata/metadata -ao $results/AlphaGo/english/audios -vo $results/AlphaGo/english/videos -s youtube

echo "##############################################"
echo "dataset extract audios"
echo "##############################################"
# python3 $src/dataset/extract_audio.py $results/AlphaGo/chinese/videos -o $results/AlphaGo/chinese/audios
# python3 $src/dataset/extract_audio.py $results/AlphaGo/english/videos -o $results/AlphaGo/english/audios

echo "##############################################"
echo "dataset extract transcripts"
echo "##############################################"
# python3 $src/dataset/extract_transcript.py $results/AlphaGo/chinese/audios key.json [gcp-bucket-name] -o $results/AlphaGo/chinese/transcripts -l cmn-Hans-CN -d audios_cn -t "AlphaGo" "AlphaZero" "DeepMind"
# python3 $src/dataset/extract_transcript.py $results/AlphaGo/english/audios key.json [gcp-bucket-name] -o $results/AlphaGo/english/transcripts -l en-US -d audios_en -t "AlphaGo" "Lee Sedol" "Ke Jie"

echo "##############################################"
echo "dataset process transcript"
echo "##############################################"
# python3 $src/dataset/process_transcript.py $results/AlphaGo/chinese/transcripts -o $results/AlphaGo/chinese/processed_transcript.json
# python3 $src/dataset/process_transcript.py $results/AlphaGo/english/transcripts -o $results/AlphaGo/english/processed_transcript.json

echo "##############################################"
echo "dataset extract frame"
echo "##############################################"
# python3 $src/dataset/extract_frame.py $results/AlphaGo/chinese/processed_transcript.json $results/AlphaGo/chinese/videos -o $results/AlphaGo/chinese/frames -d $results/AlphaGo/chinese/image_text_pairs
# python3 $src/dataset/extract_frame.py $results/AlphaGo/english/processed_transcript.json $results/AlphaGo/english/videos -o $results/AlphaGo/english/frames -d $results/AlphaGo/english/image_text_pairs

echo "##############################################"
echo "dataset extract features"
echo "##############################################"
# python3 $src/dataset/extract_feature.py $results/AlphaGo/chinese/image_text_pairs -o $results/AlphaGo/chinese/features_data
# python3 $src/dataset/extract_feature.py $results/AlphaGo/english/image_text_pairs -o $results/AlphaGo/english/features_data

echo "##############################################"
echo "dataset find duplicate"
echo "##############################################"
# python3 $src/dataset/find_duplicate.py $results/AlphaGo/chinese/features_data $results/AlphaGo/english/features_data -o $results/AlphaGo/pairs.json -t 0.25 -d angular