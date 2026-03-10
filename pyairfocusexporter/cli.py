from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .fetcher.airfocus_fetcher import AirfocusFetcher
from .exporter.miro_exporter import MiroExporter
from . import constants

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Export airfocus workspaces to external services."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@cli.command()
@click.option(
    "--workspace-id",
    required=True,
    help="The ID of the airfocus workspace to extract",
)
@click.option(
    "--target",
    default="miro",
    help="Export target (miro)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Fetch data without pushing to the target service",
)
@click.option(
    "--ignore-ssl",
    is_flag=True,
    help="Ignore SSL certificate verification (for development/testing)",
)
@click.option(
    "--stop-on-error",
    is_flag=True,
    help="Halt execution on first error encountered",
)
@click.option(
    "--max-depth",
    type=int,
    default=None,
    help="Maximum recursion depth for child workspaces (default: unlimited)",
)
@click.option(
    "--miro-board-id",
    envvar="MIRO_BOARD_ID",
    help="Miro board ID (required for miro target)",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity",
)
def export(
    workspace_id: str,
    target: str,
    dry_run: bool,
    ignore_ssl: bool,
    stop_on_error: bool,
    max_depth: Optional[int],
    miro_board_id: Optional[str],
    verbose: int,
) -> None:
    """Export workspace to target service."""
    if verbose > 0:
        console.print(f"[dim]Starting export for workspace: {workspace_id}[/dim]")

    api_key = constants.AIRFOCUS_API_KEY
    if not api_key:
        console.print("[red]Error: AIRFOCUS_API_KEY not configured[/red]")
        console.print(
            "[yellow]Please copy constants.py.example to constants.py and configure your API keys[/yellow]"
        )
        raise click.Abort()

    access_token = None
    board_id = None

    if target.lower() == "miro":
        access_token = constants.MIRO_ACCESS_TOKEN
        if not access_token:
            console.print("[red]Error: MIRO_ACCESS_TOKEN not configured[/red]")
            console.print(
                "[yellow]Please copy constants.py.example to constants.py and configure your API keys[/yellow]"
            )
            raise click.Abort()
        board_id = miro_board_id
        if not board_id and not dry_run:
            console.print("[red]Error: --miro-board-id is required for miro target[/red]")
            raise click.Abort()

    try:
        with AirfocusFetcher(
            api_key=api_key,
            base_url=constants.AIRFOCUS_API_BASE_URL,
            ignore_ssl=ignore_ssl,
        ) as fetcher:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("[cyan]Fetching workspace data...", total=None)
                workspace_data = fetcher.fetch_workspace(workspace_id, max_depth=max_depth)
                progress.update(task, completed=True)

            console.print(f"[green]Fetched workspace: {workspace_data.name}[/green]")
            total_items = len(workspace_data.items)
            for child in workspace_data.child_workspaces:
                total_items += len(child.items)
            console.print(f"[green]Total items: {total_items}[/green]")

            if dry_run:
                console.print("[yellow]Dry run mode - skipping export[/yellow]")
                return

            if target.lower() == "miro" and access_token and board_id:
                with MiroExporter(
                    access_token=access_token,
                    board_id=board_id,
                    ignore_ssl=ignore_ssl,
                ) as exporter:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("[cyan]Exporting to Miro...", total=None)
                        result = exporter.export(workspace_data)
                        progress.update(task, completed=True)

                    if result.success:
                        console.print(
                            f"[green]Export successful! Exported {result.exported_count} items[/green]"
                        )
                    else:
                        console.print(
                            f"[red]Export completed with {result.error_count} errors[/red]"
                        )
                        for error in result.errors:
                            console.print(f"[red]  - {error.message}[/red]")
                    for warning in result.warnings:
                        console.print(f"[yellow]  Warning: {warning}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose > 0:
            import traceback

            console.print(traceback.format_exc())
        raise click.Abort()


if __name__ == "__main__":
    cli()
