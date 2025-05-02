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


register_type(Path)


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
    #url = "https://affluences.com/piscine-de-la-butte-aux-cailles"
    if output is None:
        output = Path(f'{url.split("/")[-1]}.csv')
    while True:
        try:
            result = requests.get(url)
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
            #date = datetime.datetime.fromtimestamp(timestamp)
           # weekday = datetime.datetime.isoweekday(date)
           # print(timestamp, date, weekday)
        time.sleep(interval)


if __name__ == "__main__":
    CLI(main)