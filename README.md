<!-- Competition badges are added in this top section by the maintainer. -->

# The World in One Day — Friday 20 November 2026

A make.fun news-image entry for the competition "Sum up 20 November's world
news in one image".

`main.py` is a self-contained Python program (Pillow + standard library) that
draws the whole page itself — no image file is shipped. Run it and it writes
`entry.png` to `/output` (or to the directory named by the
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
