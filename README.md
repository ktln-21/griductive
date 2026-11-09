# Griductive Solver (CSC14003 - Project 2)
### Giải đố Logic Thuần túy (Deductive SAT Logic) với DPLL Solver và Giao diện Web NiceGUI Pixel Art 2D

Đồ án triển khai hệ thống giải đố **Griductive** dựa trên logic mệnh đề (Propositional Logic) và thuật toán **DPLL SAT Solver** tự cài đặt từ đầu (không sử dụng thư viện SAT bên thứ ba). Trò chơi đảm bảo **100% No-Guess** (suy diễn logic tất định, không cần đoán mò).

---

## 1. Cấu trúc Dự án

```
.
├── main.py                     # Entry point khởi chạy NiceGUI server (http://127.0.0.1:8080)
├── requirements.txt            # Thư viện phụ thuộc (nicegui, pytest, matplotlib)
├── README.md                   # Tài liệu hướng dẫn chi tiết
├── core/
│   ├── __init__.py
│   ├── models.py               # Mô hình dữ liệu: Character, Clue, Region, Role, PublicKnowledgeState
│   ├── regions.py              # Xử lý tọa độ (A1..E5), ROW, COL, NEIGHBORS, CORNERS, COMMON_NEIGHBORS
│   ├── semantics.py            # Direct Semantic Evaluator (đánh giá clue trực tiếp không qua CNF)
│   └── engine.py               # GameEngine độc lập, cô lập tuyệt đối dữ liệu ẩn với LogicAgent
├── solver/
│   ├── __init__.py
│   ├── cnf_encoder.py          # Chuyển đổi Clue sang CNF (6 cơ bản + 2 mở rộng PARITY, COMPARE_COUNT)
│   ├── dpll.py                 # Thuật toán DPLL SAT Solver tự code (Unit Propagation, Conflict, MOMs)
│   └── agent.py                # Deductive Logic Agent (Entailment Check, Hint, Step AI, Auto-Solve, Uniqueness)
├── generator/
│   └── level_gen.py            # Script sinh tự động và kiểm duyệt 55 màn chơi No-Guess
├── levels/
│   └── levels_manifest.json    # Bộ 55 màn chơi chuẩn (3x3: 1-15, 4x4: 16-43, 5x5: 44-55)
├── ui/
│   ├── __init__.py
│   ├── theme.py                # Theme Pixel Art 2D (Fonts Press Start 2P, VT323, Avatar SVG tự sinh)
│   ├── components.py           # Card nhân vật 2D, bảng metrics SAT/DPLL, Detective Notebook log
│   └── app.py                  # Ghép nối luồng sự kiện UI với GameEngine và DeductiveLogicAgent
├── benchmark/
│   ├── run_experiments.py      # Script chạy thực nghiệm tự động qua toàn bộ 55 màn chơi
│   ├── experiment_results.csv  # Kết quả thực nghiệm chi tiết từng màn
│   ├── experiment_summary.md   # Bảng tổng hợp số liệu Markdown
│   ├── experiment_table.tex    # Bảng LaTeX chèn báo cáo PDF
│   └── plots/                  # Biểu đồ thực nghiệm độ phân giải cao (Runtime, DPLL Ops, SAT Calls)
└── tests/
    ├── test_core.py            # Kiểm thử DPLL cơ bản, Semantic Evaluator, Role Isolation
    └── test_all.py             # Bộ test toàn diện (vét cạn 512 phép gán CNF và giải 100% 55 levels)
```

---

## 2. Các Tính năng & Kỹ thuật Cốt lõi

### 2.1. Cô lập dữ liệu tuyệt đối (Role Separation)
- **`GameEngine`**: Nắm giữ đáp án ẩn `_hidden_solution` và manh mối úp `_unrevealed_clues`.
- **`LogicAgent`**: CHỈ nhận `PublicKnowledgeState` gồm kích thước lưới, thông tin nhân vật, các ô và manh mối đã công khai.
- **Verdict Protocol**: Khi người chơi gửi phán quyết `(cell_id, verdict)`:
  - Gọi `agent.check_entailment()`:
    - Nếu trạng thái bị ép bởi $KB_t$: Chấp nhận (`ACCEPTED`), lật thẻ và mở manh mối mới.
    - Nếu không bị ép ($KB_t \wedge C$ và $KB_t \wedge \neg C$ đều SAT): Trả về `NOT_PROVABLE` (Cảnh báo "Do not guess!", rung thẻ).
    - Nếu trạng thái ngược lại mới là bắt buộc: Trả về `CONTRADICTED` (Cảnh báo mâu thuẫn).

