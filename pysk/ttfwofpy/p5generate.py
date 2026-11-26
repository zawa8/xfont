#!/usr/bin/env python3
# fine_tune_by_claude
"""
p5generate.py

Generate TTF/WOFF2 from sfdfinal/**/*.sfd -> xnglofonts/

Two layouts are handled:

  variant families (xi38 / xi52):  sfdfinal/<family>/<variant>/<name>.sfd
    sfdfinal/38/asc/xh38asc.sfd
    -> xnglofonts/ttf/38/asc/xh38asc.ttf
    -> xnglofonts/woff2/38/asc/xh38asc.woff2

  flat families (x4, xskii4 4finger maths):  sfdfinal/<family>/<name>.sfd
    sfdfinal/x4/x4e.sfd
    -> xnglofonts/ttf/x4/x4e.ttf
    -> xnglofonts/woff2/x4/x4e.woff2

Run:
    fontforge -lang=py -script pysk/ttfwofpy/p5generate.py            (everything)
    fontforge -lang=py -script pysk/ttfwofpy/p5generate.py x4         (one family)
    fontforge -lang=py -script pysk/ttfwofpy/p5generate.py x4e        (one font)
    python3 pysk/ttfwofpy/p5generate.py x4 --verify                   (needs python3-fontforge)

Optional arguments:
    names         family folder names and/or font names (without .sfd) to build;
                  default = every sfd under sfdfinal
    --no-woff2    only make ttf
    --verify      re-open every generated file and check that all encoded
                  codepoints of the source sfd are still present
                  (off by default, keeps the xi38/xi52 build unchanged)

Exit code: 0 all ok, 1 nothing to do, 2 some fonts failed.
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

import fontforge

script_dir = Path(__file__).parent
pff_root = script_dir.parent.parent

log_dir = pff_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "p5generate.log"

logging.basicConfig(
    filename=str(log_file),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='w'
)
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logging.getLogger('').addHandler(console)

SFDFINAL_DIR = pff_root / "sfdfinal"
TTF_ROOT = pff_root / "xnglofonts" / "ttf"
WOFF2_ROOT = pff_root / "xnglofonts" / "woff2"


def output_dirs(sfd_path):
    """Return (ttf_dir, woff2_dir) for one sfd, from its place under sfdfinal."""
    rel = sfd_path.relative_to(SFDFINAL_DIR)
    parts = rel.parts
    family = parts[0]            # xi38, xi52, x4, ...

    if len(parts) == 2:
        # flat family: sfdfinal/x4/x4e.sfd -> ttf/x4/x4e.ttf
        ttf_dir = TTF_ROOT / family.replace("sfd", "ttf")
        woff2_dir = WOFF2_ROOT / family.replace("sfd", "woff2")
    else:
        # variant family: sfdfinal/38/asc/xh38asc.sfd
        variant = parts[1]       # asc, utf, mono, ...
        ttf_dir = TTF_ROOT / family.replace("sfd", "ttf") / variant
        woff2_dir = WOFF2_ROOT / family.replace("sfd", "woff2") / variant
    return ttf_dir, woff2_dir


def verify_output(out_path, codepoints):
    """Re-open a generated font; return the codepoints that did not survive."""
    chk = fontforge.open(str(out_path))
    try:
        return [cp for cp in codepoints if cp not in chk]
    finally:
        chk.close()


def process_sfd(sfd_path, make_woff2=True, verify=False):
    """Generate TTF/WOFF2 from one SFD file."""
    name = sfd_path.stem  # xh38asc, x4e, ...

    ttf_dir, woff2_dir = output_dirs(sfd_path)
    ttf_dir.mkdir(parents=True, exist_ok=True)
    if make_woff2:
        woff2_dir.mkdir(parents=True, exist_ok=True)

    ttf_path = ttf_dir / f"{name}.ttf"
    woff2_path = woff2_dir / f"{name}.woff2"

    try:
        f = fontforge.open(str(sfd_path))
    except Exception as e:
        logging.error(f"Error opening {sfd_path}: {e}")
        return False

    try:
        codepoints = []
        if verify:
            codepoints = sorted(g.unicode for g in f.glyphs() if g.unicode >= 0)

        f.generate(str(ttf_path))
        logging.info(f"TTF: {ttf_path.relative_to(pff_root)}")
        if make_woff2:
            f.generate(str(woff2_path))
            logging.info(f"WOFF2: {woff2_path.relative_to(pff_root)}")
        f.close()
    except Exception as e:
        logging.error(f"Error generating {sfd_path}: {e}")
        try:
            f.close()
        except:
            pass
        return False

    if verify:
        outputs = [ttf_path] + ([woff2_path] if make_woff2 else [])
        for out in outputs:
            missing = verify_output(out, codepoints)
            if missing:
                shown = ", ".join(f"U+{c:04X}" for c in missing[:10])
                logging.error(f"{name}: {out.suffix} lost {len(missing)} codepoints: {shown}")
                return False
        logging.info(f"{name}: verified {len(codepoints)} codepoints in output")

    return True


def select_sfds(names):
    """All sfd under sfdfinal, or only those whose family folder / stem is in names."""
    sfd_files = sorted(SFDFINAL_DIR.glob("**/*.sfd"))
    if not names:
        return sfd_files
    wanted = set(names)
    return [
        s for s in sfd_files
        if s.stem in wanted or s.relative_to(SFDFINAL_DIR).parts[0] in wanted
    ]


def main():
    ap = argparse.ArgumentParser(description="sfdfinal/**/*.sfd -> ttf / woff2")
    ap.add_argument("names", nargs="*", help="family folders and/or font names to build (default: all)")
    ap.add_argument("--no-woff2", action="store_true", help="only make ttf")
    ap.add_argument("--verify", action="store_true", help="check codepoints in generated files")
    args = ap.parse_args()

    logging.info("=" * 60)
    logging.info(f"Started: {datetime.now()}")

    if not SFDFINAL_DIR.exists():
        print(f"ERROR: {SFDFINAL_DIR} not found")
        return 1

    sfd_files = select_sfds(args.names)
    print(f"Found {len(sfd_files)} .sfd files")
    if not sfd_files:
        if args.names:
            print(f"ERROR: nothing in {SFDFINAL_DIR} matches {args.names}")
        return 1

    success = 0
    fail = 0
    for sfd in sfd_files:
        if process_sfd(sfd, make_woff2=not args.no_woff2, verify=args.verify):
            success += 1
        else:
            fail += 1

    logging.info("=" * 60)
    logging.info(f"Finished: {datetime.now()}")
    logging.info(f"Success: {success}, Fail: {fail}")
    print(f"\nDone! Success: {success}, Fail: {fail}")
    print(f"Logs: {log_file}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
