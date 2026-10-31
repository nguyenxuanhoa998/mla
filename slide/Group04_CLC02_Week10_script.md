# Kịch bản thuyết trình – Nhóm 04, CLC02 – Tuần 10

Slide: `Group04_CLC02_Week10.pptx` (12 slide, cùng định dạng slide giữa kỳ). Thời lượng dự kiến khoảng 10–11 phút, mỗi slide 45–60 giây. Slide viết bằng tiếng Anh như bản giữa kỳ; kịch bản này viết bằng tiếng Việt, giữ nguyên thuật ngữ tiếng Anh (QWK, M0–M3, leave-one-prompt-out…).

Mọi con số lấy từ `AFP_Project/results/*.csv` và khớp với `AFP_Project/report/Group04_Week10_Report.docx`. Nếu chạy lại mô hình, chạy lại `python build_slides.py` để slide tự cập nhật.

---

## Slide 1 – Tiêu đề (10 giây)

"Em chào thầy. Nhóm 04 báo cáo tiến độ tuần 10 về câu hỏi: cấu trúc lập luận có giúp máy chấm điểm bài luận không, trên PERSUADE 2.0. Nhóm tập trung vào RQ1 và RQ2 theo đề nghị của thầy."

## Slide 2 – 1. Scope and what we answered (50 giây)

- Nhắc lại phạm vi sau góp ý: **lõi là Step 3 (chấm điểm cả bài), RQ1 và RQ2**. Step 2 chỉ là kết quả phụ, RQ3 (công bằng) để sau.
- Thiết kế đã khóa: 8 đề independent, leave-one-prompt-out, Gradient Boosting, 3 seed.
- Số liệu: **7.869 bài**, **77.639 đoạn có nhãn hiệu quả**, lớp Ineffective chỉ **1,9%**.
- Nói trước kết luận để thầy theo dõi: "cấu trúc gold giúp nhỏ, khoảng +0,02 QWK; vai trò dự đoán chưa thêm gì ngoài ranh giới đoạn".

Chuyển: "Trước khi vào kết quả, nhóm trả lời câu hỏi của thầy Duy về dữ liệu."

## Slide 3 – 2. Data workflow (60 giây)

- File gốc: mỗi dòng là một đoạn, toàn văn bài lặp lại trên mọi dòng (khoảng 600 MB).
- Tách hai bảng: bảng bài (bỏ trùng, 15.594 bài, mỗi bài một điểm) và bảng đoạn (173.266 đoạn).
- Lọc task = Independent còn 7.869 bài, 8 đề, vì bảy đề source-based có điểm phụ thuộc tài liệu nguồn.
- 43 đặc trưng ngôn ngữ tính bằng biểu thức chính quy, thêm 28 đặc trưng cấu trúc từ vai trò.
- Bảng bên phải: lý do từng lựa chọn. Nhấn mạnh: **vai trò chỉ vào M2, M3 để ba mô hình chỉ khác nhau ở một khối**.
- Số cần nhớ: Ineffective là 1,9% ở 8 đề này (4,5% trên cả 15 đề).

## Slide 4 – 3. One essay, step by step (60 giây)

- Bài F3CB6601CF24, đề Seeking multiple opinions, điểm thật 5, 741 từ.
- Chuỗi vai trò gold: Lead, Position, Claim, Evidence lặp ba lần, Concluding. `evidence_per_claim = 3/3 = 1,0`.
- Độ dài: 741 từ và 3.928 ký tự so với trung bình 464 và 2.591. Điểm tăng theo độ dài: từ 272 từ (điểm 1) đến 854 từ (điểm 6). Đây là ví dụ cho `n_chars` mà thầy Duy hỏi.
- Dự đoán: M0a 5,07; M1 4,62; M2 4,33; M3 4,10.
- **Nói thẳng**: đây là ca mà cấu trúc kéo điểm lệch khỏi điểm thật. Một ca chỉ minh họa cơ chế, không phải bằng chứng.

## Slide 5 – 4. Models and formulas (50 giây)

- Công thức: QWK (phạt nặng khi lệch xa, hợp với thang thứ tự), macro-F1 (vì lớp Ineffective hiếm), `evidence_per_claim`, Flesch, trọng số lớp.
- Bảng mô hình: M0a, M0b (đối chứng độ dài), M1, **M1 + B (chỉ ranh giới đoạn)**, M2 (oracle), M3 (thực tế hơn).
- Lý do chỉ dùng các công thức này: mỗi công thức đếm được một hiện tượng nêu tên được; lựa chọn khác (MTLD, parser quan hệ diễn ngôn) cần công cụ ngoài, nhóm chưa dùng.

## Slide 6 – 5. Length explains most of M1 (60 giây)

- M1 hơn M0a là 0,090, trong đó **0,077 (86%) đã nằm trong nhóm đặc trưng độ dài**. Phần ngôn ngữ thêm chỉ +0,013.
- RQ1: M2 − M1 = **+0,023**, dương ở 8/8 đề.
- RQ2: M3 − M1 = +0,012 (7/8 đề, p = 0,07).
- Điểm mấu chốt: **chỉ riêng ranh giới đoạn (M1 + B) đã cho +0,012, bằng M3**. Nghĩa là phần lớn "cấu trúc" mô hình học được là cách chia đoạn.
- Hình: thanh đen là M2.

