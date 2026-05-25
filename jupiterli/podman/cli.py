#!/usr/bin/env python3
import click, sys, os.path, pathlib
from . import podman_utils

PKG_DIR = pathlib.Path(__file__).parent

@click.group()
def cli():
    """JupiterLI command line interface."""
    pass

# -----------------------------------------------------------------------------
# init
# -----------------------------------------------------------------------------

@cli.command()
@click.option("--dry-run", "dry_run", flag_value = "do_dry_run")
@click.option("--data-dir", required=True, type=click.Path(), help="Directory where JupiterLI data will be stored.")
def init(dry_run, data_dir):
    """Initialize JupiterLI project."""
    click.echo("Initializing JupiterLI...")
    print("jupiterli will place all its files into location:", data_dir, dry_run)

    dry_run = dry_run == "do_dry_run"

    data_dir = os.path.realpath(data_dir)
    if os.path.exists(data_dir):
        print(f"data dir exists: {data_dir}, giving up...")
        sys.exit(3)

    for t_dir in ["clickhouse-data", "docker-logs"]:
        target_dir = os.path.join(data_dir, t_dir)
        if not dry_run:
            print("making dir:", target_dir)
            os.makedirs(target_dir)
        else:
            print("will be making dir:", target_dir)
        
    jli_image_name = "jupiterli-image"
    jli_container_name = "jupiterli"
    clickhouse_dir = os.path.join(data_dir, "clickhouse-data")
    log_dir = os.path.join(data_dir, "docker-logs")
    
    podman_utils.podman_build(dry_run, os.path.join(PKG_DIR, "docker"), jli_image_name, os.path.join(PKG_DIR, "docker/Dockerfile"))
    jli_container_id = podman_utils.podman_create(dry_run = dry_run, image = jli_image_name,
                                                  name = jli_container_name,
                                                  ports = [(8123, 8123), (9000, 9000), (6379, 6379), (5173, 5173)],
                                                  volumes = [(clickhouse_dir, "/var/lib/clickhouse"), (log_dir, "/logs")],
                                                  env = {"HOME": "/host-user-apps"})
    print("jli_container_id:", jli_container_id)

@cli.command()
@click.option("--dry-run", "dry_run", flag_value = "do_dry_run")
def cleanup(dry_run):
    dry_run = dry_run == "do_dry_run"
    podman_utils.podman_cleanup(dry_run)
    
    
# -----------------------------------------------------------------------------
# start / stop
# -----------------------------------------------------------------------------

@cli.command()
@click.option("--dry-run", "dry_run", flag_value = "do_dry_run")
def start(dry_run):
    """Start JupiterLI services."""
    click.echo("Starting JupiterLI...")
    dry_run = dry_run == "do_dry_run"
    podman_utils.podman_start(dry_run)

@cli.command()
@click.option("--dry-run", "dry_run", flag_value = "do_dry_run")
def stop(dry_run):
    """Stop JupiterLI services."""
    click.echo("Stopping JupiterLI...")
    dry_run = dry_run == "do_dry_run"
    podman_utils.podman_stop(dry_run)


# -----------------------------------------------------------------------------
# browser group
# -----------------------------------------------------------------------------

@cli.group()
def browser():
    """Browser-related commands."""
    pass


# -----------------------------------------------------------------------------
# browser start
# -----------------------------------------------------------------------------

@browser.command("start")
@click.option("--all", "mode", flag_value="all", help="Start all browser components.",)
@click.option("--frontend", "mode", flag_value="frontend", help="Start frontend browser component.",)
@click.option("--backend", "mode", flag_value="backend", help="Start backend browser component.",)
def browser_start(mode):
    """
    Start browser services.
    """

    if mode is None:
        raise click.UsageError(
            "Specify one of: --all, --frontend, or --backend"
        )

    click.echo(f"Starting browser mode: {mode}")


# -----------------------------------------------------------------------------
# browser stop
# -----------------------------------------------------------------------------

@browser.command("stop")
def browser_stop():
    """Stop browser services."""
    click.echo("Stopping browser services...")


# -----------------------------------------------------------------------------

def main():
    cli()

if __name__ == "__main__":
    main()
