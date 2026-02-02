"""Fly.io secrets provider (stub)."""

from lib.vibe.secrets.providers.base import Secret, SecretProvider


class FlySecretsProvider(SecretProvider):
    """
    Fly.io secrets provider.

    NOTE: This is a stub implementation. Full implementation would use
    the Fly CLI to manage secrets.

    See: https://fly.io/docs/reference/secrets/
    """

    def __init__(self, app_name: str | None = None):
        self._app_name = app_name

    @property
    def name(self) -> str:
        return "fly"

    def authenticate(self) -> bool:
        """Check if Fly CLI is authenticated."""
        import subprocess

        try:
            result = subprocess.run(
                ["fly", "auth", "whoami"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def list_secrets(self, environment: str | None = None) -> list[Secret]:
        """List Fly.io secrets."""
        # Stub - would use: fly secrets list -a app_name
        raise NotImplementedError("Fly.io secrets listing not yet implemented")

    def get_secret(self, name: str, environment: str) -> Secret | None:
        """Get a specific secret (Fly doesn't expose values)."""
        # Fly.io doesn't allow reading secret values, only listing names
        raise NotImplementedError("Fly.io secrets retrieval not yet implemented")

    def set_secret(self, name: str, value: str, environment: str) -> bool:
        """Set a Fly.io secret."""
        # Stub - would use: fly secrets set NAME=value -a app_name
        raise NotImplementedError("Fly.io secrets setting not yet implemented")

    def delete_secret(self, name: str, environment: str) -> bool:
        """Delete a Fly.io secret."""
        # Stub - would use: fly secrets unset NAME -a app_name
        raise NotImplementedError("Fly.io secrets deletion not yet implemented")

    def sync_from_local(self, env_file: str, environment: str) -> dict[str, bool]:
        """Sync secrets from a local env file to Fly.io."""
        raise NotImplementedError("Fly.io secrets syncing not yet implemented")
