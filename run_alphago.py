import argparse
from src.spidering.get_metadata import get_metadata
from src.spidering.spider import Spider
from src.spidering.download import download
from src.tool.profiler import profile
from src.analysis.count_words_cn import count
from src.analysis.trend import trend
from src.dataset.extract_audio import extract_audio
from src.dataset.extract_transcript import extract_transcript
from src.dataset.process_transcript import process_transcript
from src.dataset.extract_frame import extract_frame
from src.dataset.extract_feature import extract_feature
from src.dataset.find_duplicate import find_duplicate

def main():
    """
    The main function of the project
    """
    parser = argparse.ArgumentParser(description='Cross Cultural Analysis')
    parser.add_argument(
        '-k', '--key', help='key for Youtube API, string or path to text file')
    args = parser.parse_args()
    sources = [Spider.BILIBILI]
    result_dir = "results/AlphaGo/BILIBILI"

    # Get video metadata
    if False:
        profile(get_metadata, ("AlphaGo", 10, result_dir +
                               "/video_metadata", False, args.key, sources))

    # Download videos
    if False:
        profile(download, (result_dir+"/video_metadata/metadata",
                           result_dir+"/audios", result_dir+"/videos", sources))

    # Analysis
    if False:
        profile(count, (result_dir+"/video_metadata/titles.txt", result_dir +
                        "/video_metadata/titles_wordcounts.txt", result_dir+"/video_metadata/titles_wordcounts.png"))
        profile(trend, ("results/topics_trend/topics_2018_US.json", "results/topics_trend/topics.txt",
                        "results/topics_trend/topics_data"), {"plot_topics": ["AlphaGo"]})

    # Dataset extract audios
    if False:
        profile(extract_audio, (result_dir+"/videos", result_dir+"/audios"))

    # Dataset extract transcripts
    if False:
        profile(extract_transcript, (result_dir+"/audios", "service_key.json", "extract-transcript", result_dir+"/transcripts", "cmn-Hans-CN"), kwargs={"hint":["AlphaGo", "AlphaZero", "DeepMind"], "gs_dir": "audios_cn"})

    # Dataset process transcripts
    if False:
        profile(process_transcript, (result_dir+"/transcripts", result_dir+"/processed_transcript.json"))

    # Dataset extract frame
    if False:
        profile(extract_frame, (result_dir+"/processed_transcript.json", result_dir+"/videos", result_dir+"/frames", result_dir+"/image_text_pairs"))

    # Dataset extract features
    if True:
        profile(extract_feature, (result_dir+"/image_text_pairs", result_dir+"/features_data", result_dir+"/frames"))

    # Dataset find duplicate
    if False:
        pass
        #profile(find_duplicate, (result_dir+"/features_data", result_dir+"/features_data"))

if __name__ == '__main__':
    main()
