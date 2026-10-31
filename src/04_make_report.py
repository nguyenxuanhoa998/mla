"""Build the weekly progress report (.docx) from results/ and figs/."""
import json
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from common import RES, FIGS, ROOT

s3 = pd.read_csv(RES / "step3_summary.csv")
pp = pd.read_csv(RES / "step3_per_prompt.csv")
fair = pd.read_csv(RES / "step3_fairness_ell.csv")
unc = pd.read_csv(RES / "step3_uncertainty.csv")
imp = pd.read_csv(RES / "step3_feature_importance.csv")
s12 = pd.read_csv(RES / "step12_summary.csv")
c1 = pd.read_csv(RES / "Step1_per_class.csv").set_index("class")
c2 = pd.read_csv(RES / "Step2_per_class.csv").set_index("class")
ex = json.load(open(RES / "step3_extra.json"))
r12 = pd.read_csv(RES / "rq12_summary.csv")
pair = pd.read_csv(RES / "rq12_paired.csv")
rq_extra = json.load(open(RES / "rq12_extra.json"))
r12imp = pd.read_csv(RES / "rq12_m2_importance.csv")


def f(x, d=3):
    return f"{x:.{d}f}".replace(".", ",")


doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, a, Cm(2))
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(12)
for h, sz in (("Heading 1", 14), ("Heading 2", 12)):
    doc.styles[h].font.name = "Times New Roman"
    doc.styles[h].font.size = Pt(sz)


def para(t, bold=False, italic=False, center=False):
    p = doc.add_paragraph()
    r = p.add_run(t)
    r.bold, r.italic = bold, italic
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def bullet(t):
    doc.add_paragraph(t, style="List Bullet")


def cap(t):
    para(t, italic=True)


def table(header, rows):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    for i, h in enumerate(header):
        t.rows[0].cells[i].paragraphs[0].add_run(h).bold = True
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = str(v)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(10)
    doc.add_paragraph()


def figure(path, w, caption):
    doc.add_picture(str(path), width=Cm(w))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap(caption)


para("BÁO CÁO TIẾN ĐỘ TUẦN 8 (SAU NHẬN XÉT GIỮA KỲ): BASELINE VÀ RQ1, RQ2", bold=True, center=True)
para("Đề tài: Argument-Structure-Based Feedback Prioritisation for English Argumentative Essays", center=True)
para("Nhóm 04, lớp CLC02. Giảng viên: Bùi Quốc Khánh. Ngày 11/10/2026.", center=True)

table(["Mục", "Nội dung"], [
    ["Thành viên", "Nguyễn Xuân Hòa (2301140035); Hoàng Tùng (2301140099); Nguyễn Duy Anh (2301140006)"],
    ["Dữ liệu", "PERSUADE 2.0 (Crossley et al., 2024), tập train chính thức 15.594 bài. Tập test chưa được dùng."],
    ["Mã nguồn", "Thư mục AFP_Project (src, results, figs, report); chạy lại bằng bốn script đánh số 01 đến 04."],
    ["Trạng thái", "Đã chạy M0, M1 (chia theo đề) như thầy yêu cầu và thêm M2, M3 để có kết quả đầu tiên cho RQ1, RQ2. Chưa có ghi chú trao đổi với Nhóm 6; chưa thử transformer."],
])

