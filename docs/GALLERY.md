# School README gallery

Stills for [README.md](../README.md) — cosmic portal hero + one reel frame per lesson.

## Regenerate

From monorepo root (needs Playwright Chromium):

```bash
python3 school/build.py   # refresh ecosystem-landing/school/
python3 school/scripts/capture_readme_gallery.py
```

Live portal instead of local landing:

```bash
SCHOOL_BASE_URL=https://edu.modelmarket.dev python3 school/scripts/capture_readme_gallery.py
```

Outputs:

- `docs/recordings/school-portal-hero.png`
- `docs/screenshots/{lesson-id}.png`
