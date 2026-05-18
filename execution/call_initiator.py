"""Place an outbound call via Twilio REST.

Run: python execution/call_initiator.py --to +15551234567
"""
from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def initiate(to: str) -> str:
    from twilio.rest import Client

    sid = os.environ["TWILIO_ACCOUNT_SID"]
    token = os.environ["TWILIO_AUTH_TOKEN"]
    from_number = os.environ["TWILIO_PHONE_NUMBER"]
    public_url = os.environ["PUBLIC_URL"].rstrip("/")

    client = Client(sid, token)
    call = client.calls.create(to=to, from_=from_number, url=f"{public_url}/twiml")
    return call.sid


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--to", required=True, help="Destination phone in E.164, e.g. +15551234567")
    args = parser.parse_args()
    call_sid = initiate(args.to)
    print(f"Placed call: {call_sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
