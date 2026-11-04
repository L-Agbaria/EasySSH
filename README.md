# EasySSH
_This open-source tool follows an MIT license, created by Laith Agabria._

This a personal project to build an interactive and easy to use tool for generating and automatic SSH/SCP connections, with the main focus being scientific students being introduced to clusters.

## Requirements
Supported operating system:
 - Linux
 - MacOS
 - Windows 10/11

Requires Python 3.11+ to be installed.

## How to setup
Clone the content of this repository then download the cluster information folder (if available), it is recommended that you move this cluster folder into the `data/clusters` folder, but you can simply navigate to its location later on if you prefer not to do so.

Once all the downloads are complete open a terminal (or PowerShell) in the code location and run `python3 ui.py` (or however you run Python code), this will launch the application window which you can navigate to generate SSH/SCP commands, generate identity keys, or read basic tutorials (or markdowns).

## Application navigation
The application window is separated into three main parts: Header (top), Server tree (left), and Tabs (right).

### Header
The header contains four buttons labeled: `Clusters`, `Identities`, `Tutorials`, and `Reload`.
The first three buttons are to set the source folder that can be used by the application to generate objects, these objects are then used to make things interactive and generate commands correctly. Currently it is only possible to load from one folder at a time for any given source, and you must click the `Reload` button if you make any modifications outside the application.

Besides the buttons, there is also a quick summary of the object counts or last action taken on top right!

### Server tree
The server tree contains information parse from correctly configured cluster folders, there will be further explanations on how to create your own cluster folder below for those who are interested.
Parsed clustered show as main branches of the tree, with categories acting as secondary levels, and then `servers` as the leaves that you could connect to. Both clusters and categories can be minimized, however servers are the only selectable.

You will need to select a server to generate any command!

### Tabs
There are three main tabs you can navigate between: `Connect`, `Manage identities`, and `Read tutorials`.
- In `Connect` you are able to select an identity key that you would like to use with the server, a username you'd like to make the connection through, and possible configurations you would like to use. After completing your credentials you can select one of two options, `SSH` and `File transfer`, which allow you to either form a maintained connection with the server (SSH) or send a file between your computer and a server (SCP). After completing your configuration, you can generate the command and copy-paste it in your terminal to connect. Below everything is a `Description` box which contains information about the selected server, obtained from the imported cluster data.
- In `Manage identities` you are able to view the OpenSSH keys (identities) saved in your `Identities` source folder, you are able to create and delete identities here as well. It is recommended you add a password to your identities, however leaving them empty allows for passwordless logins.
- In `Read tutorials` you are able to very basically visualize markdown files, the intent is for there to be tutorials you are able to follow through and improve your skills until you no longer need this application.

There will be tutorials that explain how to understand port forwarding and passing identities!

## How to use
Now that you have completed the setup and gotten an understanding of how to navigate the application, you should be able to easily use this application as well.
Here is a step-by-step process:
1. Start the application,
2. Select a server,
3. Configure your identity and settings,
4. Generate and copy the command for your terminal (or PowerShell).

Congratulations, you have just seen how Easy SSH commands really are!
Although terminal commands can appear slightly scary to start with, the (future) tutorials should hopefully gently introduce you to them.

> One day you will stop using this application, I hope it is because you no longer need it.

## Additional information
This section is extra and only intended for whoever is interested in learning how this application works, or those interesting in setting up a cluster folder that can be directly imported.

### Code structure
The program is structured to contain the following classes:
 - KeyType (StrEnum): Holds the values of OpenSSH key types to be used more cleanly by the code.
 - Identity: Contains basic information that is obtained from a specific private key location, it manages everything relating to keys/identities.
 - Server: The most basic unit in a cluster setup, it is always part of a category and contains the IDs of both as well as the hostname and possible jump server ID information.
 - Category: Acts as a collection point of servers and contains the information that will be passed to them during creation, it is created for easier organizations but limits server variability.
 - Cluster: The main component that holds information about the different categories and policies, current version of the application doesn't enforce or display these policies.

The default data path is a folder called `data` within the calling directory of the `ui.py`, however this default path, as well as the default username can be modified in the `config.py` file. Additionally, running this program by directly accessing the functions, e.g. the `main.py` example file, would allow for richer explanations about each object by printing them.

Due to Windows 10/11 not supporting `ssh-copy-id` commands natively, there was no (very) easy way to create a function that generates the commands without having to setup different sections of code for different operating systems. The sending of public keys will be instead shown in a tutorial, as that gives them more legitimacy.

### How to create a cluster folder
To create a directly importable cluster folder, it will need to have at least one file called `manifest.json` which will contain information how to parse the categories and servers.

The code automatically recursively searches through whichever source directory is selected to find the manifest file, and then looks for the related category files with the manifest as the source.

The folder name doesn't really matter, however making it easy to relate would be the nice thing to do. Below are examples of how to create a `manifest.json` file, as well as a simple category file.

#### An example of a cluster manifest.json:
```json
{
    "id": "clusterID",
    "name": "Cluster name",
    "hostname": "example.com",
    "description": "Introduction about the cluster.",
    "ssh_key_policy": {
        "allowed_algorithm": [
            "ed25519"
        ],
        "preferred_algorithm": "ed25519"
    },

    "categories": {
        "gateway.json": {
            "id": "gateway",
            "name": "Gateways",
            "description": "Remote entry points.",
            "connect_through": null,
            "subdomain": false
        },
        "category.json": {
            "id": "cat",
            "name": "Category name",
            "description": "Category purpose.",
            "connect_through": {
                "category_id": "gateway",
                "server_id": "main"
            },
            "subdomain": true
        }
    }
}
```

#### An example of a category.json:
```json
{
    "id": "cat",
    "name": "Category name",
    "servers": [
        {
            "id": "node1",
            "name": "GPU Server",
            "hostname": "gpu.node",
            "port": 22,
            "description": "AI node."
        }
    ]
}
```