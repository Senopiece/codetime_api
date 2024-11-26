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
        "--project",
        type=str,
        default=None,
        help="The project name prefix to filter by (optional).",
    )
    parser.add_argument(
        "--since",
        type=str,
        required=True,
        help="Start date in YYYY-MM-DD format from which to calculate time.",
    )

    args = parser.parse_args()

    # Load session token
    load_dotenv()
    session_token = os.getenv("CODETIME_SESSION")
    if session_token is None:
        print(
            "Session token is missing. Please set CODETIME_SESSION environment variable."
        )
        sys.exit(1)

    try:
        # Parse the input date
        input_date = datetime.strptime(args.since, "%Y-%m-%d")
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

        # Filter projects if --project is provided
        total_time = 0
        for project in projects:
            if args.project is None or project.field.startswith(args.project):
                total_time += project.minutes
                print(f"{project.field}: {project.minutes}")

        # Output results
        print()
        print("===> Total:")
        print(total_time, "minutes")
        print(total_time / 60, "hours")

    except ValueError:
        print("Invalid date format. Please use YYYY-MM-DD.")
    except CodetimeResponseError as e:
        print(f"An error occurred with status code: {e.status_code}")


if __name__ == "__main__":
    main()
