import subprocess
from pathlib import Path
from enum import StrEnum


class KeyType(StrEnum):
    ED25519 = "ed25519"
    RSA = "rsa"
    ECDSA = "ecdsa"
    DSA = "dsa"
    ED25519_SK = "ed25519-sk"
    ECDSA_SK = "ecdsa-sk"
    MLDSA44_ED25519 = "mldsa44-ed25519"
    UNKNOWN = ""


def is_private_key(
        path: Path,
) -> bool:
    # Try to create a public key, don't generate anything
    result = subprocess.run(
        ["ssh-keygen", "-y", "-f",  str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


class Identity:
    @staticmethod
    def _get_key_type(
            public_key: Path,
        ) -> KeyType:
        # Get public key fields
        fields: list[str] = public_key.read_text(encoding="utf-8").split()
        if len(fields) == 0:
            raise ValueError(f"Empty public key file: {public_key}")
        # Get algorithm
        algorithm: str = fields[0]
        match algorithm:
            case "ssh-ed25519":
                return KeyType.ED25519
            case "ssh-rsa":
                return KeyType.RSA
            case "ecdsa-sha2-nistp256" | "ecdsa-sha2-nistp384" | "ecdsa-sha2-nistp521":
                return KeyType.ECDSA
            case "ssh-dss":
                return KeyType.DSA
            case "sk-ssh-ed25519@openssh.com":
                return KeyType.ED25519_SK
            case "sk-ecdsa-sha2-nistp256@openssh.com":
                return KeyType.ECDSA_SK
            case "ssh-mldsa44-ed25519" | "ssh-mldsa44-ed25519@openssh.com":
                return KeyType.MLDSA44_ED25519
            case _:
                print(f"Err ({public_key.stem}.pub) Unsupported SSH key algorithm: {algorithm}")
                return KeyType.UNKNOWN
        
    @staticmethod
    def _get_public_key(
            private_key: Path,
        ) -> Path:
        # Check if public key already exists
        public_key: Path = Path(f"{private_key}.pub")
        if public_key.exists():
            return public_key
        # Create a new one
        result = subprocess.run(
            ["ssh-keygen", "-y", "-f", str(private_key)],
            stdout=subprocess.PIPE,
            text=True,
            check=True,
        )
        public_key.write_text(result.stdout, encoding="utf-8")
        return public_key
    
    @staticmethod
    def generate_identity(
            name: str,
            identities_dir: Path,
            key_type: KeyType = KeyType.ED25519,
        ):
        # Verify
        if key_type == KeyType.DSA:
            raise ValueError("DSA key generation is not supported by current OpenSSH.")
        if not identities_dir.exists():
            raise FileNotFoundError("Provided identities directory not found,", identities_dir)
        # File location
        private_key: Path = identities_dir / name
        public_key: Path = Path(f"{private_key}.pub")
        if private_key.exists() or public_key.exists():
            print(f"Identity {name} already exists.")
        else:  # Generate key
            subprocess.run(
                [
                    "ssh-keygen",
                    "-q",
                    "-t", key_type.value,
                    "-C", name,
                    "-f", str(private_key),
                ],
                check=True,
            )
        # Create identity
        return Identity(name, private_key)

    def __init__(
            self, 
            name: str, 
            private_key: Path,
        ):
        self.name: str = name
        self.private_key: Path = private_key
        self.public_key: Path = Identity._get_public_key(self.private_key)
        self.key_type: KeyType = Identity._get_key_type(self.public_key)

    def __repr__(self) -> str:
        return f"{'='*32}\n" \
               f"{' '*12}Identity\n" \
               f"Identity: {self.name}\n" \
               f"Private key: {self.private_key}\n" \
               f"Public key: {self.public_key}\n" \
               f"Key type: {self.key_type}\n" \
               f"{'='*32}"
    
    def delete_identity(self) -> None:
        self.private_key.unlink()
        self.public_key.unlink()
    

def get_identities(
        idn_dir: Path,
) -> list[Identity]:
    identities: list[Identity] = []
    for path in idn_dir.rglob('*'):
        if path.is_file() and is_private_key(path):
            identities.append(Identity(
                name=path.stem,
                private_key=path
            ))
    return identities

def wipe_identities(
        idn_list: list[Identity],
) -> None:
    for idn in idn_list:
        idn.delete_identity()
    idn_list.clear()
