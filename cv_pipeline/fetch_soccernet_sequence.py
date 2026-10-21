"""Extract one public SoccerNet tracking sequence without downloading its full ZIP."""

from __future__ import annotations

import argparse
import binascii
import struct
import zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from remotezip import RemoteZip


REPOS = {"train": "train.zip", "test": "test.zip", "challenge2023": "challenge2023.zip"}
BASE = "https://huggingface.co/datasets/SoccerNet/SN-Tracking-2023/resolve/main/"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=REPOS, default="train")
    parser.add_argument("--sequence", default="SNMOT-101")
    parser.add_argument("--output", type=Path, default=Path("cv_data/soccernet"))
    parser.add_argument("--workers", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    options = parse_args()
    archive_url = BASE + REPOS[options.split]
    prefix = f"{options.split}/{options.sequence}/"
    destination = options.output / options.sequence
    destination.mkdir(parents=True, exist_ok=True)

    with RemoteZip(archive_url) as remote:
        members = [item for item in remote.infolist() if item.filename.startswith(prefix) and not item.is_dir()]
    if not members:
        raise SystemExit(f"Sequence not found: {prefix}")

    probe = requests.get(archive_url, headers={"Range": "bytes=0-0"}, timeout=60)
    probe.raise_for_status()
    signed_url = probe.url

    def extract(item):
        relative = item.filename[len(prefix):]
        target = destination / relative
        if target.exists() and target.stat().st_size == item.file_size:
            return relative
        target.parent.mkdir(parents=True, exist_ok=True)
        start = item.header_offset
        end = start + 4096 + item.compress_size
        response = requests.get(signed_url, headers={"Range": f"bytes={start}-{end}"}, timeout=120)
        response.raise_for_status()
        payload = response.content
        if payload[:4] != b"PK\x03\x04":
            raise ValueError(f"Bad local ZIP header for {item.filename}")
        header = struct.unpack("<4s5H3I2H", payload[:30])
        compression, filename_length, extra_length = header[3], header[9], header[10]
        compressed = payload[30 + filename_length + extra_length:][:item.compress_size]
        if compression == 0:
            content = compressed
        elif compression == 8:
            content = zlib.decompress(compressed, -15)
        else:
            raise ValueError(f"Unsupported ZIP method {compression} for {item.filename}")
        if len(content) != item.file_size or binascii.crc32(content) & 0xFFFFFFFF != item.CRC:
            raise ValueError(f"Integrity check failed for {item.filename}")
        target.write_bytes(content)
        return relative

    complete = 0
    with ThreadPoolExecutor(max_workers=options.workers) as pool:
        futures = [pool.submit(extract, member) for member in members]
        for future in as_completed(futures):
            future.result()
            complete += 1
            if complete % 50 == 0 or complete == len(members):
                print(f"{complete}/{len(members)} files ready", flush=True)
    print(destination)


if __name__ == "__main__":
    main()
