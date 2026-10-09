#!/usr/bin/env python3
import math
from pathlib import Path
import threading
import time
import signal
import cv2
import numpy as np
import rclpy
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from dataclasses import dataclass

@dataclass(frozen=True)
class Lane:
    near_left: float
    near_right: float
    far_left: float
    far_right: float
    near_y: int
    far_y: int
    width: int

    @property
    def near_error(self):
        return ((self.width - 1) / 2 - (self.near_left + self.near_right) / 2) / ((self.near_right - self.near_left) / 2)

    @property
    def far_error(self):
        return ((self.width - 1) / 2 - (self.far_left + self.far_right) / 2) / ((self.far_right - self.far_left) / 2)

def _runs(row):
    transitions = np.diff(np.r_[False, row.astype(bool), False].astype(np.int8))
    return list(zip(np.where(transitions == 1)[0], np.where(transitions == -1)[0] - 1))

def _section(mask, fraction, anchor):
    h, w = mask.shape
    y = round(fraction * (h - 1))
    radius = max(1, round(h * .008))
    rows = mask[max(0, y-radius):min(h, y+radius+1)]
    bands = []
    for row in rows:
        runs = [(l, r) for l, r in _runs(row) if r-l >= .08*w]
        if not runs: continue
        l, r = min(runs, key=lambda run: abs((run[0]+run[1])/2-anchor))
        bands.append((l, r))
    if len(bands) < math.ceil(.65 * len(rows)): return None
    left, right = np.median(bands, axis=0)
    return float(left), float(right), y

def lane_from_mask(mask, near_row=.84, far_row=.63):
    if mask is None or mask.ndim != 2 or min(mask.shape) < 20: return None
    h, w = mask.shape
    near = _section(mask, near_row, (w-1)/2)
    if near is None: return None
    far = _section(mask, far_row, (near[0]+near[1])/2)
    if far is None: return None
    nw, fw = near[1]-near[0], far[1]-far[0]
    if near[0] <= 1 or near[1] >= w-2 or not .18*w <= nw <= .97*w: return None
    if not .15 <= fw/nw <= .95: return None
    lane = Lane(near[0], near[1], far[0], far[1], near[2], far[2], w)
    if abs(lane.near_error) > .85 or abs(lane.far_error) > 1.2: return None
    return lane

def select_lane(masks, near_row=.84, far_row=.63):
    candidates = [lane_from_mask(m, near_row, far_row) for m in masks]
    candidates = [x for x in candidates if x is not None]
    if not candidates: return None
    return min(candidates, key=lambda x: abs(x.near_error)+.25*abs(x.far_error))

@dataclass
class ControlConfig:
    speed: float = 1.0          
    min_speed: float = .30      
    wheelbase: float = 2.65
    kp: float = .30
    kd: float = .035
    deadband: float = .025
    smoothing_tau: float = .20
    max_steer: float = .35
    steer_rate: float = .30
    acceleration: float = .60   

class LaneController:
    def __init__(self, config=None):
        self.c = config or ControlConfig()
        self.reset()

    def reset(self):
        self.filtered = None
        self.target, self.steer, self.speed, self.near_error = 0.0, 0.0, 0.0, 0.0
        self.last_observation = None

    def observe(self, lane, now):
        error = .35*lane.near_error + .65*lane.far_error
        dt = None if self.last_observation is None else now-self.last_observation
        if self.filtered is None or dt is None or dt <= 0 or dt > 1:
            self.filtered, derivative = error, 0.0
        else:
            alpha = 1-math.exp(-dt/self.c.smoothing_tau)
            derivative = max(-2.0, min(2.0, (error-self.filtered)/dt))
            self.filtered += alpha*(error-self.filtered)
        self.last_observation = now
        self.near_error = lane.near_error
        proportional = 0.0 if abs(self.filtered) < self.c.deadband else self.filtered
        self.target = max(-self.c.max_steer, min(self.c.max_steer, self.c.kp*proportional + self.c.kd*derivative))

    def command(self, dt):
        dt = max(0.0, min(dt, .10))
        self.steer += max(-self.c.steer_rate*dt, min(self.c.steer_rate*dt, self.target-self.steer))
        severity = max(abs(self.near_error)/.45, abs(self.steer)/self.c.max_steer)
        target_speed = max(self.c.min_speed, self.c.speed*(1-.7*min(1,severity)))
        self.speed += max(-self.c.acceleration*dt, min(self.c.acceleration*dt, target_speed-self.speed))
        yaw_rate = self.speed*math.tan(self.steer)/self.c.wheelbase
        return self.speed, yaw_rate

