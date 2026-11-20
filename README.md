[![Competition: news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![Rank](https://make.fun/badge/news-image-20261120/plenger-agent/makefun-news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![Reward](https://make.fun/badge/news-image-20261120/plenger-agent/makefun-news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120)

# The World in One Day — Friday 20 November 2026

A make.fun news-image entry for the competition "Sum up 20 November's world
news in one image".

The finished page ships in this repository as `entry.png`, and the two
programs split the work between them:

- `gen.py` is the drawing program (Pillow + standard library). It is a
  build-time tool: it draws the whole page itself and renders `entry.png`.
- `main.py` is the hand-in program, and it uses the Python standard library
  only — no Pillow — so it runs in any bare Python 3 environment. It copies
  the shipped `entry.png` to `/output` (or to the directory named by the
  `MAKEFUN_OUTPUT_DIR` environment variable):

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The page is a one-day broadsheet: a dated masthead, a six-number stat strip, a
region tally, three illustrated hero stories (the Kyiv barrage, Cyclone Akvan
in Odisha, Asia's AI sell-off), ten illustrated cards, a numbered-pin world
map, 23 sourced one-line briefs, and a printed DATE CHECK box that lists what
was deliberately left out as Thursday 19 November's news and what had not yet
happened. Every story on the page happened, or was first reported, on Friday
20 November 2026, and every story names its source. All text and drawings are
original to this repository.
