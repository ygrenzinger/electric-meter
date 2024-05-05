
import os
import sqlite3
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

print("Script started at", datetime.now())

con = sqlite3.connect("electric-measures.db")
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
    exit()

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

domain = "www.myelectricaldata.fr"


def retrieve_and_insert_data(type):
    identifier = config[type]["identifier"]
    token = config[type]["token"]
    url = f"https://{domain}/{type}_load_curve/{identifier}/start/{start}/end/{end}"

    response = requests.get(url, headers={"Authorization": token})
    if response.status_code != 200:
        print("error retrieving data")
        exit()

    data = response.json()
    measures = [(measure["date"], measure["value"])
                for measure in data["meter_reading"]["interval_reading"]]

    cur.executemany(f"INSERT INTO {type} VALUES(?, ?)", measures)
    con.commit()


print("retrieving production data")
retrieve_and_insert_data('production')

print("retrieving consumption data")
retrieve_and_insert_data('consumption')

print("Data retrieved")
