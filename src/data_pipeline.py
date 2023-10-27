import os

import click
import toml
import pandas as pd
from html import unescape
from datetime import datetime
import isodate
import googleapiclient.discovery

from transformers import pipeline

from utils import get_service_account_cred
from youtube_api import (
    get_channel_info,
    get_playlist_info,
    get_video_details,
    get_video_comments
)


@click.command()
@click.option('--config_file', default="config/config.toml", help='Path to config file')
def main(config_file):

    print("#############################################")
    print("main: STARTED")
    print("##############################################\n\n")

    # Load a config file
    with open(config_file, 'r') as f:
        config = toml.load(f)

    print("Configs:", config)

    api_key = os.environ["YOUTUBE_API_KEY"]
    youtube = googleapiclient.discovery.build(
        serviceName=config["youtube"]["api_service_name"],
        version=config["youtube"]["api_version"],
        developerKey=api_key
    )

    # #############################################
    # # Get data by calling YouTube API
    # #############################################

    # Channel Information
    channel_info = get_channel_info(youtube, config["channels"]["channel_ids"])
    print("channel_info.shape", channel_info.shape)

    # Playlist Information
    playlist_info = get_playlist_info(youtube, channel_info["playlist_id"].to_list())
    print("playlist_info.shape", playlist_info.shape)
    print(playlist_info.groupby("channel_name", as_index=False).size())

    # Get video stats
    video_details = get_video_details(youtube, playlist_info["video_id"].to_list())
    print("video_details.shape", video_details.shape)

    # Detail of latest video for each channel
    playlist_info.published_at = pd.to_datetime(playlist_info.published_at, format='%Y-%m-%dT%H:%M:%SZ')
    playlist_info["recency_rank"] = playlist_info.groupby("channel_id")["published_at"].rank(method="first", ascending=False)

    latest_video_list = playlist_info.loc[playlist_info["recency_rank"] == 1, "video_id"].to_list()
    latest_video_details = get_video_details(youtube, latest_video_list)
    print("latest_video_details.shape", latest_video_details.shape)

    # Get Video Comments
    comment_details = get_video_comments(youtube, latest_video_list)
    print("comment_details.shape", comment_details.shape)
    print(comment_details.groupby("video_id", as_index=False).size())

    print("Get data from YouTube: COMPLETED")
    print("##############################################\n\n")

    # #############################################
    # # Data Processing
    # #############################################

    # Remove HTML character reference from string
    comment_details["text_display"] = comment_details["text_display"].apply(unescape)

    # Get proper duration
    latest_video_details['duration_sec'] = latest_video_details['duration'].apply(lambda x: isodate.parse_duration(x))
    latest_video_details['duration_sec'] = latest_video_details['duration_sec'].dt.total_seconds()
    latest_video_details.drop('duration', axis=1, inplace=True)

    video_details['duration_sec'] = video_details['duration'].apply(lambda x: isodate.parse_duration(x))
    video_details['duration_sec'] = video_details['duration_sec'].dt.total_seconds()
    video_details.drop('duration', axis=1, inplace=True)

    # Fix datatypes
    channel_info = channel_info.astype({
        "view_count": float,
        "subscriber_count": float,
        "video_count": float,
    })

    video_details = video_details.astype({
        "view_count": float,
        "like_count": float,
        "comment_count": float,
    })
    video_details.published_at = pd.to_datetime(video_details.published_at, format='%Y-%m-%dT%H:%M:%SZ')

    latest_video_details = latest_video_details.astype({
        "view_count": float,
        "like_count": float,
        "comment_count": float,
    })
    latest_video_details.published_at = pd.to_datetime(latest_video_details.published_at, format='%Y-%m-%dT%H:%M:%SZ')

    comment_details.like_count = comment_details.like_count.astype(int)
    comment_details.published_at = pd.to_datetime(comment_details.published_at, format='%Y-%m-%dT%H:%M:%SZ')

    print("Data Processing: COMPLETED")
    print("##############################################\n\n")

    # #############################################
    # # Text Analysis of Comments
    # #############################################

    # Classify based on sentiments
    sentiment_classifier = pipeline(
        task="text-classification",
        model="nickwong64/bert-base-uncased-poems-sentiment",
        model_kwargs={"cache_dir": "../model_cache"}
    )

    # Restrict words to first 400 words to make sure model inference doesn't fail due to large input
    comments_list = [" ".join(comment.split()[:400]) for comment in comment_details.text_display.to_list()]

    sentiments = pd.DataFrame(sentiment_classifier(comments_list))
    sentiments.rename({"label": "sentiment", "score": "sentiment_score"}, axis=1, inplace=True)

    comment_details = comment_details.join(sentiments)

    # Classify as questions vs statements
    question_statement_classifier = pipeline(
        task="text-classification",
        model="shahrukhx01/question-vs-statement-classifier",
        model_kwargs={"cache_dir": "../model_cache"}
    )
    question_labels = pd.DataFrame(question_statement_classifier(comments_list))
    question_labels.rename({"label": "question_category", "score": "question_score"}, axis=1, inplace=True)

    question_labels.loc[question_labels["question_category"] == "LABEL_0", "question_category"] = "statement"
    question_labels.loc[question_labels["question_category"] == "LABEL_1", "question_category"] = "question"

    comment_details = comment_details.join(question_labels)

    print("Text analysis: COMPLETED")
    print("##############################################\n\n")

    # #############################################
    # # Push data to BQ
    # #############################################
    credentials = get_service_account_cred()

    # Before pushing, it is useful to add load_timestamp to the table

    # Push channel details
    channel_info["load_timestamp"] = datetime.now()
    channel_info.to_gbq(destination_table='{}.channel_info'.format(config["gcp"]["bq_dataset"]),
                        project_id=config["gcp"]["gcp_project_id"],
                        if_exists='append',
                        credentials=credentials)
    print("Push channel_info: COMPLETED")

    # Push all video details
    video_details["load_timestamp"] = datetime.now()
    video_details.to_gbq(destination_table='{}.video_details'.format(config["gcp"]["bq_dataset"]),
                         project_id=config["gcp"]["gcp_project_id"],
                         if_exists='replace',
                         credentials=credentials)
    print("Push video_details: COMPLETED")

    # Push latest video details
    latest_video_details["load_timestamp"] = datetime.now()
    latest_video_details.to_gbq(destination_table='{}.latest_video_details'.format(config["gcp"]["bq_dataset"]),
                                project_id=config["gcp"]["gcp_project_id"],
                                if_exists='replace',
                                credentials=credentials)
    print("Push latest_video_details: COMPLETED")

    # Push comment details
    comment_details["load_timestamp"] = datetime.now()
    comment_details.to_gbq(destination_table='{}.comment_details'.format(config["gcp"]["bq_dataset"]),
                           project_id=config["gcp"]["gcp_project_id"],
                           if_exists='replace',
                           credentials=credentials)
    print("Push comment_details: COMPLETED")

    print("ALL COMPLETED")
    print("##############################################\n\n")


if __name__ == "__main__":
    print("a")
    main()
