# UTE City — bản thử nghiệm 1

Khuôn viên dạng thành phố nhỏ cho **Gazebo Harmonic, SDF 1.8**. Lấy cảm hứng từ các nhóm nhà, xưởng, sân thể thao và cây xanh trong bản đồ UTE bạn cung cấp. Đây là bố cục thử nghiệm, **chưa phải bản sao chính xác của trường**.

## Chạy nhanh

Cần Gazebo Harmonic có Ogre2. Không cần tải mesh, texture, model Fuel hay biên dịch C++.

Mở terminal tại thư mục này:

```bash
bash run.sh
```

Script sinh lại world từ mã nguồn và mở Gazebo ở trạng thái chạy. Giao diện có góc nhìn tổng thể và cửa sổ **Front camera**. Nếu cửa sổ ảnh chưa hiện, mở menu plugin của Gazebo → **Image Display**, chọn `/ute_car/front_camera/image`. Simulation phải ở trạng thái Play để có ảnh.

Nếu dùng ROS 2 Jazzy và terminal chưa nhận `gz`, script sẽ tự thử source `/opt/ros/jazzy/setup.bash`. Bạn cũng có thể chạy world đã sinh sẵn trực tiếp:

```bash
gz sim -r worlds/ute_city.sdf
```

Chạy server không mở giao diện:

```bash
bash run.sh -s --headless-rendering
```

Không cần ROS để chạy world. ROS chỉ cần nếu bạn muốn bridge topic sang hệ thống điều khiển ROS sau này.

## Giao diện chỉnh sửa và chạy xe trực tiếp (đã sửa)

Bản cập nhật khôi phục bộ GUI mặc định của Harmonic: Entity Tree, Component Inspector, chọn model, Transform Control, Shapes, Lights, Spawn và Copy/Paste. Giao diện trước thiếu các plugin này; world không phải một ảnh/map cố định.

- **Chọn và sửa vị trí:** Pause, chọn nhà/cây/xe trong Entity Tree hoặc cảnh 3D, dùng Transform Control để kéo hoặc xoay. Các nhà static vẫn có thể được đặt lại vị trí bằng công cụ GUI; static chỉ tắt chuyển động do vật lý.
- **Thêm vật thể:** dùng Shapes trên thanh công cụ. Để thêm model, mở menu plugin → Resource Spawner, chọn nguồn model phù hợp. Model tải qua Fuel cần mạng; có thể dùng model cục bộ.
- **Lái xe ngay trong GUI:** nhấn Play; bảng **Drive UTE car** (plugin Teleop) đã đặt topic `/model/ute_car/cmd_vel`. Đặt Forward = 2 m/s và Yaw = 0.25 rad/s. Trong tab Buttons, bật tiến, bật trái/phải để vừa đi vừa rẽ, nhấn Stop để dừng. Trong tab Keyboard, giữ W để tiến, W+A/W+D để rẽ. Xe Ackermann không quay tại chỗ khi chỉ nhấn A/D. Không cần Python cho cách điều khiển này.
- **Lưu thay đổi:** dùng chức năng Save World As của Gazebo nếu có trong menu phiên bản bạn cài, lưu ra SDF mới và mở file đó lần sau. Đừng chạy `run.sh` để mở bản chỉnh tay: script sẽ sinh lại world từ nguồn.

