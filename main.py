import json
import requests
import logging as logger
import sys
from itertools import cycle

logger.basicConfig(
    level=logger.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logger.StreamHandler(sys.stdout)
    ]
)


with open("input/cookies.txt", "r") as f:
    pool = (f.read().splitlines())
    cookies = cycle(pool)

with open("input/proxies.txt", "r") as f:
    proxpool = (f.read().splitlines())
    proxies = cycle(proxpool)

content_ids = []
content_scores = []

def read_file_lines(file_path):
    with open(file_path, "r") as file:
        return file.read().splitlines()

def get_csrf_token(c, client):
    response = client.post(f"https://auth.roblox.com/v2/logout", cookies={".ROBLOSECURITY": c})
    return response.headers['x-csrf-token']

def get_session_id(c, client):
    response = client.get(f"https://www.roblox.com/discover#/sortName/v2/Continue", cookies={".ROBLOSECURITY": c})
    return response.cookies['RBXSessionTracker'].replace("sessionid=", "")

def get_game_content_ids(session_id, csrf, c, client):
    global content_ids
    global content_scores

    response = client.post(f"https://apis.roblox.com/discovery-api/omni-recommendation", json={"pageType": "Home", "sessionId": session_id, "supportedTreatmentTypes": ["SortlessGrid"]}, headers={"x-csrf-token": csrf}, cookies={".ROBLOSECURITY": c})
    if response.json()['sorts'][0]['topic'] != "Continue":
        return False
    
    sorts = response.json()['sorts'][0]["recommendationList"]

    for i in sorts:
        content_ids.append(i['contentId'])
        content_scores.append(i['contentMetadata']['Score'])

    return True

def get_games(content_ids, content_scores, session_id, csrf, c, client):
    contents = []

    for i in range(len(content_ids)):
        contents.append({"contentType": "Game", "contentId": content_ids[i], "contentStringId": "", "contentMetadata": {"Score": content_scores[i]}})
    
    response = client.post(f"https://apis.roblox.com/discovery-api/omni-recommendation-metadata", json={"sessionId": session_id, "contents": contents}, headers={"x-csrf-token": csrf}, cookies={".ROBLOSECURITY": c})
    
    game_table = []
    game_info = response.json()['contentMetadata']
    
    for game_id, game_data in game_info['Game'].items():
        game_table.append({"id": game_data['rootPlaceId'], "name": game_data['name']})
    return game_table

def main():
    cookies = cycle(read_file_lines("input/cookies.txt"))
    proxies = cycle(read_file_lines("input/proxies.txt"))

    cookie = next(cookies)
    proxy = next(proxies)

    client = requests.Session()
    client.proxies = {"http://": proxy, "https://": proxy}

    csrf = get_csrf_token(cookie, client)
    session_id = get_session_id(cookie, client)

    if not get_game_content_ids(session_id, csrf, cookie, client):
        return logger.warning("No continue games found.")

    games = get_games(content_ids, content_scores, session_id, csrf, cookie, client)

    logger.info(f"Found {len(games)} continue games.")
    
    with open("accounts.txt", "a") as file:
        file.write(f"{cookie}\n")
        for game in games:
            file.write(f"{game['id']} | {game['name']}\n")

if __name__ == "__main__":
    main()
