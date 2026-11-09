# 🛠️ How this profile works

Everything on the profile page is generated from two small data files, so you never have to touch SVG or HTML by hand.

| File | What it controls |
|---|---|
| `data/profile.json` | Name, typing phrases, terminal lines, intro, focus, education, tech stack, certifications, talks, featured projects, cats |
| `data/guestbook.json` | Guestbook signatures (written by the guestbook bot) |
| `tools/build.py` | Turns the data into `README.md` + every SVG in `assets/` |
| `tools/pixelkit.py` | Pixel font, icons, window chrome, badge generator, cat sprites |
| `tools/sprites/` | Coco, Nemo and Tofu sprite sheets (6 frames × 80 px) |
| `.github/scripts/stats_card.py` | Daily `system_monitor.exe` activity card (public data, built-in token) |
| `.github/scripts/guestbook.py` | Adds a visitor's login to the guestbook (login only, no free text) |
| `.github/workflows/profile.yml` | Rebuilds README on data changes + daily snake & stats → `output` branch |
| `.github/workflows/guestbook.yml` | Signs the guestbook when someone opens a "Guestbook" issue |

## Edit something

1. Change `data/profile.json` (on github.com is fine).
2. Commit to `main`. The **Profile** workflow rebuilds `README.md` and `assets/` for you.

Or locally: `python tools/build.py` (Python 3.9+, no dependencies).

Common edits:

- **Hide a credential** → set `"show": false` on it. Counters (`12 certifications`, `3 issuers`) update automatically.
- **Add your Microsoft Learn transcript link** → set `"verify_url"`.
- **Add your portfolio** → set `"portfolio"`; a portfolio button appears next to LinkedIn.
- **New talk** → add an entry to `"talks"` (the first one is drawn as the talk card).

## First run after uploading

1. Go to **Actions** → enable workflows if GitHub asks.
2. Open **Profile** → **Run workflow**. This creates the `output` branch with the snake and the stats card (until then those two images show as broken).
3. Open **Issues** → check that the "✍️ Sign the guestbook" template appears. Optional: create a `guestbook` label.

## Notes

- Animations are pure CSS/SMIL inside SVG (GitHub strips JavaScript). They respect `prefers-reduced-motion`.
- Light and dark mode are served with `<picture>` + `prefers-color-scheme`.
- External images: skillicons.dev (icons row), komarev.com (visitor counter), GitHub avatars (guestbook). Everything else is self-hosted.
- To remove a guestbook signature, delete it from `data/guestbook.json` and commit.
