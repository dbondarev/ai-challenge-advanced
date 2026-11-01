# Day 07 task: reply status for a LinkedIn sales thread

## Fill-in block

```
System (repo / service): Nexus outreach, reply-status labeling (apps/api/app/services/outreach_reply_status_label.py)
Raw data source: prod Nexus API, inbound LinkedIn replies since 2026-10-20 with v2 labels (gpt-5.6-luna), 12 projects; eval = project 98, manual gold
Input in one sentence: a LinkedIn thread (OUT = us, IN = prospect), ending with the prospect's latest reply
Output in one sentence: one word, how that reply changes the prospect's status
Correct answer (scoring rule): prediction after normalization is in gold_key
Restrictions (PII, secrets, clients): people, employers / brands, emails, phones, URLs replaced with fakes; no tokens
Three gold examples (user → assistant):
1) OUT: ...What's the best email to send our collection?\nIN (last): sofia.keller@example.com → mql
2) OUT: ...What's easier for you, WhatsApp or email?\nIN: Hi. Sure\nIN (last): +847 49390964 → sql
3) OUT: ...\nIN (last): Thanks for the offer, but this is not my area. Try greta.sato@example.com → not_ta
```

## Task

Given the thread up to and including the prospect's last reply (`IN (last)`), say how that reply
changes the prospect's status in the sales funnel.

## System (one line, all splits)

```
How does the last IN message change the prospect's status in this LinkedIn sales thread? Reply with one word: no_change, rejection, not_ta, positive, mql, sql, meeting_held.
```

## Assistant format

Regex: `^(no_change|rejection|not_ta|positive|mql|sql|meeting_held)$`

| Value | Meaning |
|---|---|
| `no_change` | the reply does not move the status (small talk, already shared, their own pitch to us) |
| `rejection` | refuses our offer, no buying reason |
| `not_ta` | wrong person / left company / not their area / points to a colleague |
| `positive` | polite reply or "maybe later" without a next step |
| `mql` | asks for materials, shares their own email, agrees to meet later without an exact time |
| `sql` | shares their own phone, or locks an exact date and time |
| `meeting_held` | the meeting already happened |

Own email vs a colleague's: the anonymizer keeps the name inside the address consistent with the
person it belongs to, so `greta@example.com` from Greta is "own email" (mql), and from someone else
it is a referral (not_ta).

## Meaning of the label (same in all files)

The label is the **change caused by the last IN message**, not the thread's cumulative status.
An acknowledgement after a step already happened ("got it", "received, thanks", "👍", a signature line,
an email sent after the same person already asked for materials) is `no_change`, even if the thread is
at `mql` or `sql`. Eval gold was rewritten to this meaning on 2026-10-29 (`eval-relabel.json`, 16 rows).

## Test sets

- `eval.jsonl` (68): project 98, mostly "what's the best email?" replies. Manual gold.
- `eval2.jsonl` (149): 7 projects that are not in train (telecom, events, communities, hiring tools,
  conference outreach). Labeled by claude-opus-5-5 and reviewed row by row (`eval2-review.json`,
  17 labels changed, 2 rows dropped). Report both; eval2 is the less biased one.

## Metric

Accuracy: `normalize(prediction) in gold_key`.
Normalization: lowercase, strip whitespace, quotes, backticks and a trailing period; take the first
token matching the regex. No match = wrong.

`gold_key` usually has one value. Some eval rows accept two (for example `["not_ta", "mql"]`, when the
manual gold marked the reply as ambiguous). `assistant` is always the first, preferred value.
