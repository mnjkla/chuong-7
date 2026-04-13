# Đồ án Quản lý Cơ sở dữ liệu Đa phương tiện - Chương 7

## Giới thiệu
Chương 7 bao gồm phần lõi của **Chỉ mục Video (Video Indexing)** và AI.
Hệ thống sử dụng **RS-Tree** (cây phân đoạn) để lưu trữ thông tin không/thời gian của đối tượng trong video. Module này nạp dữ liệu từ hệ thống nhận diện **YOLO** vào cấu trúc RS-Tree để đảm bảo thời gian truy xuất và tìm kiếm được rút ngắn cực kỳ nhanh chóng.

## Hướng dẫn chạy
Yêu cầu thư viện: Python 3.x, Tkinter, `pillow`, `opencv-python`, `ultralytics`.

```bash
pip install pillow opencv-python ultralytics
python btchuong7.py
```
