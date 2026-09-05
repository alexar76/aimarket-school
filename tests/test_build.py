"""AIMarket School build contract.

No network: the whole site is generated from lessons.yaml + i18n.yaml, so the
things that used to break silently (stale notebooks, half-translated UI, a
mirror competing with the portal in the index, demo endpoints that no longer
match the nginx bridge) are all checkable offline.

Works in both layouts: monorepo (``school/tests``) and the exported satellite
(``tests`` at the repo root).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

SCHOOL = Path(__file__).resolve().parents[1]
BUILD = SCHOOL / "build.py"
LANGS = ("en", "ru", "es", "fr", "zh")
CANON = "https://edu.modelmarket.dev"

# Endpoints the browser demos call through the same-origin bridge. Kept in sync
# with deploy/nginx/snippets/school-hub-bridge.conf (asserted below).
HUB_PATHS = {
    "/ai-market/v2/search",
    "/ai-market/v2/invoke",
    "/.well-known/ai-market.json",
}


def _lessons() -> list[dict]:
    data = yaml.safe_load((SCHOOL / "lessons.yaml").read_text(encoding="utf-8"))
    return sorted(data["lessons"], key=lambda L: L["order"])


def _i18n() -> dict:
    return yaml.safe_load((SCHOOL / "i18n.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lessons() -> list[dict]:
    return _lessons()


@pytest.fixture(scope="module")
def i18n() -> dict:
    return _i18n()


@pytest.fixture(scope="module")
def builds(tmp_path_factory) -> dict[str, Path]:
    """Run the real builder twice (portal + nested mirror) in a scratch copy."""
    work = tmp_path_factory.mktemp("school-build")
    src = work / "school"
    shutil.copytree(
        SCHOOL,
        src,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    env_common = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    portal_out = work / "portal"
    subprocess.run(
        [sys.executable, str(src / "build.py")],
        check=True,
        capture_output=True,
        text=True,
        env={
            **env_common,
            "SEO_BASE_URL": CANON,
            "SCHOOL_MOUNT": "",
            "SCHOOL_OUT": str(portal_out),
            "LEARN_BASE": "https://modeldev.modelmarket.dev",
        },
    )

    mirror_out = work / "mirror"
    subprocess.run(
        [sys.executable, str(src / "build.py")],
        check=True,
        capture_output=True,
        text=True,
        env={**env_common, "SCHOOL_OUT": str(mirror_out)},
    )
    return {"portal": portal_out, "mirror": mirror_out, "src": src}


# ── content contracts ────────────────────────────────────────────────────────


def test_ten_lessons_with_unique_ids_and_orders(lessons):
    assert len(lessons) == 10
    assert len({L["id"] for L in lessons}) == 10
    assert [L["order"] for L in lessons] == list(range(1, 11))


def test_lesson_fields_present(lessons):
    for L in lessons:
        for key in ("id", "title", "punch", "minutes", "academy", "academy_label", "demo"):
            assert L.get(key), f"{L['id']} missing {key}"
        assert L["colab_cells"], f"{L['id']} has no notebook cells"
        assert len(L["short_beats"]) == 3, f"{L['id']} needs 3 reel beats"
        assert L["academy"].endswith("-course"), L["academy"]


def test_every_demo_kind_is_implemented(lessons):
    """A lesson pointing at a missing branch would render 'Unknown demo'."""
    js = BUILD.read_text(encoding="utf-8")
    for L in lessons:
        kind = L["demo"]
        assert f"'{kind}'" in js, f"schoolDemo has no branch for {kind}"


def test_i18n_ui_is_complete(i18n):
    ui = i18n["ui"]
    en = set(ui["en"])
    for lang in LANGS:
        assert set(ui[lang]) == en, f"{lang} UI keys drift from EN"


def test_i18n_covers_every_lesson_in_every_language(lessons, i18n):
    blocks = i18n["lessons"]
    assert set(blocks) == {L["id"] for L in lessons}
    for L in lessons:
        for lang in LANGS:
            block = blocks[L["id"]].get(lang)
            assert block, f"{L['id']}/{lang} missing"
            for key in ("title", "punch", "academy_label", "demo_label", "short_beats"):
                assert block.get(key), f"{L['id']}/{lang} missing {key}"
            assert len(block["short_beats"]) == 3


def test_lesson_04_does_not_promise_a_402_the_hub_may_not_send(i18n, lessons):
    """The live hub serves free-trial invokes with 200 — copy must stay true.

    Pinned in every language and in the notebook, not just EN: a $0.02 Platon
    capability answered 200 with output when invoked without a channel.
    """
    block = i18n["lessons"]["ai-pays-ai"]
    for lang in LANGS:
        loc = block[lang]
        assert "402" not in loc["demo_label"], lang
        # The punch may mention 402 as an outcome, never as a promise.
        for promise in ("real HTTP 402", "Живой HTTP 402", "HTTP 402 real",
                        "vrai HTTP 402", "真实 HTTP 402"):
            assert promise not in loc["punch"], (lang, promise)
    lesson = next(L for L in lessons if L["id"] == "ai-pays-ai")
    cells = "\n".join(lesson["colab_cells"])
    # The notebook printed nothing at all when the invoke succeeded.
    assert "urllib.error" in cells
    assert "r.status" in cells or "print('status'" in cells
    nb = json.loads((SCHOOL / "notebooks" / "ai-pays-ai.ipynb").read_text(encoding="utf-8"))
    code = "".join(
        "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        for c in nb["cells"]
        if c["cell_type"] == "code"
    )
    assert "except urllib.error.HTTPError" in code
    assert "served without a channel" in code


# ── notebooks ────────────────────────────────────────────────────────────────


def test_committed_notebooks_match_a_fresh_build(builds, lessons):
    fresh = builds["src"] / "notebooks"
    for L in lessons:
        name = f"{L['id']}.ipynb"
        assert (fresh / name).read_text(encoding="utf-8") == (
            SCHOOL / "notebooks" / name
        ).read_text(encoding="utf-8"), f"{name} is stale — re-run school/build.py"


def test_notebooks_are_valid_and_reference_the_academy(lessons):
    for L in lessons:
        nb = json.loads((SCHOOL / "notebooks" / f"{L['id']}.ipynb").read_text(encoding="utf-8"))
        assert nb["nbformat"] == 4
        kinds = [c["cell_type"] for c in nb["cells"]]
        assert kinds[0] == "markdown"
        assert kinds[-1] == "markdown"
        assert kinds.count("code") >= 1
        assert L["academy"] in nb["cells"][0]["source"][0]
        code_chars = sum(
            len("".join(c["source"]) if isinstance(c["source"], list) else c["source"])
            for c in nb["cells"]
            if c["cell_type"] == "code"
        )
        assert code_chars >= 400, f"{L['id']} notebook too thin ({code_chars} chars)"
        assert any(
            ("".join(c["source"]) if isinstance(c["source"], list) else c["source"]).strip()
            for c in nb["cells"]
            if c["cell_type"] == "code"
        )

# ── generated site ───────────────────────────────────────────────────────────


def test_portal_and_mirror_have_every_page(builds, lessons):
    for kind, root in (("portal", builds["portal"]), ("mirror", builds["mirror"])):
        base = root if kind == "portal" else root / "school"
        assert (base / "index.html").is_file()
        for lang in LANGS[1:]:
            sub = root / lang if kind == "portal" else root / lang / "school"
            assert (sub / "index.html").is_file(), f"{kind}/{lang} portal missing"
            for L in lessons:
                assert (sub / L["id"] / "index.html").is_file(), f"{kind}/{lang}/{L['id']}"
        for L in lessons:
            assert (base / L["id"] / "index.html").is_file()


def test_mirror_canonicalizes_to_the_portal(builds, lessons):
    """Both hosts serve the same lessons — only the portal may be indexed."""
    page = (builds["mirror"] / "school" / lessons[0]["id"] / "index.html").read_text(
        encoding="utf-8"
    )
    assert f'<link rel="canonical" href="{CANON}/{lessons[0]["id"]}/" />' in page
    ru = (builds["mirror"] / "ru" / "school" / lessons[0]["id"] / "index.html").read_text(
        encoding="utf-8"
    )
    assert f'<link rel="canonical" href="{CANON}/ru/{lessons[0]["id"]}/" />' in ru


def test_hreflang_is_complete_and_canonical(builds):
    page = (builds["portal"] / "index.html").read_text(encoding="utf-8")
    for lang in LANGS:
        expect = f'hreflang="{lang}" href="{CANON}{"" if lang == "en" else "/" + lang}/"'
        assert expect in page, expect
    assert f'hreflang="x-default" href="{CANON}/"' in page


def test_social_preview_images_ship_and_resolve(builds, lessons):
    for kind, root, base_url, prefix in (
        ("portal", builds["portal"], CANON, ""),
        ("mirror", builds["mirror"] / "school", "https://modeldev.modelmarket.dev", "/school"),
    ):
        og_dir = root / "og"
        assert (og_dir / "portal.png").is_file()
        portal = (root / "index.html").read_text(encoding="utf-8")
        assert f'og:image" content="{base_url}{prefix}/og/portal.png"' in portal
        assert 'name="twitter:card" content="summary_large_image"' in portal
        for L in lessons:
            assert (og_dir / f"{L['id']}.png").is_file(), f"{kind} og/{L['id']}.png"
            page = (root / L["id"] / "index.html").read_text(encoding="utf-8")
            assert f'og:image" content="{base_url}{prefix}/og/{L["id"]}.png"' in page


def test_only_the_canonical_site_ships_robots_and_sitemap(builds, lessons):
    portal = builds["portal"]
    mirror = builds["mirror"] / "school"
    assert (portal / "robots.txt").is_file()
    assert (portal / "sitemap.xml").is_file()
    assert not (mirror / "robots.txt").exists()
    assert not (mirror / "sitemap.xml").exists()

    robots = (portal / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {CANON}/sitemap.xml" in robots

    sitemap = (portal / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    assert len(locs) == (len(lessons) + 1) * len(LANGS)
    assert all(u.startswith(CANON) for u in locs)
    assert f"{CANON}/{lessons[0]['id']}/" in locs
    assert "lastmod" not in sitemap  # keeps rebuilds byte-stable


def test_pages_carry_working_demo_and_deep_links(builds, lessons):
    page = (builds["portal"] / lessons[0]["id"] / "index.html").read_text(encoding="utf-8")
    assert 'id="run-demo"' in page
    assert "colab.research.google.com" in page
    assert "alexar76.github.io/aimarket-courses" in page
    assert "__HUB_PUBLIC__" not in page  # placeholders must be substituted
    assert "__HUB_PROXY__" not in page
    assert 'window.SCHOOL_I18N = {' in page


def test_demo_prefers_the_same_origin_bridge(builds):
    page = (builds["portal"] / "agents-in-5-min" / "index.html").read_text(encoding="utf-8")
    assert 'const HUB_PROXY = "/hub"' in page
    assert 'const HUB = "https://modelmarket.dev"' in page
    assert "hubFetch(" in page


def test_aria_current_marks_only_the_current_page(builds, lessons):
    portal = (builds["portal"] / "index.html").read_text(encoding="utf-8")
    lesson = (builds["portal"] / lessons[0]["id"] / "index.html").read_text(encoding="utf-8")
    # portal: nav "Lessons" + the active language; lesson page: language only.
    assert portal.count('aria-current="page"') == 2
    assert lesson.count('aria-current="page"') == 1


def test_rebuild_keeps_hand_added_site_files(builds, lessons):
    """The portal cleanup must not wipe CNAME / extra assets."""
    portal = builds["portal"]
    (portal / "CNAME").write_text("edu.modelmarket.dev\n", encoding="utf-8")
    extra = portal / "assets"
    extra.mkdir(exist_ok=True)
    (extra / "keep.txt").write_text("keep me", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(builds["src"] / "build.py")],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SEO_BASE_URL": CANON,
            "SCHOOL_MOUNT": "",
            "SCHOOL_OUT": str(portal),
            "LEARN_BASE": "https://modeldev.modelmarket.dev",
        },
    )
    assert (portal / "CNAME").is_file()
    assert (extra / "keep.txt").is_file()
    assert (portal / "index.html").is_file()
    assert (portal / lessons[0]["id"] / "index.html").is_file()


# ── deploy contract ──────────────────────────────────────────────────────────


def test_nginx_bridge_covers_every_endpoint_the_demos_call():
    """Monorepo-only: the bridge and DEMO_JS must not drift apart."""
    snippet = SCHOOL.parent / "deploy" / "nginx" / "snippets" / "school-hub-bridge.conf"
    if not snippet.is_file():
        pytest.skip("satellite export — nginx snippet lives in the monorepo")
    conf = snippet.read_text(encoding="utf-8")
    js = BUILD.read_text(encoding="utf-8")
    for path in HUB_PATHS:
        assert f"location = /hub{path}" in conf, f"bridge misses {path}"
        assert path in js, f"DEMO_JS no longer calls {path}"
    assert "location ^~ /hub/ {" in conf and "return 403" in conf


def test_hub_rate_limit_zone_is_declared_exactly_once():
    """Two vhosts declaring zone=school_hub make nginx refuse to start."""
    nginx = SCHOOL.parent / "deploy" / "nginx"
    if not nginx.is_dir():
        pytest.skip("satellite export — nginx config lives in the monorepo")
    declarations = [
        p.relative_to(nginx).as_posix()
        for p in sorted(nginx.rglob("*.conf"))
        if "limit_req_zone" in p.read_text(encoding="utf-8")
        and "zone=school_hub" in p.read_text(encoding="utf-8")
    ]
    assert declarations == ["snippets/school-hub-zone.conf"], declarations


def test_rebuild_removes_a_renamed_lessons_stale_page(builds):
    """A page whose lesson was renamed must stop serving at its old URL.

    It self-canonicalizes to a live URL, so a leftover directory keeps competing
    in the index forever.
    """
    portal = builds["portal"]
    stale = portal / "old-lesson-slug"
    stale.mkdir(exist_ok=True)
    (stale / "index.html").write_text("<h1>stale</h1>", encoding="utf-8")

    manifest = portal / ".school-build.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["entries"] = sorted(set(data["entries"]) | {"old-lesson-slug"})
    manifest.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")

    subprocess.run(
        [sys.executable, str(builds["src"] / "build.py")],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SEO_BASE_URL": CANON,
            "SCHOOL_MOUNT": "",
            "SCHOOL_OUT": str(portal),
            "LEARN_BASE": "https://modeldev.modelmarket.dev",
        },
    )
    assert not stale.exists(), "orphaned lesson page survived the rebuild"
    assert (portal / "index.html").is_file()
