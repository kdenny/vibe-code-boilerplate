"""Tests for git worktree management."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.vibe.git.worktrees import (
    Worktree,
    cleanup_stale_worktrees,
    cleanup_worktree,
    create_worktree,
    get_primary_repo_root,
    get_worktree_base_path,
    list_worktrees,
)


class TestWorktreeDataclass:
    """Tests for Worktree dataclass."""

    def test_worktree_defaults(self) -> None:
        wt = Worktree(path="/path/to/wt", branch="feature", commit="abc123")
        assert wt.path == "/path/to/wt"
        assert wt.branch == "feature"
        assert wt.commit == "abc123"
        assert wt.is_main is False

    def test_worktree_is_main(self) -> None:
        wt = Worktree(path="/path/to/main", branch="main", commit="def456", is_main=True)
        assert wt.is_main is True


class TestGetPrimaryRepoRoot:
    """Tests for get_primary_repo_root function."""

    def test_primary_repo_root_normal_repo(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = "/home/user/project/.git\n"

        with patch("lib.vibe.git.worktrees.subprocess.run", return_value=mock_result):
            root = get_primary_repo_root()

        # Path may be resolved with system-specific prefix (e.g. /System/Volumes/Data on macOS)
        assert str(root).endswith("/home/user/project") or root.name == "project"

    def test_primary_repo_root_from_worktree(self) -> None:
        # When in a worktree, git_dir is .git/worktrees/<name>
        mock_result = MagicMock()
        mock_result.stdout = "/home/user/project/.git/worktrees/feature-123\n"

        with patch("lib.vibe.git.worktrees.subprocess.run", return_value=mock_result):
            root = get_primary_repo_root()

        # Should resolve to the primary repo, not the worktree
        # Path may be resolved with system-specific prefix
        assert str(root).endswith("/home/user/project") or root.name == "project"


class TestGetWorktreeBasePath:
    """Tests for get_worktree_base_path function."""

    def test_default_base_path(self) -> None:
        mock_config = {"worktrees": {"base_path": "../{repo}-worktrees"}}

        with (
            patch("lib.vibe.git.worktrees.load_config", return_value=mock_config),
            patch("lib.vibe.git.worktrees.get_primary_repo_root") as mock_root,
        ):
            mock_root.return_value = Path("/home/user/my-project")
            base_path = get_worktree_base_path()

        assert "my-project-worktrees" in str(base_path)

    def test_custom_base_path(self) -> None:
        mock_config = {"worktrees": {"base_path": "/custom/worktrees"}}

        with (
            patch("lib.vibe.git.worktrees.load_config", return_value=mock_config),
            patch("lib.vibe.git.worktrees.get_primary_repo_root") as mock_root,
        ):
            mock_root.return_value = Path("/home/user/project")
            base_path = get_worktree_base_path()

        assert str(base_path) == "/custom/worktrees"

    def test_empty_config_uses_default(self) -> None:
        mock_config = {}

        with (
            patch("lib.vibe.git.worktrees.load_config", return_value=mock_config),
            patch("lib.vibe.git.worktrees.get_primary_repo_root") as mock_root,
        ):
            mock_root.return_value = Path("/home/user/repo")
            base_path = get_worktree_base_path()

        assert "repo-worktrees" in str(base_path)


class TestCreateWorktree:
    """Tests for create_worktree function."""

    def test_create_worktree_new_branch(self, tmp_path: Path) -> None:
        """Test creating a worktree with a new branch."""
        worktree_base = tmp_path / "worktrees"
        repo_root = tmp_path / "repo"

        # Mock subprocess calls
        def mock_run(cmd, *args, **kwargs):
            result = MagicMock()
            if "rev-parse" in cmd and "--verify" in cmd:
                # Branch doesn't exist
                result.returncode = 1
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.stdout = "abc123def"
            elif "worktree" in cmd and "add" in cmd:
                result.returncode = 0
            result.returncode = getattr(result, "returncode", 0)
            return result

        with (
            patch("lib.vibe.git.worktrees.get_primary_repo_root", return_value=repo_root),
            patch("lib.vibe.git.worktrees.get_worktree_base_path", return_value=worktree_base),
            patch("lib.vibe.git.worktrees.subprocess.run", side_effect=mock_run),
            patch("lib.vibe.git.worktrees.add_worktree") as mock_add,
        ):
            wt = create_worktree("feature-123", "main")

        assert wt.branch == "feature-123"
        assert wt.commit == "abc123def"
        assert wt.is_main is False
        mock_add.assert_called_once()

    def test_create_worktree_existing_branch(self, tmp_path: Path) -> None:
        """Test creating a worktree for an existing branch."""
        worktree_base = tmp_path / "worktrees"
        repo_root = tmp_path / "repo"

        call_count = 0

        def mock_run(cmd, *args, **kwargs):
            nonlocal call_count
            result = MagicMock()
            if "rev-parse" in cmd and "--verify" in cmd:
                # Branch exists
                result.returncode = 0
            elif "rev-parse" in cmd and "HEAD" in cmd:
                result.stdout = "existingcommit123"
            result.returncode = getattr(result, "returncode", 0)
            call_count += 1
            return result

        with (
            patch("lib.vibe.git.worktrees.get_primary_repo_root", return_value=repo_root),
            patch("lib.vibe.git.worktrees.get_worktree_base_path", return_value=worktree_base),
            patch("lib.vibe.git.worktrees.subprocess.run", side_effect=mock_run),
            patch("lib.vibe.git.worktrees.add_worktree"),
        ):
            wt = create_worktree("existing-branch")

        assert wt.branch == "existing-branch"
        assert wt.commit == "existingcommit123"


class TestCleanupWorktree:
    """Tests for cleanup_worktree function."""

    def test_cleanup_worktree_success(self) -> None:
        with (
            patch("lib.vibe.git.worktrees.subprocess.run") as mock_run,
            patch("lib.vibe.git.worktrees.remove_worktree") as mock_remove,
        ):
            mock_run.return_value = MagicMock(returncode=0)
            result = cleanup_worktree("/path/to/worktree")

        assert result is True
        mock_remove.assert_called_once_with("/path/to/worktree")

    def test_cleanup_worktree_force(self) -> None:
        with (
            patch("lib.vibe.git.worktrees.subprocess.run") as mock_run,
            patch("lib.vibe.git.worktrees.remove_worktree"),
        ):
            mock_run.return_value = MagicMock(returncode=0)
            cleanup_worktree("/path/to/worktree", force=True)

        call_args = mock_run.call_args[0][0]
        assert "--force" in call_args

    def test_cleanup_worktree_failure(self) -> None:
        import subprocess

        with (
            patch("lib.vibe.git.worktrees.subprocess.run") as mock_run,
            patch("lib.vibe.git.worktrees.remove_worktree") as mock_remove,
        ):
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            result = cleanup_worktree("/path/to/worktree")

        assert result is False
        mock_remove.assert_not_called()


class TestListWorktrees:
    """Tests for list_worktrees function."""

    def test_list_worktrees_multiple(self) -> None:
        porcelain_output = """worktree /home/user/project
