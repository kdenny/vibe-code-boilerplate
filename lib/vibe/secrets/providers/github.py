"""GitHub Actions secrets provider (stub)."""

from lib.vibe.secrets.providers.base import Secret, SecretProvider


class GitHubSecretsProvider(SecretProvider):
    """
    GitHub Actions secrets provider.

    Uses the GitHub CLI (gh) to manage repository and environment secrets.
    """

    def __init__(self, owner: str | None = None, repo: str | None = None):
        self._owner = owner
        self._repo = repo

    @property
    def name(self) -> str:
        return "github"

    def authenticate(self) -> bool:
        """Check if gh CLI is authenticated."""
        import subprocess

        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def list_secrets(self, environment: str | None = None) -> list[Secret]:
        """List GitHub Actions secrets."""
        import subprocess

        if not self._owner or not self._repo:
            return []

        try:
            cmd = ["gh", "secret", "list", "-R", f"{self._owner}/{self._repo}"]
            if environment:
                cmd.extend(["--env", environment])

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            secrets = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    name = parts[0] if parts else ""
                    secrets.append(
                        Secret(
                            name=name,
                            value=None,  # GitHub doesn't expose values
                            environment=environment or "repository",
                            provider=self.name,
                        )
                    )
            return secrets
        except subprocess.CalledProcessError:
            return []

    def get_secret(self, name: str, environment: str) -> Secret | None:
        """Get a secret (value not available from GitHub)."""
        secrets = self.list_secrets(environment)
        for secret in secrets:
            if secret.name == name:
                return secret
        return None

    def set_secret(self, name: str, value: str, environment: str) -> bool:
        """Set a GitHub Actions secret."""
        import subprocess

        if not self._owner or not self._repo:
            return False

        try:
            cmd = ["gh", "secret", "set", name, "-R", f"{self._owner}/{self._repo}"]
            if environment != "repository":
                cmd.extend(["--env", environment])

            subprocess.run(cmd, input=value, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def delete_secret(self, name: str, environment: str) -> bool:
        """Delete a GitHub Actions secret."""
        import subprocess

        if not self._owner or not self._repo:
            return False

        try:
            cmd = ["gh", "secret", "delete", name, "-R", f"{self._owner}/{self._repo}"]
            if environment != "repository":
                cmd.extend(["--env", environment])

            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def sync_from_local(self, env_file: str, environment: str) -> dict[str, bool]:
        """Sync secrets from a local env file to GitHub."""
        from pathlib import Path

        results: dict[str, bool] = {}
        env_path = Path(env_file)

        if not env_path.exists():
            return results

        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    results[key] = self.set_secret(key, value, environment)

        return results