doc.add_heading("1. Nhận xét của thầy và cách nhóm xử lý", 1)
para("Thầy đánh giá cao thiết kế thí nghiệm nhưng lo về khối lượng: ba bước pipeline cộng ba câu hỏi nghiên cứu là nhiều cho sáu tuần. Thầy đề nghị lấy RQ1 và RQ2 ở Step 3 làm lõi, làm RQ3 (công bằng) khi hai câu đầu đã xong. Bảng 1 ghi từng góp ý, việc đã làm và việc còn thiếu.")
cap("Bảng 1. Tình trạng xử lý từng góp ý")
table(["#", "Góp ý", "Nhóm đã làm", "Tình trạng"], [
    ["1", "Lấy RQ1, RQ2 ở Step 3 làm lõi; RQ3 để sau", "Đưa M2 (cấu trúc gold) và M3 (cấu trúc dự đoán) vào chạy thử; mục 4 là phần lõi. Kết quả ELL chỉ giữ ở mức quan sát phụ (mục 6.2), không phát triển thêm.", "Đã có kết quả đầu tiên"],
    ["2", "Mang kết quả M0 và M1 với chia theo đề", "Leave-one-prompt-out trên 8 đề independent (mục 3).", "Đã xong"],
    ["3", "Bước 1, 2: transformer (DeBERTa, BERT) cho cấu trúc dự đoán tốt hơn, ảnh hưởng RQ2", "Mới có baseline tuyến tính (mục 5). Chưa tinh chỉnh transformer. Mục 4 cho thấy chênh lệch M2 − M3 hiện chỉ 0,010 QWK, nên mức lợi tối đa của một bộ nhận vai trò tốt hơn cũng nằm trong khoảng này.", "Chưa làm, đã lên kế hoạch"],
    ["4", "Gặp Nhóm 6, tránh trùng câu hỏi, có thể dùng chung tiền xử lý; mang ghi chú buổi sau", "Chưa có ghi chú. File báo cáo tuần 8 của Nhóm 6 mà nhóm đang giữ dùng bộ dữ liệu sinh viên VNU, không phải PERSUADE, nên cần hỏi lại Nhóm 6 xem họ còn dùng PERSUADE không.", "Chưa làm"],
    ["5", "Kiểm lại tên và nơi đăng của hai bài 2026 (ArguLens; Chen, Wu & Zhang)", "Tìm trên web: ArguLens có trên arXiv (2608.17356) với tên đầy đủ khác slide, chưa xác nhận được tên tác giả. Chưa tìm thấy bài Chen, Wu & Zhang. Xem mục 8.", "Làm một phần"],
])
para("Mọi số liệu dưới đây đến từ một lượt chạy trên tập train, một seed, tham số gần như mặc định. Nhóm dùng chúng làm kết quả sơ bộ, chưa xem là kết luận.")


doc.add_heading("2. Dữ liệu và cách chia", 1)
para("Step 3 chỉ dùng 8 đề independent (7.869 bài). Bảy đề dựa trên tài liệu nguồn (7.725 bài) bị loại vì điểm của chúng phụ thuộc việc dùng đúng nội dung tài liệu. Cách loại này cho 7.869 bài, không trùng con số 10.669 ghi ở slide giữa kỳ. Nhóm chưa xác định được năm đề nào cho ra 10.669, nên tạm loại theo trường task của dữ liệu và sẽ thống nhất lại trước khi chạy tập test.")
para("Mỗi lượt giữ lại một đề làm tập kiểm tra và huấn luyện trên 7 đề còn lại, nên không có bài hay đề nào dùng chung giữa hai phía. Điểm gộp ghép dự đoán của cả 8 lượt.")
para("Nhãn đoạn trong 8 đề này lệch rõ: Adequate chiếm khoảng 77%, Ineffective chỉ 1.474 đoạn (khoảng 1,9% số đoạn có nhãn hiệu quả). Trên cả tập train, tỷ lệ Ineffective là 4,5%.")
figure(FIGS / "length_vs_score.png", 8, "Hình 1. Số từ và điểm tổng thể (8 đề independent). r = " + f(ex["r_len_score"], 2) + ", khớp với 0,76 ở slide.")

