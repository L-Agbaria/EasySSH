import json
from pathlib import Path
from identity import KeyType


class Server:
    def __init__(
            self,
            category_id: str, 
            server_id: str,
            name: str,
            hostname: str,
            port: int,
            description: str | None,
            connect_through: tuple[str, str],
        ):
        self.category_id = category_id
        self.server_id = server_id
        self.name = name
        self.hostname = hostname
        self.port = port
        self.description = description if description is not None else ""
        self.connect_through = connect_through

    def __repr__(self) -> str:
        if self.connect_through != ("", ""):
            gateway = f"Must connect through " \
                      f'"{self.connect_through[0]} - {self.connect_through[1]}"'
        else:
            gateway = "Can connect directly"
        return f"{'='*32}\n" \
               f"{' '*13}Server\n" \
               f"CategoryID: {self.category_id}\n" \
               f"ServerID: {self.server_id}\n" \
               f"Name: {self.name}\n" \
               f"Hostname: {self.hostname}\n" \
               f"Port: {self.port}\n" \
               f"{gateway}\n" \
               f"{'='*32}"


def get_server(
    file: dict,
    connect_through: dict,
    cluster_hostname: str,
) -> dict[str, Server]:
    # Attempt to read file content
    try:
        with open(file, 'r') as f:
            server_content = json.load(f)
    except Exception as err:
        print(f"Encountered error {err} while parsing servers in {file}, skipping...")
        return {}
    # Check if there are any servers
    server_list: list[dict] = server_content["servers"]
    if server_list is None:
        return {}
    # Populate servers
    servers = {}
    for server in server_list:
        servers[server["id"]] = Server(
            category_id=server_content["id"],
            server_id=server["id"],
            name=server["name"],
            hostname=f"{server['hostname']}.{cluster_hostname}" if cluster_hostname != "" else server["hostname"],
            port=server["port"],
            description=server["description"],
            connect_through=connect_through,
        )
    return servers


class Category:
    def __init__(
            self,
            id: str,
            name: str,
            description: str,
            connect_through: dict | None,
            file_path : Path,
            cluster_hostname: str,
        ):
        self.id = id
        self.name = name
        self.description = description
        self.connect_through = connect_through
        self.file_path = file_path
        self.servers: dict[str, Server] = get_server(file_path, 
                                                     connect_through, 
                                                     cluster_hostname)

    def __getitem__(
            self, 
            server_id: str,
        ) -> Server:
        return self.servers[server_id]
    
    def __len__(self) -> int:
        return len(self.servers)
    
    def keys(self) -> list[str]:
        return list(self.servers.keys())
    
    def values(self) -> list[Server]:
        return list(self.servers.values())
    
    def items(self) -> list[tuple]:
        return self.servers.items()
    

def get_categories(
        cluster: Path,
        cluster_hostname: str,
        category_content: dict,
) -> dict[str, Category]:
    # No categories exist
    if category_content is None:
        return {}
    # Iterate over all categories
    categories = {}
    for category in category_content.keys():
        # Confirm category exists and can be read
        file: Path = cluster / category
        if not file.exists():
            print(f"Category {file.stem} does not exist in {cluster}.")
            continue
        if not file.suffix == ".json":
            print(f"Category {file.stem} is not stored as json.")
            continue
        # Generate servers within category
        cat = category_content[category]
        if cat["connect_through"] is not None:
            connect_through = (cat["connect_through"]["category_id"], 
                               cat["connect_through"]["server_id"])
        else:
            connect_through = ("", "")
        categories[cat["id"]] = Category(
            id=cat["id"],
            name=cat["name"],
            description=cat["description"],
            connect_through=connect_through,
            file_path=file,
            cluster_hostname=cluster_hostname if cat["subdomain"] else "",
        )
    return categories


class Cluster:
    def __init__(
            self,
            id: str,
            name: str,
            hostname: str,
            description: str | None,
            key_policy: list[KeyType],
            preferred_policy: KeyType,
            categories: dict[str, Category],
        ):
        self.id = id
        self.name = name
        self.hostname = hostname
        self.description = description if description is not None else ""
        self.key_policy = key_policy
        self.preferred_policy = preferred_policy
        self.categories = categories
    
    def __repr__(self):
        category_items: list[tuple] = [(key, len(val)) 
                                       for (key, val) in self.categories.items()]
        return f"{'='*32}\n" \
               f"{' '*12}Cluster\n" \
               f"ID: {self.id}\n" \
               f"Name: {self.name}\n" \
               f"Hostname: {self.hostname}\n" \
               f"Description: {self.description}\n" \
               f"Categories:\n" \
               f"{''.join(f'\t{cat_id}: {count} servers.\n' 
                          for (cat_id, count) in category_items)}" \
               f"{'='*32}"
    
    def __getitem__(
            self, 
            category_id: str,
            server_id: str | None = None,
        ) -> Category | Server:
        # For directly using Server.connect_through
        if isinstance(category_id, tuple) and len(category_id) == 2:
            return self.categories[category_id[0]][category_id[1]]
        # For directly using Server.id
        if server_id is not None:
            return self.categories[category_id][server_id]
        # Just get the category
        return self.categories[category_id]

    def read_manifest(
            manifest: Path
        ) -> Cluster:
            pass


def get_policy(
        policy_content: dict,
) -> tuple[list[KeyType], KeyType]:
    # No policy provided
    if policy_content is None:
        return [], KeyType.UNKNOWN
    # Get allowed KeyTypes
    key_policy = []
    if policy_content["allowed_algorithm"] is not None:
        for key in policy_content["allowed_algorithm"]:
            key_policy.append(KeyType(key))
    # Get preferred key
    preferred_key = KeyType.UNKNOWN
    if (key := policy_content["preferred_algorithm"]) is not None:
        preferred_key = KeyType(key)
    return key_policy, preferred_key

def get_clusters(
        clst_dir: Path
) -> list[Cluster]:
    clusters: list[Cluster] = []
    for path in clst_dir.rglob('*'):
        if path.name == "manifest.json":
            # Load content
            try:
                with open(path) as f:
                    content: dict = json.load(f)
            except Exception as err:
                print(f"Encountered error {err} while reading {path}, skipping...")
            # Extract information
            key_policy, preferred_policy = get_policy(content["ssh_key_policy"])
            categories: list[Category] = get_categories(path.parent, 
                                                        content["hostname"], 
                                                        content["categories"])
            # Generate cluster
            clusters.append(Cluster(
                id=content["id"],
                name=content["name"],
                hostname=content["hostname"],
                description=content["description"],
                key_policy=key_policy,
                preferred_policy=preferred_policy,
                categories=categories,
            ))
    return clusters