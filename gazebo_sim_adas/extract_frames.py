import cv2
import os

video_path = 'data_chay_xe_2.avi'
output_dir = 'dataset_frames'

# Tạo thư mục chứa ảnh nếu chưa có
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

cap = cv2.VideoCapture(video_path)
count = 0
frame_id = 0

# Cứ cách 5 khung hình thì cắt 1 tấm để tránh dữ liệu trùng lặp
frame_skip = 5 

print(f"Đang phân giải video '{video_path}' thành từng khung hình riêng lẻ...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break # Kết thúc video
    
    if count % frame_skip == 0:
        # Lưu file với định dạng số 0 đứng trước (vd: frame_0001.jpg, frame_0002.jpg)
        filename = os.path.join(output_dir, f"frame_{frame_id:04d}.jpg")
        cv2.imwrite(filename, frame)
        frame_id += 1
        
    count += 1

cap.release()
print(f"Hoàn tất! Đã trích xuất thành công {frame_id} bức ảnh vào thư mục '{output_dir}'.")