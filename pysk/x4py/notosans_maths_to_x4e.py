#!/usr/bin/env fontforge
# -*- coding: utf-8 -*-
# fine_tune_by_claude
"""
notosans_maths_to_x4e.py

Build xfont/notosfd/x4e.sfd

  * base font  : notosfd/x4i26/x4e26.sfd   (xskii4 / 4finger maths based)
  * symbol src : pysk/notopy/NotoSansMath-Regular.ttf
  * result     : notosfd/x4e.sfd

What it does
------------
xskii4 supports only small case a-z and snake_case coding, so the capital
slots G-Z (0x47-0x5A, exactly 20 slots) are unused by the encoding.
This script copies the 20 most useful programming / logic / maths symbols
from NotoSansMath-Regular.ttf and pastes them into those 20 slots.

        slot  symbol  U+      meaning in code
        ----  ------  ------  -----------------------------
         G     ≠      2260    not equal            (!=)
         H     ≤      2264    less or equal        (<=)
         I     ≥      2265    greater or equal     (>=)
         J     ≈      2248    approximately equal
         K     ≡      2261    identical / equivalent (===)
         L     ←      2190    assignment / left arrow (<-)
         M     →      2192    returns / maps to    (->)
         N     ⇒      21D2    implies / lambda arrow (=>)
         O     ∧      2227    logical and          (&&)
         P     ∨      2228    logical or           (||)
         Q     ¬      00AC    logical not          (!)
         R     ⊕      2295    xor / direct sum     (^)
         S     ∈      2208    membership           (in)
         T     ∉      2209    non-membership       (not in)
         U     ∅      2205    empty set / none / null
         V     ∞      221E    infinity
         W     λ      03BB    lambda
         X     √      221A    square root
         Y     ×      00D7    multiply             (*)
         Z     ÷      00F7    divide               (/)

Edit the SYMBOLS list below to swap any symbol; the only rule is that the list
has to stay inside the G-Z slot range (max 20 entries).

Only glyph outlines are copied. Glyph NAMES and unicode slots of the base font
(G, H ... Z) are kept, so anything else that refers to these slots by name keeps
working. Capital letter glyphs that used to sit in G-Z are replaced.

run (from anywhere):
    fontforge -script pysk/x4py/notosans_maths_to_x4e.py
or
    python3 pysk/x4py/notosans_maths_to_x4e.py        (needs python3-fontforge)

optional arguments:
    --base  PATH   base sfd   (default notosfd/x4i26/x4e26.sfd)
    --noto  PATH   math ttf   (default pysk/notopy/NotoSansMath-Regular.ttf)
    --out   PATH   output sfd (default notosfd/x4e.sfd)
"""

import argparse
import logging
import sys
from pathlib import Path

import fontforge

# --------------------------------------------------------------------------- #
# paths  (same convention as pysk/notopy/noto_copy.py : repo root = parents[2])
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "notosfd" / "x4i26" / "x4e26.sfd"
DEFAULT_NOTO = ROOT / "pysk" / "notopy" / "NotoSansMath-Regular.ttf"
DEFAULT_OUT = ROOT / "notosfd" / "x4e.sfd"
LOG_DIR = ROOT / "logs"
LOG_FILE = LOG_DIR / "notosans_maths_to_x4e.log"

# destination range : capital G .. capital Z  = 0x47 .. 0x5A  = 20 slots
SLOT_FIRST = ord("G")
SLOT_LAST = ord("Z")