## Slide 7 – 6. Structure inside length groups (60 giây)

- Chia 7.869 bài thành 5 nhóm bằng nhau theo số từ (khoảng 1.570 bài mỗi nhóm).
- Cấu trúc gold dương ở cả 5 nhóm, từ +0,026 đến +0,085.
- Ở các nhóm ngắn hơn, ranh giới gần như giải thích hết.
- **Ở nhóm dài nhất, nhãn vai trò thêm +0,063 so với chỉ ranh giới (CI 95% từ 0,036 đến 0,086)**: ở bài dài, biết đoạn nào là gì có ích thật.
- Nói rõ hạn chế: kiểm soát độ dài chỉ một phần, trong nhóm điểm vẫn thay đổi.

## Slide 8 – 7. How good must the role tagger be? (60 giây)

- Thí nghiệm thầy đề nghị: làm hỏng 10, 20, 40, 60, 80% nhãn vai trò, giữ ranh giới, chạy lại M2 trên cùng fold, 3 lần làm hỏng mỗi mức.
- Kết quả: M2 giảm từ 0,775 xuống 0,766 (10%), 0,763 (20%), rồi phẳng khoảng 0,760. **Từ 20%, M2 không còn hơn M1 + ranh giới (0,764).**
- Bộ nhận vai trò của nhóm (macro-F1 0,675) nằm trong vùng đó. Trả lời RQ2: với bộ nhận vai trò hiện tại, vai trò dự đoán chưa giúp ngoài việc đếm đoạn.
- Hạn chế (đã ghi trong slide): lỗi ngẫu nhiên đồng đều không giống lỗi thật (Claim bị nhầm với Evidence); một seed GB cho mỗi lần.

## Slide 9 – 8. Step 2: segment effectiveness (60 giây)

- Baseline: macro-F1 0,433, F1 lớp Ineffective 0,07 (thầy nói quá thấp).
- Cải tiến: thêm vai trò, độ dài, vị trí, ngữ cảnh bài, tín hiệu văn bản, chỉnh trọng số lớp trên các đề huấn luyện: **0,510 gộp, nhưng 0,477 theo đề**, F1 Ineffective 0,126.
- **Nói thẳng**: vượt 0,5 chỉ ở số gộp, và mức tăng chủ yếu do đổi ngưỡng quyết định. Embedding và độ tương đồng ngữ cảnh không thêm gì (0,473 so với 0,477).
- Đo bằng xếp hạng: gắn cờ 5% đoạn đáng ngờ nhất thì 9,3% cờ đúng (gấp 4,7 lần đoán bừa), bắt được 23% đoạn Ineffective. Precision khoảng 0,10: chín cờ trong mười là sai. Vì vậy chưa dùng làm cờ cho giáo viên.

## Slide 10 – 9. Related work, 2024–2026 (60 giây)

- Yang et al. (2024): mô hình đặc trưng + cây khái quát tốt, cơ sở cho thiết kế của nhóm.
- Wang et al. (2026), ArguLens: gold discourse +0,055 QWK, bài tự nói là chẩn đoán oracle. Nhóm dùng sự phân biệt này: M2 là oracle, M3 trung gian.
- Gui (2026): tín hiệu hiệu quả đoạn phần lớn theo độ dài và mức triển khai, khớp với kết quả Step 2.
- Ormerod (2025), Keramati & Warschauer (2026): hướng dùng mô hình encoder và LLM tinh chỉnh, nhóm chưa làm vì cần GPU.
- Chen, Wu & Zhang (2026): nhóm đã đọc toàn văn. Hai độ đo conditional disparity ratio và difference so sánh các nhóm ở cùng mức năng lực thật, trên tập kiểm tra tách riêng. Bài không xét ELL. Nhóm dùng cho RQ3 sau khi RQ1 và RQ2 xong.
- **Không đặt QWK của nhóm (0,753–0,776) cạnh 0,813 của ArguLens**: khác dữ liệu, đặc trưng, cách chia.

## Slide 11 – 10. Working with Group 6 (50 giây)

- Nhóm 6 làm Step 2 bằng DeBERTa, chia ngẫu nhiên 80/20 trên 15 đề (macro-F1 0,577). Nhóm 4 làm Step 3, chia theo đề trên 8 đề.
- Trả lời câu "lấy kết quả hay copy quy trình": **copy quy trình, không lấy số**, vì khác cách chia.
- File dự đoán validation của họ sẽ làm rò rỉ đề (mô hình họ đã thấy đề nhóm mình giữ lại).
- Đề xuất trao đổi: nhóm gửi danh sách 8 đề, vai trò dự đoán, đặc trưng cấp bài; họ gửi xác suất leave-one-prompt-out bằng RF/LR trên 8 đề và chạy DeBERTa 1–2 fold. Nhóm chưa có GPU.
- Nói rõ: biên bản mới là dự thảo, Nhóm 6 chưa xác nhận.

