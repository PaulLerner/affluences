#!/usr/bin/env python
# coding: utf-8
from jsonargparse import CLI
from jsonargparse.typing import register_type
import warnings
import time
import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from urllib3.exceptions import MaxRetryError


register_type(Path)


def request(query, session, tries=0, max_tries=100, sleep_time: float = 60.0*10.0):
    """GET query via requests, handles exceptions and returns None if something went wrong"""
    response = None
    base_msg = f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}: Something went wrong when requesting for '{query}':\n"
    if tries >= max_tries:
        raise RuntimeError(f"{base_msg}Maximum number of tries ({max_tries}) exceeded: {tries}")
    try:
        response = session.get(query, headers={'User-Agent':'affluences bot 0.1'})
    except requests.exceptions.ConnectionError as e:
        warnings.warn(f"{base_msg}requests.exceptions.ConnectionError: {e}")
    except MaxRetryError as e:
        warnings.warn(f"{base_msg}MaxRetryError: {e}")
    except OSError as e:
        warnings.warn(f"{base_msg}OSError: {e}")
    except Exception as e:
        warnings.warn(f"{base_msg}Exception: {e}")

    if response is None:
        time.sleep(sleep_time)
        return request(query, session, tries+1, max_tries=max_tries, sleep_time=sleep_time)
    elif response.status_code != requests.codes.ok:
        warnings.warn(f"{base_msg}status code: {response.status_code}")
        if response.status_code == 429:
            sleep_time = int(response.headers.get("Retry-After", sleep_time))
        time.sleep(sleep_time)
        return request(query, session, tries+1, max_tries=max_tries, sleep_time=sleep_time)
    return response


def get_value(soup):
    values = set()
    matches=list(soup.find_all(class_="app-counter"))
    for counter in matches:
        if not bool(counter.get("forecast", False)):
            values.add(counter["value"])
    if len(values) > 1:
        warnings.warn(f"Multiple values {values}\n{matches}")
    elif len(values) == 0:
        warnings.warn(f"No values\n{matches}")
    else:
        try: 
            value = int(next(iter(values)))
        except ValueError:
            warnings.warn(f"caught ValueError {values}")
            value = None
        return value


def main(url: str, output: Path = None, interval: float = 60.0*10.0):
    session = requests.Session()
    if output is None:
        output = Path(f'{url.split("/")[-1]}.csv')
    while True:
        result = request(url, session)
        try:
            soup = BeautifulSoup(result.text)
        except Exception as e:
            warnings.warn(f"caught Exception {e}")
            soup = None
        if soup is not None:
            value = get_value(soup)
        else:
            value = None
        if value is not None:
            timestamp=time.time()
            with open(output, "at") as file:
                file.write(f"{value},{timestamp}\n")
        time.sleep(interval)


if __name__ == "__main__":
    CLI(main)
