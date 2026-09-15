"""
Alibaba OpenCodeReview & Vercel Skills Automated Workflow Helper
Executes diff audits, directory scans, and skill management commands
for the Belajar Kripto Workstation.
"""

import subprocess
import sys
import os

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_ocr_review(target_branch: str = "main") -> int:
    """Runs Alibaba OpenCodeReview on working changes against target branch."""
    cmd = f"npx -y @alibaba-group/open-code-review review --target {target_branch}"
    print(f"🔍 Executing OpenCodeReview against {target_branch}...")
    try:
        return subprocess.run(cmd, shell=True, check=False).returncode
    except Exception as e:
        print(f"❌ Error running OCR: {e}")
        return 1

def run_ocr_scan(target_path: str = ".") -> int:
    """Runs full-directory static and security scan using OCR."""
    cmd = f"npx -y @alibaba-group/open-code-review scan --path {target_path}"
    print(f"🛡️ Executing full OCR scan on {target_path}...")
    try:
        return subprocess.run(cmd, shell=True, check=False).returncode
    except Exception as e:
        print(f"❌ Error running OCR scan: {e}")
        return 1

def list_installed_skills() -> int:
    """Lists installed skills across agent environments via Vercel Skills CLI."""
    cmd = "npx -y skills list"
    print("⚡ Listing installed skills via Vercel Skills CLI:")
    try:
        return subprocess.run(cmd, shell=True, check=False).returncode
    except Exception as e:
        print(f"❌ Error listing skills: {e}")
        return 1

if __name__ == "__main__":
    print("=" * 60)
    print("🛠️ WORKFLOW HELPER: OPENCODEREVIEW & VERCEL SKILLS")
    print("=" * 60)
    list_installed_skills()
    print("=" * 60)
