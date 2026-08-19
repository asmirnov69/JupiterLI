import subprocess
import sys, os
import shlex, json

def show_stdout(process, additional_out = None, return_last_line = True):
    # Stream output live, returns last line
    last_line = None

    for line in process.stdout:
        if additional_out is None:
            print(line, end="")
            sys.stdout.flush()
        else:
            print(".", end="", file = sys.stderr); sys.stderr.flush()
            print(line, end="", file = additional_out); additional_out.flush()

        if return_last_line:
            if line.strip():
                last_line = line.strip()

    return last_line

def podman_verify():
    cmd = "podman --version"
    process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,)
    image_id = show_stdout(process)
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(f"podman --version  failed with exit code {return_code}")

def podman_status():
    cmds = []
    cmds.append(("status", "podman inspect -f '{{ index .State.Status }}' jupiterli"))
    cmds.append(("image", "podman inspect -f '{{ index .RepoTags }} ' jupiterli-image"))
    cmds.append(("datadir", "podman inspect -f '{{ index .Config.Labels \"datadir\" }}' jupiterli"))
    cmds.append(("db-access-port", "podman inspect -f '{{ index .Config.Labels \"db-access-port\" }}' jupiterli"))
    for l, cmd in cmds:
        print(l, end = ': ')
        process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,)
        show_stdout(process)
    
def podman_build(quiet_mode, context_dir, image_name, dockerfile, data_dir):
    tag = image_name
    curr_uid = os.getuid(); curr_gid = os.getgid()

    cmd = []
    cmd.extend(["podman", "build"])
    cmd.extend(["--build-arg", f"CURR_UID={curr_uid}", "--build-arg", f"CURR_GID={curr_gid}"])
    cmd.extend(["-t", tag, "-f", dockerfile, context_dir])

    if not quiet_mode:
        print("podman_build::", " ".join(cmd))

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,)
    build_log_fn = os.path.join(data_dir, "podman-build.txt")
    print(f"podman build log: {build_log_fn}")
    with open(build_log_fn, "w") as build_log:
        image_id = show_stdout(process, build_log)
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(f"podman build failed with exit code {return_code}")

    print()
    print("Build completed successfully, image_id:", image_id)

def podman_create(quiet_mode, image, name, labels: list[tuple[str, str]], ports, volumes, env, command = None):
    """
    Create podman container.

    Parameters
    ----------
    image : str
        Container image name.

    name : str | None
        Optional container name.

    ports : list[tuple[int, int]]
        List of (host_port, container_port)

    volumes : list[tuple[str, str]]
        List of (host_path, container_path)

    env : dict
        Environment variables.

    command : list[str] | None
        Command to run inside container.
    """

    cmd = ["podman", "create"]

    # container name
    if name:
        cmd += ["--name", name]

    for label_key, label_value in labels:
        cmd += ["--label", f'{label_key}={label_value}']
    
    # additional options to match users
    cmd += ["--userns", "keep-id"]
    curr_uid = os.getuid(); curr_gid = os.getgid()
    cmd += ["--user", f"{curr_uid}:{curr_gid}"]
    
    # port mappings
    if ports:
        for host_port, container_port in ports:
            cmd += ["-p", f"{host_port}:{container_port}"]

    # volume mappings
    if volumes:
        for host_path, container_path in volumes:
            cmd += ["-v", f"{host_path}:{container_path}:Z"]

    # environment variables
    if env:
        for key, value in env.items():
            cmd += ["-e", f"{key}={value}"]

    # image
    cmd.append(image)

    # command inside container
    if command:
        cmd.extend(command)

    if not quiet_mode:
        print("podman_create::", " ".join(cmd))

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,)
    container_id = show_stdout(process)
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(
            f"podman create failed with exit code {return_code}"
        )

    print("Container created successfully, container_id:", container_id)

    return container_id

def podman_cleanup(quiet_mode):
    # remove container first
    cmd = shlex.split("podman rm -f jupiterli")
    if not quiet_mode:
        print("podman_cleanup::", " ".join(cmd))
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("failed:", result.stderr)
        return
        
    # remove image
    cmd = ["podman", "image", "rm", "jupiterli-image"]
    if not quiet_mode:
        print("podman_cleanup:", " ".join(cmd))
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("failed:", result.stderr)

    print("all done")

def podman_start(quiet_mode):
    cmd = "podman start jupiterli"
    if not quiet_mode:
        print("podman_start::", cmd)

    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        print("failed:", result.stderr)
    print("all done")

def podman_stop(quiet_mode):
    cmd = "podman stop jupiterli"
    if not quiet_mode:
        print("podman_stop::", cmd)
        
    result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        print("failed:", result.stderr)
    print("all done")

        
