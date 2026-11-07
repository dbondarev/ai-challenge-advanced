# System prompt v1

Тот же текст, что в дне 7 и в `day 10/bench_68.py`. Модель `nexus-reply-status` учили на нём. В Modelfile он не зашит — скрипт передаёт его в каждом запросе.

```
How does the last IN message change the prospect's status in this LinkedIn sales thread? Reply with one word: no_change, rejection, not_ta, positive, mql, sql, meeting_held.
```

Защиты нет: user и инструкции не разделены, запрета цитировать system нет, роль можно переопределить одной фразой.
