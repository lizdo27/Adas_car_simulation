# 🚗 UTE ADAS Car Simulation (ROS 2 & Gazebo)

An Advanced Driver Assistance System (ADAS) simulation project built on ROS 2 and Gazebo. This project integrates artificial intelligence (YOLOv8) for semantic lane detection and a PID controller for an automated Lane Keep Assist (LKA) system.

## 📸 System Validation & HUD Demo

![Lane Keep Assist System](media/detection_demo.jpg)
*(Note: Real-time Lane Keep Assist validation. **Left:** `rqt_image_view` HUD displaying YOLOv8-seg lane detection (green lines), center trajectory calculation (red dots), and PID intervention status. **Right:** Gazebo Harmonic top-down view of the physical response).*<img width="1862" height="1166" alt="Untitled" src="https://github.com/user-attachments/assets/6820b259-6928-440e-b085-2e5ca3708af6" />



<img width="1280" height="800" alt="campus_preview" src="https://github.com/user-attachments/assets/2c721479-a177-429f-97ed-ed2cb6628050" /><img width="900" height="600" alt="car_preview" src="https://github.com/user-attachments/assets/4ab9b7b3-9e6a-4793-82f0-a6da66fafc45" />


---

## ✨ Core Features
- **Lane Detection (Semantic Segmentation):** Real-time road segmentation using a lightweight YOLOv8-seg model (`best.pt`).
- **Kinematic Control (PID Controller):** Smooth steering adjustments based on geometric lane error calculation.
- **Lane Keep Assist (LKA):** Automatically decelerates and intervenes with the steering wheel when the vehicle drifts out of the safe lane zone.
- **Heads-Up Display (HUD):** Real-time visualization of warning statuses, speed, and steering angle via `rqt_image_view`.

---

## ⚙️ Prerequisites

Ensure your system meets the following requirements before running the project:
- **OS:** Ubuntu 24.04
- **ROS 2:** Jazzy (with Gazebo Harmonic)
- **Python 3 Dependencies:**
  ```bash
  pip3 install ultralytics opencv-python torch torchvision "numpy<2" --break-system-packages
  ```

## 🚀 Installation & Build

1. Clone the repository into your ROS 2 Workspace:
   ```bash
   cd ~/ros2_ws/src
   git clone https://github.com/lizdo27/Adas_car_simulation.git
   ```

2. Build the package:
   ```bash
   cd ~/ros2_ws
   colcon build --packages-select gazebo_sim_adas
   source install/setup.bash
   ```

## 🎮 Usage

**Step 1: Launch the Gazebo Simulation Environment**
*(Make sure the UTE car and campus world are loaded and publishing camera data)*

**Step 2: Open the Camera HUD**
```bash
ros2 run rqt_image_view rqt_image_view
```
*Select the topic `/ute_lane_assist/debug_image` from the dropdown menu.*

**Step 3: Run the ADAS Brain (Lane Assist Node)**
```bash
ros2 run gazebo_sim_adas ute_lane_assist
```

---
*Developed by students of Ho Chi Minh City University of Technology and Education (HCMUTE).*
