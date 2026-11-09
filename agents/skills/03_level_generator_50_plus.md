---
name: griductive-level-generator
description: Thuật toán sinh tự động hơn 50 màn chơi Griductive đa dạng độ khó, đảm bảo 100% giải được bằng suy diễn logic thuần túy không cần đoán.
---

# Quy tắc Sinh tự động 50+ Màn chơi (No-Guess Procedural Generator)

## 1. Phân bổ 55 màn chơi tiêu chuẩn (`generator/level_gen.py`)
Viết script sinh tự động và lưu thành file JSON trong `levels/levels_manifest.json` với tối thiểu **55 màn chơi** chia làm 4 chương (Chapters):
- **Chapter 1 - Rookie Detective (Màn 1 - 15)**: Lưới $3 \times 3$, sử dụng các clue cơ bản (`FACT`, `SAME`, `DIFFERENT`, `EXACTLY` trên Row/Col/Neighbors). Số ô mở sẵn ban đầu: 1–2 ô.
- **Chapter 2 - Senior Inspector (Màn 16 - 35)**: Lưới $4 \times 4$, kết hợp toàn bộ 6 clue cơ bản (`AT_LEAST`, `AT_MOST`, `EXACTLY`, `SAME`, `DIFFERENT`) và vùng nâng cao (`COMMON_NEIGHBORS`, `CORNERS`). Số ô mở sẵn ban đầu: 1–2 ô.
- **Chapter 3 - Mastermind (Màn 36 - 50)**: Lưới $4 \times 4$ phức tạp và $5 \times 5$, tích hợp đầy đủ 2 Extensions (`PARITY`, `COMPARE_COUNT`), đòi hỏi chuỗi suy diễn sâu (6–12 reveal waves) và kết hợp nhiều manh mối cùng lúc mới suy ra được 1 ô.
- **Chapter 4 - Stress Test Suite (Màn 51 - 55)**: Lưới $5 \times 5$ mật độ ràng buộc chéo cao, dùng riêng cho phần đánh giá thực nghiệm (Experiments) trong báo cáo.

## 2. Thuật toán Sinh màn chơi Đảm bảo Suy diễn (Forward-Chaining Constructive Generation)
Để đảm bảo màn chơi **100% No-Guess** và không bị dư thừa hay mâu thuẫn, áp dụng quy trình 5 bước sau với `random.seed` cố định cho từng level:
1. **Khởi tạo Ground Truth ($S^*$)**: Sinh ngẫu nhiên một bảng phân bố `CRIMINAL` / `INNOCENT` cho lưới $N \times N$ (tỷ lệ tội phạm khoảng 35% – 65%), gán tên nhân vật theo thứ tự chữ cái (Abel, Bea, Clara, Derek, Eliza...) và nghề nghiệp (Guard, Detective, Cook, Clerk, Farmer, Pilot, Doctor, Judge...).
2. **Tạo Kho Manh mối Ẩn (Candidate Clue Pool)**: Với mỗi ô, sinh ra một tập hợp các manh mối **đúng với $S^*$** (kiểm chứng bằng `Direct Semantic Evaluator`). Ưu tiên các manh mối liên kết chéo giữa các vùng (ví dụ: đếm số tội phạm láng giềng của một nhân vật cụ thể, hoặc so sánh hàng và cột).
3. **Mô phỏng Chuỗi Mở Thẻ (Iterative Wave Construction)**:
   - Chọn 1 hoặc 2 ô mở sẵn ban đầu ($R_0$).
   - Tại bước $t$, chạy `DeductiveLogicAgent` trên các ô đã mở $R_t$.
   - Nếu Agent tìm được ít nhất 1 ô bắt buộc (Forced cell): Tiếp tục mở ô đó và nạp clue của nó.
   - Nếu Agent bị kẹt (`UNKNOWN` cho mọi ô chưa mở) khi chưa giải xong bàn cờ: Chọn một ô đã mở nhưng chưa có clue mạnh, thay thế/cập nhật clue của ô đó từ `Candidate Clue Pool` sao cho khi thêm vào $KB_t$, nó kết hợp với các clue đang mở để ép (entail) được ít nhất 1 ô mới (ưu tiên clue chỉ giúp mở được 1–2 ô tiếp theo thay vì mở toạc cả bàn cờ).
4. **Hậu kiểm Độc nhất & Không đoán (Verification Gate)**:
   - Reset màn chơi về trạng thái ban đầu, chạy `DeductiveLogicAgent.auto_solve()` từ đầu đến cuối.
   - Màn chơi chỉ được chấp nhận lưu vào file nếu:
     - Giải thành công 100% số ô mà không gặp bất kỳ bước `UNKNOWN` hay `INCONSISTENT` nào.
     - Hàm `uniqueness_check()` xác nhận nghiệm là duy nhất.
5. **Sinh câu thoại tự nhiên (Natural Language Renderer)**:
   - Mỗi clue lưu kèm cấu trúc JSON tường minh (`type`, `params`, `referenced_cells`) VÀ chuỗi văn bản hiển thị tự nhiên giống hệt game gốc (ví dụ: *"Exactly 2 of the 4 Innocents neighboring Mara are in column B"*).