doc.add_heading("3. Step 3: M0 và M1 dự đoán điểm 1 đến 6", 1)
para("M0 chỉ nhận số từ. M1 nhận 45 đặc trưng: độ dài, cấu trúc câu và đoạn, độ đa dạng từ vựng, độ dễ đọc (Flesch, Flesch-Kincaid), dấu câu, các proxy lỗi bề mặt (chữ i viết thường, từ lặp, thiếu dấu kết thúc), ngôi nhân xưng và sáu nhóm từ nối. Các đặc trưng tự cài đặt bằng biểu thức chính quy nên chỉ gần với bộ của Yang et al. (2024), chưa tái hiện đầy đủ. Dự đoán liên tục được làm tròn về 1 đến 6 trước khi tính QWK và MAE.")
rows = [[r.model, f(r.pooled_QWK), f(r.pooled_MAE), f(r.adj_acc), f(r.mean_QWK_over_prompts) + " ± " + f(r.std_QWK), f(r.worst_QWK)] for r in s3.itertuples()]
cap("Bảng 2. Kết quả M0 và M1, leave-one-prompt-out, 7.869 bài (Adj. acc: tỷ lệ lệch không quá 1 điểm)")
table(["Mô hình", "QWK gộp", "MAE", "Adj. acc", "QWK TB theo đề ± độ lệch chuẩn", "QWK đề kém nhất"], rows)
m0lin, m0gb, m1rf, m1gb = (s3.iloc[i] for i in range(4))
para(f"M1 cao hơn M0 rõ ràng ở cùng thuật toán boosting: QWK gộp {f(m1gb.pooled_QWK)} so với {f(m0gb.pooled_QWK)}, MAE {f(m1gb.pooled_MAE)} so với {f(m0gb.pooled_MAE)}. Phần chênh là đóng góp thêm của đặc trưng ngôn ngữ ngoài số từ. M0 tuyến tính kém ổn định giữa các đề: QWK đề kém nhất chỉ {f(m0lin.worst_QWK)}, độ lệch chuẩn {f(m0lin.std_QWK)}. M0 dạng cây và M1 ổn định hơn (độ lệch chuẩn khoảng {f(m1gb.std_QWK)}).")
para(f"QWK trung bình theo đề của M1 là {f(m1gb.mean_QWK_over_prompts)}, gần mức đồng thuận của người chấm (weighted κ = 0,75). Hai chỉ số không cùng cách tính, nên nhóm không kết luận hệ thống đã ngang người chấm. Chênh lệch giữa Random Forest và Gradient Boosting ở M1 ({f(m1rf.pooled_QWK)} và {f(m1gb.pooled_QWK)}) quá nhỏ để rút ra điều gì.")
figure(FIGS / "qwk_per_prompt.png", 15, "Hình 2. QWK khi giữ lại từng đề làm tập kiểm tra.")
figure(FIGS / "feature_importance.png", 11, "Hình 3. Độ quan trọng đặc trưng của Random Forest M1 (huấn luyện trên cả 8 đề, chỉ để quan sát, không dùng để đánh giá).")
top = ", ".join(f"{row[1]} ({f(row[2])})" for row in imp.head(5).itertuples(name=None))
para("Năm đặc trưng quan trọng nhất: " + top + ". Số ký tự (một đại lượng độ dài) một mình chiếm " + f(imp.iloc[0, 1] * 100, 0) + "% độ quan trọng, nên M1 vẫn dựa chủ yếu vào độ dài và chưa thể nói nó chấm dựa trên chất lượng lập luận.")

doc.add_heading("4. Phần lõi: M2 và M3 cho RQ1 và RQ2", 1)
para("RQ1: cấu trúc lập luận giúp chấm bài trên đề chưa thấy được bao nhiêu. RQ2: mất bao nhiêu khi dùng cấu trúc do mô hình dự đoán thay cho cấu trúc thật. Ba mô hình dùng cùng thuật toán và cùng cách chia theo đề, chỉ khác đầu vào:")
bullet("M1: 45 đặc trưng ngôn ngữ (mục 3).")
bullet("M2: M1 cộng đặc trưng cấu trúc tính từ nhãn vai trò gold: số đoạn, tỷ lệ và số từ của từng vai trò (Lead, Position, Claim, Counterclaim, Rebuttal, Evidence, Concluding), có hay không Counterclaim, Rebuttal, số Evidence trên mỗi Claim, số vai trò khác nhau.")
bullet("M3: M1 cộng cùng đặc trưng cấu trúc nhưng tính từ vai trò do mô hình Step 1 dự đoán (LinearSVC trên TF-IDF băm kèm vị trí). Với đề giữ lại p, bộ nhận vai trò của bài huấn luyện không bao giờ thấy nhãn của p, và không thấy nhãn của chính đề chứa bài đó.")
r1 = rq_extra["step1_macroF1_heldout"]
para(f"Bộ nhận vai trò dùng cho M3 đạt Macro-F1 {f(r1)} trên đề giữ lại (cùng cỡ với baseline LR ở mục 5). Ranh giới đoạn vẫn lấy từ nhãn gold; chỉ nhãn vai trò được dự đoán.")
rows = [[r.algo, r.model, f(r.pooled_QWK), f(r.pooled_MAE), f(r.mean_QWK_prompts) + " ± " + f(r.std_QWK), f(r.worst_QWK)] for r in r12.itertuples()]
cap("Bảng 3. M1, M2, M3 theo leave-one-prompt-out (GB: Gradient Boosting; RF: Random Forest)")
table(["Thuật toán", "Mô hình", "QWK gộp", "MAE", "QWK TB theo đề ± độ lệch chuẩn", "QWK đề kém nhất"], rows)
rows = []
for r in pair.itertuples():
    rows.append([r.algo, r.comparison, "+" + f(r.dQWK) if r.dQWK >= 0 else f(r.dQWK), f"[{f(r.ci_lo)}; {f(r.ci_hi)}]", f"{r.prompts_higher}/8"])
