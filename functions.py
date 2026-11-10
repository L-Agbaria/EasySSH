import re
import sys
import shlex
from pathlib import PurePath

from config import *
from identity import Identity, KeyType
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


def _generate_jump(
        username: str,
        server: Server,
        cluster: Cluster,
        max_jumps: int = 4,
) -> str:
    hosts = []
    depth = 0
    while server.connect_through != ("", ""):
        if max_jumps < depth:
            raise RecursionError("Too many jump connections.")
        depth += 1
        server = cluster[server.connect_through]
        hosts.append(f"{username}{server.hostname}")
    return "-J " + ",".join(reversed(hosts))


def _check_key_policy(
        identity: Identity | None,
        cluster: Cluster | None,
) -> str | None:
    # Nothing to check: no key, no cluster, or cluster has no allowed list
    if identity is None or cluster is None or not cluster.key_policy:
        return None
    # Unknown key types can't be verified, so they count as not allowed
    if identity.key_type not in cluster.key_policy:
        allowed = ", ".join(key.value for key in cluster.key_policy)
        found = identity.key_type.value or "unknown"
        return (f"Identity '{identity.name}' uses key type {found}, "
                f"but cluster '{cluster.name}' only allows: {allowed}.")
    return None


def describe_key_policy(
        cluster: Cluster,
) -> str:
    if not cluster.key_policy:
        return "No restrictions."
    text = "Allowed: " + ", ".join(key.value for key in cluster.key_policy) + "."
    if cluster.preferred_policy != KeyType.UNKNOWN:
        text += f" Preferred: {cluster.preferred_policy.value}."
    return text
    

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
        remote_command: str | None = None,
        tunnel: bool = False,
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
        # Key policy of the cluster
        if (problem := _check_key_policy(identity, cluster)) is not None:
            return f"Error during key policy check: {problem}"
    # ProxyJump
    if server.connect_through != ("", ""):
        if cluster is None or not isinstance(cluster, Cluster):
            return "Error during proxy jumping: Cluster object must be provided!"
        options.append(_generate_jump(username, server, cluster))
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
    # Remote command text (multiple lines are joined with "; ")
    command_text = ""
    if remote_command is not None:
        lines = [ln.strip() for ln in remote_command.splitlines() if ln.strip()]
        command_text = "; ".join(lines)
    # Skipped with -n, as stdin is /dev/null then.
    if command_text and not no_shell:
        options.append("-t")
    # Tunneling
    if tunnel:
        options.append("-T")
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
    # Remote command, quoted so the local shell passes it on untouched
    if command_text:
        parts.append(_quote(command_text))
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
        # Key policy of the cluster
        if (problem := _check_key_policy(identity, cluster)) is not None:
            return f"Error during key policy check: {problem}"
    # ProxyJump
    if server.connect_through != ("", ""):
        if cluster is None or not isinstance(cluster, Cluster):
            return "Error during proxy jumping: Cluster object must be provided!"
        options.append(_generate_jump(username, server, cluster))
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


def generate_config(
        server: Server,
        cluster: Cluster | None = None,
        identity: Identity | None = None,
        username: str | None = None,
        alias: str | None = None,
        local_forwarding: tuple | None = None,
        remote_forwarding: tuple | None = None,
        dynamic_forwarding: int | None = None,
        trusted_graphical: bool = False,
        graphical: bool = False,
        compress: bool = False,
        quiet: bool = False,
) -> str:
    if username is None:
        username = USERNAME
    if alias is None:
        alias = f"{cluster.id}-" if cluster else ""
        alias += f"{server.category_id}-{server.server_id}"
    alias = re.sub(r"\s+", "-", alias.strip())
    if not alias:
        raise ValueError("A host alias is required.")

    lines = [f"Host {alias}", f"\tHostName {server.hostname}"]
    if username != "":
        lines.append(f"\tUser {username}")
    if server.port != 22:
        lines.append(f"\tPort {server.port}")
    # Identity file
    if identity is not None:
        if not isinstance(identity, Identity):
            raise ValueError("Identity must be an Identity object.")
        if (problem := _check_key_policy(identity, cluster)) is not None:
            raise ValueError(f"Key policy: {problem}")
        lines.append(f"\tIdentityFile {_remote(identity.private_key)}")
        lines.append("\tIdentitiesOnly yes")
    # ProxyJump
    if server.connect_through != ("", ""):
        if cluster is None or not isinstance(cluster, Cluster):
            raise ValueError("Cluster object must be provided for proxy jumping.")
        user_at = f"{username}@" if username != "" else ""
        jump = _generate_jump(user_at, server, cluster).removeprefix("-J ")
        lines.append(f"\tProxyJump {jump}")
    # Port forwarding
    if local_forwarding is not None:
        if not all(isinstance(p, int) for p in local_forwarding):
            raise ValueError("Local forwarding ports must be integers.")
        lines.append(f"\tLocalForward {local_forwarding[0]} localhost:{local_forwarding[1]}")
    if remote_forwarding is not None:
        if not all(isinstance(p, int) for p in remote_forwarding):
            raise ValueError("Remote forwarding ports must be integers.")
        lines.append(f"\tRemoteForward {remote_forwarding[0]} localhost:{remote_forwarding[1]}")
    if dynamic_forwarding is not None:
        if not isinstance(dynamic_forwarding, int):
            raise ValueError("Dynamic forwarding port must be an integer.")
        lines.append(f"\tDynamicForward {dynamic_forwarding}")
    # Additional
    if trusted_graphical:
        lines += ["\tForwardX11 yes", "\tForwardX11Trusted yes"]
    elif graphical:
        lines.append("\tForwardX11 yes")
    if compress:
        lines.append("\tCompression yes")
    if quiet:
        lines.append("\tLogLevel QUIET")
    return '\n'.join(lines) + '\n'


def generate_cluster_config(
        cluster: Cluster,
        identity: Identity | None = None,
        username: str | None = None,
        **options,
) -> str:
    blocks = [f"# {cluster.name} (generated by EasySSH)\n"]
    for category in cluster.categories.values():
        for server in category.values():
            blocks.append(generate_config(server=server,
                                          cluster=cluster,
                                          identity=identity,
                                          username=username,
                                          **options))
    return '\n'.join(blocks)
