
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.logistics.etl.extract import extract
from apps.logistics.etl.load import load
from apps.logistics.etl.quality import quality_report
from apps.logistics.etl.transform import transform
from apps.logistics.models import EtlRun

DEFAULT = settings.BASE_DIR.parent / "data" / "raw" / "DataCoSupplyChainDataset.csv"

class Command(BaseCommand):
    help = "Pipeline ETL DataCo : extraction, nettoyage, chargement dans PostgreSQL (idempotent)."
    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(DEFAULT))
        parser.add_argument("--limit", type=int, help="ne lire que N lignes (tests, débogage)")
        parser.add_argument("--dry-run", action="store_true", help="transforme et rapporte, sans écrire en base")
    def handle(self, *args, **o):
        path = Path(o["file"])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f"Fichier introuvable : {path}"))
            raise SystemExit(1)
        run = EtlRun.objects.create(source_file=str(path))
        try:
            raw = extract(path, o["limit"])
            orders, line_items, rejects, stats = transform(raw)
            report = quality_report(orders, rejects, stats)
            self.stdout.write(report)
            if len(rejects):
                out = settings.BASE_DIR.parent / "data" / "processed"
                out.mkdir(parents=True, exist_ok=True)
                rejects.to_csv(out / f"rejects_{timezone.now():%Y%m%d_%H%M%S}.csv", index=False)
            counts = {"commandes": 0, "expeditions": 0, "lignes_commande": 0} if o["dry_run"] else load(orders, line_items)
            run.status, run.message = EtlRun.Status.SUCCESS, report
            run.rows_read, run.rows_rejected = stats["rows_in"], stats["rows_rejected"]
            run.commandes_loaded, run.expeditions_loaded = counts["commandes"], counts["expeditions"]
            run.lignes_commande_loaded = counts["lignes_commande"]
        except Exception as exc:
            run.status, run.message = EtlRun.Status.FAILED, repr(exc)
            raise
        finally:
            run.finished_at = timezone.now()
            run.save()