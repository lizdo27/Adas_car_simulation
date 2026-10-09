# 🚗 UTE ADAS Car Simulation (ROS 2 & Gazebo)

An Advanced Driver Assistance System (ADAS) simulation project built on ROS 2 and Gazebo. This project integrates artificial intelligence (YOLOv8) for semantic lane detection and a PID controller for an automated Lane Keep Assist (LKA) system.

## 📸 Demo & Screenshots

*(Front Camera view with integrated HUD for speed and steering angle)*
![Front Camera HUD](media/front_camera_preview.png)

*(UTE Car and Campus Simulation World)*
![Car & Campus Preview](media/car_preview.png)

---

## ✨ Core Features

* **Lane Detection (Semantic Segmentation):** Real-time road segmentation using a lightweight YOLOv8-seg model (`best.pt`).
* **Kinematic Control (PID Controller):** Smooth steering adjustments based on geometric lane error calculation.
* **Lane Keep Assist (LKA):** Automatically decelerates and intervenes with the steering wheel when the vehicle drifts out of the safe lane zone.
* **Heads-Up Display (HUD):** Real-time visualization of warning statuses, speed, and steering angle via `rqt_image_view`.

---

## ⚙️ Prerequisites

Ensure your system meets the following requirements before running the project:
* **OS:** Ubuntu 24.04
* **ROS 2:** Jazzy (with Gazebo Harmonic)
* **Python 3 Dependencies:**
  ```bash
  pip3 install ultralytics opencv-python torch torchvision "numpy<2" --break-system-packages
