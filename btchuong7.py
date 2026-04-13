import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import os
import json
import datetime
import threading

# ==============================================================================
# DATA MODEL & RS-TREE LOGIC
# ==============================================================================

class VideoSegment:
    """Đại diện cho một phân đoạn video (Video ID, Start, End, Entity, Type, Property, Value)."""
    def __init__(self, vid, start, end, entity, e_type, prop=None, val=None):
        self.vid = vid
        self.start = start
        self.end = end
        self.entity = entity      # Tên Object hoặc Activity
        self.type = e_type        # "Object" hoặc "Activity"
        self.prop = prop          # Tên thuộc tính (p)
        self.val = val            # Giá trị thuộc tính (z)

class RSTree:
    """Cấu trúc RS-tree đơn giản hóa để lập chỉ mục các phân đoạn."""
    def __init__(self):
        self.segments = []

    def build(self, segment_table):
        self.segments = segment_table

    # --- 8 FUNCTIONS IMPLEMENTATION ---

    def find_video_with_object(self, obj_name):
        return sorted(list(set(s.vid for s in self.segments if s.entity == obj_name and s.type == "Object")))

    def find_video_with_activity(self, activity_name):
        return sorted(list(set(s.vid for s in self.segments if s.entity == activity_name and s.type == "Activity")))

    def find_video_with_activity_and_prop(self, activity, prop, val):
        return sorted(list(set(s.vid for s in self.segments if s.entity == activity and s.type == "Activity" and s.prop == prop and s.val == val)))

    def find_video_with_object_and_prop(self, obj, prop, val):
        return sorted(list(set(s.vid for s in self.segments if s.entity == obj and s.type == "Object" and s.prop == prop and s.val == val)))

    def find_objects_in_video(self, vid, s_frame, e_frame):
        return sorted(list(set(s.entity for s in self.segments if s.vid == vid and s.type == "Object" and s.start <= e_frame and s.end >= s_frame)))

    def find_activities_in_video(self, vid, s_frame, e_frame):
        return sorted(list(set(s.entity for s in self.segments if s.vid == vid and s.type == "Activity" and s.start <= e_frame and s.end >= s_frame)))

    def find_activities_and_props_in_video(self, vid, s_frame, e_frame):
        results = []
        for s in self.segments:
            if s.vid == vid and s.type == "Activity" and s.start <= e_frame and s.end >= s_frame:
                results.append(f"{s.entity}({s.prop}={s.val})")
        return sorted(list(set(results)))

    def find_objects_and_props_in_video(self, vid, s_frame, e_frame):
        results = []
        for s in self.segments:
            if s.vid == vid and s.type == "Object" and s.start <= e_frame and s.end >= s_frame:
                results.append(f"{s.entity}({s.prop}={s.val})")
        return sorted(list(set(results)))

# ==============================================================================
# GUI - GRAPHICAL USER INTERFACE
# ==============================================================================

