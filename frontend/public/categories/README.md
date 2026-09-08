# Category card images

These are already in place and wired up in
`frontend/src/components/gigs/CategoryStrip.tsx`. Cards crop to cover a
190×132 box, so a roughly 3:2 landscape shot with the subject centered looks
best. Resized to 800px wide, JPEG quality 82 (~60-95KB each, ~720KB total) —
plenty for a card this size.

| Filename              | Category      |
| --------------------- | ------------- |
| `all.jpg`             | All gigs      |
| `academic-help.jpg`   | Academic Help |
| `design.jpg`          | Design        |
| `development.jpg`     | Development   |
| `writing.jpg`         | Writing       |
| `tutoring.jpg`        | Tutoring      |
| `events.jpg`          | Events        |
| `photography.jpg`     | Photography   |
| `others.jpg`          | Other         |

A missing file falls back to a flat violet background under the gradient
overlay — nothing breaks, it just won't have a photo. To replace one, keep it
under ~100KB and roughly 800px wide so the strip stays fast.