### 2.2. Mã hóa CNF Tự động & 2 Mở rộng (Extensions)
- Ánh xạ biến tất định: Ô $(r, c) \mapsto v = r \times N + c + 1$. Biến dương $+v$ là `CRIMINAL`, âm $-v$ là `INNOCENT`.
- **6 Clue cơ bản**: `FACT`, `SAME`, `DIFFERENT`, `AT_LEAST(k, R)`, `AT_MOST(k, R)`, `EXACTLY(k, R)`.
- **2 Extensions**:
  1. **Advanced Region**: `COMMON_NEIGHBORS(c1, c2)` (giao của 2 tập láng giềng) và `CORNERS` (4 góc bàn cờ).
  2. **Advanced Clue**:
     - `PARITY(region, is_odd)`: Mã hóa tính chẵn/lẻ của số lượng tội phạm trong vùng.
     - `COMPARE_COUNT(region_A, region_B, op)`: So sánh số tội phạm giữa hai vùng (`=`, `>`, `<`).

### 2.3. DPLL SAT Solver Tự viết (From Scratch)
- **Unit Clause Propagation**: Lan truyền đơn vị và cập nhật trạng thái mệnh đề bằng watch-lists.
- **Conflict Detection**: Nhận diện mệnh đề rỗng và quay lui (backtracking).
- **Deterministic Heuristic**: MOMs (Maximum Occurrences in clauses of Minimum size) có tie-break theo chỉ số biến.
- **Metrics Tracking**: Đo lường chính xác `decisions`, `propagations`, `backtracks`, `sat_calls`, và `runtime_ms`.

### 2.4. Deductive Logic Agent (Không đoán mò)
- Kiểm tra suy diễn hợp thức (Entailment):
  - $KB_t \wedge \neg C_i \implies \text{UNSAT} \implies KB_t \models C_i$ (`CRIMINAL`).
  - $KB_t \wedge C_i \implies \text{UNSAT} \implies KB_t \models \neg C_i$ (`INNOCENT`).
- Hỗ trợ đầy đủ: `get_hint()`, `step_solve()`, `auto_solve()`, và `check_uniqueness()`.

### 2.5. 55 Màn chơi No-Guess Chuẩn hóa (`levels/levels_manifest.json`)
- **Chapter 1 (Levels 1 - 15)**: Lưới 3x3, manh mối cơ bản (FACT, SAME, DIFFERENT, EXACTLY).
- **Chapter 2 (Levels 16 - 35)**: Lưới 4x4, kết hợp 6 clue cơ bản và vùng nâng cao (COMMON_NEIGHBORS, CORNERS).
- **Chapter 3 (Levels 36 - 50)**: Lưới 4x4 & 5x5, tích hợp đầy đủ PARITY, COMPARE_COUNT, chuỗi suy diễn sâu.
- **Chapter 4 (Levels 51 - 55)**: Lưới 5x5 Stress Test mật độ ràng buộc cao phục vụ đo lường thực nghiệm.

### 2.6. Giao diện Web NiceGUI Pixel Art 2D
- **Visuals**: Google Fonts `'Press Start 2P'` và `'VT323'`. Bảng màu retro detective (`#1a1c2c`, `#333c57`, `#38b764`, `#e43b44`, `#ffcd75`).
- **Pixel Avatar SVG**: Tự động sinh SVG Pixel Art 16x16 bằng Python không phụ thuộc internet (mũ thám tử, cảnh sát, đầu bếp, kính mắt...).
- **Tương tác**: Click vào thẻ/manh mối để tự động highlight vàng các ô thuộc vùng tham chiếu (`referenced_cells`).
- **Bảng theo dõi**: Real-time CNF & DPLL metrics và nhật ký suy diễn từng bước (Detective Notebook).

---

## 3. Cài đặt và Khởi chạy

### Bước 1: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### Bước 2: Chạy kiểm thử tự động (Unit Tests)
```bash
python -m pytest tests/test_all.py -v
```
Toàn bộ 4 bài test (bao gồm kiểm thử vét cạn 512 phép gán trên 3x3 và giải tự động 55 màn chơi) sẽ chạy và đạt 100% PASS.

### Bước 3: Chạy Thực nghiệm & Xuất Biểu đồ cho Báo cáo
```bash
python benchmark/run_experiments.py
```
Kết quả được xuất ra:
- `benchmark/experiment_results.csv`
- `benchmark/experiment_summary.md`
- `benchmark/experiment_table.tex`
- `benchmark/plots/` (3 biểu đồ PNG)

### Bước 4: Khởi chạy Giao diện Web NiceGUI
```bash
python main.py
```
Truy cập trình duyệt tại địa chỉ: **`http://127.0.0.1:8080`**

---

## 4. Tóm tắt Kết quả Thực nghiệm

| Kích thước | Số lượng màn | Mệnh đề CNF TB | SAT Calls TB | Decisions TB | Propagations TB | Backtracks TB | Thời gian chạy TB | Tỷ lệ giải được |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **3x3** | 15 màn | 28.2 | 52.2 | 119.5 | 414.2 | 0.0 | **4.71 ms** | **100.0%** |
| **4x4** | 28 màn | 50.9 | 141.6 | 822.4 | 2044.3 | 0.0 | **29.01 ms** | **100.0%** |
| **5x5** | 12 màn | 83.1 | 327.7 | 3500.1 | 7638.3 | 0.0 | **114.30 ms** | **100.0%** |
