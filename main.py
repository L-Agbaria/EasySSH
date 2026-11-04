from config import *
from identity import KeyType, Identity, get_identities
from server import Server, Category, Cluster, get_clusters
from functions import *


if __name__=="__main__":
    identities: list[Identity] = get_identities(DATA/"identities")
    clusters: list[Cluster] = get_clusters(DATA/"clusters")

    cluster = clusters[0]
    server = cluster["compute"]["101"]
    identity = identities[0]

    print(generate_ssh(server=server, 
                       cluster=cluster,
                       identity=identity,
                       local_forwarding=(8080, 8080),
                       ))
    
    print(generate_scp(server=server, 
                       cluster=cluster,
                       sources=Path("main.py"), 
                       destination=Path("~/main.py"),
                       username="user",
                       ))
