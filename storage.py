import json

WATCHLIST_FILE = "watchlist.json"
LAST_DISCOUNTS_FILE = "last_discounts.json"


def load_watchlist():
    try:
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f, indent=2)


def load_last_discounts():
    try:
        with open(LAST_DISCOUNTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_last_discounts(discounts):
    with open(LAST_DISCOUNTS_FILE, "w") as f:
        json.dump(discounts, f, indent=2)


def extract_appid(text):
    if text.isdigit():
        return text

    parts = text.split("/")
    if "app" in parts:
        app_index = parts.index("app")
        return parts[app_index + 1]

    return None