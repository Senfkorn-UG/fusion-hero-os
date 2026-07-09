import typer
from normal_os.core.config import settings

app = typer.Typer(help="NormalOS - Clean orchestration platform")


@app.command()
def version():
    """Show version and environment."""
    typer.echo(f"normalOS v0.5.0 | env={settings.environment}")


@app.command()
def status():
    """Show system status."""
    typer.echo("NormalOS is running in clean mode.")
    typer.echo(f"Database: {settings.database_url}")


if __name__ == "__main__":
    app()