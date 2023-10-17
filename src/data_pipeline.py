print("#############################################")
print("Python Code: STARTED")
print("##############################################\n\n")

import os

import pandas as pd
from html import unescape
from datetime import datetime
import isodate
import googleapiclient.discovery
from google.oauth2 import service_account

from transformers import pipeline


api_key = os.environ["YOUTUBE_API_KEY"]
gcp_project_id = "wide-hexagon-397214"

api_service_name = "youtube"
api_version = "v3"

channel_ids = ["UCueeXkuJezkCqu0YryvJnnQ",   #@harsh1kumar
               "UCs8a-hjf6X4pa-O0orSoC8w",   #@amitvarma
               "UCJQJAI7IjbLcpsjWdSzYz0Q",   #@Thuvu5
              ]

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=api_key
)

service_account_json = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
credentials = service_account.Credentials.from_service_account_file(
    service_account_json,
)

##############################################
## Functions to get data from YouTube Data API
##############################################

## Function for Channel information
def get_channel_info(youtube, channel_ids):
    
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=",".join(channel_ids)
    )
    response = request.execute()
    
    all_data = []
    for items in response["items"]:
        data = {
            "channel_name": items["snippet"]["title"],
            "view_count": items["statistics"]["viewCount"],
            "subscriber_count": items["statistics"]["subscriberCount"],
            "video_count": items["statistics"]["videoCount"],
            "channel_id": items["id"],
            "playlist_id": items["contentDetails"]["relatedPlaylists"]["uploads"],
        }

        all_data.append(data)

    return pd.DataFrame(all_data)


## Function for Playlist Information
def get_playlist_info(youtube, playlist_ids):
    
    all_data = []
    
    for pid in playlist_ids:
        next_page_token = ""

        while next_page_token is not None:
            request = youtube.playlistItems().list(
                part="snippet,contentDetails",
                maxResults=50,
                playlistId=pid,
                pageToken = next_page_token
            )
            response = request.execute()

            for items in response["items"]:
                data = {
                    "title": items["snippet"]["title"],
                    "published_at": items["snippet"]["publishedAt"],
                    "channel_name": items["snippet"]["videoOwnerChannelTitle"],
                    "channel_id": items["snippet"]["channelId"],
                    "video_id": items["snippet"]["resourceId"]["videoId"]
                }
                all_data.append(data)
            
            next_page_token = response.get('nextPageToken')

    return pd.DataFrame(all_data)


## Function for Video Information
def get_video_details(youtube, video_ids):

    all_data = []
    for i in range(0, len(video_ids), 10):
        # Make request for 10 videos at a time
        vid = video_ids[i: i+10]
    
        request = youtube.videos().list(
            part="contentDetails,snippet,statistics",
            id=",".join(vid)
        )
        response = request.execute()
        
        
        for items in response["items"]:
            data = {
                "video_id": items["id"],
                "title": items["snippet"]["title"],
                "published_at": items["snippet"]["publishedAt"],
                "duration": items["contentDetails"]["duration"],
                "view_count": items["statistics"]["viewCount"],
                "like_count": items["statistics"]["likeCount"],
                "comment_count": items["statistics"]["commentCount"],
            }
    
            all_data.append(data)

    return pd.DataFrame(all_data)

