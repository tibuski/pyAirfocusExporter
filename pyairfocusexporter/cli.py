from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .fetcher.airfocus_fetcher import AirfocusFetcher
from .exporter.miro_exporter import MiroExporter
from . import constants
from .utils.logging import setup_logging, get_logger

console = Console()
logger = get_logger()


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
    default=None,
    help="The ID of the airfocus workspace to extract (or set in constants.py)",
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
    help="Increase verbosity (-v for INFO, -vv for DEBUG)",
)
def export(
    workspace_id: Optional[str],
    target: str,
    dry_run: bool,
    ignore_ssl: bool,
    stop_on_error: bool,
    max_depth: Optional[int],
    miro_board_id: Optional[str],
    verbose: int,
) -> None:
    """Export workspace to target service."""
    setup_logging()

    if verbose >= 2:
        from . import constants as const

        const.LOG_LEVEL = "DEBUG"
        setup_logging()

    logger.info("Starting export")
    logger.info(f"Target: {target}, Dry run: {dry_run}, Ignore SSL: {ignore_ssl}")

    workspace_id = workspace_id or constants.AIRFOCUS_WORKSPACE_ID
    if not workspace_id:
        logger.error("WORKSPACE_ID not configured")
        console.print("[red]Error: WORKSPACE_ID not configured[/red]")
        console.print(
            "[yellow]Please set --workspace-id or configure AIRFOCUS_WORKSPACE_ID in constants.py[/yellow]"
        )
        raise click.Abort()

    logger.info(f"Workspace ID: {workspace_id}")

    api_key = constants.AIRFOCUS_API_KEY
    if not api_key:
        logger.error("AIRFOCUS_API_KEY not configured")
        console.print("[red]Error: AIRFOCUS_API_KEY not configured[/red]")
        console.print(
            "[yellow]Please copy constants.py.example to constants.py and configure your API keys[/yellow]"
        )
        raise click.Abort()

    access_token = None
    board_id = None

    if target.lower() == "miro" and not dry_run:
        access_token = constants.MIRO_ACCESS_TOKEN
        if not access_token:
            logger.error("MIRO_ACCESS_TOKEN not configured")
            console.print("[red]Error: MIRO_ACCESS_TOKEN not configured[/red]")
            console.print(
                "[yellow]Please copy constants.py.example to constants.py and configure your API keys[/yellow]"
            )
            raise click.Abort()
        board_id = miro_board_id or constants.MIRO_BOARD_ID
        if not board_id:
            logger.error("--miro-board-id is required for miro target")
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
                logger.warning("Dry run mode - skipping export")
                console.print("[yellow]Dry run mode - skipping export[/yellow]")
                return

            if target.lower() == "miro" and access_token and board_id:
                with MiroExporter(
                    access_token=access_token,
                    board_id=board_id,
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
                        logger.info(f"Export successful! Exported {result.exported_count} items")
                        console.print(
                            f"[green]Export successful! Exported {result.exported_count} items[/green]"
                        )
                    else:
                        logger.error(f"Export completed with {result.error_count} errors")
                        console.print(
                            f"[red]Export completed with {result.error_count} errors[/red]"
                        )
                        for error in result.errors:
                            console.print(f"[red]  - {error.message}[/red]")
                    for warning in result.warnings:
                        logger.warning(warning)
                        console.print(f"[yellow]  Warning: {warning}[/yellow]")
    except Exception as e:
        logger.error(f"Error: {e}")
        console.print(f"[red]Error: {e}[/red]")
        if verbose > 0:
            import traceback

            console.print(traceback.format_exc())
        raise click.Abort()


if __name__ == "__main__":
    cli()
