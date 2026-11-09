import sys
import shlex
from pathlib import PurePath

from config import *
from identity import Identity
from server import Server, Cluster


def _quote(
        path: str | PurePath
) -> str:
    text = str(path)
    if sys.platform == "win32":
        return f'"{text}"' if any(c.isspace() for c in text) else text
    return shlex.quote(text)


def _remote(
        path: str | PurePath
) -> str:
    text = str(path)
    if any(c.isspace() for c in text):
        return f'"{text}"'
    return text


def generate_jump(
        username: str,
        server: Server,
        cluster: Cluster,
        max_jumps: int = 4,
) -> str:
    flag = "-J "
    depth = 0
    while server.connect_through != ("", ""):
        if max_jumps < depth:
            raise RecursionError("Too many jump connections.")
        depth += 1
        server = cluster[server.connect_through]
        flag += f"{username}{server.hostname},"
    return flag[:-1]
    

def generate_ssh(
        server: Server,
        cluster: Cluster| None = None,
        identity: Identity | None = None,
        username: str | None = None,
        local_forwarding: tuple | None = None,
        remote_forwarding: tuple | None = None,
        dynamic_forwarding: int | None = None,
        no_shell: bool = False,
        trusted_graphical: bool = False,
        graphical: bool = False,
        compress: bool = False,
        quiet: bool = False,
        verbose: int = 0,
) -> str:
    # Determine username
    if username is None:
        username = USERNAME
    if username != "":
        username += '@'

    # Populate options
    options = []
    # Server port
    if server.port != 22:
        options.append(f"-p {server.port}")
    # Identity file
    if identity is not None:
        if not isinstance(identity, Identity):
            return "Error during adding identity: Must be Identity object!"
        options.append(f"-i {_quote(identity.private_key)}")
    # ProxyJump
    if server.connect_through != ("", ""):
        if cluster is None or not isinstance(cluster, Cluster):
            return "Error during proxy jumping: Cluster object must be provided!"
        options.append(generate_jump(username, server, cluster))
    # Local port forwarding
    if local_forwarding is not None:
        if not (isinstance(local_forwarding[0], int) and isinstance(local_forwarding[1], int)):
            return "Error during local forwarding: Ports must be integers!"
        options.append(f"-L {local_forwarding[0]}:localhost:{local_forwarding[1]}")
    # Remote port forwarding
    if remote_forwarding is not None:
        if not (isinstance(remote_forwarding[0], int) and isinstance(remote_forwarding[1], int)):
            return "Error during remote forwarding: Ports must be integers!"
        options.append(f"-R {remote_forwarding[0]}:localhost:{remote_forwarding[1]}")
    # Dynamic port forwarding
    if dynamic_forwarding is not None:
        if not isinstance(dynamic_forwarding, int):
            return "Error during dynamic forwarding: Port must be integer!"
        options.append(f"-D {dynamic_forwarding}")
    # No shell
    if no_shell:
        options.append("-n")
    # Trusted X11 graphical
    if trusted_graphical:
        options.append("-Y")
    # Secure X11 graphical
    if graphical and not trusted_graphical:
        options.append("-X")
    # Gzip compression for low-bandwith
    if compress:
        options.append("-C")
    # Quiet mode
    if quiet:
        options.append("-q")
    # Verbose level
    if verbose != 0:
        if not (isinstance(verbose, int) and (1 <= verbose <= 3)):
            return "Error during vebose setting: Must be integer between 0 and 3 (incl.)!"
        options.append('-' + 'v'*verbose)

    # Generate command
    parts = ["ssh", *options, f"{username}{server.hostname}"]
    return ' '.join(parts)


def generate_scp(
        server: Server,
        sources: Path | PurePath | list[Path | PurePath],
        destination: Path | PurePath,
        download: bool = False,
        cluster: Cluster| None = None,
        identity: Identity | None = None,
        username: str | None = None,
        compress: bool = False,
        quiet: bool = False,
        verbose: int = 0,
        directory: bool = False,
        preserve_metadata: bool = False,
) -> str:
    # Determine username and settle sources
    if username is None:
        username = USERNAME
    if username != "":
        username += '@'
    # Accept Path, PurePosixPath (= PurePath) or a list of either
    if isinstance(sources, PurePath):
        sources = [sources]
    sources = list(sources)
    if not sources:
        raise ValueError("At least one source is required.")
    dest_text = str(destination).strip()
    if dest_text in ("", "."):
        raise ValueError("A destination is required.")
    # Choose file transfer direction
    if download:
        remote = f"{username}{server.hostname}:"
        sources = ' '.join(f"{remote}{_remote(src)}" for src in sources)
        target = _quote(destination)
    else:
        sources = ' '.join(_quote(src) for src in sources)
        target = f"{username}{server.hostname}:{_remote(destination)}"

    # Populate options
    options = []
    # Server port
    if server.port != 22:
        options.append(f"-P {server.port}")
    # Identity file
    if identity is not None:
        if not isinstance(identity, Identity):
            return "Error during adding identity: Must be Identity object!"
        options.append(f"-i {_quote(identity.private_key)}")
    # ProxyJump
    if server.connect_through != ("", ""):
        if cluster is None or not isinstance(cluster, Cluster):
            return "Error during proxy jumping: Cluster object must be provided!"
        options.append(f"-J {username}{cluster[server.connect_through].hostname}")
    # Gzip compression for low-bandwith
    if compress:
        options.append("-C")
    # Quiet mode
    if quiet:
        options.append("-q")
    # Verbose level
    if verbose != 0:
        if not (isinstance(verbose, int) and (1 <= verbose <= 3)):
            return "Error during vebose setting: Must be integer between 0 and 3 (incl.)!"
        options.append('-' + 'v'*verbose)
    # Recursive copy
    if directory:
        options.append("-r")
    # Preserve history
    if preserve_metadata:
        options.append("-p")

    # Generate command
    parts = ["scp", *options, sources, target]
    return ' '.join(parts)
