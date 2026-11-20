#!/usr/bin/env python3
"""Delivery script for the news-image-20261120 entry.

The artwork itself is finished ahead of time and stored in this folder
as ``entry.png``.  All this script has to do at run time is place a
copy of that file where the judging harness expects to find it.  It
relies on nothing outside the Python standard library, so it behaves
the same in any bare Python 3 environment.
"""

import os
import shutil

IMAGE_NAME = "entry.png"
OUTPUT_DIR_ENV = "MAKEFUN_OUTPUT_DIR"
DEFAULT_OUTPUT_DIR = "/output"


def locate_image():
    """Absolute path of the artwork sitting next to this script."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, IMAGE_NAME)


def destination_dir():
    """Where the harness wants the image; '/output' when unspecified."""
    chosen = os.environ.get(OUTPUT_DIR_ENV)
    if chosen:
        return chosen
    return DEFAULT_OUTPUT_DIR


def deliver():
    src = locate_image()
    if not os.path.isfile(src):
        raise SystemExit("artwork missing beside the script: " + src)
    folder = destination_dir()
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, IMAGE_NAME)
    shutil.copyfile(src, target)
    # A truncated copy would hand the judges a broken page, so confirm
    # the delivered file carries exactly as many bytes as the original.
    if os.path.getsize(target) != os.path.getsize(src):
        raise SystemExit("copy size mismatch for " + target)
    return target


if __name__ == "__main__":
    placed = deliver()
    print("entry.png delivered to " + placed)
