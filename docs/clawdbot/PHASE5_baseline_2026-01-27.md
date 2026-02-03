# PHASE 5 — Clawdbot Baseline + Hardening + Rollback (2026-01-27)

## 1) Healthy State Checklist
- LaunchAgent loaded and running for `com.clawdbot.gateway`.
- Gateway listening on `127.0.0.1:18789` (loopback-only).
- `clawdbot gateway status` reports **Reachable: yes** and **RPC probe: ok**.
- `clawdbot status --deep` succeeds.
- `clawdbot gateway probe` shows **Connect: ok** and **RPC: ok**.
- Note: If probes intermittently fail with `EPERM` / `1006`, use the reload sequence in Section 5.
- Permissions: `~/.clawdbot`, `~/.clawdbot/credentials`, `~/.clawdbot/logs` are `700`.
- `gateway.bind` remains `loopback` (trusted proxies warning acceptable when local-only).

## 2) Environment Snapshot
- OS: macOS 15.7.4 (arm64)
- Node (system): v25.2.1 at `/opt/homebrew/bin/node`
- Clawdbot CLI: v2026.1.24-3 at `/Users/<USER>/.nvm/versions/node/v24.13.0/bin/clawdbot`
- Gateway port: `18789` (loopback)

## 3) Timeline of Fixes (High-Level)
- Resolved Node PATH conflict (Homebrew node vs nvm) to stabilize LaunchAgent.
- Confirmed iMessage disabled (expected) and not required for gateway health.
- Cleaned a missing transcript/session reference in `sessions.json`.
- Corrected LaunchAgent `ProgramArguments` to a single nvm Node path + gateway entry.
- Restored stability via bootout/bootstrap/kickstart reload sequence.

## 4) Current Security Posture
- Credentials directory hardened: `~/.clawdbot/credentials` is `700`.
- Logs directory hardened: `~/.clawdbot/logs` is `700`.
- Trusted proxies warning: acceptable because gateway is loopback-only.
- Remaining warnings: version manager usage warning is expected due to nvm Node.
- Intermittent probe failures may appear as `EPERM` / `1006` even when the listener is up.

## 5) Rollback Steps
### Restore LaunchAgent plist backup (globbed)
```
cp -a "$HOME/Library/LaunchAgents/com.clawdbot.gateway.plist.bak."* \
  "$HOME/Library/LaunchAgents/com.clawdbot.gateway.plist"
```

### Reload LaunchAgent (bootout/bootstrap/kickstart)
```
uid="$(id -u)"
launchctl bootout "gui/$uid/com.clawdbot.gateway" 2>/dev/null || true
launchctl bootstrap "gui/$uid" "$HOME/Library/LaunchAgents/com.clawdbot.gateway.plist"
launchctl kickstart -k "gui/$uid/com.clawdbot.gateway"
```

### Recovery: gateway loaded but probe/status fails (EPERM/1006)
```
uid="$(id -u)"
launchctl bootout "gui/$uid/com.clawdbot.gateway" 2>/dev/null || true
launchctl bootstrap "gui/$uid" "$HOME/Library/LaunchAgents/com.clawdbot.gateway.plist"
launchctl kickstart -k "gui/$uid/com.clawdbot.gateway"
sleep 2
clawdbot gateway status
clawdbot status --deep
clawdbot gateway probe
```

### Restore Clawdbot state from tarball
```
# Use the most recent backup tarball:
# ~/clawdbot_state_backup_YYYYMMDD_HHMMSS.tgz
rm -rf "$HOME/.clawdbot"
mkdir -p "$HOME/.clawdbot"
tar -xzf ~/clawdbot_state_backup_*.tgz -C / 
```

## 6) Do Not Do (OPSEC)
- Do NOT print or dump any tokens or env vars containing TOKEN/KEY/SECRET.
- Do NOT run `plutil -p` on full LaunchAgent plist without filtering.
- Avoid sharing log files without redaction.

## 7) Next Actions (Optional)
- Sanity-check auth/profile state: `clawdbot status --all`.
- Verify memory plugin availability (if needed) after gateway reloads.
- If ever exposing gateway via reverse proxy, set `gateway.trustedProxies`.
