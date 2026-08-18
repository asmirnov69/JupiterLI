#!/usr/bin/env python3
import typer
import sys, os.path, pathlib, shutil
from . import podman_utils

app = typer.Typer(add_completion=False,
                  pretty_exceptions_enable=False,  # disables Rich tracebacks
                  rich_markup_mode=None,           # disables Rich markup parsing
                  context_settings={"color": False, "help_option_names": ["-h", "--help"]}
                  )

PKG_DIR = pathlib.Path(__file__).parent

def print_line(quiet_mode, s):
    if quiet_mode == False:
        print(s)

def print_error(s):
    print("PROBLEM:", s)    
    
def handle_proceed_yn(proceed):
    if proceed == False:
        yn = input("proceed: [y/N] ").strip()
        #print(f"yn: '{yn}'")
        yn = yn if yn != "" else "n"
        print("yn:", yn)
        if yn.lower() in ["y", "yes"]:
            return
        else:
            print("aborted by user")
            sys.exit(2)

@app.command()
def verify():
    """verify local system as suitable for jupiterli-podman server"""
    podman_utils.podman_verify()
    
@app.command()
def status():
    """Shows jupiterli-podman status and related information"""
    podman_utils.podman_status()
            
@app.command()
def init(quiet_mode: bool = typer.Option(False, "--quiet", "-q", help = "don't show podman commands"),
         proceed: bool = typer.Option(False, "--yes", "-y", help = "will answer yes to proceed with command execution"),
         force_data_dir_creation: bool = typer.Option(False, "--force", "-f", help = "will force creation of new data dir, will remove old data"),
         data_dir: str = typer.Option(..., "--data-dir", help = "jupiterli-podman container directory to store data and logs")):
    """Initialize JupiterLI project"""
    print_line(quiet_mode, "Initializing JupiterLI...")
    
    if data_dir is None:
        print_error("data_dir is not specified, giving up...")
        return

    data_dir = os.path.expanduser(data_dir)
    
    print_line(quiet_mode, f"jupiterli will place all its files into location: {data_dir}")
    handle_proceed_yn(proceed)

    data_dir = os.path.realpath(data_dir)
    if os.path.exists(data_dir):
        if force_data_dir_creation == False:
            print_error(f"data dir exists: {data_dir}, giving up...")
            sys.exit(3)
        else:
            print_line(quiet_mode, f"forced to remove existing data_dir: {data_dir}")
            handle_proceed_yn(proceed)
            shutil.rmtree(data_dir)

    for t_dir in ["sqlite3-data", "docker-logs"]:
        target_dir = os.path.join(data_dir, t_dir)
        print_line(quiet_mode, f"making dir: {target_dir}")
        os.makedirs(target_dir)
        
    jli_image_name = "jupiterli-image"
    jli_container_name = "jupiterli"
    sqlite3_dir = os.path.join(data_dir, "sqlite3-data")
    log_dir = os.path.join(data_dir, "docker-logs")
    
    podman_utils.podman_build(quiet_mode, os.path.join(PKG_DIR, "docker"), jli_image_name, os.path.join(PKG_DIR, "docker/Dockerfile"), data_dir)
    jli_container_id = podman_utils.podman_create(quiet_mode = quiet_mode, image = jli_image_name,
                                                  name = jli_container_name, labels = [("datadir", data_dir), ("browser-port", 5173)],
                                                  ports = [(1883, 1883), (5173, 5173)],
                                                  volumes = [(sqlite3_dir, "/sqlite3-data"), (log_dir, "/logs")],
                                                  env = {"HOME": "/host-user-apps"})
    print_line(quiet_mode, f"jli_container_id: {jli_container_id}")

@app.command()
def cleanup(quiet_mode: bool = typer.Option(False, "--quiet", "-q", help = "don't show podman commands"),
            proceed: bool = typer.Option(False, "--yes", "-y", help = "will answer yes to proceed with command execution")):
    """Removing data-dir and podman image/container used by jupiterli"""

    handle_proceed_yn(proceed)
    podman_utils.podman_cleanup(quiet_mode)
    
@app.command()
def start(quiet_mode: bool = typer.Option(False, "--quiet", "-q", help = "don't show podman commands")):
    """Start JupiterLI services"""
    print("Starting JupiterLI...")
    podman_utils.podman_start(quiet_mode)

@app.command()
def stop(quiet_mode: bool = typer.Option(False, "--quiet", "-q", help = "don't show podman commands")):
    """Stop JupiterLI services"""
    print("Stopping JupiterLI...")
    podman_utils.podman_stop(quiet_mode)

def main():
    app()
