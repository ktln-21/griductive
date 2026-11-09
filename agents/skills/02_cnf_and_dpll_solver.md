---
name: griductive-cnf-dpll-solver
description: Cài đặt bộ chuyển đổi tự động Clue sang CNF, thuật toán DPLL SAT Solver từ đầu và Deductive Logic Agent không đoán mò.
---

# Quy tắc Logic học, Mã hóa CNF & DPLL SAT Solver

## 1. Biến mệnh đề và Mã hóa CNF tự động (`solver/cnf_encoder.py`)
- Không dùng thư viện SAT có sẵn (như PySAT, Z3). Tự cài đặt hoàn toàn bằng Python chuẩn.
- Ánh xạ biến tất định (Deterministic variable map): Mỗi ô/nhân vật $i$ ứng với một số nguyên dương $v_i \in \{1, 2, \dots, N^2\}$ theo thứ tự row-major.
  - Literal dương `+v_i`: Nhân vật $i$ là `CRIMINAL` ($C_i = \text{True}$).
  - Literal âm `-v_i`: Nhân vật $i$ là `INNOCENT` ($C_i = \text{False}$).
- Biến phụ (Auxiliary variables) nếu dùng phải bắt đầu từ $N^2 + 1$ trở đi và được thống kê tách biệt với biến chính.
- **Quy tắc chuyển đổi 6 Clue cơ bản sang CNF**:
  1. `FACT(i, status)`: Mệnh đề đơn `[[v_i]]` nếu Criminal, `[[-v_i]]` nếu Innocent.
  2. `SAME(i, j)` ($C_i \leftrightarrow C_j$): `[[-v_i, v_j], [v_i, -v_j]]`.
  3. `DIFFERENT(i, j)` ($C_i \oplus C_j$): `[[-v_i, -v_j], [v_i, v_j]]`.
  4. `AT_LEAST(k, R)` ($\sum_{i \in R} C_i \ge k$): Với mọi tổ hợp con kích thước $|R| - k + 1$ của vùng $R$, tạo một mệnh đề chứa tất cả các literal dương trong tổ hợp đó. (Nếu $k \le 0$: trả về `[]`; nếu $k > |R|$: trả về `[[]]` - UNSAT).
  5. `AT_MOST(k, R)` ($\sum_{i \in R} C_i \le k$): Với mọi tổ hợp con kích thước $k + 1$ của vùng $R$, tạo một mệnh đề chứa tất cả các literal âm của các phần tử trong tổ hợp đó.
  6. `EXACTLY(k, R)`: Kết hợp danh sách mệnh đề của `AT_LEAST(k, R)` và `AT_MOST(k, R)`. Từ khóa `NO` tương đương `EXACTLY(0, R)`.
  - *Lưu ý*: Nếu clue đếm số người `INNOCENT` (ví dụ: "Exactly 2 innocents in row 1"), hãy đảo dấu toàn bộ các literal trong vùng $R$ trước khi áp dụng công thức đếm, hoặc quy đổi số tội phạm $k_{\text{crim}} = |R| - k_{\text{inno}}$.
- **Quy tắc chuyển đổi 2 Clue mở rộng sang CNF**:
  - `PARITY(R, is_odd)`: Tổ hợp các mệnh đề loại trừ các phép gán trên vùng $R$ có tổng số literal dương không khớp tính chẵn/lẻ.
  - `COMPARE_COUNT(R1, R2, op)`: Mã hóa tổ hợp hoặc dùng biến phụ bộ đếm tuần tự (Sequential Counter Encoding) cho các vùng giao/tách.

## 2. Thuật toán DPLL SAT Solver (`solver/dpll.py`)
Cài đặt class `DPLLSolver` với các tính năng bắt buộc:
- **Unit Propagation**: Tìm các mệnh đề đơn `[lit]`, gán giá trị cho `lit`, rút gọn tập mệnh đề (xóa mệnh đề chứa `lit`, xóa `-lit` khỏi các mệnh đề khác). Lặp lại đến khi không còn mệnh đề đơn.
- **Conflict Detection**: Nếu xuất hiện mệnh đề rỗng `[]`, lập tức trả về `UNSAT` và backtrack.
- **Deterministic Variable Selection**: Chọn biến chưa gán theo thứ tự từ điển/số thứ tự nhỏ nhất (hoặc heuristic Jeroslow-Wang / MOMs có tie-break tất định) để đảm bảo kết quả chạy lặp lại 100% giống nhau.
- **Recursive Branching & Backtracking**: Thử gán `True` trước, nếu thất bại thì backtrack và thử `False`.
- **Metrics Tracking**: Ghi nhận chính xác trong mỗi lần gọi:
  - `decisions`: Số lần rẽ nhánh đệ quy.
  - `propagations`: Số lần lan truyền đơn vị.
  - `backtracks`: Số lần quay lui khi gặp mâu thuẫn.
  - `runtime_ms`: Thời gian thực thi (đo bằng `time.perf_counter()`).

## 3. Deductive Logic Agent (`solver/agent.py`)
- Xây dựng $KB_t = \text{CNF}(\text{revealed\_clues}) \cup \{\text{unit clauses của các ô đã mở}\}$.
- Kiểm tra suy diễn hợp thức (Entailment Check) cho từng ô chưa mở $i$:
  - Gọi DPLL kiểm tra $KB_t \wedge \neg C_i$ (tức thêm `[-v_i]` vào $KB_t$). Nếu `UNSAT` $\implies$ $KB_t \models C_i$ (`CRIMINAL`).
  - Ngược lại, gọi DPLL kiểm tra $KB_t \wedge C_i$ (thêm `[v_i]` vào $KB_t$). Nếu `UNSAT` $\implies$ $KB_t \models \neg C_i$ (`INNOCENT`).
  - Nếu cả hai đều `SAT` $\implies$ trả về `UNKNOWN` (Tuyệt đối không đoán).
  - Nếu bản thân $KB_t$ đã `UNSAT` $\implies$ trả về `INCONSISTENT`.
- **Thứ tự ưu tiên**: Nếu có nhiều ô cùng suy diễn được ở bước $t$, chọn ô đầu tiên theo thứ tự Row-major (A1 -> B1 -> C1 -> A2...).
- **Deduction Trace**: Lưu lịch sử từng bước giải gồm: `step_number`, `active_clue_ids`, `sat_queries_count`, `target_cell`, `verdict`, `newly_revealed_clue`, và các metrics của DPLL.
- **Uniqueness Check**: Hàm kiểm tra toàn bộ tập manh mối của màn chơi có duy nhất 1 nghiệm hay không (tìm 1 nghiệm $M$ bằng DPLL, sau đó thêm mệnh đề phủ định nghiệm $\neg M$ vào KB và gọi DPLL lần 2; nếu lần 2 trả về `UNSAT` thì nghiệm là duy nhất).