HEAD abc123
branch refs/heads/main

worktree /home/user/project-worktrees/feature-1
HEAD def456
branch refs/heads/feature-1

worktree /home/user/project-worktrees/feature-2
HEAD ghi789
branch refs/heads/feature-2
"""
        mock_result = MagicMock()
        mock_result.stdout = porcelain_output

        with patch("lib.vibe.git.worktrees.subprocess.run", return_value=mock_result):
            worktrees = list_worktrees()

        assert len(worktrees) == 3
        assert worktrees[0].path == "/home/user/project"
        assert worktrees[0].branch == "main"
        assert worktrees[0].commit == "abc123"
        assert worktrees[1].path == "/home/user/project-worktrees/feature-1"
        assert worktrees[1].branch == "feature-1"
        assert worktrees[2].branch == "feature-2"

    def test_list_worktrees_single(self) -> None:
        porcelain_output = """worktree /home/user/project
HEAD abc123
branch refs/heads/main
"""
        mock_result = MagicMock()
        mock_result.stdout = porcelain_output

        with patch("lib.vibe.git.worktrees.subprocess.run", return_value=mock_result):
            worktrees = list_worktrees()

        assert len(worktrees) == 1
        assert worktrees[0].branch == "main"

    def test_list_worktrees_bare_repo(self) -> None:
        porcelain_output = """worktree /home/user/project.git
bare

worktree /home/user/project-worktrees/main
HEAD abc123
branch refs/heads/main
"""
        mock_result = MagicMock()
        mock_result.stdout = porcelain_output

        with patch("lib.vibe.git.worktrees.subprocess.run", return_value=mock_result):
            worktrees = list_worktrees()

        assert len(worktrees) == 2
        assert worktrees[0].is_main is True  # bare repo
        assert worktrees[1].is_main is False

    def test_list_worktrees_empty(self) -> None:
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("lib.vibe.git.worktrees.subprocess.run", return_value=mock_result):
            worktrees = list_worktrees()

        assert worktrees == []


class TestCleanupStaleWorktrees:
    """Tests for cleanup_stale_worktrees function."""

    def test_cleanup_stale_worktrees_removes_nonexistent(self, tmp_path: Path) -> None:
        # Create one existing path and one that doesn't exist
        existing_path = tmp_path / "existing"
        existing_path.mkdir()
        nonexistent_path = str(tmp_path / "nonexistent")

        state = {"active_worktrees": [str(existing_path), nonexistent_path]}

        with (
            patch("lib.vibe.git.worktrees.load_state", return_value=state),
            patch("lib.vibe.git.worktrees.remove_worktree") as mock_remove,
        ):
            cleaned = cleanup_stale_worktrees()

        assert cleaned == [nonexistent_path]
        mock_remove.assert_called_once_with(nonexistent_path)

    def test_cleanup_stale_worktrees_none_stale(self, tmp_path: Path) -> None:
        # Create all paths that exist
        path1 = tmp_path / "wt1"
        path2 = tmp_path / "wt2"
        path1.mkdir()
        path2.mkdir()

        state = {"active_worktrees": [str(path1), str(path2)]}

        with (
            patch("lib.vibe.git.worktrees.load_state", return_value=state),
            patch("lib.vibe.git.worktrees.remove_worktree") as mock_remove,
        ):
            cleaned = cleanup_stale_worktrees()

        assert cleaned == []
        mock_remove.assert_not_called()

    def test_cleanup_stale_worktrees_all_stale(self) -> None:
        state = {"active_worktrees": ["/nonexistent/path1", "/nonexistent/path2"]}

        with (
            patch("lib.vibe.git.worktrees.load_state", return_value=state),
            patch("lib.vibe.git.worktrees.remove_worktree") as mock_remove,
        ):
            cleaned = cleanup_stale_worktrees()

        assert len(cleaned) == 2
        assert mock_remove.call_count == 2

    def test_cleanup_stale_worktrees_empty_state(self) -> None:
        state = {"active_worktrees": []}

        with (
            patch("lib.vibe.git.worktrees.load_state", return_value=state),
            patch("lib.vibe.git.worktrees.remove_worktree") as mock_remove,
        ):
            cleaned = cleanup_stale_worktrees()

        assert cleaned == []
        mock_remove.assert_not_called()
