#!/usr/bin/env python3
"""Terminal teleoperation; release key to stop after 0.65 s.

Requires Gazebo Harmonic Python bindings (gz.transport13 / gz.msgs10).
Commands are speed [m/s] and yaw rate [rad/s], not raw steering angle.
"""
import argparse
import math
import select
import sys
import termios
import time
import tty

try:
    from gz.transport13 import Node
    from gz.msgs10.twist_pb2 import Twist
except ImportError:
    sys.exit('Thiếu Python bindings Gazebo. Thử source /opt/ros/jazzy/setup.bash. '
             'Nếu cài Gazebo độc lập, cần python3-gz-transport13 và python3-gz-msgs10. '
             'README có lệnh gz topic để điều khiển không cần bindings.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--speed', type=float, default=2.0)
    args = ap.parse_args()
    if not 0 < args.speed <= 5:
        ap.error('--speed phải trong (0, 5] m/s')
    if not sys.stdin.isatty():
        sys.exit('Chạy teleop trong terminal tương tác.')
    node = Node()
    pub = node.advertise('/model/ute_car/cmd_vel', Twist)
    print('Giữ W: thẳng | A/D: chạy và rẽ trái/phải | S: lùi | Space: dừng | Q: thoát')
    print('Thả phím: gửi lệnh dừng sau 0.65 s. Giữ focus ở terminal này.')
    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    v = delta = 0.0
    last_key = time.monotonic()
    try:
        tty.setcbreak(fd)
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if ready:
                key = sys.stdin.read(1).lower()
                if key == 'q':
                    break
                if key in 'wasd ':
                    last_key = time.monotonic()
                    if key == 'w': v, delta = args.speed, 0.0
                    elif key == 's': v, delta = -min(args.speed, 1.5), 0.0
                    elif key == 'a': v, delta = args.speed, 0.40
                    elif key == 'd': v, delta = args.speed, -0.40
                    else: v, delta = 0.0, 0.0
            if time.monotonic() - last_key > 0.65:
                v, delta = 0.0, 0.0
            msg = Twist()
            msg.linear.x = v
            msg.angular.z = v * math.tan(delta) / 2.65
            pub.publish(msg)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)
        for _ in range(5):
            pub.publish(Twist())
            time.sleep(0.05)


if __name__ == '__main__':
    main()