cap("Bảng 4. Chênh lệch QWK gộp giữa các mô hình (bootstrap 1.000 lần theo bài, 95% CI; cột cuối: số đề mà vế đầu cao hơn)")
table(["Thuật toán", "So sánh", "ΔQWK", "95% CI", "Đề cao hơn"], rows)
g = pair[pair.algo == "GB"].set_index("comparison")
gm2, gm3, gl = g.iloc[0], g.iloc[1], g.iloc[2]
para(f"RQ1: với Gradient Boosting, thêm cấu trúc gold tăng QWK gộp {f(gm2.dQWK)} (từ {f(r12[(r12.algo=='GB')&(r12.model=='M1')].pooled_QWK.iloc[0])} lên {f(r12[(r12.algo=='GB')&(r12.model=='M2')].pooled_QWK.iloc[0])}) và MAE giảm từ {f(r12[(r12.algo=='GB')&(r12.model=='M1')].pooled_MAE.iloc[0])} xuống {f(r12[(r12.algo=='GB')&(r12.model=='M2')].pooled_MAE.iloc[0])}; M2 cao hơn M1 ở cả 8 đề. Với Random Forest, mức tăng chỉ {f(pair[(pair.algo=='RF')].iloc[0].dQWK)} và chỉ 6/8 đề. Cấu trúc lập luận giúp, nhưng mức giúp nhỏ so với phần M1 đã đạt.")
para(f"RQ2: dùng cấu trúc dự đoán, Gradient Boosting giữ lại khoảng {f(gm3.dQWK / gm2.dQWK * 100, 0)}% mức tăng (M3 − M1 = +{f(gm3.dQWK)}; M2 − M3 = +{f(gl.dQWK)}). Với Random Forest, M3 gần như không khác M1 (CI chứa 0). Vậy hơn một nửa mức lợi của cấu trúc gold biến mất khi cấu trúc là dự đoán, ít nhất với bộ nhận vai trò hiện tại.")
para("Cần đọc các con số này thận trọng:")
bullet("Mức tăng nhỏ (dưới 0,02 QWK) và CI ở Bảng 4 chỉ lấy mẫu lại các bài với dự đoán đã cố định, không tính biến động do huấn luyện lại hay do chọn đề; kết luận đáng tin hơn khi có nhiều seed.")
bullet(f"Số ký tự vẫn là đặc trưng quan trọng nhất của M2 ({f(r12imp.iloc[0,1]*100,0)}%); các đặc trưng cấu trúc đứng sau (words_evidence, rebuttal_per_counterclaim, n_distinct_roles nằm trong top 10).")
bullet("Chỉ dùng nhãn vai trò, chưa dùng nhãn hiệu quả của đoạn; ranh giới đoạn là gold nên M3 chưa phản ánh trường hợp phải tự tách đoạn.")
bullet("Sự giảm từ M2 sang M3 phụ thuộc vào chất lượng Step 1, nên đây là chỗ một mô hình mạnh hơn (DeBERTa/BERT) có thể thu hẹp khoảng cách, đúng như thầy gợi ý.")


doc.add_heading("5. Steps 1 và 2: vai trò và mức ưu tiên của đoạn", 1)
rows = []
for r in s12.itertuples():
    rec = r.recall_Rebuttal if r.task == "Step1" else r.recall_Ineffective
    rows.append([("Step 1 (8 lớp vai trò)" if r.task == "Step1" else "Step 2 (3 lớp hiệu quả)"), r.model,
                 f(r.macroF1_pooled), f(r.macroF1_mean_prompts) + " ± " + f(r.std), f(r.accuracy), f(rec)])
