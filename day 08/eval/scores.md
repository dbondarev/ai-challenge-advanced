# Day 8 eval scores

## Format (enum)

| Mode | Hits | Acc | |
|---|---|---|---|
| `base` no system | 0/68 | 0.000 |  |
| `base` + system | 34/68 | 0.500 |  |
| `day7` + system | 47/68 | 0.691 |  |
| `day8 best` + system | 41/68 | 0.603 |  |
| `day8 last` + system | 43/68 | 0.632 |  |

## Facts

| Mode | Hits | Acc | split |
|---|---|---|---|
| `base_facts` | 0/12 | 0.000 | verbatim 0/6; paraphrase 0/6 |
| `base_facts_prompt` | 12/12 | 1.000 | verbatim 6/6; paraphrase 6/6 |
| `best_facts` | 9/12 | 0.750 | verbatim 6/6; paraphrase 3/6 |
| `last_facts` | 7/12 | 0.583 | verbatim 5/6; paraphrase 2/6 |

## Style

| Mode | Hits | Acc | |
|---|---|---|---|
| `base` | 0/8 | 0.000 |  |
| `base` + style system | 5/8 | 0.625 |  |
| `day8 best` | 7/8 | 0.875 |  |
| `day8 last` | 8/8 | 1.000 |  |

## OOD

| Mode | Hits | Acc | enum collapse |
|---|---|---|---|
| `base_ood` | 9/9 | 1.000 | collapse 0/9 |
| `day7_ood` | 8/9 | 0.889 | collapse 0/9 |
| `best_ood` | 8/9 | 0.889 | collapse 0/9 |
| `last_ood` | 8/9 | 0.889 | collapse 0/9 |
