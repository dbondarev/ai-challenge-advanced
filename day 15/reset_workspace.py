#!/usr/bin/env python3
"""Offline reset; stop this challenge's containers, preserve evidence. No git writes."""
from sandbox import Sandbox
if __name__ == '__main__':
    Sandbox().stop_all()
    print('Stopped day15 v2 containers. For online reset use POST /v1/reset.')