class RSTreeApp:
    def __init__(self, root, rs_tree):
        self.root = root
        self.rs_tree = rs_tree
        self.root.title("Hệ thống Chỉ mục Video RS-Tree (Chương 7)")
        self.root.geometry("800x600")
        
        # UI Layout
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Section
        input_frame = ttk.LabelFrame(main_frame, text="Tham số truy vấn", padding="10")
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="Object/Activity:").grid(row=0, column=0, sticky=tk.W)
        self.ent_entry = ttk.Entry(input_frame)
        self.ent_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Video ID:").grid(row=0, column=2, sticky=tk.W)
        self.vid_entry = ttk.Entry(input_frame)
        self.vid_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(input_frame, text="Property (p):").grid(row=1, column=0, sticky=tk.W)
        self.prop_entry = ttk.Entry(input_frame)
        self.prop_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Value (z):").grid(row=1, column=2, sticky=tk.W)
        self.val_entry = ttk.Entry(input_frame)
        self.val_entry.grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(input_frame, text="Start Frame:").grid(row=2, column=0, sticky=tk.W)
        self.start_entry = ttk.Entry(input_frame)
        self.start_entry.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="End Frame:").grid(row=2, column=2, sticky=tk.W)
        self.end_entry = ttk.Entry(input_frame)
        self.end_entry.grid(row=2, column=3, padx=5, pady=2)

        # AI Section
        ai_frame = ttk.LabelFrame(main_frame, text="Phân tích Video thực tế với AI YOLO (best.pt)", padding="10")
        ai_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(ai_frame, text="📂 Chọn Video", command=self.choose_video).pack(side=tk.LEFT, padx=5)
        ttk.Button(ai_frame, text="▶ Chạy Nhận Diện AI", command=self.run_yolo_thread).pack(side=tk.LEFT, padx=5)
        
        self.video_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "video_demo.mp4")
        self.ai_status_lbl = ttk.Label(ai_frame, text=f"Sẵn sàng: {os.path.basename(self.video_path)}")
        self.ai_status_lbl.pack(side=tk.LEFT, padx=10)

        # Buttons Section
        btn_frame = ttk.LabelFrame(main_frame, text="Chức năng tìm kiếm", padding="10")
        btn_frame.pack(fill=tk.X, pady=5)

        queries = [
            ("FindVideoWithObject", self.q1),
            ("FindVideoWithActivity", self.q2),
            ("FindVideoWithActivityAndProp", self.q3),
            ("FindVideoWithObjectAndProp", self.q4),
            ("FindObjectsInVideo", self.q5),
            ("FindActivitiesInVideo", self.q6),
            ("FindActivitiesAndPropsInVideo", self.q7),
            ("FindObjectsAndPropsInVideo", self.q8),
        ]

        for i, (text, func) in enumerate(queries):
            r, c = divmod(i, 4)
            ttk.Button(btn_frame, text=text, command=func).grid(row=r, column=c, padx=5, pady=5, sticky="ew")

        # Image Preview Section
        self.img_frame = ttk.LabelFrame(main_frame, text="Xem trước (Frame Preview)", padding="10")
        self.img_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.img_label = ttk.Label(self.img_frame, text="[Chọn một truy vấn để xem hình ảnh mẫu]")
        self.img_label.pack()

        # Log & Quick Search Section
        log_frame = ttk.LabelFrame(main_frame, text="💾 Log nhận diện & Tìm kiếm nhanh", padding="8")
        log_frame.pack(fill=tk.X, pady=5)

        # Row 0: tìm kiếm nhanh theo tên biển báo
        ttk.Label(log_frame, text="Tìm theo biển báo:").grid(row=0, column=0, sticky=tk.W, padx=4)
        self.search_entry = ttk.Entry(log_frame, width=25)
        self.search_entry.grid(row=0, column=1, padx=4, pady=3)
        ttk.Button(log_frame, text="🔍 Tìm trong Log",
                   command=self.quick_search_log).grid(row=0, column=2, padx=4)
        ttk.Button(log_frame, text="📂 Nạp Log cũ",
                   command=self.load_detection_log).grid(row=0, column=3, padx=4)
        ttk.Button(log_frame, text="📖 Xem Log JSON",
                   command=self.view_log_json).grid(row=0, column=4, padx=4)

        # Row 1: hiển thị đường dẫn log
        self.log_path_lbl = ttk.Label(log_frame,
            text="Chưa có log. Hãy chạy nhận diện AI hoặc nhấn 'Nạp Log cũ'.",
            foreground="gray")
        self.log_path_lbl.grid(row=1, column=0, columnspan=5, sticky=tk.W, padx=4)

        # Status/Results Section
        res_frame = ttk.LabelFrame(main_frame, text="Kết quả", padding="10")
        res_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.res_text = tk.Text(res_frame, height=10)
        self.res_text.pack(fill=tk.BOTH, expand=True)

        # Load sample image
        self.sample_img_path = "assets/video_sample.png"
        self.photo = None
        if os.path.exists(self.sample_img_path):
            try:
                # Tkinter's PhotoImage supports PNG since 8.6
                self.photo = tk.PhotoImage(file=self.sample_img_path)
            except Exception as e:
                print(f"Lỗi nạp ảnh: {e}")

    def choose_video(self):
        """Mở hộp thoại để người dùng chọn video."""
        file_path = filedialog.askopenfilename(
            title="Chọn Video",
            filetypes=[("Video Files", "*.mp4 *.avi *.mkv *.mov")]
        )
        if file_path:
            self.video_path = file_path
            self.ai_status_lbl.config(
                text=f"Đã chọn: {os.path.basename(self.video_path)}"
            )

    def display(self, data):
        self.res_text.delete(1.0, tk.END)
        if not data:
            self.res_text.insert(tk.END, "Không tìm thấy kết quả phù hợp.")
            self.img_label.config(image='', text="[Không có dữ liệu hình ảnh]")
        else:
            self.res_text.insert(tk.END, "\n".join(map(str, data)))
            if self.photo:
                self.img_label.config(image=self.photo, text="")
            else:
                self.img_label.config(image='', text="[Đã tìm thấy nhưng không nạp được file assets/video_sample.png]")

    # ── Log helpers ──────────────────────────────────────────────────────────
    def _log_path(self):
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "assets", "detection_log.json")

    def quick_search_log(self):
        """Tìm trong log JSON theo tên biển báo (không phân biệt HOA/thường)."""
        keyword = self.search_entry.get().strip().lower()
        if not keyword:
            messagebox.showwarning("Đầu vào", "Vui lòng nhập từ khóa tìm kiếm.")
            return

        lp = self._log_path()
        if not os.path.exists(lp):
            messagebox.showinfo("Không có Log",
                "Chưa có file log.\nHãy chạy nhận diện AI trước.")
            return

        try:
            with open(lp, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được log: {e}")
            return

        segs = log_data.get("segments", [])
        hits = [s for s in segs if keyword in s["entity"].lower()]

        self.res_text.delete(1.0, tk.END)
        self.res_text.insert(tk.END,
            f"Tìm '{keyword}' trong log ({log_data.get('recorded_at','?')}):\n"
            f"Tổng: {len(segs)} segments  |  Phù hợp: {len(hits)}\n"
            + "─" * 60 + "\n")

        for s in hits:
            self.res_text.insert(tk.END,
                f"  [{s['vid']}] {s['entity']:30s}  "
                f"frames {s['start']:>6} – {s['end']:>6}\n")

        if not hits:
            self.res_text.insert(tk.END, "  Không tìm thấy biển báo nào khớp.")

    def load_detection_log(self):
        """Nạp lại kết quả từ log JSON vào RS-Tree (không cần chạy lại YOLO)."""
        lp = self._log_path()
        if not os.path.exists(lp):
            messagebox.showinfo("Không có Log",
                f"File log chưa tồn tại:\n{lp}\n\nHãy chạy nhận diện AI trước.")
            return

        try:
            with open(lp, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được log: {e}")
            return

        segs = log_data.get("segments", [])
        loaded = [
            VideoSegment(
                s["vid"], s["start"], s["end"],
                s["entity"], s["type"],
                s.get("prop"), s.get("val")
            )
            for s in segs
        ]
        self.rs_tree.build(loaded)

        # Thống kê
        classes = sorted(set(s["entity"] for s in segs))
        self.ai_status_lbl.config(
            text=f"✅ Đã nạp log {log_data.get('recorded_at','?')} – {len(loaded)} segments."
        )
        self.log_path_lbl.config(
            text=f"💾 {lp}  |  {len(loaded)} segments  |  "
                 f"{len(classes)} loại biển: {', '.join(classes[:6])}"
                 + (" ..." if len(classes) > 6 else ""),
            foreground="#1a7a1a"
        )
        messagebox.showinfo("Đã nạp Log",
            f"✅ Nạp thành công!\n\n"
            f"📅 Ghi lúc : {log_data.get('recorded_at', 'N/A')}\n"
            f"📹 Tổng frames: {log_data.get('total_frames', 'N/A')}\n"
            f"📦 Segments  : {len(loaded)}\n"
            f"🛣️ Loại biển  : {len(classes)}\n\n"
            f"📌 Các loại:\n" + "\n".join(f"  • {c}" for c in classes[:15])
            + ("\n  ..." if len(classes) > 15 else "")
        )

    def view_log_json(self):
        """Hiển thị nội dung file JSON log vào res_text."""
        lp = self._log_path()
        if not os.path.exists(lp):
            messagebox.showinfo("Không có Log", "Chưa có file log.")
            return
        try:
            with open(lp, "r", encoding="utf-8") as f:
                log_data = json.load(f)
            self.res_text.delete(1.0, tk.END)
            # Trang summary
            self.res_text.insert(tk.END,
                f"=== LOG NHẬN DIỆN AI ===\n"
                f"Ghi lúc   : {log_data.get('recorded_at')}\n"
                f"Frames    : {log_data.get('total_frames')}\n"
                f"Segments  : {len(log_data.get('segments', []))}\n"
                f"Video out : {log_data.get('output_video', 'N/A')}\n"
                + "─" * 60 + "\n"
                + "VID          ENTITY                         START    END\n"
                + "─" * 60 + "\n"
            )
            for s in log_data.get("segments", []):
                self.res_text.insert(tk.END,
                    f"{s['vid']:12s} {s['entity']:30s} "
                    f"{s['start']:>8} {s['end']:>8}\n")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không hiển thị log: {e}")

    # Callback functions
    def q1(self): self.display(self.rs_tree.find_video_with_object(self.ent_entry.get()))
    def q2(self): self.display(self.rs_tree.find_video_with_activity(self.ent_entry.get()))
    def q3(self): self.display(self.rs_tree.find_video_with_activity_and_prop(self.ent_entry.get(), self.prop_entry.get(), self.val_entry.get()))
    def q4(self): self.display(self.rs_tree.find_video_with_object_and_prop(self.ent_entry.get(), self.prop_entry.get(), self.val_entry.get()))
    
    def q5(self): 
        try: self.display(self.rs_tree.find_objects_in_video(self.vid_entry.get(), int(self.start_entry.get()), int(self.end_entry.get())))
        except: messagebox.showerror("Error", "Cần nhập VideoID, StartFrame, EndFrame (số)")

    def q6(self):
        try: self.display(self.rs_tree.find_activities_in_video(self.vid_entry.get(), int(self.start_entry.get()), int(self.end_entry.get())))
        except: messagebox.showerror("Error", "Cần nhập VideoID, StartFrame, EndFrame (số)")

    def q7(self):
        try: self.display(self.rs_tree.find_activities_and_props_in_video(self.vid_entry.get(), int(self.start_entry.get()), int(self.end_entry.get())))
        except: messagebox.showerror("Error", "Cần nhập VideoID, StartFrame, EndFrame (số)")

    def q8(self):
        try: self.display(self.rs_tree.find_objects_and_props_in_video(self.vid_entry.get(), int(self.start_entry.get()), int(self.end_entry.get())))
        except: messagebox.showerror("Error", "Cần nhập VideoID, StartFrame, EndFrame (số)")

    # AI Processing Functions
    def run_yolo_thread(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "assets", "best.pt")
        video_path = getattr(self, "video_path", os.path.join(base_dir, "assets", "video_demo.mp4"))

        try:
            import cv2
            from ultralytics import YOLO
            has_ai = True
        except ImportError as e:
            has_ai = False

        self._stop_demo = False

        if not has_ai:
            self.ai_status_lbl.config(text="⚠️ Chế độ giả lập: Thiếu opencv-python / ultralytics")
            threading.Thread(target=self.process_video_simulated, daemon=True).start()
            return

        if not os.path.exists(model_path):
            messagebox.showerror("Thiếu file", f"Không tìm thấy mô hình:\n{model_path}")
            return
        if not os.path.exists(video_path):
            messagebox.showerror("Thiếu file", f"Không tìm thấy video:\n{video_path}")
            return

        self.ai_status_lbl.config(text="⏳ Đang nạp mô hình YOLO...")
        threading.Thread(target=self.process_video_yolo,
                         args=(model_path, video_path),
                         daemon=True).start()

    def process_video_simulated(self):
        import time, random
        self.root.after(0, lambda: self.ai_status_lbl.config(text="▶ Đang chạy giả lập nhận diện..."))
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(base_dir, "assets", "detection_log.json")
        new_segments = []
        total_frames = 4500
        
        # Thử đọc từ log cũ để dữ liệu giả lập chất lượng hơn
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    log_data = json.load(f)
                    total_frames = log_data.get("total_frames", 4500)
                    for s in log_data.get("segments", []):
                        new_segments.append(VideoSegment(
                            s["vid"], s["start"], s["end"],
                            s["entity"], s["type"], s.get("prop"), "YOLO_Simulated"
                        ))
            except Exception:
                pass
                
        # Nếu chưa có log, tạo dữ liệu ảo
        if not new_segments:
            mock_classes = ["P.130", "R.302a", "P.102", "R.415a", "I.434a", "P.127*60"]
            frame_idx = 0
            for i in range(25):
                start = frame_idx + random.randint(30, 150)
                end = start + random.randint(10, 50)
                cls = random.choice(mock_classes)
                new_segments.append(VideoSegment(
                    "TrafficCam", start, end, cls, "Object", "AI_Source", "YOLO_Simulated"
                ))
                frame_idx = end
                
        # Giả lập thời gian chạy (tạo hiệu ứng loading cho demo)
        for i in range(1, 101, 5):
            if self._stop_demo: break
            time.sleep(0.15)
            fake_f = int(total_frames * i / 100)
            fake_s = len(new_segments) * i // 100
            self.root.after(0, lambda f=fake_f, s=fake_s:
                self.ai_status_lbl.config(text=f"▶ Giả lập Frame {f}  |  Segments: {s}")
            )
            
        if self._stop_demo: return
            
        self.rs_tree.build(new_segments)
        total = len(new_segments)
        classes = sorted(set(s.entity for s in new_segments))
        
        self.root.after(0, lambda: [
            self.ai_status_lbl.config(text=f"✅ Giả lập hoàn tất! {total_frames} frames – {total} segments."),
            self.log_path_lbl.config(
                text=f"⚠️ Dữ liệu giả lập (Survival Mode)  |  {total} segments  |  {len(classes)} loại biển",
                foreground="#f9e2af"
            ),
            messagebox.showinfo(
                "Demo Giả Lập",
                f"✅ Nhận diện giả lập (Survival Mode) hoàn tất!\n"
                f"(Chương trình không tìm thấy thư viện opencv-python/ultralytics "
                f"nên đã dùng dữ liệu mô phỏng).\n\n"
                f"📦 Số phân đoạn RS-Tree : {total}\n"
                f"🛣️ Các loại biển báo:\n" + "\n".join(f"  • {c}" for c in classes[:10])
                + ("\n  ..." if len(classes) > 10 else "")
            )
        ])

    def process_video_yolo(self, model_path, video_path):
        """Chạy YOLO trên video_demo.mp4, hiển thị cửa sổ live preview,
           cập nhật RS-Tree và lưu video kết quả ra assets/output_demo.mp4."""
        import cv2
        from ultralytics import YOLO

        # --- 1. Nạp mô hình ---
        try:
            model = YOLO(model_path)
            # Vá tương thích AAttn (YOLOv12 weights cũ + ultralytics mới)
            # Model cũ có qk + v tách rời; ultralytics mới gọi self.qkv(x) → cần gộp lại
            try:
                import torch.nn as _nn
                from ultralytics.nn.modules.block import AAttn as _AAttn

                class _QKVWrapper(_nn.Module):
                    """Gộp qk (2C) + v (1C) → 3C để khớp với AAttn.forward() mới."""
                    def __init__(self, qk, v):
                        super().__init__()
                        self.qk = qk
                        self.v  = v
                    def forward(self, x):
                        import torch as _torch
                        return _torch.cat([self.qk(x), self.v(x)], dim=1)

                _patched = 0
                for _m in model.model.modules():
                    if isinstance(_m, _AAttn) and hasattr(_m, 'qk') and hasattr(_m, 'v') and not hasattr(_m, 'qkv'):
                        _m.qkv = _QKVWrapper(_m.qk, _m.v)
                        _patched += 1
                print(f"[AAttn patch] QKVWrapper applied to {_patched} modules")
            except Exception as _patch_e:
                print(f"[AAttn patch] Skipped: {_patch_e}")
        except Exception as e:
            self.root.after(0, lambda err=str(e): [
                self.ai_status_lbl.config(text=f"❌ Lỗi nạp mô hình: {err}"),
                messagebox.showerror("Lỗi YOLO", f"Không thể nạp best.pt:\n{err}")
            ])
            return

        # --- 2. Mở video ---
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.root.after(0, lambda: [
                self.ai_status_lbl.config(text="❌ Không mở được video."),
                messagebox.showerror("Lỗi Video", "Không thể mở video_demo.mp4")
            ])
            return

        fps  = cap.get(cv2.CAP_PROP_FPS) or 25.0
        W    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        H    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # --- 3. Writer lưu video output ---
        base_dir  = os.path.dirname(os.path.abspath(__file__))
        out_path  = os.path.join(base_dir, "assets", "output_demo.mp4")
        writer    = cv2.VideoWriter(
            out_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps, (W, H)
        )

        # --- 4. Vòng lặp xử lý ---
        # NOTE: cv2.imshow() KHÔNG dùng được từ background thread trên Windows
        # → Dùng PIL + tkinter để hiển thị preview trong cửa sổ chính
        SKIP        = 3        # inference mỗi SKIP frame (0,3,6,...) → nhanh 3x
        IMGSZ       = 832      # giữ đúng kích thước train của best.pt
        CONF        = 0.28
        IOU         = 0.45
        PREVIEW_EVERY = 20     # cập nhật ảnh preview tkinter mỗi N frame

        frame_idx    = 0
        active_objs  = {}      # {class_name: start_frame}
        new_segments = []
        last_results = None    # giữ kết quả cũ để vẽ khi skip frame
        _pil_available = True  # có PIL để resize ảnh không

        try:
            from PIL import Image, ImageTk
        except ImportError:
            _pil_available = False

        self.root.after(0, lambda: self.ai_status_lbl.config(
            text=f"▶ Đang chạy demo... ({W}x{H}@{fps:.0f}fps | skip={SKIP} | imgsz={IMGSZ})"
        ))

        try:
            while cap.isOpened() and not self._stop_demo:
                ret, frame = cap.read()
                if not ret:
                    break

                try:
                    # ── Inference (chỉ mỗi SKIP frame) ──────────────────
                    if frame_idx % SKIP == 0:
                        # Resize frame về IMGSZ trước khi predict → tránh shape mismatch
                        frame_in = cv2.resize(frame, (IMGSZ, IMGSZ))
                        results      = model.predict(
                            frame_in, imgsz=IMGSZ,
                            conf=CONF, iou=IOU, verbose=False
                        )
                        last_results = results
                    else:
                        results = last_results  # dùng lại kết quả trước

                    # ── Vẽ bounding box lên frame gốc (không phải frame resize) ─
                    if results:
                        # Plot trên frame_in để tránh scale sai, sau đó resize lại
                        ann_small = results[0].plot()
                        annotated  = cv2.resize(ann_small, (W, H))
                    else:
                        annotated = frame.copy()

                    # HUD overlay
                    hud = (f"Frame {frame_idx}  |  conf>{CONF}  "
                           f"| skip={SKIP}  | seg={len(new_segments)}")
                    cv2.putText(annotated, hud, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 200), 2)

                    writer.write(annotated)

                    # ── Preview trong tkinter (mỗi PREVIEW_EVERY frame) ──
                    if frame_idx % PREVIEW_EVERY == 0 and _pil_available:
                        try:
                            rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(rgb)
                            pil_img.thumbnail((480, 270))   # giới hạn kích thước
                            img_tk = ImageTk.PhotoImage(pil_img)
                            # Lưu ref để tránh garbage-collect
                            self._preview_tk = img_tk
                            self.root.after(0, lambda i=img_tk:
                                self.img_label.config(image=i, text="")
                            )
                        except Exception:
                            pass  # preview lỗi không làm dừng vòng lặp

                    # ── Cập nhật RS-Tree segment tracking ───────────────
                    if results:
                        current_classes = set()
                        for r in results:
                            for c in r.boxes.cls:
                                current_classes.add(model.names[int(c)])

                        for cls in current_classes:
                            if cls not in active_objs:
                                active_objs[cls] = frame_idx

                        to_remove = []
                        for cls in list(active_objs):
                            if cls not in current_classes:
                                new_segments.append(VideoSegment(
                                    "TrafficCam", active_objs[cls], frame_idx - 1,
                                    cls, "Object", "AI_Source", "YOLO"
                                ))
                                to_remove.append(cls)
                        for cls in to_remove:
                            del active_objs[cls]

                    # ── Cập nhật status label tkinter mỗi 30 frame ──────
                    if frame_idx % 30 == 0:
                        _f, _s = frame_idx, len(new_segments)
                        self.root.after(0, lambda f=_f, s=_s:
                            self.ai_status_lbl.config(
                                text=f"▶ Frame {f}  |  Segments: {s}"
                            )
                        )

                except Exception as frame_err:
                    # Lỗi ở 1 frame → in ra nhưng KHÔNG dừng vòng lặp
                    err_type = type(frame_err).__name__
                    print(f"[WARN] Frame {frame_idx} skip ({err_type}): {str(frame_err)[:80]}")

                frame_idx += 1

        finally:
            # Đóng các segment vẫn còn active khi video kết thúc
            for cls, start_f in active_objs.items():
                new_segments.append(VideoSegment(
                    "TrafficCam", start_f, frame_idx,
                    cls, "Object", "AI_Source", "YOLO"
                ))

            cap.release()
            writer.release()
            cv2.destroyAllWindows()

            # ── Lưu detection log ra JSON ────────────────────────────────
            log_data = {
                "recorded_at"  : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source_video" : video_path,
                "output_video" : out_path,
                "total_frames" : frame_idx,
                "segments"     : [
                    {
                        "vid"   : s.vid,
                        "start" : s.start,
                        "end"   : s.end,
                        "entity": s.entity,
                        "type"  : s.type,
                        "prop"  : s.prop,
                        "val"   : s.val,
                    }
                    for s in new_segments
                ]
            }
            _log_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "assets", "detection_log.json"
            )
            try:
                with open(_log_path, "w", encoding="utf-8") as _f:
                    json.dump(log_data, _f, ensure_ascii=False, indent=2)
                print(f"[LOG] Đã lưu: {_log_path}")
            except Exception as _log_e:
                print(f"[LOG] Lỗi ghi log: {_log_e}")

            # Cập nhật RS-Tree
            self.rs_tree.build(new_segments)

            total = len(new_segments)
            classes = sorted(set(s.entity for s in new_segments))
            self.root.after(0, lambda: self.ai_status_lbl.config(
                text=f"✅ Hoàn tất! {frame_idx} frames – {total} segments – Đã lưu log."
            ))
            self.root.after(0, lambda p=_log_path, n=total, c=classes: self.log_path_lbl.config(
                text=f"💾 {p}  |  {n} segments  |  {len(c)} loại biển: {', '.join(c[:6])}"
                     + (" ..." if len(c) > 6 else ""),
                foreground="#1a7a1a"
            ))
            self.root.after(0, lambda: messagebox.showinfo(
                "Demo Hoàn Tất",
                f"✅ Nhận diện biển báo YOLO xong!\n\n"
                f"📹 Frames đã xử lý : {frame_idx}\n"
                f"📦 Segments RS-Tree  : {total}\n"
                f"💾 Log JSON        : assets/detection_log.json\n"
                f"💾 Video kết quả  : assets/output_demo.mp4\n\n"
                f"🛣️ Các loại biển báo nhận được:\n" + "\n".join(f"  • {c}" for c in classes)
            ))


# ==============================================================================
# MAIN & DATA GENERATION
# ==============================================================================

if __name__ == "__main__":
    # Tạo dữ liệu giả lập cho video 100 frames
    # Cú pháp: VideoSegment(vid, start, end, entity, type, prop, val)
    mock_data = [
        VideoSegment("V1", 0, 40, "PersonA", "Object", "Action", "Walking"),
        VideoSegment("V1", 10, 60, "CarX", "Object", "Color", "Red"),
        VideoSegment("V1", 20, 50, "Walking", "Activity", "Intensity", "Low"),
        VideoSegment("V2", 0, 100, "PersonB", "Object", "Role", "Runner"),
        VideoSegment("V2", 30, 70, "Running", "Activity", "Speed", "High"),
        VideoSegment("V1", 70, 100, "PersonA", "Object", "Action", "Sitting"),
    ]

    rs = RSTree()
    rs.build(mock_data)

    root = tk.Tk()
    app = RSTreeApp(root, rs)
    
    # In ra terminal hướng dẫn
    print("--- Ứng dụng RS-tree đã khởi động ---")
    print("Dữ liệu mẫu Video V1 (0-100 frames) và V2 (0-100 frames) đã được nạp.")
    
    root.mainloop()
