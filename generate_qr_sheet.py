# -*- coding: utf-8 -*-
"""
generate_qr_sheet.py  —  Python 3.10
=======================================================================
WHAT IT DOES
  1. Reads members.json  (produced by material_details_qr.py in CAD)
  2. Copies members.json into docs/ folder for GitHub Pages
  3. Pushes docs/ to your GitHub repo  (git must be installed)
  4. Generates a print-ready A4 PDF with QR codes
     Each QR encodes:  https://USERNAME.github.io/REPO/member.html?id=PIECEMARK
  5. Opens the PDF automatically

FIRST-TIME SETUP  (do once)
  1. Create a free GitHub account at https://github.com
  2. Create a new public repository (e.g. "qr-materials")
  3. Go to repo Settings → Pages → Source: "main branch /docs folder" → Save
  4. Set GITHUB_USERNAME and GITHUB_REPO below
  5. Run:  git init  /path/to/this/folder
          git remote add origin https://github.com/USERNAME/REPO.git
  6. Run this script — it will commit & push automatically every time

INSTALL
  pip install qrcode[pil] Pillow reportlab

USAGE
  python generate_qr_sheet.py
  python generate_qr_sheet.py path/to/members.json
=======================================================================
"""

import sys
import json
import os
import io
import shutil
import subprocess
from pathlib import Path

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ── CONFIGURE THESE ────────────────────────────────────────────────────────
GITHUB_USERNAME = "vectorshades-hub"
GITHUB_REPO     = "qr-materials"
# ───────────────────────────────────────────────────────────────────────────

# ── Layout ─────────────────────────────────────────────────────────────────
COLS          = 2          # QR cards per row
ROWS_PER_PAGE = 4          # rows per page  →  2×4=8  |  set 3 for 6/page
QR_BOX_SIZE   = 10         # pixels per module
QR_BORDER     = 3          # quiet-zone modules
PIECEMARK_PT  = 9          # font pt for label under QR
# ───────────────────────────────────────────────────────────────────────────

PAGE_W, PAGE_H = A4
MARGIN_H = 14 * mm
MARGIN_V = 14 * mm
HEADER_H =  9 * mm
CELL_W   = (PAGE_W - 2 * MARGIN_H) / COLS
CELL_H   = (PAGE_H - 2 * MARGIN_V - HEADER_H) / ROWS_PER_PAGE

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "docs"


# ── GitHub deployment ───────────────────────────────────────────────────────

def deploy_to_github(json_path):
    """
    Copy members.json into docs/, then git add/commit/push.
    Returns True on success.
    """
    docs_dir = DOCS_DIR
    docs_dir.mkdir(exist_ok=True)

    # Copy members.json into docs/
    dest = docs_dir / "members.json"
    shutil.copy(str(json_path), str(dest))
    print("Copied members.json → docs/members.json")

    # Check that member.html and index.html exist in docs/
    for required in ("member.html", "index.html"):
        if not (docs_dir / required).exists():
            print("WARNING: docs/{} not found — copy it into the docs/ folder".format(required))

    # Git operations
    try:
        repo_dir = str(BASE_DIR)

        # Init if needed
        if not (BASE_DIR / ".git").exists():
            subprocess.run(["git", "init"], cwd=repo_dir, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin",
                 "https://github.com/{}/{}.git".format(GITHUB_USERNAME, GITHUB_REPO)],
                cwd=repo_dir, check=True
            )
            print("Git repo initialised.")

        subprocess.run(["git", "add", "docs/"], cwd=repo_dir, check=True)

        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_dir
        )
        if result.returncode == 0:
            print("No changes to push — members.json already up to date on GitHub.")
            return True

        subprocess.run(
            ["git", "commit", "-m", "Update members.json"],
            cwd=repo_dir, check=True
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=repo_dir, check=True
        )
        print("Pushed to GitHub successfully.")
        return True

    except subprocess.CalledProcessError as e:
        print("Git error: {}".format(e))
        print("Push the docs/ folder to GitHub manually and re-run.")
        return False
    except FileNotFoundError:
        print("Git not found. Install from https://git-scm.com then re-run.")
        return False


# ── QR generation ───────────────────────────────────────────────────────────