def image_to_bgr(msg):
    h, w, step = int(msg.height), int(msg.width), int(msg.step)
    data = np.frombuffer(bytes(msg.data), dtype=np.uint8)
    pixels = data.reshape(h, step)[:, :w*3].reshape(h, w, 3)
    return pixels.copy(order='C')

def bgr_to_image(bgr):
    msg = Image()
    msg.height, msg.width = bgr.shape[:2]
    msg.encoding = 'bgr8'
    msg.step = msg.width * 3
    msg.data = np.ascontiguousarray(bgr).tobytes()
    return msg

class UltralyticsLaneModel:
    def __init__(self, path, class_id, imgsz, confidence, threads):
        import torch
        from ultralytics import YOLO
        torch.set_num_threads(threads)
        self.model = YOLO(path)
        self.class_id, self.imgsz, self.conf = 0, imgsz, confidence

    def masks(self, bgr):
        result = self.model.predict(source=bgr, imgsz=self.imgsz, conf=self.conf, classes=[self.class_id], device='cpu', retina_masks=True, verbose=False)[0]
        if result.masks is None: return []
        return result.masks.data.detach().cpu().numpy() > .5

class LaneAssist(Node):
    def __init__(self):
        super().__init__('ute_lane_assist')
        defaults = dict(
            model_path='/home/lizdo/ros2_ws/src/gazebo_sim_adas/gazebo_sim_adas/best.pt', image_topic='/ute_car/front_camera/image', cmd_topic='/model/ute_car/cmd_vel', 
            lane_class_id=-1, enabled=True, imgsz=320, confidence=.40, torch_threads=4, near_row=.84, far_row=.63, 
            speed=1.0, min_speed=.30, wheelbase=2.65, kp=.30, kd=.035, deadband=.025, smoothing_tau=.20, 
            max_steer=.35, steer_rate=.30, acceleration=.60, control_rate=20.0, 
            max_frame_age=3.0, check_source_stamp=False, max_source_age=1.0, good_frames_required=1, publish_debug=True)
        
        self.cfg = defaults
        self.controller = LaneController(ControlConfig())
        self.lock = threading.Condition()
        self.pending, self.result, self.status = None, None, None
        self.sequence, self.last_result_sequence, self.good_frames = 0, -1, 0
        self.quitting = False
        self.last_tick, self.last_debug = time.monotonic(), 0.0
        
        self.pub = self.create_publisher(Twist, self.cfg['cmd_topic'], 1)
        self.status_pub = self.create_publisher(String, '/ute_lane_assist/status', 1)
        self.debug_pub = self.create_publisher(Image, '/ute_lane_assist/debug_image', 1)
        self.sub = self.create_subscription(Image, self.cfg['image_topic'], self.on_image, QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=1))
        
        self.detector = UltralyticsLaneModel(self.cfg['model_path'], self.cfg['lane_class_id'], self.cfg['imgsz'], self.cfg['confidence'], self.cfg['torch_threads'])
        self.steady_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self.timer = self.create_timer(1/self.cfg['control_rate'], self.control_tick, clock=self.steady_clock)
        self.worker = threading.Thread(target=self.inference_loop, daemon=True)
        self.worker.start()

    def on_image(self, msg):
        with self.lock:
            self.sequence += 1
            self.pending = (self.sequence, msg, time.monotonic())
            self.lock.notify()

    def inference_loop(self):
        consumed = -1
        while True:
            with self.lock:
                self.lock.wait_for(lambda: self.quitting or (self.pending is not None and self.pending[0] != consumed))
                if self.quitting: return
                seq, msg, received = self.pending
                consumed = seq
            lane, debug, reason = None, None, 'NO_LANE'
            try:
                bgr = image_to_bgr(msg)
                masks = self.detector.masks(bgr)
                lane = select_lane(masks, self.cfg['near_row'], self.cfg['far_row'])
                if lane is not None: reason = 'VALID'
                if self.cfg['publish_debug']:
                    debug = bgr.copy()
                    if lane is not None:
                        for left, right, y in [(lane.near_left, lane.near_right, lane.near_y), (lane.far_left, lane.far_right, lane.far_y)]:
                            cv2.line(debug, (round(left),y), (round(right),y), (0,200,0),2)
                            cv2.circle(debug,(round((left+right)/2),y),5,(0,0,255),-1)
            except Exception as exc:
                reason = f'ERR: {exc}'
            with self.lock:
                self.result = dict(seq=seq,lane=lane,received=received,reason=reason,debug=debug,header=msg.header)

    def set_status(self, status):
        if status != self.status:
            self.status = status
            self.get_logger().info(status)

    def publish_stop(self):
        self.pub.publish(Twist())

    def stop_control(self, reason):
        self.controller.reset()
        self.good_frames = 0
        #self.publish_stop()
        self.set_status(reason)

    def control_tick(self):
        now = time.monotonic()
        dt, self.last_tick = now-self.last_tick, now
        with self.lock:
            result, latest = self.result, self.pending
        
        if result is not None and result['debug'] is not None and now-self.last_debug >= 0.2:
            debug_img = result['debug']
            cv2.putText(debug_img, f"Status: {self.status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(debug_img, f"Spd: {self.controller.speed:.2f} m/s | Str: {self.controller.steer:.2f} rad", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if self.controller.near_error > 0.4: cv2.putText(debug_img, "LECH PHAI -> KEO TRAI!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            elif self.controller.near_error < -0.4: cv2.putText(debug_img, "LECH TRAI -> KEO PHAI!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            msg = bgr_to_image(debug_img)
            msg.header = result['header']
            self.debug_pub.publish(msg)
            self.last_debug = now

        if latest is None or result is None:
            self.stop_control('WAITING')
            return
        if now-latest[2] > self.cfg['max_frame_age']:
            self.stop_control('STALE_FRAME')
            return
        
        lane = result['lane']
        if lane is None:
            self.stop_control(result['reason'])
            return
            
        if result['seq'] != self.last_result_sequence:
            self.last_result_sequence = result['seq']
            self.good_frames += 1
            self.controller.observe(lane,result['received'])
            
        if self.good_frames < self.cfg['good_frames_required']:
            self.publish_stop()
            self.set_status('ACQUIRING')
            return
            
        speed, yaw = self.controller.command(dt)
        
        # CHẾ ĐỘ PHỤ TRỢ: Chỉ can thiệp khi sai số lệch làn lớn hơn 0.3
        if abs(self.controller.near_error) > 0.3:
            msg = Twist()
            msg.linear.x = speed  # Hãm tốc độ theo tính toán của AI cho an toàn
            msg.angular.z = yaw   # Bẻ vô lăng kéo xe lại
            self.pub.publish(msg)
            self.set_status('ASSISTING: KEO LAI LAN')
        else:
            # Xe đang ở giữa làn an toàn, không phát lệnh để nhường quyền cho bàn phím
            self.set_status('SAFE ZONE: Tự do lái')

def main():
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = LaneAssist()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()