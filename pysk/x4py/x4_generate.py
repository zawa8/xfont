#!/usr/bin/env fontforge
# -*- coding: utf-8 -*-
"""
x4_generate.py

Generate TTF + WOFF2 from the x4*.sfd fonts (xskii4 / 4finger maths family).

  sfdfinal/x4/x4e.sfd
    -> xnglofonts/ttf/x4/x4e.ttf
    -> xnglofonts/woff2/x4/x4e.woff2

This is the x4 counterpart of pysk/ttfwofpy/p5generate.py. The xi38/xi52
pipeline expects sfdfinal/<family>/<variant>/<name>.sfd, the x4 fonts are
flat (no asc/utf/mono variants), so they get their own small script.

pipeline position (x4):
  pysk/x4py/notosans_maths_to_x4e.py   -> notosfd/x4e.sfd
  (manual review in fontforge)         -> sfdsrc/x4i26/ -> sfdfinal/x4/
  pysk/x4py/x4_generate.py             -> xnglofonts/{ttf,woff2}/x4/

run:
    fontforge -script pysk/x4py/x4_generate.py                 (all sfdfinal/x4/x4*.sfd)
    fontforge -script pysk/x4py/x4_generate.py x4e             (one font, by name)
or
    python3 pysk/x4py/x4_generate.py [name ...]                (needs python3-fontforge)

options:
    --src DIR   folder holding x4*.sfd   (default sfdfinal/x4)
    --ttf DIR   ttf output folder        (default xnglofonts/ttf/x4)
    --woff2 DIR woff2 output folder      (default xnglofonts/woff2/x4)
    --no-woff2  only make ttf
    --no-verify skip the re-open check of the generated files

exit code: 0 all ok, 1 nothing found / bad folder, 2 some fonts failed
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import fontforge

# same convention as the other pysk scripts : repo root = parents[2]
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SRC = ROOT / "sfdfinal" / "x4"
DEFAULT_TTF = ROOT / "xnglofonts" / "ttf" / "x4"
DEFAULT_WOFF2 = ROOT / "xnglofonts" / "woff2" / "x4"
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "x4_generate.log"

log = logging.getLogger("x4_generate")


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s  %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def verify(out_path, expected_codepoints):
    """Re-open a generated font and check that every x4 codepoint survived."""
    chk = fontforge.open(str(out_path))
    try:
        missing = [cp for cp in expected_codepoints if cp not in chk]
    finally:
        chk.close()
    return missing


def process_sfd(sfd_path, ttf_dir, woff2_dir, make_woff2=True, do_verify=True):
    """Generate ttf (+ woff2) from one sfd. Returns True on success."""
    name = sfd_path.stem
    ttf_path = ttf_dir / f"{name}.ttf"
    woff2_path = woff2_dir / f"{name}.woff2"

    try:
        font = fontforge.open(str(sfd_path))
    except Exception as e:  # noqa: BLE001 - fontforge raises plain EnvironmentError
        log.error(f"{name}: cannot open {sfd_path}: {e}")
        return False

    try:
        # every real encoded glyph the source has, to compare after generating
        codepoints = sorted(g.unicode for g in font.glyphs() if g.unicode >= 0)

        ttf_dir.mkdir(parents=True, exist_ok=True)
        font.generate(str(ttf_path))
        log.info(f"{name}: ttf   {_rel(ttf_path)}  ({ttf_path.stat().st_size} bytes)")

        if make_woff2:
            woff2_dir.mkdir(parents=True, exist_ok=True)
            font.generate(str(woff2_path))
            log.info(f"{name}: woff2 {_rel(woff2_path)}  ({woff2_path.stat().st_size} bytes)")
    except Exception as e:  # noqa: BLE001
        log.error(f"{name}: generate failed: {e}")
        return False
    finally:
        font.close()

    if do_verify:
        outputs = [ttf_path] + ([woff2_path] if make_woff2 else [])
        for out in outputs:
            missing = verify(out, codepoints)
            if missing:
                shown = ", ".join(f"U+{c:04X}" for c in missing[:10])
                log.error(f"{name}: {out.suffix} lost {len(missing)} codepoints: {shown}")
                return False
        log.info(f"{name}: verified {len(codepoints)} codepoints in output")

    return True


def _rel(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main():
    ap = argparse.ArgumentParser(description="x4*.sfd -> ttf / woff2")
    ap.add_argument("names", nargs="*", help="font names without .sfd, e.g. x4e (default: all x4*.sfd)")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC)
    ap.add_argument("--ttf", type=Path, default=DEFAULT_TTF)
    ap.add_argument("--woff2", type=Path, default=DEFAULT_WOFF2)
    ap.add_argument("--no-woff2", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()

    setup_logging()
    log.info("=" * 60)
    log.info(f"started {datetime.now():%Y-%m-%d %H:%M:%S}")

    if not args.src.is_dir():
        log.error(f"source folder not found: {args.src}")
        return 1

    if args.names:
        sfd_files = [args.src / f"{n}.sfd" for n in args.names]
        absent = [p for p in sfd_files if not p.exists()]
        if absent:
            for p in absent:
                log.error(f"not found: {p}")
            return 1
    else:
        sfd_files = sorted(args.src.glob("x4*.sfd"))

    if not sfd_files:
        log.error(f"no x4*.sfd in {args.src}")
        return 1

    log.info(f"src  : {args.src}  ({len(sfd_files)} fonts)")
    ok = fail = 0
    for sfd in sfd_files:
        if process_sfd(sfd, args.ttf, args.woff2, not args.no_woff2, not args.no_verify):
            ok += 1
        else:
            fail += 1

    log.info(f"finished: {ok} ok, {fail} failed")
    log.info(f"log: {LOG_FILE}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
