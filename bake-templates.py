#!/usr/bin/env python3
"""
Bake LaTeX Templates to PDF — Optimized for Linux Mint
"""

import shlex
import subprocess
import sys
from pathlib import Path

def bake_templates():
    templates_dir = Path("./booktacular/data/templates").resolve()
    pdf_dir = Path("./booktacular/data/templates/pdf").resolve()
    pdf_dir.mkdir(parents=True, exist_ok=True)

    tex_files = sorted(templates_dir.glob("*.tex"))
    if not tex_files:
        print("⚠️  No .tex files found.")
        return

    print(f"🔨 Found {len(tex_files)} template(s) to bake → {pdf_dir}\n")

    for tex_file in tex_files:
        pdf_filename = f"{tex_file.stem}.pdf"
        print(f"Compiling → {tex_file.name}")

        try:
            success = True
            for run in range(2):  # Two passes needed for some layouts
                cmd_parts = [
                    "pdflatex",
                    "-halt-on-error",
                    "-interaction=nonstopmode",
                    "-output-directory", str(pdf_dir),
                    tex_file.name
                ]
                print(shlex.join(cmd_parts))
                result = subprocess.run(
                    cmd_parts,
                    cwd=templates_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    success = False
                    print(f"   ✗ Failed on run {run+1}")
                    # Show only the relevant error part
                    lines = result.stdout.splitlines()[-50:]
                    print("\n".join(lines))
                    break

            if success:
                pdf_path = pdf_dir / pdf_filename
                if pdf_path.exists():
                    size_kb = pdf_path.stat().st_size / 1024
                    print(f"   ✓ Success → {pdf_filename} ({size_kb:.1f} KB)")
                else:
                    print("   ⚠️  PDF not created")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Optional: clean auxiliary files
        for ext in [".aux", ".log", ".out"]:
            aux = templates_dir / f"{tex_file.stem}{ext}"
            if aux.exists():
                aux.unlink()

    print("\n🎉 Baking finished! Check data/templates/pdf/")

if __name__ == "__main__":
    bake_templates()
