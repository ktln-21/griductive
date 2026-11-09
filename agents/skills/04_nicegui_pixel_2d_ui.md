---
name: griductive-nicegui-pixel-ui
description: Thiết kế giao diện web bằng NiceGUI theo phong cách Pixel Art 2D cổ điển, đầy đủ hiệu ứng lật thẻ, highlight vùng manh mối, Hint, Auto-Solve và bảng theo dõi thực nghiệm.
---

# Quy tắc Giao diện NiceGUI Phong cách Pixel Art 2D

## 1. Phong cách Thị giác Pixel Art 2D (`ui/theme.py`)
- **Fonts**: Nhúng Google Fonts `'Press Start 2P'` (cho tiêu đề, số liệu, nút bấm, nhãn tọa độ) và `'VT323'` hoặc `'Silkscreen'` (kích thước chữ lớn dễ đọc cho nội dung manh mối trên thẻ).
- **Bảng màu Retro Detective (8-bit / 16-bit Palette)**:
  - Nền chính: Xám đen cổ điển `#1a1c2c` hoặc nâu gỗ bàn thám tử `#262b44`.
  - Thẻ úp (Face-down Card): Nền `#333c57`, viền pixel kép `#566c86`.
  - Thẻ `INNOCENT` (Đã mở): Nền kem sáng `#f4f4f4`, khung viền xanh ngọc/xanh lá `#38b764` hoặc `#29adff`.
  - Thẻ `CRIMINAL` (Đã mở): Nền kem sáng `#f4f4f4`, khung viền đỏ cam/tím `#e43b44` hoặc `#b13e53`.
  - Ô đang được Highlight (Referenced by selected clue): Viền vàng chớp sáng `#ffcd75` kèm hiệu ứng `box-shadow` dạng bậc thang pixel.
- **Đổ bóng & Viền (Pixel Border CSS)**:
  - Không dùng `border-radius` bo tròn mượt; sử dụng góc vuông (`border-radius: 0px`) kết hợp `box-shadow: 4px 4px 0px #000000` và `image-rendering: pixelated;`.
- **Avatar Nhân vật Pixel 2D**:
  - Tự động sinh SVG Pixel Art 8x8 / 16x16 trực tiếp bằng code Python cho từng nhân vật (dựa trên hash của tên và nghề nghiệp: mũ cảnh sát cho Guard/Detective, mũ đầu bếp cho Cook, kính cho Clerk...) để game chạy offline 100% không phụ thuộc ảnh mạng bên ngoài.

## 2. Tương tác Bàn cờ & Thẻ Nhân vật (`ui/components.py`, `ui/app.py`)
- **Hiển thị trên mỗi Thẻ (Card)**:
  - Góc trái trên: Tọa độ ô (`A1`, `B2`...).
  - Giữa: Pixel Art Avatar + Tên nhân vật (in đậm) + Nghề nghiệp.
  - Nếu thẻ đang úp: Hiển thị 2 nút hành động kiểu pixel `[ INNOCENT ]` (màu xanh) và `[ CRIMINAL ]` (màu đỏ) khi người chơi click/hover vào thẻ.
  - Nếu thẻ đã mở: Hiển thị huy hiệu `INNOCENT` / `CRIMINAL` và toàn bộ câu manh mối. Các từ khóa quan trọng (tên người, tọa độ, số lượng) được tô màu nổi bật giống bản web gốc.
- **Tính năng Click Manh mối để Highlight (Bắt buộc theo đề bài)**:
  - Khi người chơi click vào một thẻ đã mở (chứa manh mối), giao diện lập tức đổi màu viền (Highlight vàng/xanh sáng) tất cả các ô trên bàn cờ nằm trong vùng tham chiếu (`referenced_cells`) của manh mối đó.
- **Phản hồi khi Phán quyết Sai / Chưa đủ bằng chứng**:
  - Nếu Engine trả về `NOT_PROVABLE`: Rung nhẹ thẻ (CSS shake animation), hiện thông báo toast kiểu pixel: `"NOT PROVABLE! Verdict is not logically forced yet — Do not guess!"`
  - Nếu Engine trả về `CONTRADICTED`: Rung thẻ, hiện thông báo cảnh báo đỏ: `"CONTRADICTED! The opposite status is logically forced by current clues!"`

## 3. Bảng Điều khiển & Thanh Công cụ (Controls & Inspector Panel)
Giao diện chia làm 2 cột chính (Trái: Bàn cờ $N \times N$ + Thanh điều khiển; Phải: Sổ tay Thám tử & Bảng thông số AI):
- **Thanh điều khiển trên cùng**:
  - Dropdown chọn màn chơi từ **Level 1 đến Level 55** (hiển thị kích thước $3\times3, 4\times4, 5\times5$ và trạng thái Đã giải / Chưa giải).
  - Nút `Restart`: Đặt lại màn chơi hiện tại về trạng thái ban đầu.
  - Nút `Hint`: Gọi `LogicAgent.get_hint()`, tô sáng nhân vật tiếp theo có thể suy diễn được cùng các manh mối đang ép trạng thái của nhân vật đó.
  - Nút `Step AI`: Để AI tự động suy diễn và mở đúng 1 ô tiếp theo.
  - Nút `Auto Solve`: Chạy vòng lặp bất đồng bộ (`asyncio.sleep(0.4)`) mở từng ô theo chuỗi suy diễn của AI trực tiếp trên giao diện.
- **Sổ tay Thám tử (Deduction Trace & CNF Metrics Panel)**:
  - Hiển thị trực quan theo thời gian thực:
    - Số biến chính (Primary Vars), Số biến phụ (Aux Vars), Số mệnh đề CNF hiện tại (CNF Clauses).
    - Thống kê DPLL cộng dồn: Số lần gọi SAT (`SAT Calls`), `Decisions`, `Propagations`, `Backtracks`, `Runtime (ms)`.
    - Nhật ký suy diễn (Step-by-step Deduction Log): Ghi rõ ở Bước $t$, AI đã dùng những clue nào để chứng minh $KB_t \wedge \neg C_i = \text{UNSAT}$ và kết luận trạng thái nhân vật.