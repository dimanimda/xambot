"""Generate a Fernet key for MULTIBOT_ENCRYPTION_KEY."""

from cryptography.fernet import Fernet


def main() -> None:
    key = Fernet.generate_key()
    print(f"MULTIBOT_ENCRYPTION_KEY={key.decode()}")


if __name__ == "__main__":
    main()
