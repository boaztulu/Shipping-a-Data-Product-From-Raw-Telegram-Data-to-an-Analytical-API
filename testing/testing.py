#!/usr/bin/env python3
# scrape_telegram.py

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import RPCError

# ———————————————————————————————————————————————————————————
async def main():
    # 1) Load your API credentials from .env
    load_dotenv()  # expects .env in the cwd
    raw_id   = os.getenv("API_ID")
    raw_hash = os.getenv("API_HASH")
    if raw_id is None or raw_hash is None:
        raise RuntimeError(
            "Missing API_ID or API_HASH in your .env file. "
            "Ensure it contains:\n"
            "  API_ID=6592689\n"
            "  API_HASH=5d9b4b87ca31121363a5421dafe3071a"
        )
    try:
        api_id = int(raw_id)
    except ValueError:
        raise RuntimeError(f"API_ID {raw_id!r} is not an integer.")
    api_hash = raw_hash

    # 2) Prepare today's directory structure
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_dir  = Path("data") / "raw" / "telegram_messages" / today_str
    media_dir = base_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # 3) Configure logging
    log_file = base_dir / "scrape.log"
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 4) Initialize and start the Telegram client
    client = TelegramClient("session_scrape", api_id, api_hash)
    try:
        await client.start()  # may prompt for phone/code on first run
        print("✅ Telegram client initialized and connected.")
        logging.info("Telegram client started successfully")
    except RPCError as e:
        logging.error(f"Failed to start Telegram client: {e!r}")
        print(f"❌ Error initializing Telegram client: {e}")
        return

    # 5) List of public channel usernames to scrape
    channels = [
        "lobelia4cosmetics",
        "tikvahpharma",
        # add more if you like...
    ]

    # 6) Scrape each channel
    for channel in channels:
        try:
            logging.info(f"Starting scrape for channel: {channel}")
            messages_data = []

            # iterate messages in chronological order
            async for msg in client.iter_messages(channel, reverse=True):
                record = {
                    "message_id": msg.id,
                    "channel":    channel,
                    "date":       msg.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "text":       msg.message,
                    "sender_id":  msg.sender_id,
                    "media_file": None
                }

                # download media if present
                if msg.media:
                    media_path = media_dir / f"{channel}_{msg.id}"
                    try:
                        file_path = await msg.download_media(file=str(media_path))
                        record["media_file"] = file_path
                    except Exception as ex:
                        logging.error(f"Media download error for {channel}#{msg.id}: {ex}")

                messages_data.append(record)

            # write out JSON
            out_json = base_dir / f"{channel}.json"
            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)

            logging.info(f"Saved {len(messages_data)} messages for {channel} → {out_json.name}")
            print(f"Scraped {len(messages_data)} messages from {channel}.")

        except RPCError as e:
            logging.error(f"RPCError scraping {channel}: {e!r}")
            print(f"Error scraping {channel}: {e}")

    # 7) Cleanly disconnect
    await client.disconnect()
    logging.info("Telegram client disconnected")
    print("🔌 Client disconnected.")

# ———————————————————————————————————————————————————————————
if __name__ == "__main__":
    asyncio.run(main())
