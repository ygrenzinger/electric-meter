import os
import sqlite3
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

from electric_meter.config import DB_PATH, PROJECT_ROOT


DOMAIN = "www.myelectricaldata.fr"


def retrieve_and_insert_data(cur, con, config, reading_type, start, end):
    identifier = config[reading_type]["identifier"]
    token = config[reading_type]["token"]
    url = f"https://{DOMAIN}/{reading_type}_load_curve/{identifier}/start/{start}/end/{end}"

    response = requests.get(url, headers={"Authorization": token})
    if response.status_code != 200:
        print("error retrieving data")
        return 1

    data = response.json()
    measures = [(measure["date"], measure["value"])
                for measure in data["meter_reading"]["interval_reading"]]

    for measure in measures:
        try:
            cur.execute(f"INSERT INTO {reading_type} VALUES(?, ?)", measure)
        except Exception as e:
            # Some days contain duplicate timestamps due to daylight saving changes.
            print(f"could not insert {measure} due to:", e)
    con.commit()
    return 0


def main() -> int:
    load_dotenv(PROJECT_ROOT / ".env")

    print("Script started at", datetime.now())

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    res = cur.execute(
        "SELECT datetime FROM production ORDER BY datetime DESC LIMIT 1"
    )
    last = res.fetchone()
    last_datetime = last[0]
    start = last_datetime.split(' ')[0]

    end = (
        datetime.strptime(start, '%Y-%m-%d') + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    if start == (datetime.today() + timedelta(days=-1)).strftime("%Y-%m-%d"):
        print("Previous day already retrieved. Nothing to do.")
        return 0

    print(f"retrieving data between {start} and {end}")

    config = {
        "production": {
            "identifier": "14232127138183",
            "token": os.environ['PRODUCTION_TOKEN']
        },
        "consumption": {
            "identifier": "14230680045501",
            "token": os.environ['CONSUMPTION_TOKEN']
        }
    }

    print("retrieving production data")
    result = retrieve_and_insert_data(cur, con, config, 'production', start, end)
    if result:
        return result

    print("retrieving consumption data")
    result = retrieve_and_insert_data(cur, con, config, 'consumption', start, end)
    if result:
        return result

    print("Data retrieved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
