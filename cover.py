import json
import os
import sys
from datetime import datetime
import argparse
from dotenv import load_dotenv
from api import CodetimeFieldType, CodetimeSession


payment_file = "payment.json"


def load_payment_until():
    payment_file = "payment.json"

    with open(payment_file, "r") as f:
        payment_data = json.load(f)

    try:
        payed_until = datetime.fromisoformat(payment_data["payed_until"])
    except KeyError:
        raise Exception("Missing 'payed_until' in payment file.")

    return payed_until


def store_payment_until(new_payed_until: datetime):
    with open(payment_file, "w") as f:
        json.dump(
            {"payed_until": new_payed_until.isoformat(timespec="minutes")},
            f,
            indent=4,
        )
    print(f"Payment until updated to {new_payed_until.isoformat(timespec='minutes')}")


def minutize(t: datetime):
    return datetime.fromisoformat(t.isoformat(timespec="minutes"))


def minutes_ago(t: datetime):
    delta = datetime.now() - t
    total_minutes = int(delta.total_seconds() / 60)
    return total_minutes


def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Update payment for CodeTime API.")
    parser.add_argument(
        "--payed",
        type=float,
        required=True,
        help="Amount paid in rubles.",
    )
    args = parser.parse_args()
    payed = args.payed

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

    # Load payment data
    payed_until = load_payment_until()

    # Load keywords
    with open("keywords.json", "r") as f:
        keywords = json.load(f)

    # Initialize API session
    session = CodetimeSession(session_token)

    # Calculate total worth since last payment
    def calculate_total_worth_since(start_time: datetime):
        """Calculate the total worth of projects from start_time to end_time."""
        print(f"Quering since {start_time.isoformat(timespec='minutes')}...")
        total_minutes = minutes_ago(start_time)

        if total_minutes <= 0:
            return 0

        projects = session.query(CodetimeFieldType.PROJECT, minutes=total_minutes)

        # Scale minutes and calculate total cost
        total_time = sum(
            project.minutes * time_scale
            for project in projects
            if any(kw in project.field for kw in keywords)
        )

        total_time_h = total_time / 60
        return total_time_h * hour_price

    total_worth = calculate_total_worth_since(payed_until)
    print(f"Total worth since last payment: {total_worth:.2f} rub")
    print(f"Amount paid: {payed:.2f} rub")

    if payed >= total_worth:
        # Overpayment scenario
        surplus = payed - total_worth
        store_payment_until(datetime.now())
        print(f"Surplus payment of {surplus:.2f} rub.")
        sys.exit(0)

    remaining_debt = total_worth - payed
    print(f"Remaining debt: {remaining_debt:.2f} rub")
    print()

    # Binary search to find new payed_until timestamp to exactly match the remaining debt
    low = payed_until
    high = datetime.now()
    while True:
        raw_mid = low + (high - low) / 2
        mid = minutize(raw_mid)

        mid_worth = calculate_total_worth_since(mid)
        print("Worth:", mid_worth, "rub")

        if mid_worth > remaining_debt:
            low = raw_mid
        else:
            high = raw_mid

        if mid == minutize(low + (high - low) / 2):
            break

    new_payed_until = mid

    print()
    store_payment_until(new_payed_until)


if __name__ == "__main__":
    main()
