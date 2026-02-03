"""Fly.io secrets provider."""

import subprocess

from lib.vibe.secrets.providers.base import Secret, SecretProvider


class FlySecretsProvider(SecretProvider):
    """
    Fly.io secrets provider.

    Uses the Fly CLI (`flyctl` or `fly`) to manage secrets.
    See: https://fly.io/docs/reference/secrets/
    """

    def __init__(self, app_name: str | None = None):
        self._app_name = app_name
        self._fly_cmd = self._detect_fly_command()

    def _detect_fly_command(self) -> str:
        """Detect whether to use 'fly' or 'flyctl' command."""
        for cmd in ["fly", "flyctl"]:
            try:
                result = subprocess.run(
                    [cmd, "version"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return cmd
            except FileNotFoundError:
                continue
        return "fly"  # Default, will fail if not installed

    @property
    def name(self) -> str:
        return "fly"

    def authenticate(self) -> bool:
        """Check if Fly CLI is authenticated."""
        try:
            result = subprocess.run(
                [self._fly_cmd, "auth", "whoami"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def list_secrets(self, environment: str | None = None) -> list[Secret]:
        """
        List Fly.io secrets.

        Note: Fly.io only shows secret names, not values.
        """
        if not self._app_name:
            raise RuntimeError("App name not configured. Set app_name in provider config.")

        cmd = [self._fly_cmd, "secrets", "list", "-a", self._app_name, "--json"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to list secrets: {result.stderr}")

            import json

            secrets_data = json.loads(result.stdout) if result.stdout.strip() else []
            return [
                Secret(
                    name=s.get("Name", ""),
                    value="<hidden>",  # Fly doesn't expose values
                    environment=environment or "production",
                )
                for s in secrets_data
            ]
        except FileNotFoundError:
            raise RuntimeError(
                "Fly CLI not found. Install from https://fly.io/docs/hands-on/install-flyctl/"
            )

    def get_secret(self, name: str, environment: str) -> Secret | None:
        """
        Get a specific secret.

        Note: Fly.io doesn't allow reading secret values, only listing names.
        """
        secrets = self.list_secrets(environment)
        for secret in secrets:
            if secret.name == name:
                return secret
        return None

    def set_secret(self, name: str, value: str, environment: str) -> bool:
        """Set a Fly.io secret."""
        if not self._app_name:
            raise RuntimeError("App name not configured. Set app_name in provider config.")

        cmd = [
            self._fly_cmd,
            "secrets",
            "set",
            f"{name}={value}",
            "-a",
            self._app_name,
            "--stage",  # Stage the change, don't deploy yet
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            raise RuntimeError(
                "Fly CLI not found. Install from https://fly.io/docs/hands-on/install-flyctl/"
            )

    def delete_secret(self, name: str, environment: str) -> bool:
        """Delete a Fly.io secret."""
        if not self._app_name:
            raise RuntimeError("App name not configured. Set app_name in provider config.")

        cmd = [
            self._fly_cmd,
            "secrets",
            "unset",
            name,
            "-a",
            self._app_name,
            "--stage",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            raise RuntimeError(
                "Fly CLI not found. Install from https://fly.io/docs/hands-on/install-flyctl/"
            )

    def sync_from_local(self, env_file: str, environment: str) -> dict[str, bool]:
        """
        Sync secrets from a local env file to Fly.io.

        Returns a dict mapping secret names to success status.
        """
        results: dict[str, bool] = {}

        # Parse the env file
        secrets = self._parse_env_file(env_file)

        for name, value in secrets.items():
            try:
                success = self.set_secret(name, value, environment)
                results[name] = success
            except Exception:
                results[name] = False

        return results

    def _parse_env_file(self, env_file: str) -> dict[str, str]:
        """Parse a .env file into a dict."""
        secrets: dict[str, str] = {}
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        # Remove quotes if present
                        value = value.strip().strip('"').strip("'")
                        secrets[key.strip()] = value
        except FileNotFoundError:
            raise RuntimeError(f"Env file not found: {env_file}")
        return secrets

    def deploy(self) -> bool:
        """
        Deploy staged secrets.

        Call this after setting multiple secrets to deploy them all at once.
        """
        if not self._app_name:
            raise RuntimeError("App name not configured.")

        cmd = [self._fly_cmd, "secrets", "deploy", "-a", self._app_name]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