cap("Bảng 5. Baseline Steps 1 và 2, leave-one-prompt-out (cột cuối: recall của Rebuttal ở Step 1, của Ineffective ở Step 2)")
table(["Bước", "Mô hình", "Macro-F1 gộp", "Macro-F1 TB theo đề ± độ lệch chuẩn", "Accuracy", "Recall lớp hiếm"], rows)
S1 = s12[s12.task == "Step1"].set_index("model")
S2 = s12[s12.task == "Step2"].set_index("model")
para(f"Step 1: Macro-F1 tăng từ {f(S1.loc['majority'].macroF1_pooled)} (đoán lớp đa số) lên {f(S1.loc['LR TF-IDF + position'].macroF1_pooled)} với LR TF-IDF kèm vị trí. Lead và Concluding Statement gần như nhận ra hết (recall {f(c1.loc['Lead'].recall_LR_tfidf,2)} và {f(c1.loc['Concluding Statement'].recall_LR_tfidf,2)}) vì chúng nằm ở đầu và cuối bài. Hai lớp khó nhất là Rebuttal (recall {f(c1.loc['Rebuttal'].recall_LR_tfidf,2)}, F1 {f(c1.loc['Rebuttal'].f1_LR_tfidf,2)}) và Counterclaim (recall {f(c1.loc['Counterclaim'].recall_LR_tfidf,2)}, F1 {f(c1.loc['Counterclaim'].f1_LR_tfidf,2)}), đúng như nhóm dự đoán vì hai lớp này hiếm và phụ thuộc ngữ cảnh.")
para(f"Step 2 yếu: Macro-F1 tốt nhất chỉ {f(S2.loc['LR TF-IDF + position'].macroF1_pooled)}. LR TF-IDF bắt được {f(S2.loc['LR TF-IDF + position'].recall_Ineffective,2)} số đoạn Ineffective với F1 của lớp này là {f(c2.loc['Ineffective'].f1_LR_tfidf,2)}, tức gắn nhãn Ineffective cho rất nhiều đoạn không phải. LR chỉ dùng vị trí và độ dài có recall Ineffective {f(S2.loc['LR position+length'].recall_Ineffective,2)} nhưng accuracy chỉ {f(S2.loc['LR position+length'].accuracy,2)}. Kết quả phù hợp với việc nhãn hiệu quả có độ đồng thuận thấp (κ = 0,32). Ở dạng hiện tại, cờ Ineffective chưa đủ tin cậy để đưa cho giáo viên; đây là bước cần cải thiện nhiều nhất.")

doc.add_heading("6. Kiểm tra rủi ro ở Step 3", 1)
doc.add_heading("6.1. Lối tắt độ dài", 2)
sh = ex["shortcut"]
para(f"Nhóm lấy ngẫu nhiên 300 bài, nối bài với chính nó rồi cho dự đoán lại (không thêm ý mới nào). Điểm dự đoán tăng trung bình {f(sh['M0_LR_mean_shift_after_duplication'],2)} điểm ở M0 tuyến tính và {f(sh['M1_RF_mean_shift_after_duplication'],2)} điểm ở Random Forest M1. M1 ít nhạy hơn nhưng vẫn tăng, nên nhân bản văn bản vẫn đánh lừa được cả hai mô hình. Hướng xử lý nhóm dự định thử: thêm đặc trưng phát hiện câu lặp. Nhóm chưa thử.")
doc.add_heading("6.2. Chênh lệch theo ELL (RQ3, quan sát phụ)", 2)
rows = [[int(r[1]), f(r[2]), f(r[3]), f(r[4])] for r in fair.itertuples(name=None)]
cap("Bảng 6. Sai số trung bình (dự đoán − điểm thật) của Random Forest M1 theo nhóm ELL, ở cùng điểm thật")
table(["Điểm thật", "Non-ELL", "ELL", "Chênh (ELL − non-ELL)"], rows)
para(f"Điểm trung bình của bài ELL thấp hơn (3,12 so với 3,80 ở 8 đề này). Ở cùng điểm thật, mô hình chấm bài ELL cao hơn bài non-ELL khoảng 0,16 đến 0,18 điểm ở mức 1 đến 3, và thấp hơn 0,81 điểm ở mức 6 (rất ít bài ELL đạt 6 nên con số này chưa ổn định). MAED trung bình trên sáu mức điểm là {f(ex['maed'],3)}. Nhóm ELL chỉ có khoảng 1.300 bài trong cả tập và chưa có khoảng tin cậy, nên nhóm chưa kết luận về thiên lệch. Theo góp ý của thầy, phần này chỉ dừng ở quan sát cho tới khi RQ1 và RQ2 xong.")
doc.add_heading("6.3. Độ bất định", 2)
rows = [[r[1], f(r[2])] for r in unc.itertuples(name=None)]
cap("Bảng 7. Sai số tuyệt đối trung bình theo tứ phân vị độ lệch chuẩn giữa các cây (Random Forest M1)")
table(["Tứ phân vị độ bất định", "MAE"], rows)
para(f"Nhóm bài có độ bất định cao nhất có MAE {f(unc.iloc[3,1],2)}, gần gấp đôi nhóm thấp nhất ({f(unc.iloc[0,1],2)}). Độ lệch giữa các cây vì vậy có thể dùng để chọn bài công cụ nên báo là chưa chắc (Quyết định 3 của giáo viên). Nhóm chưa chọn ngưỡng cụ thể.")

