# Stats

## Sources

- **train / valid**: 710 inbound replies from 12 Nexus projects (not 98), 2026-10-20 to 2026-10-29, labeled by the prod v2 labeler (gpt-5.6-luna). No human-confirmed labels in this window.
- **eval**: 68 replies from project 98 since 2026-10-19 with manual gold (`gold.json` of the Nexus reply-status eval). No overlap in projects with train.

## Counts

| Split | N |
|---|---|
| train | 623 |
| valid | 85 (13.6% of train) |
| eval | 68 |
| eval2 | 149 (projects not in train) |

Duplicates (normalized `user`): 0 dropped, 0 left in train.

## kind (input type)

| kind | train | valid | eval |
|---|---|---|---|
| contact_shared (email or phone somewhere in the thread) | 272 (43.7%) | 42 | 47 |
| single_reply (first reply from the prospect) | 205 (32.9%) | 31 | 17 |
| multi_turn (prospect replied before) | 146 (23.4%) | 12 | 4 |

No kind is above 60% of train.

## assistant (labels)

| label | train | valid | eval |
|---|---|---|---|
| no_change | 227 | 34 | 6 |
| positive | 142 | 20 | 2 |
| mql | 111 | 14 | 32 |
| not_ta | 74 | 6 | 16 |
| rejection | 45 | 4 | 9 |
| sql | 24 | 6 | 3 |
| meeting_held | 0 | 1 | 0 |

The distribution differs between train and eval: eval (project 98) is mostly "best email?" replies. `sql` is rare, and `meeting_held` has no train examples at all: every v2 `meeting_held` in train turned out to be wrong (a scheduled time, a phone, or small talk). The tuned model will not learn this class.

## Test label distribution (after the 2026-10-29 fixes)

| label | eval | eval2 |
|---|---|---|
| no_change | 22 | 74 |
| positive | 2 | 39 |
| mql | 23 | 14 |
| not_ta | 12 | 10 |
| rejection | 8 | 10 |
| sql | 1 | 2 |

eval: 16 gold labels rewritten from cumulative status to "change from the last reply" (`eval-relabel.json`).

## Leak check

- `id` overlap eval vs train/valid: 0.
- Normalized `user` overlap eval vs train/valid: 0; eval2 vs train/valid: 0; eval vs eval2: 0; train vs valid: 0.
- One `system` across all files; every `assistant` matches the regex.
- Length: user is capped at an estimated 380 tokens (target reply kept, older messages dropped first); max system+user+assistant 1527 chars.

## PII

- Contact names, employers and brands are replaced with fake names consistently within a thread. Other people and organizations in the text were found by an LLM entity pass (gpt-5.6-luna) and replaced the same way. Messenger names (WhatsApp, Zoom, …) are kept.
- Emails → `@example.com`; the local part keeps whose address it is (the fake name of that person). Phones keep their shape with random digits. URLs → `https://example.com/link`.
- Distinct people in one thread get distinct fake names (before the fix, the sender and the prospect sometimes shared one, which broke "own email vs colleague"). Remaining greeting collisions: 1 train row.
- Check: no original contact first or last name left in any thread; no email outside `example.com`; no real URLs.
- Not covered: rare names the entity pass missed, and city / event names (kept on purpose).

## Labels: how train / valid were corrected

The prod v2 labels were only a starting point. Final labels:

1. **Human audit, 130 train rows** (`audit-30.json`, `audit-100.json`): 44 fixed, the rest kept.
2. **Judge relabel of all 710 train + valid rows** with claude-opus-5-5, on the same anonymized, clipped input the student sees, with the label rules from `task.md` written out (`judge_day07.py` in the Nexus eval folder). On the 130 audited rows the judge matched the human label in 102 cases, v2 in 86.
3. **Where v2 and the judge agreed** (359 unaudited rows), that label was kept.
4. **Where they disagreed** (221 unaudited rows), I reviewed each row and picked the label: judge in 187, v2 in 16, a third label in 16, 2 dropped as ambiguous after anonymization. Every decision is in `review-disagreements.json` (`v2`, `judge`, `final`).

So 349 of the 708 kept train + valid rows were looked at by a human; the remaining 359 carry a label that two different models agreed on.

Label conventions used throughout (also the main v2 errors):
- greetings, "sure", "yes, send it" without a contact → `positive`;
- own email → `mql`; an email of someone else → `not_ta`; asking for OUR email or phone → `mql`;
- an exact date and time, or an own phone → `sql`; `meeting_held` only when a meeting already happened;
- the prospect pitching their own product, event or speaking slot, small talk, "got it / received", a repeat of an earlier message, or a step the thread already reached → `no_change`;
- "not interested / no need" from the right person → `rejection`; left the company, not their area, forwarding to another team → `not_ta`.

Remaining risk: the label is the change relative to the whole thread, and long threads are clipped, so a few `no_change` / `positive` calls depend on messages the model does not see.