`gui_layout.xml` là cấu hình giao diện nguồn, được nhúng vào SDF khi sinh world. File SDF sinh sẵn vẫn mở độc lập, không cần Python hay file XML phụ. Tham khảo [Teleop chính thức](https://gazebosim.org/api/gui/8/classplugins_1_1Teleop.html).

Đã kiểm tra lại cú pháp world sau sửa và sự hiện diện của các thư viện GUI trên máy; chưa kiểm tra thao tác GUI trực tiếp trong phiên này.

## Điều khiển xe

Mở terminal thứ hai tại thư mục dự án. Nếu cài qua ROS Jazzy, source môi trường ở terminal này trước:

```bash
source /opt/ros/jazzy/setup.bash
python3 teleop.py
```

Nếu cài Gazebo độc lập, bỏ dòng `source`. Teleop cần Python bindings `gz.transport13` và `gz.msgs10`; gói tương ứng là `python3-gz-transport13` và `python3-gz-msgs10` trên hệ thống dùng các gói Gazebo chính thức.

| Phím giữ | Tác dụng |
|---|---|
| W | Đi thẳng, 2 m/s |
| A | Vừa tiến vừa rẽ trái |
| D | Vừa tiến vừa rẽ phải |
| S | Lùi thẳng, tối đa 1,5 m/s |
| Space | Gửi lệnh dừng |
| Q hoặc Ctrl+C | Gửi lệnh dừng và thoát |

Giữ focus ở terminal điều khiển. Nếu không nhận phím trong 0,65 giây, teleop gửi tốc độ 0; xe giảm tốc theo giới hạn gia tốc, không dừng tức thời. W trả lái về thẳng. Có thể chọn tốc độ thấp hơn bằng `python3 teleop.py --speed 1`.

Điều khiển trực tiếp không cần Python bindings:

```bash
# Đi thẳng; lệnh có thể tiếp tục có hiệu lực sau khi publisher kết thúc.
gz topic -t /model/ute_car/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 2.0}, angular: {z: 0.0}'

# Tiến và rẽ trái. angular.z là yaw rate rad/s, không phải góc bánh lái.
gz topic -t /model/ute_car/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 2.0}, angular: {z: 0.25}'

# Dừng.
gz topic -t /model/ute_car/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}, angular: {z: 0.0}'
```

Plugin Ackermann nhận tốc độ tiến và tốc độ quay thân xe, tính góc hai bánh trước. Tham khảo [API Gazebo Harmonic AckermannSteering](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1AckermannSteering.html). Teleop đổi góc lái mong muốn thành yaw rate theo `v * tan(delta) / wheelbase`. Watchdog nằm trong teleop; plugin không có watchdog được cấu hình trong bản này. Nếu đóng cưỡng bức teleop hoặc dùng `gz topic`, gửi lệnh dừng hoặc Pause mô phỏng.

## Kích thước và bố cục

Tất cả dùng **mét ở tỷ lệ 1:1** để tỷ lệ xe–đường giống một xe con trong môi trường thực. Bản này không dùng xe RC 1/10. Nếu về sau cần trở lại RC, nên thu nhỏ đồng bộ cả xe lẫn map và hiệu chỉnh lại vật lý.

| Thành phần | Kích thước/cấu hình |
|---|---|
| Mặt bằng | 106 × 154 m |
| Đường hai chiều | 7 m; mỗi làn 3,5 m |
| Vỉa hè | Rộng 1,6 m; cao 0,15 m |
| Thân xe | Dài 4,4 m; rộng 1,8 m; nóc cao khoảng 1,57 m |
| Phụ kiện phía trước | Camera nhô thêm khoảng 0,1 m |
| Chiều dài cơ sở | 2,65 m |
| Vệt bánh | 1,56 m |
| Bánh xe | Bán kính 0,32 m; rộng 0,24 m |
| Khối lượng mô hình | 1178 kg |
| Camera trước | RGB, 640 × 360, 20 Hz, góc nhìn ngang 80° |
| Camera | Cao khoảng 1,10 m; chúc xuống khoảng 4,6° |
| Động học | Hai bánh trước đánh lái, hai bánh sau dẫn động |

Xe chiếm khoảng 51% bề rộng một làn. Các thông số là giá trị thiết kế hợp lý để thử thuật toán, không phải thông số đo của một mẫu xe cụ thể. Mô hình cơ khí đơn giản, chưa có hệ treo, mô hình lốp nâng cao hoặc độ trễ truyền động thực tế.

Map gồm ba trục dọc tại X = -32, 0, 32; ba đường ngang tại Y = -48, 0, 48; lối vào kéo dài đến Y = -72. Các đường nối thành nhiều vòng; giao lộ để trống vạch nhằm tránh nhầm đường ngang thành vật cản. Đường vòng ngoài có các góc vuông: đi chậm và đánh lái sớm. Bản sau có thể thay bằng góc bo theo bán kính quay.

Xe xuất hiện trong làn bên phải ở `(1.75, -62)`, nhìn về hướng +Y qua cổng vào. Khu A và C nằm phía tây bắc, xưởng phía đông bắc, thư viện và nhà công nghệ phía đông nam, sân thể thao và dịch vụ sinh viên phía tây nam.

Có cây, bóng đổ thật, cột đèn, ghế, cổng và dải cửa sổ đơn giản. Nhà, thân cây, ghế và vỉa hè có collision. Tán cây là visual để tiết kiệm tính toán. Cột đèn là vật trang trí ban ngày; chưa bật đèn chiếu sáng ban đêm. Xe chưa có thuật toán tự hành.

## Camera và dữ liệu

| Topic Gazebo | Loại |
|---|---|
| `/model/ute_car/cmd_vel` | `gz.msgs.Twist` |
| `/model/ute_car/odometry` | `gz.msgs.Odometry` |
| `/model/ute_car/joint_state` | `gz.msgs.Model` |
| `/ute_car/front_camera/image` | `gz.msgs.Image` |
| `/ute_car/front_camera/camera_info` | `gz.msgs.CameraInfo` |

Chụp một frame thật từ camera khi mô phỏng đang chạy, cần thêm Pillow:

```bash
python3 capture_camera.py --output frame.png
```

Ảnh `front_camera_preview.png`, `campus_preview.png` và `car_preview.png` đi kèm được chụp từ camera trong Gazebo. Các camera chụp minh họa chỉ được thêm trong lần kiểm tra, không nằm trong world mặc định.

## Kiểm tra đã thực hiện

Đã kiểm tra bằng Gazebo Sim **8.15.0 (Harmonic)**:

- `gz sdf -k` báo Valid cho cả world và model xe riêng.
- Chạy server với Ogre2 và nhận được ảnh RGB 640 × 360 từ camera xe.
- Xe đứng ổn định trên mặt đường; sau lệnh chạy 2 m/s trong 3 giây, vị trí thực tiến khoảng 5,06 m, bao gồm thời gian tăng tốc.
- Đối chiếu odometry với pose thực của Gazebo: xe rẽ được cả hai phía và không bị lật.
- Sau lệnh dừng, vận tốc odometry về 0. Chi tiết các pha nằm trong `verification.json`; `actual` là pose trong world, còn odometry dùng gốc ban đầu của xe.

Kiểm tra này chạy ở chế độ server; chưa kiểm tra thao tác GUI trên máy của bạn, chưa chạy hết mọi tuyến trong campus và chưa có kiểm thử thuật toán tự hành. Hiệu năng phụ thuộc GPU và driver.

## Mã nguồn để chỉnh tiếp

- `generate_world.py`: sinh toàn bộ map và xe bằng Python chuẩn.
- `config.json`: độ rộng đường, vị trí trục đường, ánh sáng, bóng, camera, vị trí xuất phát.
- `worlds/ute_city.sdf`: world độc lập, đã chứa sẵn xe, dùng trực tiếp được.
- `models/ute_car/model.sdf`: xe riêng để tái sử dụng trong world khác.
- `models/ute_car/model.config`: metadata của model.
- `teleop.py`: điều khiển bàn phím.
- `capture_camera.py`: lưu ảnh camera.
- `verification.json`: số liệu kiểm tra chuyển động.

Để sửa nhà, xem `BUILDINGS` ở đầu `generate_world.py`. Cây, ghế, cổng và sân nằm trong `make_world()`. **Tọa độ cảnh quan hiện được đặt thủ công**: nếu đổi vị trí trục đường hoặc đổi lớn bề rộng đường trong config, cần dịch các nhà/cây tương ứng để không lấn đường.

Sau khi chỉnh nguồn:

```bash
python3 generate_world.py
gz sdf -k worlds/ute_city.sdf
gz sdf -k models/ute_car/model.sdf
```

`run.sh` luôn sinh lại SDF. Nếu sửa SDF trực tiếp, chạy bằng `gz sim -r worlds/ute_city.sdf` để giữ các sửa đổi đó.

## Vòng phản hồi tiếp theo

Chạy thử bản này trước và gửi ảnh nhìn tổng thể cùng ảnh camera xe. Cho biết ba điểm: tỷ lệ xe/đường đã vừa chưa; muốn tăng độ giống UTE ở khu nào; và máy có chạy mượt khi bật bóng không. Từ đó có thể chỉnh bố cục, bo góc đường, thêm biển báo/bãi đỗ và đưa thuật toán bám làn vào.

Nếu đồ họa chậm, giảm `camera_rate` xuống 10 hoặc `shadows` thành false trong config rồi chạy lại. Cần driver đồ họa hỗ trợ Ogre2; nếu camera không có dữ liệu, kiểm tra Play, topic và lỗi renderer trong terminal Gazebo.
