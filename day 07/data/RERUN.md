# Rerun brief for days 7 and 9 (data fixed 2026-10-29)

The data in this folder changed after the first runs. Old scores (69% day 7, 51% day 9) are not
comparable with new ones: retrain and re-evaluate everything that touches the reply-status enum.

## What changed in the data

1. **One label meaning everywhere.** Eval gold mixed cumulative status with "change from the last reply".
   16 eval rows were rewritten (`eval-relabel.json`). In the first run about 7 of the 21 tuned-model errors came from this mismatch.
2. **Fake names.** The sender and the prospect sometimes got the same fake name, so the model could not
   tell "own email" from "colleague's email". Now distinct people in a thread get distinct names; all
   files were re-rendered (labels unchanged).
3. **New test set `eval2.jsonl` (149 rows)** from 7 projects not in train. Report it next to `eval.jsonl`.
4. **`teacher_opus_train.jsonl`**: the same 623 train inputs labeled by claude-opus-5-5, unfiltered.

## Day 7: rerun

- Same base model and QLoRA setup as before; train on `train.jsonl`, validate on `valid.jsonl`.
- Evaluate on the valid set every epoch (or every ~50 steps) and keep the checkpoint with the best valid
  accuracy, not the last one. Day 8 showed valid loss turning up after ~4 epochs.
- `sql` has 24 train rows: oversample them 3× in train (duplicate rows only in the training set).
- Score on `eval.jsonl` and `eval2.jsonl`, per class and per kind, three modes as before
  (base no system, base + system, tuned + system). Base numbers must be rerun too: eval gold changed.
- `meeting_held` has 0 train rows; report it as untrainable, do not count it as a failure of tuning.

## Day 9: rerun

- Teacher = `teacher_opus_train.jsonl` (claude-opus-5-5 labels, no filtering against gold).
- Student = same 1.5B QLoRA as day 7, same hyperparameters, trained on the teacher file.
- Compare on `eval.jsonl` and `eval2.jsonl`: student on teacher labels vs day 7 student on `train.jsonl`
  vs base + system. Teacher accuracy is already scored in `teacher_opus_scores.json`: eval 58/68 (85%),
  eval2 132/149 (89%, an upper bound: eval2 gold started from these labels before human review).
- Caveat to state in the write-up: the final `train.jsonl` labels themselves started from the opus labels
  (91% identical), so day 7 vs day 9 measures the effect of the 9% human corrections, not two independent
  label sources. The day 9 story is "a frontier model labels, a 1.5B learns it, how much transfers", not
  "human vs model labels".

## Day 8

No retrain needed. Optionally rescore the enum part on the new `eval.jsonl` / `eval2.jsonl`.