## Function for Comment Information
def get_video_comments(youtube, video_ids):
    
    all_data = []
    for vid in video_ids:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            maxResults=100,
            videoId=vid,
        )
        response = request.execute()

        for items in response["items"]:
            data = {

                "comment_id": items["id"],
                "video_id": items["snippet"]["videoId"],
                "channel_id": items["snippet"]["channelId"],
                "published_at": items["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                "text_display": items["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                "author_name": items["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                "like_count": items["snippet"]["topLevelComment"]["snippet"]["likeCount"],
            }

            all_data.append(data)

    return pd.DataFrame(all_data)

##############################################
## Get data by calling YouTube API
##############################################

## Channel Information
channel_info = get_channel_info(youtube, channel_ids)
print("channel_info.shape", channel_info.shape)

## Playlist Information
playlist_info = get_playlist_info(youtube, channel_info["playlist_id"].to_list())
print("playlist_info.shape", playlist_info.shape)
print(playlist_info.groupby("channel_name", as_index=False).size())

## Get video stats
video_details = get_video_details(youtube, playlist_info["video_id"].to_list())
print("video_details.shape", video_details.shape)

## Detail of latest video for each channel
playlist_info.published_at = pd.to_datetime(playlist_info.published_at, format='%Y-%m-%dT%H:%M:%SZ')
playlist_info["recency_rank"] = playlist_info.groupby("channel_id")["published_at"].rank(method="first", ascending=False)

latest_video_list = playlist_info.loc[playlist_info["recency_rank"]==1, "video_id"].to_list()
latest_video_details = get_video_details(youtube, latest_video_list)
print("latest_video_details.shape", latest_video_details.shape)

## Get Video Comments
comment_details = get_video_comments(youtube, latest_video_list)
print("comment_details.shape", comment_details.shape)
print(comment_details.groupby("video_id", as_index=False).size())

print("Get data from YouTube: COMPLETED")
print("##############################################\n\n")


##############################################
## Data Processing
##############################################

## Remove HTML character reference from string
comment_details["text_display"] = comment_details["text_display"].apply(unescape)


## Get proper duration
latest_video_details['duration_sec'] = latest_video_details['duration'].apply(lambda x: isodate.parse_duration(x))
latest_video_details['duration_sec'] = latest_video_details['duration_sec'].dt.total_seconds()

latest_video_details.drop('duration', axis=1, inplace=True)

## Fix datatypes
channel_info.view_count = channel_info.view_count.astype(int)
channel_info.subscriber_count = channel_info.subscriber_count.astype(int)
channel_info.video_count = channel_info.video_count.astype(int)

video_details.view_count = video_details.view_count.astype(int)
video_details.like_count = video_details.like_count.astype(int)
video_details.comment_count = video_details.comment_count.astype(int)
video_details.published_at = pd.to_datetime(video_details.published_at, format='%Y-%m-%dT%H:%M:%SZ')

latest_video_details.view_count = latest_video_details.view_count.astype(int)
latest_video_details.like_count = latest_video_details.like_count.astype(int)
latest_video_details.comment_count = latest_video_details.comment_count.astype(int)
latest_video_details.published_at = pd.to_datetime(latest_video_details.published_at, format='%Y-%m-%dT%H:%M:%SZ')

comment_details.like_count = comment_details.like_count.astype(int)
comment_details.published_at = pd.to_datetime(comment_details.published_at, format='%Y-%m-%dT%H:%M:%SZ')

print("Data Processing: COMPLETED")
print("##############################################\n\n")

##############################################
## Text Analysis of Comments
##############################################

## Classify based on sentiments
sentiment_classifier = pipeline(
    task="text-classification",
    model="nickwong64/bert-base-uncased-poems-sentiment",
    model_kwargs={"cache_dir": "../model_cache"}
)

# Restrict words to first 400 words to make sure model inference doesn't fail due to large input
comments_list = [" ".join(l.split()[:400]) for l in comment_details.text_display.to_list()]

sentiments = pd.DataFrame(sentiment_classifier(comments_list))
sentiments.rename({"label":"sentiment", "score":"sentiment_score"}, axis=1, inplace=True)

comment_details = comment_details.join(sentiments)


## Classify as questions vs statements
question_statement_classifier = pipeline(
    task="text-classification",
    model="shahrukhx01/question-vs-statement-classifier",
    model_kwargs={"cache_dir": "../model_cache"}
)
question_labels = pd.DataFrame(question_statement_classifier(comments_list))
question_labels.rename({"label":"question_category", "score":"question_score"}, axis=1, inplace=True)

question_labels.loc[question_labels["question_category"]=="LABEL_0","question_category"] = "statement"
question_labels.loc[question_labels["question_category"]=="LABEL_1","question_category"] = "question"

comment_details = comment_details.join(question_labels)

print("Text analysis: COMPLETED")
print("##############################################\n\n")


##############################################
## Push data to BQ
##############################################
# Before pushing, it is useful to add load_timestamp to the table

# Push channel details
channel_info["load_timestamp"] = datetime.now()
channel_info.to_gbq(destination_table='youtube_data.channel_info',
                     project_id=gcp_project_id,
                     if_exists='append',
                     credentials=credentials)
print("Push channel_info: COMPLETED")


# Push all video details
video_details["load_timestamp"] = datetime.now()
video_details.to_gbq(destination_table='youtube_data.video_details',
                     project_id=gcp_project_id,
                     if_exists='replace',
                     credentials=credentials)
print("Push video_details: COMPLETED")


# Push latest video details
latest_video_details["load_timestamp"] = datetime.now()
latest_video_details.to_gbq(destination_table='youtube_data.latest_video_details',
                            project_id=gcp_project_id,
                            if_exists='replace',
                            credentials=credentials)
print("Push latest_video_details: COMPLETED")


# Push comment details
comment_details["load_timestamp"] = datetime.now()
comment_details.to_gbq(destination_table='youtube_data.comment_details',
                       project_id=gcp_project_id,
                       if_exists='replace',
                       credentials=credentials)
print("Push comment_details: COMPLETED")


print("ALL COMPLETED")
print("##############################################\n\n")




