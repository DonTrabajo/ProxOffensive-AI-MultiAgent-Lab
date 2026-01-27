# Clawdbot Gateway Runbook

Purpose: recover the gateway when the LaunchAgent is “not loaded”.

## Reload LaunchAgent
```
uid="$(id -u)"
launchctl bootout "gui/$uid/com.clawdbot.gateway" 2>/dev/null || true
launchctl bootstrap "gui/$uid" "$HOME/Library/LaunchAgents/com.clawdbot.gateway.plist"
launchctl kickstart -k "gui/$uid/com.clawdbot.gateway"
```

## Verify
```
lsof -nP -iTCP:18789 -sTCP:LISTEN || true
clawdbot gateway status
clawdbot status --deep
clawdbot gateway probe
```

## Rollback
Delete this file or:
```
git checkout -- RUNBOOK_CLAWDBOT_GATEWAY.md
```
