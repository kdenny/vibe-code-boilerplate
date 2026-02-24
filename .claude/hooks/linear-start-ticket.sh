#!/usr/bin/env bash
# Linear status update hook - marks ticket as In Progress when starting work
# Triggers when user prompt contains a ticket ID pattern (e.g., PROJ-123)
#
# Configuration:
#   - Set LINEAR_API_KEY in .env.local
#   - Optionally set TICKET_PATTERN in .env.local (default: [A-Z]+-[0-9]+)

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Source .env.local if LINEAR_API_KEY not already set
if [ -z "$LINEAR_API_KEY" ] && [ -f "$REPO_ROOT/.env.local" ]; then
  LINEAR_API_KEY=$(grep -E '^LINEAR_API_KEY=' "$REPO_ROOT/.env.local" 2>/dev/null | cut -d= -f2-)
  export LINEAR_API_KEY
fi

# Check for API key - exit silently if not configured
if [ -z "$LINEAR_API_KEY" ]; then
  exit 0
fi

# Get ticket pattern from env or use default
TICKET_PATTERN="${TICKET_PATTERN:-[A-Z]+-[0-9]+}"

# Read the user prompt from stdin (passed by Claude Code hook)
USER_PROMPT=$(cat)

# Extract ticket ID using the pattern
TICKET_ID=$(echo "$USER_PROMPT" | grep -oE "$TICKET_PATTERN" | head -1)

if [ -z "$TICKET_ID" ]; then
  exit 0
fi

# Get the issue details and workflow states
ISSUE_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  --data "{\"query\": \"query { issue(id: \\\"$TICKET_ID\\\") { id state { type } team { states { nodes { id name type } } } } }\"}" \
  https://api.linear.app/graphql 2>/dev/null)

# Extract issue ID
ISSUE_ID=$(echo "$ISSUE_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$ISSUE_ID" ] || [ "$ISSUE_ID" = "null" ]; then
  exit 0
fi

# Check if already in progress or completed - don't downgrade status
CURRENT_STATE_TYPE=$(echo "$ISSUE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    state_type = data.get('data', {}).get('issue', {}).get('state', {}).get('type', '')
    print(state_type)
except:
    pass
" 2>/dev/null)

# Skip if already started or completed
if [ "$CURRENT_STATE_TYPE" = "started" ] || [ "$CURRENT_STATE_TYPE" = "completed" ]; then
  exit 0
fi

# Find the "In Progress" state ID (type: started)
IN_PROGRESS_STATE_ID=$(echo "$ISSUE_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    states = data.get('data', {}).get('issue', {}).get('team', {}).get('states', {}).get('nodes', [])
    for state in states:
        if state.get('type') == 'started' and 'progress' in state.get('name', '').lower():
            print(state['id'])
            break
    else:
        # Fallback to any started state
        for state in states:
            if state.get('type') == 'started':
                print(state['id'])
                break
except:
    pass
" 2>/dev/null)

if [ -z "$IN_PROGRESS_STATE_ID" ]; then
  exit 0
fi

# Update the issue status
curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: $LINEAR_API_KEY" \
  --data "{\"query\": \"mutation { issueUpdate(id: \\\"$ISSUE_ID\\\", input: { stateId: \\\"$IN_PROGRESS_STATE_ID\\\" }) { success } }\"}" \
  https://api.linear.app/graphql > /dev/null 2>&1

echo "Linear ticket $TICKET_ID marked as In Progress"
