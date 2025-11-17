"""Clean up expired warnings from database."""

import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal  # ← Agregar este import
from app.storage.models import WarningAlert


def cleanup_expired_warnings(dry_run: bool = False):
    """
    Delete warnings where valid_until < now.

    Args:
        dry_run: If True, only show what would be deleted without deleting
    """
    db = SessionLocal()

    try:
        now = datetime.now()

        # Find expired warnings
        expired_warnings = (
            db.query(WarningAlert).filter(WarningAlert.valid_until < now).all()
        )

        if not expired_warnings:
            print("✓ No expired warnings found")
            return

        print(f"Found {len(expired_warnings)} expired warnings:")
        for warning in expired_warnings:
            print(
                f"  - #{warning.warning_number} ({warning.department}): "
                f"expired on {warning.valid_until.strftime('%Y-%m-%d')}"
            )

        if dry_run:
            print("\n[DRY RUN] No warnings deleted")
        else:
            deleted = (
                db.query(WarningAlert).filter(WarningAlert.valid_until < now).delete()
            )

            db.commit()
            print(f"\n✓ Deleted {deleted} expired warnings")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Clean up expired warnings")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting",
    )
    args = parser.parse_args()

    cleanup_expired_warnings(dry_run=args.dry_run)
