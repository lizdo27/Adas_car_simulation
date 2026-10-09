import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

class VideoRecorder(Node):
    def __init__(self):
        super().__init__('video_recorder_node')
        self.subscription = self.create_subscription(
            Image,
            '/ute_car/front_camera/image',
            self.image_callback,
            10)
        self.bridge = CvBridge()
        
        # Cấu hình bộ nén video XVID, tốc độ 10 khung hình/giây, độ phân giải 640x360
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('data_chay_xe_2.avi', fourcc, 10.0, (640, 360))
        self.get_logger().info('Đang ghi hình... Hãy cho xe chạy trên Gazebo. Bấm Ctrl+C để kết thúc.')

    def image_callback(self, msg):
        try:
            # Chuyển đổi bản tin ROS thành ma trận ảnh
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            # Ghi khung hình vào file video
            self.out.write(frame)
        except Exception as e:
            self.get_logger().error(f'Lỗi biên dịch ảnh: {e}')

    def destroy_node(self):
        # Đóng file an toàn khi tắt Node
        self.out.release()
        self.get_logger().info('Đã đóng và lưu file video data_chay_xe.avi thành công!')
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = VideoRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass # Bỏ qua lỗi ngắt bàn phím để chạy lệnh đóng file ở finally
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()