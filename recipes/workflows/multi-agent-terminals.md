# Multi-Agent Terminal Workflow

When using git worktrees for parallel development, you may run multiple Claude Code sessions simultaneously. Without visual differentiation, it's easy to lose track of which terminal is working on which ticket.

This guide covers terminal setup for managing multiple AI agents effectively.

## iTerm2 Setup (macOS)

### Color-Coded Profiles

iTerm2 supports profile-based theming. Create distinct profiles for each agent context:

1. **Create profiles**: Preferences > Profiles > + (add new)
2. **Set distinct background colors**:

| Profile | Background Color | Purpose |
|---------|------------------|---------|
| Main | Default/dark | Coordination, git ops, ticket management |
| Agent 1 | Slight blue tint (`#1a1a2e`) | First parallel task |
| Agent 2 | Slight green tint (`#1a2e1a`) | Second parallel task |
| Agent 3 | Slight purple tint (`#2e1a2e`) | Third parallel task |

3. **Automatic profile switching** (by directory):
   - Profiles > Advanced > Automatic Profile Switching
   - Add rules like `/Users/*/project-worktrees/*` → Agent profile
   - Rules can match specific ticket prefixes: `/Users/*-worktrees/CITY-*` → Blue profile

### Tab Colors

Right-click any tab → "Edit Tab Color" to set per-tab colors manually. This provides quick visual identification without changing the whole profile.

### Badges

Show the current directory (or ticket number) as an overlay:
- Profiles > General > Badge: `\(path)` or `\(session.name)`
- Makes it immediately visible which worktree you're in
- Custom badge text: `\(user.ticketId)` with Shell Integration

### Session Names

Name your sessions for clarity:
- Right-click tab → Edit Session
- Set name to ticket ID: `CITY-123`
- Shows in tab and helps with `Cmd+Shift+O` (Open Quickly)

## Terminal Multiplexers

### tmux

For users who prefer tmux over iTerm2 tabs:

```bash
# Create named sessions for each agent
tmux new-session -d -s main -c ~/project
tmux new-session -d -s city-123 -c ~/project-worktrees/CITY-123
tmux new-session -d -s city-456 -c ~/project-worktrees/CITY-456

# Switch between sessions
tmux switch-client -t city-123

# List sessions
tmux list-sessions
```

Add to `~/.tmux.conf` for visual differentiation:
```bash
# Status bar shows session name prominently
set -g status-left '#[fg=green,bold]#S #[fg=white]| '
set -g status-left-length 30

# Color the pane border based on session
set-hook -g client-session-changed 'run-shell "~/.tmux/color-by-session.sh"'
```

### Screen

```bash
screen -S city-123 -c ~/project-worktrees/CITY-123
screen -S city-456 -c ~/project-worktrees/CITY-456

# List screens
screen -ls

# Attach
screen -r city-123
```

## Best Practices for Multiple Agents

### 1. One Agent Per Worktree

**Never** run two Claude Code sessions in the same directory. They will conflict on:
- File writes
- Git operations
- State files

### 2. Dedicated Coordination Terminal

Keep one terminal in the main repo for coordination tasks:

```bash
# Terminal 1 (Main - coordination)
cd ~/project
bin/ticket list           # See what's in progress
git worktree list         # See active worktrees
git fetch --all           # Get latest remote state
gh pr list                # Review open PRs
```

### 3. Limit Concurrent Agents

- **2-3 agents** is manageable for most developers
- **4+ agents** becomes chaotic without strong visual differentiation
- Consider the cognitive load of context-switching between agent outputs

### 4. Clear Naming Convention

Use ticket IDs consistently:
- Worktree path: `../project-worktrees/CITY-123`
- Branch name: `CITY-123` or `CITY-123-add-feature`
- Tab/session name: `CITY-123`
- Terminal prompt: includes current directory

### 5. Check In Periodically

Agents can go off-track. Review their work:
- Read uncommitted changes: `git -C ../project-worktrees/CITY-123 diff`
- Check their commits: `git -C ../project-worktrees/CITY-123 log --oneline -5`
- Watch for duplicated work across agents

### 6. Stagger Start Times

If launching multiple agents for different tickets:
1. Start first agent, let it begin exploration
2. Wait 30-60 seconds
3. Start second agent
4. This reduces the chance they simultaneously modify shared files (package.json, etc.)

## Quick Reference Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Tab 1: Main (default)    │ Tab 2: CITY-123 (blue) │ Tab 3: CITY-456 (green)
├─────────────────────────────────────────────────────────────────┤
│                          │                         │
│ $ bin/ticket list        │ $ claude               │ $ claude
│ $ git worktree list      │ (working on auth)      │ (working on API)
│ $ gh pr list             │                         │
│                          │                         │
│ Coordination only        │ Agent 1 workspace       │ Agent 2 workspace
│                          │                         │
└─────────────────────────────────────────────────────────────────┘
```

## iTerm2 Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New tab | `Cmd+T` |
| Split vertical | `Cmd+D` |
| Split horizontal | `Cmd+Shift+D` |
| Navigate panes | `Cmd+[` / `Cmd+]` |
| Navigate tabs | `Cmd+Shift+[` / `Cmd+Shift+]` |
| Close pane/tab | `Cmd+W` |
| Open quickly (fuzzy find tabs) | `Cmd+Shift+O` |
| Broadcast to all panes | `Cmd+Shift+I` (toggle) |

## VS Code / Cursor Multi-Root Workspaces

If using VS Code or Cursor, you can open multiple worktrees in one window:

```bash
# Create a multi-root workspace file
cat > ~/project.code-workspace << 'EOF'
{
  "folders": [
    { "path": "project", "name": "Main" },
    { "path": "project-worktrees/CITY-123", "name": "CITY-123" },
    { "path": "project-worktrees/CITY-456", "name": "CITY-456" }
  ]
}
EOF

# Open it
code ~/project.code-workspace
```

Each folder appears in the Explorer with its name, making it easy to see which agent's work you're viewing.

## Troubleshooting

### "Which terminal is which?"

1. Look at the tab color (if set)
2. Look at the prompt (shows current directory)
3. Run `pwd` to confirm
4. Check `git branch` to see the ticket branch

### Agent working on wrong files

If an agent starts modifying files outside its scope:
1. Stop the agent (`Ctrl+C` or `/stop`)
2. Review what it changed: `git diff`
3. Reset if needed: `git checkout -- <file>`
4. Restart with clearer instructions

### Merge conflicts from parallel agents

If two agents touched the same file:
1. Finish both agents' work (get to a stopping point)
2. Merge one branch first
3. Rebase the second onto updated main
4. Resolve conflicts manually

## Related

- [multi-agent-coordination.md](multi-agent-coordination.md) - Rules for preventing file conflicts
- [git-worktrees.md](git-worktrees.md) - Setting up and managing worktrees
