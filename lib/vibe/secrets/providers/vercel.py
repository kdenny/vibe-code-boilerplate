"""Vercel secrets/environment variables provider."""

import subprocess

from lib.vibe.secrets.providers.base import Secret, SecretProvider


class VercelSecretsProvider(SecretProvider):
    """
    Vercel environment variables provider.

    Uses the Vercel CLI to manage environment variables.
    See: https://vercel.com/docs/cli/env
    """

    def __init__(self, project_id: str | None = None):
        self._project_id = project_id

    @property
    def name(self) -> str:
        return "vercel"

    def authenticate(self) -> bool:
        """Check if Vercel CLI is authenticated."""
        try:
            result = subprocess.run(
                ["vercel", "whoami"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def list_secrets(self, environment: str | None = None) -> list[Secret]:
        """List Vercel environment variables."""
        cmd = ["vercel", "env", "ls"]
        if environment:
            cmd.append(environment)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to list env vars: {result.stderr}")

            # Parse the output (table format)
            secrets = []
            lines = result.stdout.strip().split("\n")
            # Skip header lines
            for line in lines[2:]:  # Skip header and separator
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    env = parts[1] if len(parts) > 1 else "all"
                    secrets.append(
                        Secret(
                            name=name,
                            value="<hidden>",  # Vercel ls doesn't show values
                            environment=env,
                            provider="vercel",
                        )
                    )
            return secrets
        except FileNotFoundError:
            raise RuntimeError("Vercel CLI not found. Install with: npm i -g vercel")

    def get_secret(self, name: str, environment: str) -> Secret | None:
        """Get a specific environment variable."""
        secrets = self.list_secrets(environment)
        for secret in secrets:
            if secret.name == name:
                return secret
        return None

    def set_secret(self, name: str, value: str, environment: str) -> bool:
        """
        Set a Vercel environment variable.

        Environment can be: production, preview, development, or all.
        """
        # Vercel CLI prompts for value, so we need to pipe it
        cmd = ["vercel", "env", "add", name, environment]

        try:
            result = subprocess.run(
                cmd,
                input=f"{value}\n",
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            raise RuntimeError("Vercel CLI not found. Install with: npm i -g vercel")

    def delete_secret(self, name: str, environment: str) -> bool:
        """Delete a Vercel environment variable."""
        cmd = ["vercel", "env", "rm", name, environment, "-y"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            raise RuntimeError("Vercel CLI not found. Install with: npm i -g vercel")

    def sync_from_local(self, env_file: str, environment: str) -> dict[str, bool]:
        """
        Sync secrets from a local env file to Vercel.

        Returns a dict mapping secret names to success status.
        """
        results: dict[str, bool] = {}

        # Parse the env file
        secrets = self._parse_env_file(env_file)

        for name, value in secrets.items():
            try:
                success = self.set_secret(name, value, environment)
                results[name] = success
            except (subprocess.CalledProcessError, OSError, RuntimeError):
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

    def pull_to_local(self, env_file: str, environment: str) -> bool:
        """
        Pull environment variables from Vercel to a local file.

        This uses Vercel's built-in env pull command.
        """
        cmd = ["vercel", "env", "pull", env_file]
        if environment != "development":
            cmd.extend(["--environment", environment])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            raise RuntimeError("Vercel CLI not found. Install with: npm i -g vercel")
