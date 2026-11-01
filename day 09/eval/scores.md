# Day 9 eval scores

| Mode | Hits | Acc | Cost |
|---|---|---|---|
| 1.5B + short system (before) | 34/68 | 0.500 | 94 ms/req, vram 3229 MiB |
| 1.5B distilled + short system | 35/68 | 0.515 | 155 ms/req, vram 3339 MiB |
| 7B 4-bit + long spec (teacher) | 40/68 | 0.588 | 302 ms/req, vram 5847 MiB |
