import subprocess
import sys, os
import shlex, json

def show_stdout(process, return_last_line = True):
    # Stream output live, returns last line
    last_line = None

    for line in process.stdout:
        print(line, end="")
        sys.stdout.flush()

        if return_last_line:
            if line.strip():
                last_line = line.strip()

    return last_line
    

def podman_build(quiet_mode, context_dir, image_name, dockerfile):
    tag = image_name
    cmd = []
    cmd.extend(["podman", "build"])
    curr_uid = os.getuid(); curr_gid = os.getgid()
    cmd.extend(["--build-arg", f"CURR_UID={curr_uid}", "--build-arg", f"CURR_GID={curr_gid}"])
    cmd.extend(["-t", tag, "-f", dockerfile, context_dir])

    if not quiet_mode:
        print("podman_build::", " ".join(cmd))

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,)
    image_id = show_stdout(process)
    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(f"podman build failed with exit code {return_code}")

    print()
    print("Build completed successfully, image_id:", image_id)

def podman_create(quiet_mode, image, name, ports, volumes, env, command = None):
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

    print()
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
    cmd = shlex.split("podman images --filter label=label=jupiterli-image --format json")
    if not quiet_mode:
        print("podman_cleanup::", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    out_j = json.loads(result.stdout)
    jupiterli_image_id = out_j[0]['Id']
    print("check_jupiterli_image:", jupiterli_image_id)

    cmd = ["podman", "image", "rm"]
    cmd.append(jupiterli_image_id)
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

        
