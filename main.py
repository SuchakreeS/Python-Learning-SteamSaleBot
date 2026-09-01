import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()
url = os.getenv("WISHLIST_URL")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

res = requests.get(url, headers=headers)
print(res.status_code)

if res.status_code == 200:
    data = res.json()
    items = data['response']['items']
    # print(res.json())

    appids = []
    for item in items:
        appids.append(item['appid'])

    print(appids)
    print(len(appids))

    wishlist_games = []
    for appid in appids :
        details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
        details_res = requests.get(details_url, headers=headers)
        details_data = details_res.json()

        appid_str = str(appid)
        game_data = details_data[appid_str]["data"]

        name = game_data["name"]
        price = game_data.get("price_overview", {}).get("final_formatted", "Free / No price listed")

        wishlist_games.append({"name": name, "price": price})

        time.sleep(1)

    print(wishlist_games)
else :
    print(f"Request fail with status code {res.status_code}")