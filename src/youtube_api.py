import pandas as pd

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