doc.add_heading("7. Hạn chế của kết quả tuần này", 1)
bullet("Một seed, tham số gần như mặc định; khoảng tin cậy chỉ mới lấy mẫu lại bài, chưa tính biến động do huấn luyện lại.")
bullet("Mức tăng của cấu trúc lập luận nhỏ (dưới 0,02 QWK) và vẫn bị lấn át bởi đặc trưng độ dài.")
bullet("Số bài sau khi lọc (7.869) khác con số trong slide (10.669); cần thống nhất tiêu chí trước khi chạy tập test.")
bullet("Đặc trưng M1 tự cài đặt, chưa dùng spaCy hay công cụ kiểm tra chính tả, nên chưa phải bản tái hiện đầy đủ của Yang et al.")
bullet("Step 1 mới dùng mô hình tuyến tính; Step 2 yếu và chưa được cải thiện vì không nằm trong phần lõi.")
bullet("M3 dùng ranh giới đoạn gold, chỉ dự đoán nhãn vai trò.")

doc.add_heading("8. Kiểm tra tài liệu tham khảo năm 2026", 1)
para("Thầy yêu cầu kiểm lại tên và nơi đăng của hai bài năm 2026 trước khi viết related work. Nhóm tìm trên web và ghi lại kết quả:")
bullet("ArguLens: tìm thấy trên arXiv (số 2608.17356) với tên \"ArguLens: An Open-Source System for Automated Essay Scoring and Label-Aware Feedback Generation\". Slide ghi \"Wang et al. (2026), ArguLens, arXiv\" nên phần tên tác giả chưa xác nhận được, cần mở trang arXiv để đối chiếu danh sách tác giả trước khi trích.")
bullet("Chen, Wu & Zhang (2026), Assessing Fairness in AI-Assisted Writing Scoring, Assessing Writing: tìm bằng tên bài, tên tác giả và tên tạp chí đều chưa thấy bài khớp. Cần kiểm trên ScienceDirect hoặc Google Scholar; nếu không xác nhận được thì nên bỏ khỏi related work hoặc thay bằng nguồn kiểm chứng được.")
bullet("Yang et al. (2024), Unveiling the Tapestry of Automated Essay Scoring: có trên arXiv (2401.05655).")

doc.add_heading("9. Kế hoạch tuần 9", 1)
rows = [
    ["Hỏi lại Nhóm 6 xem còn dùng PERSUADE không; thống nhất tiền xử lý và phân chia câu hỏi; ghi biên bản", "Ghi chú trao đổi với Nhóm 6 (thầy yêu cầu mang tới buổi sau)"],
    ["Tinh chỉnh một transformer (DeBERTa hoặc BERT) cho Step 1 và dùng nó cho M3; so với bộ nhận vai trò tuyến tính", "M3 mới và chênh lệch M2 − M3 cập nhật cho RQ2"],
    ["Chạy lại M1, M2, M3 với nhiều seed, bootstrap theo cả bài lẫn đề", "Bảng 3 và 4 có CI đáng tin hơn"],
    ["Xác nhận tên tác giả ArguLens; xác nhận hoặc bỏ bài Chen, Wu & Zhang", "Danh sách tài liệu tham khảo đã kiểm"],
    ["Thống nhất tiêu chí lọc đề (7.869 hay 10.669 bài)", "Quyết định cố định trước khi chạy test"],
]
cap("Bảng 8. Công việc và sản phẩm của tuần 9")
table(["Công việc", "Sản phẩm"], rows)
para("RQ3 (công bằng theo ELL) chỉ làm tiếp khi RQ1 và RQ2 đã xong, theo đề nghị của thầy. Tập test chính thức vẫn giữ nguyên, chỉ dùng một lần ở cuối.")

out = ROOT / "report" / "Group04_Week8_Report_v2.docx"
doc.save(out)
print("saved", out)
