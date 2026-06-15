"""Entrypoint: procesa los tickets abiertos del CRM (lo invoca el scheduler).

Uso:  python -m contact_center.run_batch   ·   cc-batch
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from .config import get_settings
from .gcp_secrets import bootstrap_secrets
from .services import process_open_tickets


def main() -> int:
    load_dotenv()
    bootstrap_secrets()
    s = get_settings()
    if not (s.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")):
        print("ERROR: falta ANTHROPIC_API_KEY (ver .env.example).")
        return 1

    print(f"▶ Procesando tickets abiertos [{s.agent_runtime}] de CRM={s.crm_provider} (DRY_RUN={s.dry_run})...")
    try:
        results = process_open_tickets()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR al traer tickets del CRM ({s.crm_provider}): {exc}")
        return 1

    ok = sum(1 for r in results if r.get("ok"))
    print("\n" + "=" * 60)
    print(f"  Tickets procesados: {ok}/{len(results)}")
    for r in results:
        mark = "✓" if r.get("ok") else "✗"
        print(f"  {mark} ticket {r.get('ticket_id')} -> run #{r.get('run_id', '-')} {r.get('error','')}")
    print(f"  Revisá/aprobá en el dashboard (make web). DB: {s.database_path}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
