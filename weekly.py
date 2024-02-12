import os
import sys
from dotenv import load_dotenv

from api import CodetimeFieldType, CodetimeResponseError, CodetimeSession


if __name__ == "__main__":
    load_dotenv()
    session_token = os.getenv("CODETIME_SESSION")
    if session_token is None:
        print(
            "Session token is missing. Please set CODETIME_SESSION environment variable."
        )
        sys.exit(1)

    session = CodetimeSession(session_token)
    try:
        projects = session.query(CodetimeFieldType.PROJECT, minutes=7 * 24 * 60)

        res = 0
        for project in projects:
            if project.field.startswith(sys.argv[1]):
                res += project.minutes

        print(res, "minutes")
        print(res / 60, "hours")
    except CodetimeResponseError as e:
        print(f"An error occurred with status code: {e.status_code}")
