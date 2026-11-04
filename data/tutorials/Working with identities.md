# Working with identities

Identities are an important part of SSH, they allow servers to limit access to certain people and things such as passwordless login.
Due to Windows 10/11 not having "ssh-copy-id" natively, there was no program created to automatically generate the command for sending over public keys correctly. Instead, this tutorial will teach you to:
 1. Send over an existing public keys,
 2. How to create private keys,
 3. How to use existing private keys in SSH and SCP commands,
 4. How to re-create public keys from an existing private key.

## 1. Sending public keys
This process is identical for both Linux and MacOS, you simply require a public key!
The command is `ssh-copy-id <destination>`, where destination is typically `<uername>@<hostname>` of the server you want to send the key to.

This command assumes that a public ssh key exists, and will try to send your default (e.g. ~/.ssh/id_ed255919.**pub**) public key to the destination. It will request your password to login, and then you'd be able to directly use this identity to log into the same user in the future.

If you need to specify a specific file, as having one identity for everything is insecure, then you can do that by specifying `-i <path>` (stands for identity) before your destination, giving you:
```bash
ssh-copy-id -i <path> <destination>
```

Windows makes things slightly more complicated, however the general structure (assuming you're connecting to Linux or MacOS) would be:
```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh <destination> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

You would need to modify your public key name directly, and possibly modify the destination location in the SSH command to the default one of the destination machine. For Windows to Windows, you would have the same remarks with the following command:
```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | ssh <destination> "powershell -Command 'New-Item -ItemType Directory -Force -Path C:\Users\username\.ssh; Add-Content -Path C:\Users\username\.ssh\authorized_keys -Value `$input'"
```

>> Note regarding Windows: If you have a Windows Linux Subsystem (WSL) or a Git Bash, you can directly use the Linux/MacOS commands there.

## 2. Create private keys
This process is uniform across all of Linux, MacOS, and Windows 10/11 through the `ssh-keygen` command. This is directly implemented in the program, and you can now learn how it works.

## 3. Using private keys in SSH and SCP

## 4. Generating public keys from private keys
