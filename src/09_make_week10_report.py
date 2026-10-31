"""Build the Week-9 report (.docx) in the same format as the earlier reports (04_make_report.py style)."""
import numpy as np, pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from common import RES, FIGS, ROOT, PROC

f = lambda x, d=3: f"{x:.{d}f}".replace(".", ",")
sg = lambda x, d=3: ("+" if x >= 0 else "−") + f(abs(x), d)

# ------------------------------------------------------------------ data pulled from results / processed tables
main = pd.read_csv(RES / "nb_main_gb.csv", index_col=0)
mrf = pd.read_csv(RES / "nb_main_rf.csv", index_col=0)
dgb = pd.read_csv(RES / "nb_delta_gb.csv", index_col=0)
drf = pd.read_csv(RES / "nb_delta_rf.csv", index_col=0)
dup = pd.read_csv(RES / "nb_duplication_oos.csv", index_col=0)
perm = pd.read_csv(RES / "nb_perm_importance_group.csv", index_col=0)
byq = pd.read_csv(RES / "w10_delta_by_length.csv")
curv = pd.read_csv(RES / "w10_corruption_summary.csv", index_col=0)
s2 = pd.read_csv(RES / "step2_improved_summary.csv")
s2pp = pd.read_csv(RES / "step2_improved_per_prompt.csv", index_col=0)
emb = pd.read_csv(RES / "step2_embed_summary.csv")
z = np.load(RES / "nb_predictions.npz", allow_pickle=True)
ess = pd.read_pickle(PROC / "essays.pkl"); ind = ess[ess.task == "Independent"].reset_index(drop=True)
X1 = pd.read_pickle(PROC / "features_independent.pkl")
seg_all = pd.read_pickle(PROC / "segments.pkl")
seg_ind = seg_all[seg_all.task == "Independent"]
n_ann = int(((seg_ind.discourse_type != "Unannotated") & seg_ind.discourse_effectiveness.notna()).sum())

# ------------------------------------------------------------------ document scaffolding (same style as 04_make_report.py)
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, a, Cm(2))
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
for h, sz in (("Heading 1", 14), ("Heading 2", 12)):
    doc.styles[h].font.name = "Times New Roman"; doc.styles[h].font.size = Pt(sz)


def para(t, bold=False, italic=False, center=False):
    p = doc.add_paragraph(); r = p.add_run(t); r.bold, r.italic = bold, italic
    if center: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def lead(bold_part, rest):
    p = doc.add_paragraph(); p.add_run(bold_part).bold = True; p.add_run(rest); return p


def bullet(t): doc.add_paragraph(t, style="List Bullet")
def cap(t): para(t, italic=True)


def table(header, rows, size=10):
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
    for i, h in enumerate(header): t.rows[0].cells[i].paragraphs[0].add_run(h).bold = True
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r): cells[i].text = str(v)
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for run in p.runs: run.font.size = Pt(size)
    doc.add_paragraph()


