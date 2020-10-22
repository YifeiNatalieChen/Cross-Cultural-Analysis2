#!/usr/bin/env bash
src="$(dirname $0)/src"
results="$(dirname $0)/results"

echo "##############################################"
echo "get video metadata"
echo "##############################################"
# python3 $src/spidering/get_metadata.py "AlphaGo" -n 5 -o $results/AlphaGo/chinese/video_metadata -s bilibili
# python3 $src/spidering/get_metadata.py "AlphaGo" -n 5 -o $results/AlphaGo/english/video_metadata -s youtube -k key.txt

echo "##############################################"
echo "download videos"
echo "##############################################"
# python3 $src/spidering/download.py $results/AlphaGo/chinese/video_metadata/metadata -ao $results/AlphaGo/chinese/audios -vo $results/AlphaGo/chinese/videos -s bilibili
# python3 $src/spidering/download.py $results/AlphaGo/english/video_metadata/metadata -ao $results/AlphaGo/english/audios -vo $results/AlphaGo/english/videos -s youtube

echo "##############################################"
echo "dataset extract audios"
echo "##############################################"
# python3 $src/dataset/extract_audio.py $results/AlphaGo/chinese/videos -o $results/AlphaGo/chinese/audios
# python3 $src/dataset/extract_audio.py $results/AlphaGo/english/videos -o $results/AlphaGo/english/audios

echo "##############################################"
echo "dataset extract transcripts"
echo "##############################################"
# python3 $src/dataset/extract_transcript.py $results/AlphaGo/chinese/audios key.json cross-culture-audios-stanley -o $results/AlphaGo/chinese/transcripts -l cmn-Hans-CN -d audios_cn -t "AlphaGo" "AlphaZero" "DeepMind"
# python3 $src/dataset/extract_transcript.py $results/AlphaGo/english/audios key.json cross-culture-audios-stanley -o $results/AlphaGo/english/transcripts -l en-US -d audios_en -t "AlphaGo" "Lee Sedol" "Ke Jie"