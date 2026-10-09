#!/usr/bin/env bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
if ! command -v gz >/dev/null 2>&1; then
  if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
  else
    echo 'Không tìm thấy gz. Cần Gazebo Harmonic trên máy.' >&2
    exit 1
  fi
fi
python3 generate_world.py
exec gz sim -r worlds/ute_city.sdf "$@"