def figure(path, w, caption):
    doc.add_picture(str(path), width=Cm(w)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER; cap(caption)


# ------------------------------------------------------------------ title block
para("BÁO CÁO TUẦN 10 – SAU NHẬN XÉT TUẦN 9 VÀ BUỔI TRAO ĐỔI", bold=True, center=True)
para("Cấu trúc lập luận có giúp chấm điểm bài luận? RQ1/RQ2 trên PERSUADE 2.0 và hướng nâng Step 2", bold=True, center=True)
para("Nhóm 04, lớp CLC02. Giảng viên: Bùi Quốc Khánh. Ngày 26/10/2026.", center=True)
table(["Mục", "Nội dung"], [
    ["Thành viên", "Nguyễn Xuân Hòa (2301140035); Hoàng Tùng (2301140099); Nguyễn Duy Anh (2301140006)"],
    ["Dữ liệu", "PERSUADE 2.0, tập train 15.594 bài; Step 3 dùng 8 đề independent (7.869 bài); Step 2 dùng " + f"{n_ann:,}".replace(",", ".") + " đoạn có nhãn hiệu quả của 8 đề này. Tập test chính thức chưa được dùng."],
    ["Mã nguồn", "Notebook AFP_Group04_Week8.ipynb (RQ1/RQ2), AFP_Group04_Week10_Step2.ipynb (nâng Step 2 bằng thước xếp hạng, embedding, ngữ cảnh; kết quả results/step2_embed_summary.csv; các block này cũng nằm cuối AFP_Group04_Week8_local_executed.ipynb), src/06 đến src/09. Kết quả trong results/."],
    ["Trạng thái", "Đã làm: bảng Δ theo năm nhóm độ dài, đường cong làm hỏng nhãn vai trò, Step 2 cải tiến, giải thích quy trình dữ liệu, ví dụ từng bước, công thức, định vị tài liệu 2024 đến 2026, dự thảo biên bản Nhóm 6. Đã chạy thêm thước xếp hạng, embedding và độ tương đồng ngữ cảnh cho Step 2. Chưa làm: đối chiếu lại sáu ca với rubric, transformer."],
])

# ------------------------------------------------------------------ 1. summary
doc.add_heading("1. Tóm tắt kết quả", 1)
m1, m2, m3, mb = (main.loc[k] for k in ["M1", "M2 (gold)", "M3 (pred)", "M1 +B(boundary only)"])
bullet(f"Chấm điểm cả bài (Step 3, Gradient Boosting, 3 seed, leave-one-prompt-out, 8 đề): mean QWK theo đề của M1 là {f(m1['mean QWK / đề'])}, M2 (cấu trúc gold) {f(m2['mean QWK / đề'])}, M3 (vai trò dự đoán) {f(m3['mean QWK / đề'])}. Số liệu này không đổi so với bản trước.")
bullet(f"Mới: cấu trúc gold giúp ở cả năm nhóm độ dài, từ {sg(byq[(byq.comparison=='M2 - M1')].dQWK.min())} đến {sg(byq[(byq.comparison=='M2 - M1')].dQWK.max())} QWK. Riêng nhóm bài dài nhất, M2 còn hơn M1 + ranh giới {sg(byq[(byq.comparison=='M2 - M1+boundary')].dQWK.iloc[-1])} (95% CI [{f(byq[(byq.comparison=='M2 - M1+boundary')].ci_lo.iloc[-1])}; {f(byq[(byq.comparison=='M2 - M1+boundary')].ci_hi.iloc[-1])}]), tức ở bài dài nhãn vai trò thêm thông tin ngoài việc đếm đoạn. Ở bốn nhóm còn lại khoảng tin cậy của hiệu này chứa 0.")
bullet(f"Mới: làm hỏng có kiểm soát nhãn vai trò (giữ ranh giới). QWK của M2 giảm từ {f(curv.loc[0.0,'meanQWK'])} (0%) xuống {f(curv.loc[0.1,'meanQWK'])} (10%), {f(curv.loc[0.2,'meanQWK'])} (20%) rồi phẳng quanh {f(curv.loc[0.4,'meanQWK'])} (40% trở lên). Từ khoảng 20% hỏng, M2 không còn hơn M1 + ranh giới ({f(mb['mean QWK / đề'])}). Bộ nhận vai trò hiện tại (macro-F1 0,675) nằm trong vùng này.")
w = s2[s2.weights == "tuned on inner OOF"].set_index("model")
ET = emb[emb.weights == "tuned"].set_index("model"); e3, e5, e6 = ET.iloc[0], ET.iloc[1], ET.iloc[2]
bullet(f"Step 2 (hiệu quả từng đoạn): macro-F1 gộp tăng từ 0,433 lên {f(w.loc['S4 +TF-IDF text signal','macroF1_pooled'])}, nhưng trung bình theo đề chỉ {f(w.loc['S4 +TF-IDF text signal','macroF1_mean_prompts'])}, chưa tới 0,5. F1 lớp Ineffective tăng từ 0,07 lên {f(w.loc['S4 +TF-IDF text signal','F1_Ineffective'])} (precision {f(w.loc['S4 +TF-IDF text signal','P_Ineffective'],2)}). Phần lớn mức tăng đến từ chỉnh trọng số lớp, không phải từ đặc trưng văn bản. Thêm embedding câu và độ tương đồng ngữ cảnh không cải thiện thêm (macro-F1 theo đề {f(e6.macroF1_mean_prompts)} so với {f(e3.macroF1_mean_prompts)}). Đo bằng xếp hạng, gắn cờ 5% đoạn đáng ngờ nhất đạt precision {f(e6.prec_top5,2)} (gấp {f(e6.lift_top5,1)} lần đoán bừa) và bắt {f(e6.recall_top5*100,0)}% số đoạn Ineffective. Vẫn chưa dùng làm cờ cho giáo viên.")
bullet("Kết luận hẹp của nhóm: trên 8 đề independent, cấu trúc gold làm tăng nhỏ nhưng nhất quán QWK (khoảng +0,02). Phần lớn lợi thế của M1 so với chỉ-số-từ là độ dài. Vai trò dự đoán chưa chứng minh được lợi ích ngoài thông tin ranh giới đoạn.")

# ------------------------------------------------------------------ 2. responses
doc.add_heading("2. Từng điểm được nêu và cách nhóm xử lý", 1)
cap("Bảng 1. Nhận xét tuần 9 của thầy và các câu hỏi sau buổi trao đổi")
table(["#", "Yêu cầu", "Nhóm đã làm", "Tình trạng"], [
    ["1", "Δ cấu trúc theo năm nhóm số từ (giữ độ dài cố định)", "Chia bài thành 5 nhóm theo phân vị số từ, tính QWK và Δ trong từng nhóm, bootstrap theo bài (mục 6.1).", "Đã xong"],
    ["2", "Đường QWK theo mức làm hỏng nhãn vai trò (10, 20, 40%)", "Làm hỏng 10, 20, 40, 60, 80% nhãn vai trò, giữ ranh giới, chạy lại M2 trên cùng các fold, ba lần làm hỏng độc lập mỗi mức (mục 6.2).", "Đã xong"],
    ["3", "Biên bản trao đổi với CLC02 Nhóm 6", "Có dự thảo dựa trên bản trả lời của Nhóm 6 (mục 9). Cần Nhóm 6 xác nhận.", "Dự thảo"],
    ["4", "Đọc lại sáu ca cùng rubric trước khi giữ diễn giải mục 5.4", "Chưa đối chiếu với rubric của người chấm. Diễn giải sáu ca được giữ như giả thuyết, không như kết luận.", "Chưa xong"],
    ["5", "Sửa tiêu đề, kế hoạch còn ghi tuần 8", "Báo cáo trước còn ghi tuần 8 ở tiêu đề; báo cáo này ghi tuần 10.", "Đã xong"],
    ["6", "Nhiều tài liệu tham khảo mới nhất, không dùng bài cũ", "Đọc lại và xác nhận từng bài 2024 đến 2026 (arXiv, ACL Anthology, và bản PDF toàn văn của bài Chen, Wu và Zhang). Sửa trích dẫn Chen theo đúng tên bài, tập 69, số bài 101066 (mục 8 và 13).", "Đã xong"],
    ["7", "Workflow biến đổi dữ liệu và lý do", "Mục 3.", "Đã xong"],
    ["8", "Test case cho M1, M2, ví dụ n_chars; dữ liệu trước và sau xử lý", "Mục 4: một bài thật đi từ văn bản gốc đến đặc trưng và điểm dự đoán.", "Đã xong"],
    ["9", "Công thức hình thành thế nào, vì sao chỉ dùng các công thức này, có công thức khác không", "Mục 5.", "Đã xong"],
    ["10", "Phương pháp xử lý text phải có tính cạnh tranh; nói kỹ về bài 2024 và 2026", "Mục 8.", "Đã xong"],
    ["11", "F1 = 0,07 của Step 2 quá thấp; mục tiêu trên 0,5", "Step 2 cải tiến và đo bằng xếp hạng (mục 7). Macro-F1 gộp vượt 0,5, trung bình theo đề chưa; embedding và ngữ cảnh không giúp thêm; F1 lớp Ineffective vẫn thấp.", "Một phần"],
    ["12", "Làm tiếp từ Nhóm 6: lấy kết quả ô này sang ô kia hay copy quy trình?", "Copy quy trình, chạy lại trên cách chia theo đề của nhóm mình (mục 9).", "Đã xong"],
])

# ------------------------------------------------------------------ 3. workflow
doc.add_heading("3. Quy trình biến đổi dữ liệu và lý do", 1)
para("Dữ liệu gốc là một bảng mà mỗi dòng là một đơn vị lập luận (discourse unit), và toàn văn bài được lặp lại trên mọi dòng của bài. Hai kiểu đơn vị phân tích (cả bài, từng đoạn) nên cần hai bảng. Bảng 2 ghi từng bước, đầu vào, đầu ra và lý do chọn cách xử lý.")
cap("Bảng 2. Workflow từ dữ liệu gốc đến dữ liệu xử lý")
table(["Bước", "Việc làm", "Đầu ra", "Vì sao làm như vậy"], [
    ["1", "Đọc persuade_corpus_2.0_train.csv, giữ các cột cần dùng (id bài, đề, task, văn bản đoạn, vị trí đoạn, nhãn vai trò, nhãn hiệu quả, điểm tổng thể, ELL)", "Bảng thô", "Giảm bộ nhớ (file gốc khoảng 600 MB vì lặp toàn văn); không dùng các cột nhân khẩu học trừ kiểm tra công bằng."],
    ["2", "Tách bảng bài: bỏ trùng theo essay_id_comp", "essays.pkl: 15.594 bài, một dòng một bài, có điểm 1 đến 6", "Đơn vị chấm điểm là bài; nếu không bỏ trùng thì bài dài (nhiều đoạn) bị đếm nhiều lần."],
    ["3", "Tách bảng đoạn: bỏ đoạn không có văn bản, đếm số từ mỗi đoạn", "segments.pkl: 173.266 đoạn", "Đơn vị của Step 1 và Step 2 là đoạn; cần độ dài đoạn để dựng đặc trưng cấu trúc."],
    ["4", "Giữ task = Independent", "7.869 bài, 8 đề", "Bảy đề còn lại có tài liệu nguồn, điểm phụ thuộc việc dùng đúng nội dung tài liệu; trộn vào sẽ làm lẫn hai loại bài toán và tăng số đề lạ lẫm cho mô hình chỉ có đặc trưng bề mặt."],
    ["5", "Tính 43 đặc trưng ngôn ngữ cho mỗi bài bằng biểu thức chính quy", "features_independent.pkl (7.869 × 43)", "Không dùng mô hình ngôn ngữ để đặc trưng giải thích được và tái lập được; mỗi đặc trưng đếm được một hiện tượng nêu tên được (mục 5)."],
    ["6", "Sắp xếp đoạn theo vị trí trong bài; tính vị trí tương đối, đoạn đầu, đoạn cuối, vai trò đoạn kề", "Bảng đoạn có đặc trưng vị trí", "Vai trò và hiệu quả của một đoạn phụ thuộc vị trí (Lead ở đầu, Concluding ở cuối)."],
    ["7", "Dựng đặc trưng cấu trúc cấp bài từ vai trò (gold hoặc dự đoán): đếm, tỷ lệ, số từ theo vai trò, Evidence trên mỗi Claim…", "28 đặc trưng cấu trúc (F_gold, F_pred)", "Biến thông tin cấp đoạn thành đầu vào cấp bài để M2, M3 chỉ khác M1 ở nhóm đặc trưng này."],
    ["8", "Chia theo đề (leave-one-prompt-out), mọi bước fit nằm trong tập huấn luyện", "8 fold", "Câu hỏi nghiên cứu là đề mới; chia ngẫu nhiên theo bài sẽ cho điểm cao hơn thực tế vì mô hình đã thấy cùng đề."],
    ["9", "Step 2: bỏ đoạn Unannotated và đoạn thiếu nhãn hiệu quả", f"{n_ann:,} đoạn".replace(",", "."), "Đoạn Unannotated không thuộc lập luận nên không có nhãn hiệu quả."],
])
para("Điều dữ liệu cho thấy ngay ở bước 4 và 9: Ineffective chỉ chiếm khoảng 1,9% đoạn của 8 đề (1.474 trên " + f"{n_ann:,}".replace(",", ".") + "), thấp hơn 4,5% trên toàn tập train vì các đề independent có ít đoạn kém hơn. Đây là lý do Step 2 khó và là lý do macro-F1 phải được đọc cùng precision và recall của lớp này.")

# ------------------------------------------------------------------ 4. worked example
doc.add_heading("4. Ví dụ từng bước: một bài đi qua M0, M1, M2, M3", 1)
eid = "F3CB6601CF24"
i = int(np.where(ind.essay_id_comp.values == eid)[0][0])
row = X1.iloc[i]
txt = ind.full_text.iloc[i]
sg_e = seg_ind[seg_ind.essay_id_comp == eid].sort_values("discourse_start")
para(f"Bài {eid}, đề Seeking multiple opinions, điểm thật {int(ind.holistic_essay_score.iloc[i])}. Dữ liệu gốc của bài này là {len(sg_e)} dòng (đoạn), mỗi dòng lặp lại toàn văn {len(txt)} ký tự. Đoạn đầu của văn bản:")
para("“" + txt[:260].replace("\n", " ").strip() + "…”", italic=True)
cap("Bảng 3. Bài này sau bước tách đoạn (nhãn gold): thứ tự, vai trò và số từ")
rows = [[k + 1, r.discourse_type, int(r.seg_len), (r.discourse_text[:70].replace("\n", " ") + "…")] for k, r in enumerate(sg_e.itertuples())]
table(["#", "Vai trò gold", "Số từ", "Mở đầu đoạn"], rows)
cap("Bảng 4. Một số trong 43 đặc trưng M1 của bài (đầu vào của M1) so với trung bình 8 đề")
pick = [("n_words", "số từ"), ("n_chars", "số ký tự"), ("n_sents", "số câu"), ("n_paras", "số đoạn xuống dòng"), ("avg_sent_len", "từ mỗi câu"),
        ("ttr", "type-token ratio"), ("root_ttr", "root TTR"), ("flesch", "Flesch reading ease"), ("fk_grade", "Flesch-Kincaid grade"),
        ("conn_total", "số từ nối"), ("first_person", "tỉ lệ ngôi thứ nhất")]
table(["Đặc trưng", "Ý nghĩa", "Giá trị của bài", "Trung bình 8 đề"], [[k, d, f(row[k], 2), f(X1[k].mean(), 2)] for k, d in pick])
para("Đọc: cột n_chars (số ký tự) thể hiện độ dài văn bản tính theo ký tự, tương quan rất cao với n_words nên hai đặc trưng gần như là một. Bài này dài hơn trung bình khá nhiều, đó là một lý do M1 đã dự đoán cao (bảng 6). Bảng 5 cho thấy độ dài tăng đều theo điểm, nên mô hình có thể học điểm từ độ dài mà không đọc nội dung.")
byscore = pd.DataFrame({"score": ind.holistic_essay_score.values, "n_words": X1.n_words.values, "n_chars": X1.n_chars.values})
bs = byscore.groupby("score").agg(n=("n_words", "size"), words=("n_words", "mean"), chars=("n_chars", "mean"))
cap("Bảng 5. Độ dài trung bình theo điểm thật (7.869 bài)")
table(["Điểm", "Số bài", "Số từ trung bình", "Số ký tự trung bình"], [[int(k), int(r.n), f(r.words, 0), f(r.chars, 0)] for k, r in bs.iterrows()])
r = X1.corrwith(pd.Series(ind.holistic_essay_score.values))
para(f"Tương quan giữa số từ và điểm là {f(r['n_words'],2)}, giữa số ký tự và điểm là {f(r['n_chars'],2)}. Đây là lý do thầy yêu cầu đối chứng độ dài (M0b, M1 − len).")
st_idx = np.where(sg_e.discourse_type.values != "Unannotated")[0]
roles_e = [x for x in sg_e.discourse_type.values if x != "Unannotated"]
cnt = pd.Series(roles_e).value_counts()
n_claim, n_ev = int(cnt.get("Claim", 0)), int(cnt.get("Evidence", 0))
cap("Bảng 6. Đặc trưng cấu trúc của bài (đầu vào thêm của M2) và dự đoán của từng mô hình")
table(["Đại lượng", "Giá trị"], [
    ["n_segments (đoạn có vai trò)", len(roles_e)], ["n_claim, n_evidence", f"{n_claim}, {n_ev}"],
    ["evidence_per_claim = n_evidence / max(n_claim, 1)", f(n_ev / max(n_claim, 1), 2)],
    ["n_distinct_roles", len(cnt)],
    ["Dự đoán M0a (chỉ số từ)", f(z["GB__M0a  words"][i], 2)], ["Dự đoán M1", f(z["GB__M1"][i], 2)],
    ["Dự đoán M2 (cấu trúc gold)", f(z["GB__M2 (gold)"][i], 2)], ["Dự đoán M3 (vai trò dự đoán)", f(z["GB__M3 (pred)"][i], 2)],
    ["Điểm thật", int(ind.holistic_essay_score.iloc[i])],
])
para("Ví dụ này lần theo đúng đường đi: văn bản gốc, tách thành đoạn với vai trò, đếm vai trò thành đặc trưng cấp bài, rồi mô hình cho điểm liên tục (làm tròn về 1 đến 6 trước khi tính QWK). Trong báo cáo tuần trước, ca này là ca duy nhất trong sáu ca mà lỗi nhận vai trò làm M3 hại thêm so với M2 (bộ nhận vai trò bỏ sót một Claim). Nhóm không dùng một ca để kết luận; ca chỉ minh họa cơ chế.")

# ------------------------------------------------------------------ 5. formulas
doc.add_heading("5. Công thức, lý do chọn và các lựa chọn khác", 1)
para("Mỗi công thức dưới đây trả lời một câu hỏi cụ thể; nhóm không dùng bộ công thức nào khác vì mỗi lựa chọn thay thế hoặc cần công cụ nhóm chưa có hoặc đo cùng một hiện tượng.")
cap("Bảng 7. Công thức dùng trong đặc trưng và đánh giá")
table(["Đại lượng", "Công thức", "Vì sao dùng", "Lựa chọn khác và vì sao chưa dùng"], [
    ["QWK", "κ_w = 1 − Σ w_ij O_ij / Σ w_ij E_ij, w_ij = (i − j)² / (k − 1)²", "Điểm là thứ tự 1 đến 6; sai lệch càng xa càng bị phạt nặng; chuẩn của nghiên cứu AES nên so được với cách báo cáo của Yang 2024.", "Accuracy bỏ qua thứ tự; MAE chỉ là phụ (báo cáo cùng QWK); Pearson không phạt lệch hệ thống."],
    ["MAE, adjacent accuracy", "MAE = mean |ŷ − y|; adj = mean(|ŷ − y| ≤ 1)", "Cho biết lệch theo đơn vị điểm, dễ hiểu với giáo viên.", "RMSE phạt lớn các lệch hiếm; chưa cần."],
    ["TTR, root TTR", "TTR = V / N; root TTR = V / √N", "Đo đa dạng từ vựng. Root TTR bớt phụ thuộc độ dài vì TTR giảm khi N tăng.", "MTLD, HD-D bền với độ dài hơn nhưng cần thư viện riêng; nhóm chưa thử."],
    ["Flesch, Flesch-Kincaid", "FRE = 206,835 − 1,015·(N/S) − 84,6·(Y/N); FK = 0,39·(N/S) + 11,8·(Y/N) − 15,59", "Công thức chuẩn, chỉ cần đếm từ, câu, âm tiết; âm tiết ước lượng bằng nhóm nguyên âm.", "Độ khó dựa tần suất từ cần bảng tần suất ngoài; bộ đếm âm tiết của nhóm chỉ là ước lượng."],
    ["Từ nối", "đếm cụm trong sáu nhóm (bổ sung, đối lập, nguyên nhân, ví dụ, kết luận, thứ tự); tổng/câu", "Từ nối là dấu hiệu tổ chức lập luận bề mặt mà không cần phân tích cú pháp.", "Phân tích quan hệ diễn ngôn (PDTB) cần parser riêng."],
    ["Đặc trưng cấu trúc", "n_r, share_r = n_r / Σn, words_r (theo vai trò r); evidence_per_claim = n_Evidence / max(n_Claim, 1); rebuttal_per_counterclaim", "Phản ánh rubric: có luận điểm, có bằng chứng cho mỗi luận điểm, có phản luận và phản bác.", "Đồ thị quan hệ giữa các đoạn (support, attack) cần nhãn quan hệ mà PERSUADE không có."],
    ["Chỉ ranh giới B", "số đoạn, tổng số từ trong đoạn, trung bình, lớn nhất, nhỏ nhất, độ lệch chuẩn, đoạn đầu, đoạn cuối", "Tách riêng thông tin chia đoạn khỏi nhãn vai trò để biết nhãn có thêm gì.", "—"],
    ["Macro-F1", "F1_k = 2 P_k R_k / (P_k + R_k); macro = trung bình F1_k", "Lớp Ineffective hiếm; accuracy sẽ cao chỉ vì đoán Adequate (77,5%).", "Weighted-F1 che lớp hiếm."],
    ["Chỉnh trọng số lớp", "ŷ = argmax_k w_k · P(k | x); w chọn trên dự đoán out-of-fold của 7 đề huấn luyện", "Đổi ngưỡng quyết định mà không nhìn đề giữ lại.", "class_weight trong lúc huấn luyện (Nhóm 6 dùng): không cho kiểm soát tách ngưỡng khỏi mô hình."],
    ["PR-AUC, precision top 5%", "AP = Σ (R_n − R_{n−1}) P_n; lift = precision / tỉ lệ nền", "Đo khả năng xếp hạng đoạn đáng ngờ, không phụ thuộc ngưỡng; hợp với mục tiêu ưu tiên feedback.", "ROC-AUC trông cao khi lớp quá hiếm."],
    ["Permutation importance theo nhóm", "ΔQWK = QWK(gốc) − QWK(xáo cột nhóm g trong tập đề giữ lại)", "Thay impurity importance theo nhận xét của thầy; xáo cả nhóm vì các đặc trưng độ dài tương quan nhau.", "SHAP: chưa cần cho câu hỏi về nhóm."],
], size=9)
para("Về câu hỏi vì sao 43 đặc trưng mà không nhiều hơn: nhóm đã đo. Bỏ nhóm độ dài làm QWK giảm 0,020 (còn 20 đặc trưng tỉ lệ vẫn đạt 0,733), và xáo trộn các nhóm lexical, readability, sentence shape, punctuation, connectives mỗi nhóm chỉ làm QWK giảm dưới 0,01 (bảng 13). Các nhóm ngoài độ dài và cấu trúc đóng góp rất ít, nên thêm đặc trưng cùng loại chưa phải việc ưu tiên.")

# ------------------------------------------------------------------ 6. step 3 results
doc.add_heading("6. Kết quả Step 3 (RQ1, RQ2)", 1)
para("Thiết kế không đổi: 8 đề independent, Gradient Boosting (300 cây, độ sâu 3, learning rate 0,05, subsample 0,8), ba seed lấy trung bình dự đoán liên tục rồi làm tròn; chỉ số chính là mean QWK theo đề, SD với ddof = 1. M3 dùng sơ đồ cross-fit kiểm bằng ID essay (không đổi so với báo cáo trước).")
names = [("M0a  words", "M0a (số từ)"), ("M0b  length-group", "M0b (nhóm độ dài)"), ("M1", "M1"), ("M1 −n_chars", "M1 − n_chars"), ("M1 −len", "M1 − len"),
         ("M1 +B(boundary only)", "M1 + B (chỉ ranh giới)"), ("M2 (gold)", "M2 (gold)"), ("M3 (pred)", "M3 (dự đoán)")]
cap("Bảng 8. Kết quả chính, Gradient Boosting, 3 seed, 8 đề")
table(["Mô hình", "Mean QWK / đề ± SD", "Đề kém nhất", "QWK gộp", "MAE"],
      [[b, f(main.loc[a, "mean QWK / đề"]) + " ± " + f(main.loc[a, "SD (ddof=1)"]), f(main.loc[a, "worst đề"]), f(main.loc[a, "pooled QWK"]), f(main.loc[a, "MAE"])] for a, b in names])
para(f"Random Forest (1 seed) cho cùng thứ tự: M1 {f(mrf.loc['M1','mean QWK / đề'])}; M2 {f(mrf.loc['M2 (gold)','mean QWK / đề'])}; M3 {f(mrf.loc['M3 (pred)','mean QWK / đề'])}.")
sel = ["Độ dài mở rộng − chỉ số từ        (M0b − M0a)", "Ngôn ngữ đầy đủ − độ dài mở rộng   (M1 − M0b)", "RQ1  gold structure                (M2 − M1)",
       "RQ1  predicted structure           (M3 − M1)", "RQ2  mất khi dùng dự đoán          (M2 − M3)", "chỉ ranh giới (không vai trò)      (M1+B − M1)",
       "cấu trúc gold trên nền độ dài      (M0b+S(gold) − M0b)", "cấu trúc pred trên nền độ dài      (M0b+S(pred) − M0b)"]
lab = ["M0b − M0a (độ dài mở rộng)", "M1 − M0b (ngôn ngữ ngoài độ dài)", "RQ1: M2 − M1", "RQ1: M3 − M1", "RQ2: M2 − M3", "Chỉ ranh giới: M1 + B − M1", "Cấu trúc gold trên M0b", "Cấu trúc dự đoán trên M0b"]
cap("Bảng 9. Δ QWK paired theo đề (mean của 8 chênh lệch, GB)")
table(["So sánh", "Mean Δ", "SD", "Min đến max", "Đề Δ > 0", "p (dấu)"],
      [[l, sg(dgb.loc[s, "mean Δ (đề)"]), f(dgb.loc[s, "SD (ddof=1)"]), sg(dgb.loc[s, "min"]) + " đến " + sg(dgb.loc[s, "max"]), f"{int(dgb.loc[s, '#đề Δ>0 /8'])}/8".replace("f", ""), f(dgb.loc[s, "sign-test p"])] for s, l in zip(sel, lab)])
para(f"Với Random Forest: M2 − M1 = {sg(drf.iloc[0,0])} (6/8 đề), M3 − M1 = {sg(drf.iloc[1,0])}, M2 − M3 = {sg(drf.iloc[2,0])}. Với 8 đề, p của kiểm định dấu chỉ có tác dụng mô tả; nhiều seed không tạo thêm đề độc lập.")

doc.add_heading("6.1. Δ cấu trúc trong năm nhóm số từ", 2)
para("Câu hỏi: nếu giữ độ dài gần cố định, cấu trúc còn giúp không? Nhóm chia 7.869 bài thành năm nhóm bằng nhau theo số từ (phân vị), dùng dự đoán ngoài mẫu đã có (leave-one-prompt-out), tính QWK từng mô hình trong từng nhóm và bootstrap 500 lần theo bài để lấy khoảng tin cậy 95%. QWK trong một nhóm hẹp độ dài thấp hơn QWK toàn tập vì khoảng điểm trong nhóm bị thu hẹp; chỉ so Δ giữa các mô hình trong cùng nhóm.")
rows = []
for g_, d in byq.groupby("group", sort=False):
    d = d.set_index("comparison")
    rows.append([g_, int(d.n.iloc[0]), f(d.mean_score.iloc[0], 2), f(d.loc["M2 - M1", "QWK_B"]),
                 sg(d.loc["M2 - M1", "dQWK"]) + f" [{f(d.loc['M2 - M1','ci_lo'])}; {f(d.loc['M2 - M1','ci_hi'])}]",
                 sg(d.loc["M1+boundary - M1", "dQWK"]), sg(d.loc["M3 - M1", "dQWK"]),
                 sg(d.loc["M2 - M1+boundary", "dQWK"]) + f" [{f(d.loc['M2 - M1+boundary','ci_lo'])}; {f(d.loc['M2 - M1+boundary','ci_hi'])}]"])
cap("Bảng 10. Δ QWK trong từng nhóm số từ (Q1 ngắn nhất đến Q5 dài nhất; GB, 3 seed)")
table(["Nhóm số từ", "n", "Điểm TB", "QWK của M1", "M2 − M1 [95% CI]", "M1 + B − M1", "M3 − M1", "M2 − (M1 + B) [95% CI]"], rows, size=9)
dd = byq[byq.comparison == "M2 - M1"].dQWK
para(f"Đọc kết quả. (i) M2 − M1 dương ở cả năm nhóm ({sg(dd.min())} đến {sg(dd.max())}); khoảng tin cậy chứa 0 ở nhóm Q3. Cấu trúc gold vì vậy không chỉ giúp ở bài ngắn hoặc bài dài, nhưng giúp nhiều nhất ở bài dài nhất. (ii) Ở bốn nhóm đầu, chỉ cần ranh giới (M1 + B) đã cho phần lớn mức tăng, và hiệu M2 − (M1 + B) có CI chứa 0. (iii) Ở nhóm dài nhất, M2 hơn M1 + B rõ ({sg(byq[(byq.comparison=='M2 - M1+boundary')].dQWK.iloc[-1])}, CI không chứa 0): với bài dài, nhãn vai trò thêm thông tin ngoài số đoạn và độ dài đoạn. Đây là điều kiện cụ thể mà nhãn vai trò có giá trị, và là điểm đáng giữ cho phần đề xuất. (iv) Điểm trung bình của nhóm dài nhất là 5,0 và của nhóm ngắn nhất là 2,5; trong từng nhóm độ dài vẫn thay đổi theo điểm nên kiểm soát bằng phân vị chỉ là kiểm soát một phần.")

doc.add_heading("6.2. Bộ nhận vai trò cần tốt đến mức nào?", 2)
para("Thí nghiệm: lấy nhãn gold, đổi ngẫu nhiên p% nhãn vai trò của các đoạn có nhãn sang một vai trò khác (đều trên bảy vai trò), giữ nguyên ranh giới, dựng lại 28 đặc trưng cấu trúc và chạy lại M2 trên cùng các fold. Mỗi mức p chạy với ba lần làm hỏng độc lập (seed khác nhau) và một seed Gradient Boosting. Sự biến động giữa ba lần làm hỏng ghi ở cột SD.")
cap("Bảng 11. QWK của M2 khi làm hỏng nhãn vai trò (mean QWK theo đề, trung bình ba lần làm hỏng)")
rows = [[f"{int(k*100)}%", f(r.meanQWK), (f(r.sd_draws) if not np.isnan(r.sd_draws) else "—"), sg(r.d_vs_M1), sg(r.d_vs_boundary)] for k, r in curv.iterrows()]
table(["Nhãn bị làm hỏng", "Mean QWK / đề", "SD giữa ba lần", "So với M1", "So với M1 + B"], rows)
figure(FIGS / "w10_length_groups_and_corruption.png", 16, "Hình 1. Trái: QWK của M2 theo mức làm hỏng nhãn vai trò (vạch ngang: M1, M1 + ranh giới). Phải: Δ QWK của cấu trúc trong từng nhóm độ dài.")
para(f"Đọc kết quả. M2 đầy đủ nhãn là {f(curv.loc[0.0,'meanQWK'])}, M1 + B là {f(mb['mean QWK / đề'])}. Chỉ với 10% nhãn hỏng, lợi thế so với M1 + B còn {sg(curv.loc[0.1,'d_vs_boundary'])}; từ 20% trở lên thì thấp hơn M1 + B ({sg(curv.loc[0.2,'d_vs_boundary'])} ở 20%, {sg(curv.loc[0.4,'d_vs_boundary'])} ở 40%). Đường cong phẳng từ 40% đến 80% và vẫn cao hơn M1 khoảng {sg(curv.loc[0.8,'d_vs_M1'])}, vì ranh giới và độ dài đoạn không bị hỏng. Bộ nhận vai trò của nhóm có macro-F1 0,675, tức nhãn sai cỡ một phần tư (accuracy của baseline Step 1 là 0,745; bộ nhận vai trò của M3 là mô hình khác nên đây chỉ là ước lượng thô), nằm trong vùng mà nhãn vai trò chưa thêm gì ngoài ranh giới. Câu trả lời cho RQ2 khi dùng bộ nhận vai trò hiện tại: không. Ngay ở 10% hỏng, lợi thế so với M1 + B chỉ còn +0,002 (số đề cao hơn M1 + B giảm từ 5/8 xuống 3 đến 5/8 giữa ba lần làm hỏng), nên một bộ nhận vai trò chỉ có ý nghĩa nếu sai ít hơn mức này, tức cần tốt hơn nhiều so với baseline tuyến tính hiện tại. Hạn chế: một seed Gradient Boosting cho mỗi lần làm hỏng; SD giữa ba lần làm hỏng ở các mức 0,001 đến 0,002 nhưng cách làm hỏng (đổi đều ngẫu nhiên) không giống lỗi thật của bộ nhận vai trò, vốn thường nhầm các vai trò gần nhau (Claim và Evidence).")

doc.add_heading("6.3. Lối tắt độ dài và importance", 2)
cap("Bảng 12. Thay đổi điểm dự đoán sau khi nhân đôi văn bản (mô hình ngoài mẫu, 320 bài)")
table(["Mô hình", "Mean Δ điểm", "Median", "% bài tăng ≥ 1 điểm"], [[k, sg(r.iloc[0], 3), sg(r.iloc[1], 3), f(r.iloc[2], 1) + "%"] for k, r in dup.iterrows()])
cap("Bảng 13. QWK giảm khi xáo trộn từng nhóm đặc trưng của M2 (đề giữ lại, trung bình 8 đề)")
table(["Nhóm", "ΔQWK", "SD qua 8 đề", "Min đến max"], [[k, f(r.iloc[0]), f(r.iloc[1]), f(r.iloc[2]) + " đến " + f(r.iloc[3])] for k, r in perm.iterrows()])
para("Chỉ M0a (số từ) bị đánh lừa rõ khi văn bản bị nhân đôi; M0b và M1 lệch dưới 0,06 điểm. Kết quả này không có nghĩa M1 không dựa vào độ dài: xáo trộn nhóm độ dài làm QWK giảm 0,545, lớn gấp hơn sáu lần nhóm cấu trúc (0,088). Các nhóm này tương quan nhau, nên nhóm không chia con số thành phần trăm đóng góp.")

# ------------------------------------------------------------------ 7. step 2
doc.add_heading("7. Step 2: nâng macro-F1 và F1 lớp Ineffective", 1)
para("Mục tiêu từ buổi trao đổi: macro-F1 trên 0,5 và F1 lớp Ineffective (0,07) không còn quá thấp. Nhóm copy quy trình của Nhóm 6 (đặc trưng vai trò, độ dài, vị trí, n-gram; xử lý mất cân bằng lớp; chỉnh ngưỡng) và chạy lại trên cách chia theo đề của nhóm mình. Mỗi dòng của bảng 14 thêm một khối đặc trưng, cùng một thuật toán (HistGradientBoosting) và cùng các fold. S4 thêm tín hiệu TF-IDF dạng xếp chồng (xác suất out-of-fold của hồi quy logistic trên TF-IDF từ và ký tự).")
order = ["S1 role+length+position", "S2 +essay context", "S3 +essay M1 features", "S4 +TF-IDF text signal", "LR TF-IDF only"]
rows = []
for k in order:
    for wt in ("argmax", "tuned on inner OOF"):
        r = s2[(s2.model == k) & (s2.weights == wt)].iloc[0]
        rows.append([k, "argmax" if wt == "argmax" else "chỉnh trọng số", f(r.macroF1_pooled), f(r.macroF1_mean_prompts) + " ± " + f(r.SD_prompts), f(r.F1_Effective), f(r.F1_Ineffective), f(r.P_Ineffective), f(r.R_Ineffective)])
cap("Bảng 14. Step 2, leave-one-prompt-out, 8 đề, 77.639 đoạn. Baseline Tuần 8: LR TF-IDF + vị trí, macro-F1 gộp 0,433, F1 Ineffective 0,07; đoán lớp đa số: 0,291")
table(["Khối", "Quyết định", "Macro-F1 gộp", "Macro-F1 TB theo đề ± SD", "F1 Effective", "F1 Ineffective", "Precision Ineff.", "Recall Ineff."], rows, size=9)
para(f"Đọc kết quả. (i) Macro-F1 gộp của S4 chỉnh trọng số là {f(w.loc['S4 +TF-IDF text signal','macroF1_pooled'])}, vượt 0,5; nhưng chỉ số theo đề, là chỉ số nhóm dùng cho Step 3, là {f(w.loc['S4 +TF-IDF text signal','macroF1_mean_prompts'])} và chỉ ba trong tám đề đạt từ 0,5 (bảng 15). Nhóm báo cả hai số. (ii) Phần lớn mức tăng đến từ chỉnh trọng số lớp (macro-F1 gộp 0,466 lên 0,510 ở S4). Khối chỉ có vai trò, độ dài và vị trí (S1) đã đạt {f(w.loc['S1 role+length+position','macroF1_pooled'])}; thêm ngữ cảnh bài, đặc trưng M1 và TF-IDF chỉ thêm khoảng 0,006. (iii) F1 lớp Ineffective lên {f(w.loc['S4 +TF-IDF text signal','F1_Ineffective'])}, nhưng precision chỉ {f(w.loc['S4 +TF-IDF text signal','P_Ineffective'],2)}: khoảng chín trong mười cờ Ineffective là báo nhầm. Lớp Effective đạt F1 {f(w.loc['S4 +TF-IDF text signal','F1_Effective'])}. (iv) Nhãn hiệu quả có độ đồng thuận người chấm κ = 0,32, và Nhóm 6 với DeBERTa cũng chỉ đạt F1 0,374 cho lớp này trên cách chia khác, nên mức trần khó cao hơn nhiều.")
cap("Bảng 15. Step 2 (S4, chỉnh trọng số) theo từng đề giữ lại")
table(["Đề", "Số đoạn", "Số Ineffective", "Macro-F1", "F1 Ineffective"], [[k, int(r.n), int(r.n_Ineffective), f(r.macroF1), f(r.F1_Ineffective)] for k, r in s2pp.iterrows()])
doc.add_heading("7.1. Thước xếp hạng, embedding câu và ngữ cảnh văn bản", 2)
para("Hướng đo theo mục tiêu ưu tiên feedback: thay vì gắn nhãn cứng, xếp các đoạn theo xác suất Ineffective và xem phần đầu của danh sách có đúng không. Nhóm thêm hai nâng cấp trên khối S3 (vai trò, độ dài, vị trí, ngữ cảnh bài, 43 đặc trưng M1): S5 thêm embedding câu (all-MiniLM-L6-v2, mô hình đóng băng, nén còn 64 chiều bằng PCA không nhãn) và S6 thêm ba độ tương đồng cosine (với câu Position, với đoạn liền trước, với trọng tâm bài). Cùng thuật toán, cùng fold, trọng số lớp chỉ chỉnh trên 7 đề huấn luyện. PR-AUC và precision top 5% được tính trong từng đề giữ lại rồi lấy trung bình 8 đề; mức đoán bừa của cả hai là tỉ lệ Ineffective trong đề (trung bình " + f(e3.base_rate * 100, 1) + "%).")
rows = []
for r in emb.itertuples():
    rows.append([r.model, "argmax" if r.weights == "argmax" else "chỉnh trọng số", f(r.macroF1_pooled), f(r.macroF1_mean_prompts), f(r.F1_Ineffective), f(r.PR_AUC), f(r.prec_top5, 3), f(r.recall_top5, 3), f(r.lift_top5, 1)])
cap("Bảng 16. Nâng cấp Step 2: macro-F1 và thước xếp hạng (8 đề; ba cột cuối là trung bình theo đề của top 5% đoạn đáng ngờ nhất; PR-AUC và ba cột cuối không phụ thuộc quyết định argmax hay chỉnh trọng số)")
table(["Khối", "Quyết định", "Macro-F1 gộp", "Macro-F1 TB theo đề", "F1 Ineffective", "PR-AUC", "Precision top 5%", "Recall top 5%", "Lift"], rows, size=9)
figure(FIGS / "step2_embed_ranking.png", 16, "Hình 2. Khối S6, theo từng đề giữ lại. Trái: PR-AUC của lớp Ineffective so với tỉ lệ nền. Phải: precision trong top 5% đoạn đáng ngờ nhất so với tỉ lệ nền.")
para(f"Đọc kết quả. (i) Embedding và độ tương đồng ngữ cảnh không cải thiện đáng kể. Từ S3 đến S6, macro-F1 gộp thay đổi {sg(e6.macroF1_pooled - e3.macroF1_pooled)} nhưng macro-F1 theo đề thay đổi {sg(e6.macroF1_mean_prompts - e3.macroF1_mean_prompts)}; PR-AUC lần lượt {f(e3.PR_AUC)}, {f(e5.PR_AUC)}, {f(e6.PR_AUC)}. Các khác biệt này nhỏ hơn nhiều so với độ lệch giữa các đề (SD macro-F1 theo đề {f(e3.SD_prompts)} đến {f(e6.SD_prompts)}), nên nhóm không kết luận hướng nào tốt hơn. Mức macro-F1 gộp trên 0,5 vẫn do chỉnh trọng số lớp. (ii) Về xếp hạng, mô hình có tín hiệu thật nhưng yếu: PR-AUC {f(e6.PR_AUC)} so với mức nền {f(e6.base_rate)}, tức khoảng {f(e6.PR_AUC / e6.base_rate, 1)} lần đoán bừa. Nếu gắn cờ 5% đoạn đáng ngờ nhất của mỗi đề thì {f(e6.prec_top5 * 100, 1)}% số cờ đúng là Ineffective (gấp {f(e6.lift_top5, 1)} lần nền) và bắt được {f(e6.recall_top5 * 100, 0)}% tổng số đoạn Ineffective. Nói cách khác, cứ khoảng mười một cờ thì chỉ một cờ đúng, và khoảng ba trong bốn đoạn Ineffective vẫn không lọt vào danh sách. (iii) Theo hình 2, PR-AUC cao hơn mức nền ở cả tám đề (đọc từ hình: khoảng 2 đến 4 lần). Precision top 5% cao nhất ở hai đề có tỉ lệ Ineffective cao nhất (Cell phones at school, Community service, khoảng 0,15 đến 0,17) và thấp nhất ở Phones and driving (khoảng 0,04); kết quả vì vậy phụ thuộc đề và tỉ lệ nền. (iv) Không có bằng chứng ở đây rằng nội dung đoạn (embedding) giúp ngoài vai trò, độ dài và vị trí; điều này khớp với Gui (2026), người thấy tín hiệu hiệu quả đoạn phần lớn theo độ dài và mức triển khai.")
para("Kết luận cho Step 2: xếp hạng tốt hơn đoán bừa rõ rệt nhưng độ chính xác tuyệt đối còn thấp, nên Step 2 vẫn chưa đủ để dùng làm cờ cho giáo viên. Cách dùng hợp lý nhất ở trạng thái hiện tại là sắp thứ tự gợi ý để người đọc xem trước, kèm lời nói rõ phần lớn gợi ý sẽ không đúng. Điều này phù hợp với giới hạn của nhãn (κ = 0,32). Muốn tiến xa hơn cần mô hình mạnh hơn (transformer) hoặc nhãn tốt hơn; cả hai nằm ngoài khả năng của máy hiện tại và nằm trong phạm vi Nhóm 6.")

# ------------------------------------------------------------------ 8. literature
doc.add_heading("8. Định vị so với tài liệu 2024 đến 2026", 1)
para("Phương pháp xử lý text của nhóm là đặc trưng viết tay giải thích được cộng mô hình cây. Để biện hộ cho lựa chọn này, nhóm đối chiếu với các bài gần nhất, mỗi bài đã được mở lại trên arXiv hoặc ACL Anthology.")
lead("Yang và cộng sự (2024), AAAI. ", "So sánh 9 phương pháp chấm điểm bằng 7 độ đo (độ chính xác và công bằng) trên PERSUADE 2.0 (hơn 25.000 bài, 15 đề). Mô hình theo từng đề chính xác hơn mô hình cross-prompt (QWK trung bình cao hơn 25,61%), nhưng thường thiên lệch theo tình trạng kinh tế nhiều hơn; mô hình học máy truyền thống với đặc trưng thiết kế kỹ có tiềm năng cân bằng độ chính xác và công bằng tốt hơn mạng nơ-ron phức tạp. Đây là cơ sở nhóm chọn leave-one-prompt-out và bộ chấm đặc trưng + cây. Vì sao cạnh tranh: nhóm dùng cùng loại biểu diễn (đặc trưng tay, cây) và cùng loại chia (cross-prompt) mà bài này khuyến nghị cho mục tiêu khái quát hóa. Nhóm không đặt QWK của mình cạnh số của bài vì tập đề, đặc trưng và cách tính khác nhau.")
lead("Wang, Shi, Tang và Qin (2026), ArguLens. ", "Hệ thống gồm bộ phân loại diễn ngôn (Qwen2.5-7B tinh chỉnh LoRA trên PERSUADE 2.0; độ chính xác 82,6%, macro-F1 0,727), bộ chấm LightGBM trên 31 đặc trưng ngôn ngữ và diễn ngôn, và bộ sinh phản hồi. Bộ chấm đạt QWK trung bình 0,813 qua 5-fold chia theo đề; thêm nhãn diễn ngôn gold tăng +0,055 QWK so với cấu hình từ vựng và cú pháp (p = 0,010). Các tác giả nói rõ đây là chẩn đoán thành phần dưới giao thức oracle, không phải kết quả end-to-end. Nhóm dùng sự phân biệt này: M2 là oracle, M3 là bước trung gian (ranh giới gold, vai trò dự đoán). Mức tăng của nhóm (+0,023) nhỏ hơn +0,055 của ArguLens; hai bài khác bộ đặc trưng (43 + 28 so với 31), số bài (7.869 so với khoảng 26.000), số đề và cách chia, nên không so cạnh nhau. Một điểm nhóm làm thêm so với bài: tách riêng thông tin ranh giới khỏi nhãn vai trò, và cho thấy ở bài ngắn phần lớn mức tăng đến từ ranh giới.")
lead("Gui (2026), AIME-Con. ", "Phân tích khoảng 144.000 đoạn PERSUADE 2.0, thấy hiệu quả của một đoạn phụ thuộc loại diễn ngôn, và phần lớn tín hiệu theo dõi mức độ triển khai và độ dài; tác giả cảnh báo không nên phản hồi tự động mà bỏ qua ngữ cảnh diễn ngôn. Điều này khớp với kết quả Step 2 của nhóm (đặc trưng độ dài và vị trí đã cho gần hết macro-F1) và với việc nhóm không dùng Step 2 làm cờ.")
lead("Ormerod (2025), arXiv:2505.22771. ", "Thêm chú thích phản hồi (lỗi chính tả, thành phần lập luận do bộ phân loại token đánh dấu) vào quy trình chấm điểm, và thấy mô hình encoder tinh chỉnh cho kết quả tốt hơn khi có chú thích. Hướng này gần M3 nhưng dùng mô hình encoder, nhóm chưa làm.")
lead("Keramati và Warschauer (2026), arXiv:2606.10327. ", "Tinh chỉnh LLaMA-3.1-8B (LoRA) theo thứ tự các thành phần lập luận (sequential) so với độc lập và ngẫu nhiên trên PERSUADE 2.0; sequential tốt nhất tổng thể (F1 65% cho evidence, 87% cho conclusion). Cho thấy mô hình nhỏ có thể cạnh tranh, và là hướng nếu nhóm có GPU.")
lead("Chen, Wu và Zhang (2026), Assessing Writing 69, 101066 (đăng trực tuyến 19/5/2026). ", "Nhóm đã đọc toàn văn bản PDF. Bài tổng quan ba cách đo công bằng trong chấm điểm tự động (so sánh sai số dự đoán theo nhóm bằng hồi quy, khác biệt chức năng đặc trưng, và các độ đo nhóm của học máy như disparate impact, demographic parity, equalized odds), chỉ ra chúng không kiểm soát năng lực hoặc chỉ dùng cho nhãn nhị phân, rồi đề xuất hai độ đo cho điểm thứ bậc: conditional disparity ratio, P(Ŷ = j | nhóm tập trung, θ = i) chia P(Ŷ = j | nhóm tham chiếu, θ = i), và conditional disparity difference (hiệu hai xác suất đó), tính riêng cho từng mức năng lực θ. Hai nguyên tắc: so sánh các nhóm cùng mức năng lực (dùng điểm người chấm làm đại diện) và đánh giá trên tập kiểm tra tách khỏi tập huấn luyện. Thí nghiệm minh họa: 2.167 bài của một đề (Facial Action Coding System) thuộc PERSUADE 2.0, gộp điểm 1 đến 6 thành 3 mức, so sánh theo giới tính và chủng tộc (White, không phải White), chia ngẫu nhiên 80/20, bốn mô hình (hồi quy logistic thứ bậc trên TF-IDF, QWK 0,73; BERT tinh chỉnh, 0,80; ChatGPT-4o-mini zero-shot 0,40 và few-shot 0,51). Kết quả chính: khi không điều kiện hóa theo năng lực, khác biệt giữa nhóm gần như bằng không (ví dụ hồi quy logistic dự đoán mức 3: tỉ số 1,049), nhưng khi điều kiện hóa thì xuất hiện thiên lệch ngược chiều ở các mức năng lực khác nhau (1,559 ở mức trung bình và 0,595 ở mức cao); chỉ số hồi quy kiểu Loukina gần như bằng không ở cả bốn mô hình. Các tác giả nhấn mạnh ba giới hạn: kết quả chỉ là thiên lệch tiềm năng chứ chưa phải bằng chứng kết luận; độ đo chỉ có nghĩa khi mô hình đủ chính xác (ChatGPT zero-shot hầu như không cho điểm cao nên trông \"công bằng\" vô nghĩa); và chia theo năng lực và nhóm làm nhiều ô rỗng hoặc rất ít bài. Bài không xét ELL và không dùng đặc trưng cấu trúc lập luận. Với nhóm, bài này là cơ sở cho RQ3: thay phép so sánh sai số trung bình ở cùng điểm thật mà nhóm dùng ở báo cáo trước bằng hai độ đo này, tính trên dự đoán ngoài mẫu của M1, M2, M3, và chỉ làm khi RQ1 và RQ2 xong. Bài cũng nêu ngưỡng tham chiếu của ETS: QWK khoảng 0,70 được coi là chấp nhận được cho chấm điểm thực tế (trích Wang và von Davier, 2014; nhóm chưa đọc nguồn gốc này).")
lead("Crossley và cộng sự (2024), PERSUADE 2.0. ", "Nguồn dữ liệu và nhãn. Báo cáo của Nhóm 6 trích bài này khi nói về độ đồng thuận người chấm; con số κ = 0,316 của Nhóm 6 nhóm chưa kiểm lại trên bài gốc.")
para("Vì sao phương pháp xử lý dữ liệu của nhóm cạnh tranh. Ba điểm, mỗi điểm đã có số: (a) kiểm soát độ dài tốt hơn mức thường gặp, vì có bốn nhóm đối chứng độ dài (M0b, M1 − n_chars, M1 − len, các khối + S) và phép nhân đôi ngoài mẫu; (b) tách thông tin ranh giới khỏi nhãn vai trò, mà bài ArguLens không làm; (c) mọi bước fit nằm trong tập huấn luyện của từng fold, kiểm bằng ID. Điểm yếu cần nói thẳng: đặc trưng M1 tự cài đặt, không dùng spaCy hay kiểm tra chính tả; không có transformer; chỉ 8 đề.")

# ------------------------------------------------------------------ 9. group 6
doc.add_heading("9. Trao đổi với CLC02 Nhóm 6 (dự thảo biên bản)", 1)
para("Nhóm 6 và Nhóm 4 cùng dùng PERSUADE 2.0. Nhóm 6 làm Step 2 (hiệu quả đoạn) bằng DeBERTa-v3-base; Nhóm 4 làm Step 3 (chấm điểm cả bài). Phần dưới tóm tắt bản trả lời của Nhóm 6 và đề xuất của Nhóm 4; mục có chữ \"đề xuất\" cần Nhóm 6 xác nhận.")
cap("Bảng 17. Điểm trao đổi và quyết định")
table(["Chủ đề", "Nhóm 6 nói", "Nhóm 4 quyết định hoặc đề xuất"], [
    ["Chạy LOPO để tránh rò rỉ đề", "DeBERTa với 15 fold cần khoảng 35 đến 45 giờ GPU, không đủ tài nguyên. Đề xuất: chọn 1 đến 2 đề giữ lại chung; hoặc họ chạy LOPO bằng Random Forest hoặc Logistic Regression (dưới 15 phút) và chỉ chạy DeBERTa ở 1 đến 2 fold. Xin danh sách 8 đề.", "Đề xuất: gửi danh sách 8 đề; xin dự đoán LOPO của RF/LR trên đúng 8 đề; không dùng file validation ngẫu nhiên 80/20 của họ."],
    ["File xác suất", "Đồng ý gửi essay_id, discourse_id (chuỗi), prob_ineffective, prob_adequate, prob_effective, pred_label, prompt_name, discourse_type; trước hết trên tập validation 29.102 đơn vị.", "File validation của họ chia ngẫu nhiên theo bài trên 15 đề nên mô hình đã thấy các đề nhóm 4 giữ lại; dùng làm đặc trưng Step 3 sẽ phá chia theo đề. Chỉ dùng dự đoán LOPO."],
    ["Nhãn vai trò dự đoán", "Muốn nhận predicted_discourse_type để đo macro-F1 của DeBERTa tụt bao nhiêu khi không có nhãn gold; muốn nhận đặc trưng cấp bài (số đoạn, vị trí tương đối, độ dài).", "Đề xuất: gửi nhãn dự đoán (macro-F1 0,675, ngoài mẫu cho 8 đề) và đặc trưng cấp bài. Lưu ý chỉ có cho 8 đề."],
    ["Lấy kết quả hay copy quy trình?", "—", "Copy quy trình. Số của Nhóm 6 (random 80/20, 15 đề) khác chia theo đề (8 đề) nên không dùng được; quy trình dùng lại được và đã chạy lại ở mục 7. Số DeBERTa của họ chỉ làm mốc tham khảo, không so trực tiếp."],
    ["GPU", "Hỏi Nhóm 4 có Colab Pro/GPU để chạy đủ 8 fold DeBERTa không.", "Chưa có GPU; cần trả lời Nhóm 6."],
    ["Ranh giới phần việc", "—", "Nhóm 6: Step 2. Nhóm 4: Step 3, Step 1 phục vụ M3. Hai nhóm trao đổi nhãn vai trò dự đoán và đặc trưng cấp bài."],
])
para("Cần cẩn thận nếu dùng dự đoán hiệu quả đoạn làm đặc trưng chấm điểm: theo Gui (2026), nhãn hiệu quả phần lớn theo độ dài và mức triển khai, nên dễ vòng lại về độ dài. Nếu làm, phải đo lại trên nền M0b và M1 − len.")

# ------------------------------------------------------------------ 10. self-check
doc.add_heading("10. Trả lời các câu tự kiểm tra", 1)
para("Nếu một bài có đủ Claim và Evidence nhưng được viết trong ít đoạn, mô hình hiện tại sẽ chấm thế nào? Nhiều khả năng thấp. Dòng chỉ ranh giới cho thấy mô hình học quy tắc nhiều đoạn là tốt, ít đoạn là yếu; sáu ca ở báo cáo trước (ví dụ AA798BC0E56D, E5C524E8ECB8) có dấu hiệu này. Nhóm chưa tạo bài tổng hợp để kiểm trực tiếp và chưa đối chiếu với rubric.")
para("Ở mức hỏng nhãn nào M2 sẽ không còn hơn M1 + ranh giới? Từ khoảng 20% (bảng 11). Nhóm chưa ghi dự đoán trước khi chạy; kết quả cho thấy lợi thế mất rất sớm, ngay ở 10% hỏng chỉ còn +0,002.")
para("Nếu thêm riêng n_chars vào M0 đã tăng mạnh, M1 − M0 còn là lợi ích ngôn ngữ ngoài độ dài không? Không. Khoảng 86% của M1 − M0a nằm sẵn trong nhóm độ dài; phần còn lại là +0,013.")

# ------------------------------------------------------------------ 11. limits
doc.add_heading("11. Hạn chế và phạm vi kết luận", 1)
bullet("Chỉ 8 đề; nhiều seed không thêm đề độc lập; tập test chính thức cùng đề với train nên chỉ kiểm bài mới trên các đề đó.")
bullet("Ranh giới đoạn là gold; M3 chưa là hệ thống nhận bài thô.")
bullet("Thí nghiệm làm hỏng nhãn dùng một seed Gradient Boosting mỗi lần và cách làm hỏng đồng đều ngẫu nhiên, không giống lỗi thật của bộ nhận vai trò.")
bullet("Δ theo nhóm độ dài là kiểm soát một phần: trong từng nhóm độ dài vẫn thay đổi theo điểm.")
bullet("Step 2: mức tăng phần lớn do chỉnh trọng số lớp; trung bình theo đề chưa tới 0,5; embedding và ngữ cảnh không giúp thêm; precision top 5% khoảng 0,09; chưa đánh giá đầu ra feedback. Embedding dùng một mô hình nhỏ (MiniLM, 384 chiều) và PCA 64 chiều, chưa thử mô hình lớn hơn hay tinh chỉnh.")
bullet("Chưa đối chiếu sáu ca với rubric; chưa kiểm κ = 0,75 (mức đồng thuận người chấm điểm bài ở slide giữa kỳ) là loại nào so với QWK. Mốc 0,70 mà Chen và cộng sự trích từ ETS là một tham chiếu khác, chưa đọc nguồn gốc.")
bullet("Đặc trưng M1 tự cài đặt bằng biểu thức chính quy (43 đặc trưng), chỉ gần với bộ của Yang et al. (2024).")

# ------------------------------------------------------------------ 12. plan + refs
doc.add_heading("12. Kế hoạch tuần tới", 1)
cap("Bảng 18. Công việc và sản phẩm")
table(["Công việc", "Sản phẩm"], [
    ["Lưu lại đầu ra của notebook (file .ipynb trên đĩa hiện chưa có output; kết quả nằm trong results/step2_embed_summary.csv)", "Notebook có đầu ra để nộp"],
    ["Xin Nhóm 6 chạy DeBERTa ở 1 đến 2 fold trên đúng các đề của nhóm mình để biết trần của Step 2 theo cách chia theo đề", "Một con số DeBERTa so được với S3 đến S6"],
    ["Gửi Nhóm 6 danh sách 8 đề, nhãn vai trò dự đoán, đặc trưng cấp bài; xin dự đoán LOPO của họ; trả lời câu hỏi GPU; chốt biên bản", "Biên bản được hai nhóm xác nhận"],
    ["Đối chiếu sáu ca với rubric người chấm; thêm ví dụ bài có đủ Claim, Evidence nhưng ít đoạn", "Mục diễn giải sáu ca được xác nhận hoặc sửa"],
    ["Thêm biến thể ranh giới dự đoán để tiến gần end-to-end", "M3 không dùng ranh giới gold"],
    ["Kiểm κ = 0,75 của người chấm là loại nào; khi làm RQ3, cài đặt conditional disparity ratio và difference của Chen và cộng sự trên dự đoán ngoài mẫu", "Phần so sánh với người chấm chính xác; độ đo công bằng theo cách của bài 2026"],
])
doc.add_heading("13. Tài liệu tham khảo", 1)
for t in [
    "Crossley, S. A. et al. (2024). A large-scale corpus for assessing written argumentation: PERSUADE 2.0. Assessing Writing, 61, 100865. Dữ liệu CC BY-NC-SA 4.0.",
    "Wang, W., Shi, H., Tang, H. & Qin, W. (2026). ArguLens: An Open-Source System for Automated Essay Scoring and Label-Aware Feedback Generation. arXiv:2608.17356.",
    "Gui, Y. (2026). Latent Factors of Discourse Type and Effectiveness in PERSUADE 2.0 for AES. Proceedings of AIME-Con (Coordinated Session Papers), pp. 251–259. NCME. Anthology ID 2026.aimecon-sessions.27.",
    "Keramati, A. & Warschauer, M. (2026). The Order Matters: Sequential Fine-Tuning of LLaMA for Coherent Automated Essay Scoring. arXiv:2606.10327.",
    "Chen, G., Wu, A. D. & Zhang, C. (2026). Assessing fairness in AI-assisted writing scoring: Developing fairness measures to detect predictive bias in automated essay scoring. Assessing Writing, 69, 101066. DOI 10.1016/j.asw.2026.101066. Đã đọc toàn văn (PDF, truy cập mở CC BY-NC-ND).",
    "Ormerod, C. (2025). Automated Essay Scoring Incorporating Annotations from Automated Feedback Systems. arXiv:2505.22771.",
    "Yang, K., Raković, M., Li, Y., Guan, Q., Gašević, D. & Chen, G. (2024). Unveiling the Tapestry of Automated Essay Scoring: A Comprehensive Investigation of Accuracy, Fairness, and Generalizability. AAAI 2024, arXiv:2401.05655.",
    "Nhóm 6, CLC02 (2026). Technical Research Report, Week 9: Empirical Benchmarking, Error Audit, and Methodological Rigor on PERSUADE 2.0 for Argumentative Discourse Effectiveness Assessment. Báo cáo nội bộ lớp.",
]:
    doc.add_paragraph(t, style="List Number")

out = ROOT / "report" / "Group04_Week10_Report.docx"
doc.save(out)
print("saved", out)
