---
name: griductive-experiments-and-testing
description: Xây dựng bộ kiểm thử tự động và script chạy thực nghiệm xuất bảng số liệu/biểu đồ phục vụ báo cáo PDF.
---

# Quy tắc Thực nghiệm (Experiments) & Kiểm thử (Testing)

## 1. Script Thực nghiệm Tự động (`benchmark/run_experiments.py`)
Theo mục 4.5 của đề bài, viết script chạy tự động qua tập các màn chơi $3\times3$, $4\times4$, và $5\times5$ (stress cases) để thu thập đầy đủ 6 nhóm số liệu:
1. Số lượng Primary variables và Auxiliary variables.
2. Số lượng mệnh đề CNF (CNF clauses).
3. Tổng số lần gọi SAT solver (`SAT calls`).
4. Tổng số `Decisions`, `Propagations`, và `Backtracks`.
5. Số bước suy diễn (`Deduction steps`) và số đợt mở thẻ (`Reveal waves`).
6. Thời gian chạy (`Runtime` tính bằng mili-giây).

Script tự động xuất kết quả ra:
- File `benchmark/experiment_results.csv` và bảng định dạng LaTeX / Markdown để chèn thẳng vào báo cáo.
- Các biểu đồ so sánh (dùng `matplotlib`) lưu thành file ảnh PNG độ phân giải cao trong `benchmark/plots/`.

## 2. Bộ Kiểm thử Đảm bảo Chất lượng (`tests/test_all.py`)
Trước khi hoàn tất, Agent phải chạy kiểm thử xác nhận:
- **Test CNF vs Direct Semantics**: Với mọi mẫu clue (6 cơ bản + 2 mở rộng) trên lưới $3\times3$, vét cạn toàn bộ $2^9 = 512$ phép gán để đảm bảo tập nghiệm thỏa mãn công thức CNF trùng khớp 100% với kết quả của `Direct Semantic Evaluator`.
- **Test DPLL**: Kiểm tra các công thức SAT, UNSAT, mệnh đề đơn, mâu thuẫn trực tiếp.
- **Test Role Isolation**: Đảm bảo `LogicAgent` không chứa bất kỳ tham chiếu nào tới thuộc tính ẩn của `GameEngine`.
- **Test 55 Levels**: Chạy solver tự động qua toàn bộ 55 màn chơi trong `levels_manifest.json` để đảm bảo cả 55 màn chơi đều giải xong 100% mà không cần đoán.