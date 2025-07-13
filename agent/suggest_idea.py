# SwarmNodeとローカル実行を両立させた構成

import os
import requests
from openai import OpenAI

# SwarmNodeで実行中かどうかを判定（ローカルなら ImportError）
try:
    from swarm import agent, parameter  # type: ignore

    swarm_mode = True
except ImportError:
    swarm_mode = False
    from dotenv import load_dotenv

    load_dotenv()  # ローカル環境では.envから読み込む

# 環境変数からAPIキー取得
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# SwarmNode用のデコレーター（ローカルでは無視）
if swarm_mode:

    @agent()  # type: ignore
    @parameter("channel_url", type="string", required=True)  # type: ignore
    def suggest_video_idea(channel_url: str):
        return run_suggestion(channel_url)

else:

    def suggest_video_idea(channel_url: str):
        return run_suggestion(channel_url)


# 共通の処理ロジック
def run_suggestion(channel_url: str):
    def extract_channel_id(url):
        if "/channel/" in url:
            return url.split("/channel/")[-1]
        raise ValueError("URL形式が /channel/ を含んでいません")

    def get_uploads_playlist(channel_id):
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": YOUTUBE_API_KEY,
        }
        res = requests.get(url, params=params).json()
        return res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def get_latest_video_titles(playlist_id, max_results=5):
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY,
        }
        res = requests.get(url, params=params).json()
        # レスポンス確認用ログ
        print("YouTube API response:", res)
        return [item["snippet"]["title"] for item in res["items"]]

    def generate_idea(titles):
        prompt = f"""以下はあるYouTubeチャンネルの人気動画タイトルです：
          {chr(10).join(titles)}
          このチャンネルの傾向に合った、新しい動画ネタを1つ提案してください。
          出力形式：
          1. タイトル案（15文字以内）
          2. 内容の狙いや補足（1文）
          日本語でお願いします。"""

        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4", messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    try:
        channel_id = extract_channel_id(channel_url)
        playlist_id = get_uploads_playlist(channel_id)
        titles = get_latest_video_titles(playlist_id)
        return generate_idea(titles)
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"


# ローカルでの実行時用
if __name__ == "__main__":
    test_url = "https://www.youtube.com/channel/UCBR8-60-B28hp2BmDPdntcQ"
    result = suggest_video_idea(test_url)
    print(result)
