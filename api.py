import argparse
import json
import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel
import requests
from enum import Enum
import zlib


class CodetimeFieldType(Enum):
    PROJECT = "project"
    LANGUAGE = "language"
    PLATFORM = "platform"


class CodetimeItem(BaseModel):
    field: str
    minutes: float


class CodetimeResponseError(Exception):
    def __init__(self, status_code: int):
        self.status_code = status_code


# sync interface, hardcoded url and minimal error handling for now
class CodetimeSession:
    def __init__(self, session_token: str):
        self.session_token = session_token

    def query(
        self,
        field: CodetimeFieldType,
        minutes: int | None = None,
        limit: int | None = None,
    ):
        url = "https://api.codetime.dev/top"
        params = {
            "field": field.value,
            "minutes": minutes,
            "limit": limit,
        }
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
            "Accept-Language": "ru,en;q=0.9,zh;q=0.8",
            "Origin": "https://codetime.dev",
            "Referer": "https://codetime.dev/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        cookies = {
            "CODETIME_SESSION": self.session_token,
        }
        response = requests.get(
            url,
            params=params,
            headers=headers,
            cookies=cookies,
        )

        if response.status_code == 200:
            try:
                # Try to decode the response as JSON
                data = response.json()
                return [CodetimeItem(**item) for item in data]
            except ValueError as e:
                # If JSON decoding fails, try to decompress the response
                try:
                    decompressed_data = zlib.decompress(response.content, 16+zlib.MAX_WBITS)
                    data = json.loads(decompressed_data)
                    return [CodetimeItem(**item) for item in data]
                except zlib.error as e:
                    raise CodetimeResponseError(f"Failed to decompress response: {e}")
                except json.JSONDecodeError as e:
                    raise CodetimeResponseError(f"Failed to decode JSON: {e}")
        else:
            raise CodetimeResponseError(response.status_code)


def main():
    parser = argparse.ArgumentParser(description="Query CodeTime API")
    parser.add_argument(
        "field_type",
        choices=[ftype.value for ftype in CodetimeFieldType],
        help="The field type",
    )
    parser.add_argument(
        "--minutes",
        type=int,
        help="Filter items by the number of minutes they were active within the last N minutes",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of items to return",
    )

    args = parser.parse_args()

    load_dotenv()
    session_token = os.getenv("CODETIME_SESSION")
    if session_token is None:
        print(
            "Session token is missing. Please set CODETIME_SESSION environment variable."
        )
        sys.exit(1)

    session = CodetimeSession(session_token)
    try:
        result = session.query(
            CodetimeFieldType(args.field_type), minutes=args.minutes, limit=args.limit
        )
        for item in result:
            print(f'"{item.field}": {item.minutes} minutes')
    except CodetimeResponseError as e:
        print(f"An error occurred with status code: {e.status_code}")


if __name__ == "__main__":
    main()
