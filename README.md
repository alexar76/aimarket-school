<!-- aicom-mirror-notice -->
> **📖 Read-only mirror.** `aimarket-school` is published from the canonical AI-Factory monorepo.
> **Pull requests are not accepted** — any commit pushed here is overwritten by
> `scripts/mirror_satellites.sh` on the next sync.
> 🐞 Found a bug or have a request? Please **[open an issue](https://github.com/alexar76/aimarket-school/issues)**.

# AIMarket School

Clip-length lessons that on-ramp into the [10 academies](https://alexar76.github.io/aimarket-courses/).

**Live portal:** [edu.modelmarket.dev](https://edu.modelmarket.dev/)  
Locales: `/ru/` · `/es/` · `/fr/` · `/zh/`  
Mirror on ecosystem landing: [modeldev…/school/](https://modeldev.modelmarket.dev/school/)

**GitHub:** [alexar76/aimarket-school](https://github.com/alexar76/aimarket-school)  
**Monorepo path:** `school/` (clip lessons). Academy labs stay in `courses/` → satellite `aimarket-courses`.

**Push:**
```bash
# School satellite → alexar76/aimarket-school
./scripts/mirror_satellites.sh --satellite aimarket-school

# School notebooks also land on factory aicom (Colab path)
./scripts/publish_aicom_factory.sh
# or full pipeline
./scripts/publish_all_repos.sh --factory-only

# Monorepo → Gitea
./scripts/push_gitea_monorepo.sh

# Live edu portal
./scripts/deploy_edu_school.sh --remote my-vps
```

```bash
# Nested under modeldev (/school/)
python3 school/build.py

# Dedicated edu portal (site root)
SEO_BASE_URL=https://edu.modelmarket.dev SCHOOL_MOUNT= SCHOOL_OUT=edu-landing \
  LEARN_BASE=https://modeldev.modelmarket.dev python3 school/build.py

# Deploy edu.modelmarket.dev
./scripts/deploy_edu_school.sh --remote my-vps
```

Copy: `lessons.yaml` (structure + demos) · `i18n.yaml` (EN/RU/ES/FR/ZH).

Each lesson: hype title · autoplay short · live Try-it · Colab · Academy link.

Browser Try-it needs hub `AIMARKET_CORS_ORIGINS` including `https://edu.modelmarket.dev`.
