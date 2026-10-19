"""CLI: publish [--month YYYY-MM]."""

from __future__ import annotations

import logging
from typing import Optional

import typer

from dfb_publisher.period import parse_month, previous_month
from dfb_publisher.pipeline import run_publish
from dfb_publisher.settings import load_settings

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Publica el respaldo mensual Issabel a Google Drive.",
)


@app.callback()
def main() -> None:
    """dfb-publisher"""


@app.command("publish")
def publish(
    month: Optional[str] = typer.Option(
        None,
        "--month",
        "-m",
        help="Mes a publicar (YYYY-MM). Por defecto: mes calendario anterior.",
    ),
    debug: bool = typer.Option(False, "--debug", help="Log detallado"),
) -> None:
    """Valida job.json, baja el mes, zippea programas, sube a Drive y avisa por correo."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        period = parse_month(month) if month else previous_month()
        settings = load_settings()
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Publicando {period.year_dir}/{period.month_dir} …")
    result = run_publish(settings, period)
    typer.echo(result.message)
    raise typer.Exit(code=result.exit_code)


if __name__ == "__main__":
    app()
