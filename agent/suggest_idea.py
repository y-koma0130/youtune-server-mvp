import os
import requests
from openai import OpenAI

# 環境変数
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# プレイリストIDの取得
def get_uploads_playlist(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY,
    }
    res = requests.get(url, params=params).json()
    return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]


# 動画タイトルの取得
def get_latest_video_titles(playlist_id):
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": playlist_id,
        "maxResults": 5,
        "key": YOUTUBE_API_KEY,
    }
    res = requests.get(url, params=params).json()
    return [item["snippet"]["title"] for item in res.get("items", [])]


# GPTによるアイデア提案
def generate_idea_from_titles(titles):
    prompt = f"""以下はあるYouTubeチャンネルの人気動画タイトルです：
        {chr(10).join(titles)}
        このチャンネルの傾向に合った、新しい動画ネタを1つ提案してください。
        出力形式：
        1. タイトル案（15文字以内）
        2. 内容の狙いや補足（1文）
        ※必ず日本語で出力してください。英語は禁止です。"""

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# SwarmNodeエージェントのエントリーポイント
def main(request, store):
    payload = getattr(request, "payload", {})
    channel_url = payload.get("channel_url")
    if not channel_url:
        return "channel_url が指定されていません"

    try:
        channel_id = channel_url.rstrip("/").split("/")[-1]
        playlist_id = get_uploads_playlist(channel_id)
        titles = get_latest_video_titles(playlist_id)
        ideas = generate_idea_from_titles(titles)
        return ideas
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"
