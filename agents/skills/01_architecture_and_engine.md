---
name: griductive-core-engine
description: Xây dựng mô hình dữ liệu, hệ thống vùng (Regions), bộ đánh giá ngữ nghĩa trực tiếp (Direct Semantic Evaluator) và Game Engine tách biệt hoàn toàn với Logic Agent.
---

# Quy tắc Kiến trúc & Game Engine (Griductive)

## 1. Nguyên tắc cô lập dữ liệu (Strict Role Separation)
- **GameEngine (`core/engine.py`)**: Nắm giữ toàn bộ trạng thái màn chơi bao gồm `hidden_solution` (Criminal/Innocent của toàn bộ $N \times N$ ô) và các `unrevealed_clues`.
- **LogicAgent (`solver/agent.py`)**: CHỈ ĐƯỢC PHÉP nhận `PublicKnowledgeState` (gồm kích thước lưới $N$, danh sách tên/nghề nghiệp, các trạng thái đã được chứng minh và các manh mối đã lật mở). Tuyệt đối không truy cập vào `hidden_solution` của Engine.

## 2. Hệ tọa độ và Định danh (`core/models.py`, `core/regions.py`)
- Lưới kích thước $N \times N$ với $N \in \{3, 4, 5\}$.
- Cột đánh chữ cái từ trái sang phải (`A`, `B`, `C`...), hàng đánh số từ trên xuống dưới (`1`, `2`, `3`...). Ví dụ: `C2` là cột C (index 2), hàng 2 (index 1).
- Nhân vật trên bàn cờ được sắp xếp tên theo thứ tự bảng chữ cái tăng dần từ trái sang phải, từ trên xuống dưới (Row-major order).
- **Regions cơ bản**:
  - `ROW(r)`: Tất cả các ô thuộc hàng `r`.
  - `COL(c)`: Tất cả các ô thuộc cột `c`.
  - `NEIGHBORS(cell_id)`: Tối đa 8 ô xung quanh chạm ngang, dọc, chéo với `cell_id` (loại trừ chính `cell_id`).
  - `CELLS([id1, id2, ...])`: Danh sách các ô chỉ định tường minh.
- **2 Extensions bắt buộc (Mở rộng vùng & loại manh mối)**:
  1. **Advanced Region (`COMMON_NEIGHBORS(cell_1, cell_2)` và `BOUNDARY` / `CORNERS`)**: Giao của 2 tập láng giềng hoặc các ô nằm ở viền/góc bàn cờ.
  2. **Advanced Clue (`PARITY(region, is_odd)` và `COMPARE_COUNT(region_A, region_B, op)`)**: Tổng số tội phạm trong vùng là chẵn/lẻ, hoặc so sánh số lượng tội phạm giữa 2 vùng (`=`, `>`, `<`).

## 3. Direct Semantic Evaluator (`core/semantics.py`)
- Bắt buộc cài đặt hàm `evaluate_clue_directly(clue: Clue, assignment: dict[str, bool]) -> bool` cho TẤT CẢ các mẫu manh mối (6 mẫu cơ bản + 2 mẫu mở rộng).
- Hàm này kiểm tra tính đúng/sai của một manh mối dựa trực tiếp trên một phép gán đầy đủ (`assignment` ánh xạ `cell_id -> True/False`) bằng toán học/logic thông thường mà **không gọi qua bộ mã hóa CNF**. Dùng để kiểm thử chéo (cross-validate) CNF Encoder và dùng trong quá trình sinh màn chơi.

## 4. Cơ chế kiểm tra phán quyết (Verdict Protocol)
Khi người chơi hoặc Agent gửi một phán quyết `(cell_id, verdict)` với `verdict` $\in \{\text{CRIMINAL}, \text{INNOCENT}\}$:
- Engine gọi `LogicAgent.check_entailment(public_state, cell_id)` để kiểm tra xem phán quyết có được suy diễn hợp thức từ $KB_t$ hiện tại hay không:
  - Nếu đúng với trạng thái bắt buộc (Entailed): Chấp nhận, mở thẻ, thêm trạng thái và manh mối mới vào $KB_{t+1}$, trả về `ACCEPTED`.
  - Nếu không có trạng thái nào bắt buộc (cả 2 nhánh SAT đều thỏa): Giữ nguyên trạng thái, trả về `NOT_PROVABLE`.
  - Nếu trạng thái ngược lại mới là bắt buộc: Giữ nguyên trạng thái, trả về `CONTRADICTED`.