def make_qr_reader(url):
    """Generate QR for a URL and return ReportLab ImageReader."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=QR_BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def member_url(piecemark):
    return "https://{}.github.io/{}/member.html?id={}".format(
        GITHUB_USERNAME, GITHUB_REPO, piecemark
    )


# ── PDF cell ────────────────────────────────────────────────────────────────

def draw_cell(c, member, col, row):
    pm  = member.get("piecemark", "N/A")
    url = member_url(pm)

    x0  = MARGIN_H + col * CELL_W
    y0  = PAGE_H - MARGIN_V - HEADER_H - (row + 1) * CELL_H
    pad = 3 * mm

    # Card border
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.5)
    c.roundRect(x0 + pad, y0 + pad,
                CELL_W - 2 * pad, CELL_H - 2 * pad,
                radius=2 * mm, stroke=1, fill=0)

    # Piecemark label strip at bottom
    label_strip = PIECEMARK_PT * 2.2

    # QR fills remaining space — keep square
    qr_max  = CELL_H - 2 * pad - label_strip - 2 * mm
    qr_size = min(qr_max, CELL_W - 2 * pad - 4 * mm)

    qr_x = x0 + (CELL_W - qr_size) / 2
    qr_y = y0 + pad + label_strip          # above label

    c.drawImage(make_qr_reader(url),
                qr_x, qr_y,
                width=qr_size, height=qr_size,
                preserveAspectRatio=True)

    # Piecemark — centred directly below QR
    c.setFont("Helvetica-Bold", PIECEMARK_PT)
    c.setFillColor(colors.black)
    label_y = y0 + pad + (label_strip - PIECEMARK_PT) / 2
    c.drawCentredString(x0 + CELL_W / 2, label_y, pm)


# ── PDF build ───────────────────────────────────────────────────────────────

def generate_pdf(members, output_path):
    c           = canvas.Canvas(str(output_path), pagesize=A4)
    per_page    = COLS * ROWS_PER_PAGE
    total_pages = (len(members) + per_page - 1) // per_page

    c.setTitle("Material QR Codes")

    for page_idx in range(0, len(members), per_page):
        page_members = members[page_idx: page_idx + per_page]
        page_num     = page_idx // per_page + 1

        print("  Page {}/{}".format(page_num, total_pages))

        # Header
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.HexColor("#1a4e79"))
        c.drawString(MARGIN_H, PAGE_H - MARGIN_V + 2 * mm, "Material QR Codes")

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#888888"))
        c.drawRightString(PAGE_W - MARGIN_H, PAGE_H - MARGIN_V + 2 * mm,
                          "Page {} / {}  |  Scan with phone camera".format(
                              page_num, total_pages))

        c.setStrokeColor(colors.HexColor("#DDDDDD"))
        c.setLineWidth(0.4)
        c.line(MARGIN_H, PAGE_H - MARGIN_V,
               PAGE_W - MARGIN_H, PAGE_H - MARGIN_V)

        for i, member in enumerate(page_members):
            pm = member.get("piecemark", "?")
            print("    {} → {}".format(pm, member_url(pm)))
            draw_cell(c, member, col=i % COLS, row=i // COLS)

        c.showPage()

    c.save()
    print("\nPDF saved: {}".format(output_path))


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    # Validate config
    if GITHUB_USERNAME == "YOUR_GITHUB_USERNAME":
        print("=" * 60)
        print("ERROR: Set GITHUB_USERNAME and GITHUB_REPO at the top of this file.")
        print("=" * 60)
        sys.exit(1)

    # Find members.json
    if len(sys.argv) >= 2:
        json_path = Path(sys.argv[1])
    else:
        json_path = BASE_DIR / "QR_Codes" / "members.json"

    if not json_path.exists():
        print("ERROR: Cannot find " + str(json_path))
        sys.exit(1)

    with open(str(json_path), "r", encoding="utf-8") as f:
        members = json.load(f)

    print("\n" + "=" * 55)
    print("  Members loaded : {}".format(len(members)))
    print("  GitHub Pages   : https://{}.github.io/{}/".format(
        GITHUB_USERNAME, GITHUB_REPO))
    print("  Layout         : {} cols × {} rows = {} per page".format(
        COLS, ROWS_PER_PAGE, COLS * ROWS_PER_PAGE))
    print("=" * 55)

    # Step 1 — Push to GitHub
    print("\n[1/2] Deploying to GitHub Pages...")
    deploy_to_github(json_path)

    # Step 2 — Generate PDF
    print("\n[2/2] Generating PDF...")
    output_path = json_path.parent / "qr_sheet.pdf"
    generate_pdf(members, output_path)

    print("\n" + "=" * 55)
    print("  DONE!")
    print("  PDF  : {}".format(output_path))
    print("  Web  : https://{}.github.io/{}/".format(GITHUB_USERNAME, GITHUB_REPO))
    print("\n  NOTE: GitHub Pages takes ~1 minute to go live after first push.")
    print("  Print the PDF after that 1-minute wait.")
    print("=" * 55)

    # Auto-open PDF
    import platform
    try:
        if platform.system() == "Windows":
            os.startfile(str(output_path))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(output_path)])
        else:
            subprocess.Popen(["xdg-open", str(output_path)])
    except Exception:
        pass


if __name__ == "__main__":
    main()