## Slide 12 – 11. Limits and next steps (50 giây)

- Giới hạn: chỉ 8 đề; ranh giới đoạn là gold; thí nghiệm làm hỏng nhãn còn đơn giản; Step 2 tăng chủ yếu do ngưỡng; sáu ca chưa đối chiếu rubric.
- Việc tiếp theo: đọc lại sáu ca với rubric và thêm bài có đủ Claim, Evidence nhưng ít đoạn; thay ranh giới gold bằng ranh giới dự đoán; xác nhận κ = 0,75 là loại nào; nhờ Nhóm 6 chạy DeBERTa 1–2 fold; sau đó RQ3.
- Kết: "Điều nhóm khẳng định được: trên 8 đề, cấu trúc gold thêm khoảng +0,02 QWK; vai trò dự đoán chưa thêm gì ngoài ranh giới. Em xin hết, mời thầy nhận xét."

---

## Câu hỏi thầy có thể hỏi và cách trả lời

**1. Nếu một bài có đủ Claim và Evidence nhưng viết trong ít đoạn, mô hình chấm thế nào?**
Nhiều khả năng thấp. Dòng chỉ ranh giới cho thấy mô hình học quy tắc "nhiều đoạn là tốt, ít đoạn là yếu"; hai ca AA798BC0E56D và E5C524E8ECB8 có dấu hiệu này. Nhóm chưa tạo bài tổng hợp để kiểm trực tiếp và chưa đối chiếu rubric, nên đây là giả thuyết.

**2. Ở mức hỏng nhãn nào M2 không còn hơn M1 + ranh giới?**
Từ khoảng 20% (QWK 0,763 so với 0,764). Nhóm chưa ghi dự đoán trước khi chạy.

**3. Thêm riêng n_chars vào M0 đã tăng mạnh, M1 − M0 còn là lợi ích ngôn ngữ không?**
Không. 86% của M1 − M0a nằm trong nhóm độ dài; phần ngôn ngữ còn lại là +0,013.

**4. Vì sao F1 của Step 2 vẫn thấp?**
Ineffective chỉ 1,9% đoạn, nhãn nhiễu (người chấm đồng thuận κ = 0,32), và tín hiệu văn bản bổ sung (embedding) không giúp. Nhóm 6 với DeBERTa cũng chỉ đạt F1 0,374 cho lớp này trên cách chia khác.

**5. Máy chấm ngang người chấm rồi sao?**
QWK trung bình theo đề của M2 là 0,776, gần mức đồng thuận người chấm (κ = 0,75), nhưng nhóm chưa xác nhận hai chỉ số cùng cách tính, và phần lớn điểm đến từ độ dài. Nhóm không kết luận máy ngang người.

**6. M3 biết ranh giới gold thì biết gì mà công cụ nhận bài thô chưa có?**
Số đoạn, vị trí và độ dài từng đoạn, và đoạn nào không thuộc lập luận. Chỉ riêng chúng đã cho +0,012, bằng M3.

**7. Vì sao M2 không phải trần của mọi mô hình?**
M2 là một scorer cụ thể (Gradient Boosting với đặc trưng tay). Scorer hoặc đặc trưng khác có thể cho thứ hạng khác; M2 − M3 = 0,011 là chênh của một cấu hình.

**8. Vì sao không thử transformer?**
Máy nhóm chỉ có CPU; tinh chỉnh transformer cho 8 fold mất nhiều ngày. Nhóm đề nghị Nhóm 6 chạy 1–2 fold DeBERTa.

**9. Bài Chen, Wu & Zhang nói gì, và liên quan gì đến nhóm?**
Nhóm đã đọc toàn văn (Assessing Writing 69, 101066). Bài đề xuất hai độ đo cho điểm thứ bậc: conditional disparity ratio và difference, tính riêng cho từng mức năng lực thật, trên tập kiểm tra tách khỏi tập huấn luyện. Họ thử trên 2.167 bài của một đề (Facial Action Coding System) theo giới tính và chủng tộc, không xét ELL. Phát hiện chính: không điều kiện hóa thì khác biệt giữa nhóm gần như bằng không, điều kiện hóa thì thấy thiên lệch ngược chiều ở từng mức năng lực. Họ cũng nhấn mạnh đây chỉ là thiên lệch tiềm năng, và độ đo chỉ có nghĩa khi mô hình đủ chính xác. Với nhóm: làm RQ3 sau, thay phép so sánh sai số trung bình ở cùng điểm thật bằng hai độ đo này.

---

## Lưu ý khi trình bày

- Luôn nói **"gold"** khi nói về M2 và **"ranh giới gold"** khi nói về M3; không gọi M3 là hệ thống nhận bài thô.
- Không nói "73% điểm do độ dài" (impurity importance không cho phép kết luận này). Có thể nói: xáo trộn nhóm độ dài làm QWK giảm 0,545, nhóm cấu trúc 0,088, và các nhóm này tương quan nhau.
- Không so QWK của nhóm với bài khác như cùng một benchmark.
- Khi nói Step 2 "vượt 0,5", luôn nói kèm "chỉ ở số gộp".