# (destination ascii char, NotoSansMath unicode codepoint, description)
SYMBOLS = [
    ("G", 0x2260, "not equal"),
    ("H", 0x2264, "less than or equal"),
    ("I", 0x2265, "greater than or equal"),
    ("J", 0x2248, "approximately equal"),
    ("K", 0x2261, "identical / equivalent"),
    ("L", 0x2190, "left arrow (assign)"),
    ("M", 0x2192, "right arrow (returns / maps to)"),
    ("N", 0x21D2, "implies / lambda arrow"),
    ("O", 0x2227, "logical and"),
    ("P", 0x2228, "logical or"),
    ("Q", 0x00AC, "logical not"),
    ("R", 0x2295, "xor / circled plus"),
    ("S", 0x2208, "element of (in)"),
    ("T", 0x2209, "not element of (not in)"),
    ("U", 0x2205, "empty set (none / null)"),
    ("V", 0x221E, "infinity"),
    ("W", 0x03BB, "lambda"),
    ("X", 0x221A, "square root"),
    ("Y", 0x00D7, "multiplication"),
    ("Z", 0x00F7, "division"),
]

log = logging.getLogger("notosans_maths_to_x4e")


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


def validate_symbols():
    """The symbol table must fit the G-Z range, once per slot."""
    seen = set()
    for ch, cp, _ in SYMBOLS:
        if len(ch) != 1 or not (SLOT_FIRST <= ord(ch) <= SLOT_LAST):
            raise ValueError(f"slot '{ch}' is outside G-Z")
        if ch in seen:
            raise ValueError(f"slot '{ch}' used twice")
        seen.add(ch)


def get_or_create_slot(font, cp, name):
    """Return the glyph at unicode slot cp, creating it if the slot is empty."""
    if cp in font:
        return font[cp]
    return font.createChar(cp, name)


def copy_symbol(src, dst, src_cp, dst_ch):
    """Copy one glyph from the math ttf to the ascii slot dst_ch in dst."""
    dst_cp = ord(dst_ch)

    if src_cp not in src:
        log.warning(f"  '{dst_ch}' U+{src_cp:04X} not found in {src.fontname}")
        return False
    src_g = src[src_cp]
    if not src_g.isWorthOutputting():
        log.warning(f"  '{dst_ch}' U+{src_cp:04X} exists but is empty")
        return False

    dst_g = get_or_create_slot(dst, dst_cp, dst_ch)
    dst_g.clear()  # also drops old references (e.g. G used to reference 'period')

    src.selection.select(("unicode",), src_cp)
    src.copy()
    dst.selection.select(("unicode",), dst_cp)
    dst.paste()

    dst_g = dst[dst_cp]
    dst_g.width = src_g.width  # copy keeps outlines, force the advance too
    dst_g.unlinkRef()          # paste may leave a reference, make real outlines
    return True


def main():
    ap = argparse.ArgumentParser(description="NotoSansMath -> x4e.sfd (slots G-Z)")
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    ap.add_argument("--noto", type=Path, default=DEFAULT_NOTO)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    setup_logging()
    validate_symbols()

    for p in (args.base, args.noto):
        if not p.exists():
            log.error(f"missing input: {p}")
            return 1

    log.info(f"base : {args.base}")
    log.info(f"noto : {args.noto}")
    log.info(f"out  : {args.out}")

    base = fontforge.open(str(args.base))
    noto = fontforge.open(str(args.noto))

    if base.em != noto.em:
        # glyphs are copied 1:1, so scale the source if the em sizes differ
        log.warning(f"em differs (base {base.em}, noto {noto.em}); scaling noto")
        noto.em = base.em

    copied = failed = 0
    for dst_ch, src_cp, desc in SYMBOLS:
        ok = copy_symbol(noto, base, src_cp, dst_ch)
        if ok:
            copied += 1
            log.info(f"  {dst_ch}  <-  U+{src_cp:04X}  {chr(src_cp)}  {desc}")
        else:
            failed += 1

    # naming : this is a new font, not x4e26
    base.fontname = "XngloEnglish-x4e"
    base.familyname = "Xnglo English x4e"
    base.fullname = "Xnglo English x4e Regular"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    base.save(str(args.out))
    log.info(f"saved {args.out}  ({copied} copied, {failed} failed)")

    noto.close()
    base.close()
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
