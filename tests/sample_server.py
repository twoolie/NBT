import hashlib
import os
import subprocess

from .downloadsample import download_with_external_tool

server_dir = 'tests/sample_server'
server_jar_path = os.path.join(server_dir, 'server.jar')
world_dir = os.path.join(server_dir, 'world')


# minecraft 1.20.2
server_jar_url = 'https://piston-data.mojang.com/v1/objects/5b868151bd02b41319f54c8d4061b8cae84e665c/server.jar'
server_jar_sha256_hex = '1daee4838569ad46e41f0a6f459684c500c7f2685356a40cfb7e838d6e78eae8'
stop_command = b'/stop\n'


def make_world():
    if os.path.exists(world_dir):
        # if world exists, do nothing
        return

    os.makedirs(server_dir, exist_ok=True)
    install_server()
    start_server()


def install_server():
    if not is_server_digest_ok():
        download_with_external_tool(server_jar_url, server_jar_path)
        assert is_server_digest_ok()

    # fill in eula
    with open(os.path.join(server_dir, 'eula.txt'), 'wt') as f:
        # Well, is this even legal?
        f.write('eula=true\n')

    # configure server.properties
    with open(os.path.join(server_dir, 'server.properties'), 'wt') as f:
        f.write('level-seed=testseed\n')


def start_server():
    subprocess.run(
        ['java', '-jar', 'server.jar', 'nogui'],
        cwd=server_dir,
        input=stop_command,
        check=True,
        timeout=120,  # seconds
    )


def is_server_digest_ok():
    if os.path.exists(server_jar_path):
        with open(server_jar_path, 'rb') as f:
            current_sha256_hex = hashlib.sha256(f.read()).hexdigest()
    else:
        current_sha256_hex = None
    return current_sha256_hex == server_jar_sha256_hex


if __name__ == '__main__':
    make_world()
