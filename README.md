# AFP – Argument-Structure-Based Feedback Prioritisation (Group 04, CLC02)

Data: `../persuade_corpus_2.0_train.csv` (PERSUADE 2.0, CC BY-NC-SA 4.0). The test set is not touched until the end.

```
AFP_Project/
  src/common.py                paths, QWK/MAE
  src/features.py              ~45 hand-made linguistic features (M1)
  src/01_prepare_data.py       essay table + segment table -> data/processed
  src/02_step3_baselines.py    M0, M1; leave-one-prompt-out; ELL gap; uncertainty; duplication test
  src/03_steps12_baselines.py  Step 1 (role) and Step 2 (effectiveness) baselines
  src/04_make_report.py        builds report/Group04_Week8_Report.docx
  results/  figs/  report/
```

Run in order from `src/` (set `PYTHONIOENCODING=utf-8` on Windows):

```
python 01_prepare_data.py
python 02_step3_baselines.py
python 03_steps12_baselines.py
python 04_make_report.py
```
