import requests
import time
import logging
ping_url = "https://ya.ru/"


def IsInternetAvailable():
    try:
        if requests.get(ping_url).status_code == 200:
            return True
    except:
        return False


def WaitUntilInternetWillAvailable():
    while not IsInternetAvailable():
        time.sleep(5)
        logging.warning("Internet is unavailable. Waiting...")
