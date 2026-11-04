from config import *
from identity import Identity
from server import Server, Cluster


def generate_ssh(
        server: Server,
        cluster: Cluster| None = None,
        identity: Identity | None = None,
        username: str | None = None,
        local_forwarding: tuple | None = None,
        remote_forwarding: tuple | None = None,
        dynamic_forwarding: int | None = None,
        no_shell: bool = False,
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
    # Identity file
    if identity is not None:
        if not isinstance(identity, Identity):
            return "Error during adding identity: Must be Identity object!"
        options.append(f"-i {identity.private_key}")
    # ProxyJump
    if server.connect_through != ("", ""):
        if cluster is None or not isinstance(cluster, Cluster):
            return "Error during proxy jumping: Cluster object must be provided!"
        options.append(f"-J {username}{cluster[server.connect_through].hostname}")
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
    return "ssh " + ' '.join(options) + f" {username}{server.hostname}"


def generate_scp(
        server: Server,
        sources: Path | list[Path],
        destination: Path,
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
    if isinstance(sources, Path):
        sources = [sources]
    if download:
        sources =  f" {username}{server.hostname}:".join([str(src) for src in sources])
    else:
        sources = ' '.join([str(src) for src in sources])
        destination = f" {username}{server.hostname}:{destination}"

    # Populate options
    options = []
    # Identity file
    if identity is not None:
        if not isinstance(identity, Identity):
            return "Error during adding identity: Must be Identity object!"
        options.append(f"-i {identity.private_key}")
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
    return "scp " + ' '.join(options) + " " + sources + destination
