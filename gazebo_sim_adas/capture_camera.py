#!/usr/bin/env python3
"""Save one real camera frame from Gazebo. Requires Pillow + Gazebo bindings."""
import argparse
import threading
from pathlib import Path
from gz.transport13 import Node
from gz.msgs10.image_pb2 import Image as ImageMsg, RGB_INT8
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topic', default='/ute_car/front_camera/image')
    ap.add_argument('--output', default='front_camera.png')
    ap.add_argument('--timeout', type=float, default=30)
    args = ap.parse_args()
    done = threading.Event()
    result = {}
    node = Node()

    def callback(msg):
        if done.is_set():
            return
        if msg.pixel_format_type != RGB_INT8:
            result['error'] = f'Expected RGB_INT8, got {msg.pixel_format_type}'
        else:
            frame = Image.frombytes('RGB', (msg.width, msg.height), msg.data,
                                    'raw', 'RGB', msg.step, 1)
            frame.save(Path(args.output))
            result['size'] = (msg.width, msg.height)
        done.set()

    if not node.subscribe(ImageMsg, args.topic, callback):
        raise SystemExit('Cannot subscribe to camera topic.')
    if not done.wait(args.timeout):
        raise SystemExit('No camera frame: ensure simulation is playing and Sensors loaded.')
    if 'error' in result:
        raise SystemExit(result['error'])
    print(f"Saved {args.output}: {result['size']}")


if __name__ == '__main__':
    main()
