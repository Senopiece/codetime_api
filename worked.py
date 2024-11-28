import json
import os
import sys
from datetime import datetime
import argparse
from dotenv import load_dotenv
from api import CodetimeFieldType, CodetimeResponseError, CodetimeSession


def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Query CodeTime API.")
    parser.add_argument(
        "--keywords",
        type=str,
        default="keywords.json",
        help="The project keywords to filter.",
    )
    parser.add_argument(
        "--since",
        type=str,
        required=True,
        help="Start date in YYYY-MM-DDThh:mm:ss format from which to calculate time.",
    )

    args = parser.parse_args()

    # Load session token
    load_dotenv()
    session_token = os.getenv("CODETIME_SESSION")
    time_scale = float(os.getenv("TIME_SCALE"))
    hour_price = float(os.getenv("HOUR_PRICE"))
    if session_token is None:
        print(
            "Session token is missing. Please set CODETIME_SESSION environment variable."
        )
        sys.exit(1)

    with open("keywords.json", "r") as f:
        keywords = json.load(f)

    def has_keyword(s):
        return any(kw in s for kw in keywords)

    try:
        # Parse the input date
        input_date = datetime.fromisoformat(args.since)
        current_date = datetime.now()

        # Calculate the number of minutes from the input date to now
        delta = current_date - input_date
        total_minutes = int(delta.total_seconds() / 60)

        if total_minutes < 0:
            print("The provided date is in the future. Please enter a past date.")
            sys.exit(1)

        # Initialize session and query
        session = CodetimeSession(session_token)
        projects = session.query(CodetimeFieldType.PROJECT, minutes=total_minutes)

        # Scale minutes
        for project in projects:
            project.minutes = project.minutes * time_scale

        # Filter projects if --project is provided
        total_time = 0
        for project in projects:
            if has_keyword(project.field):
                total_time += project.minutes
                print(f"{project.field}: {project.minutes}")

        # Output results
        print()
        total_time_h = total_time / 60
        print("===> Total:")
        print(total_time, "minutes")
        print(total_time_h, "hours")
        print(total_time_h * hour_price, "rub")

    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
    except CodetimeResponseError as e:
        print(f"An error occurred with status code: {e.status_code}")


if __name__ == "__main__":
    main()
