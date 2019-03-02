import requests
import json
import sys
import argparse


def send(message, route):
    res = ""
    try:
        res = requests.post(endpoint + route, message)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to Prosecutor Service, exiting")
        sys.exit(0)

    return res


if __name__ == "__main__":
    endpoint = "http://127.0.0.1:5000/flargs"
    res = send("yeet",endpoint)
    print(res.content.decode())
