# Dropped teacher labels

Train inputs: 623
Kept: 232
Dropped: 391

## Reasons

- `disagree_gold`: 390
- `no_enum`: 1

## Teacher vs gold (dropped disagreements)

- gold `positive` -> teacher `no_change`: 87
- gold `no_change` -> teacher `mql`: 64
- gold `not_ta` -> teacher `rejection`: 28
- gold `no_change` -> teacher `sql`: 25
- gold `no_change` -> teacher `positive`: 21
- gold `no_change` -> teacher `rejection`: 20
- gold `positive` -> teacher `mql`: 18
- gold `mql` -> teacher `not_ta`: 16
- gold `no_change` -> teacher `meeting_held`: 15
- gold `mql` -> teacher `no_change`: 15
- gold `no_change` -> teacher `not_ta`: 14
- gold `positive` -> teacher `not_ta`: 11
- gold `not_ta` -> teacher `no_change`: 9
- gold `mql` -> teacher `sql`: 8
- gold `mql` -> teacher `meeting_held`: 5
- gold `positive` -> teacher `rejection`: 5
- gold `positive` -> teacher `sql`: 5
- gold `sql` -> teacher `no_change`: 4
- gold `rejection` -> teacher `no_change`: 4
- gold `mql` -> teacher `rejection`: 2

## Sample (up to 10)

- `tr-001` reason=disagree_gold gold=['mql'] pred=meeting_held raw='meeting_held'
- `tr-002` reason=disagree_gold gold=['not_ta'] pred=rejection raw='rejection'
- `tr-003` reason=disagree_gold gold=['no_change'] pred=rejection raw='rejection'
- `tr-004` reason=disagree_gold gold=['positive'] pred=no_change raw='no_change'
- `tr-007` reason=disagree_gold gold=['no_change'] pred=meeting_held raw='meeting_held'
- `tr-008` reason=disagree_gold gold=['no_change'] pred=mql raw='mql'
- `tr-010` reason=disagree_gold gold=['no_change'] pred=not_ta raw='not_ta'
- `tr-013` reason=disagree_gold gold=['no_change'] pred=positive raw='positive'
- `tr-016` reason=disagree_gold gold=['no_change'] pred=not_ta raw='not_ta'
- `tr-017` reason=disagree_gold gold=['no_change'] pred=positive raw='positive'
