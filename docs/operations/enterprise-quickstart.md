# Enterprise quickstart

One-liner to start the enterprise local stack, wait for health and optionally stream logs:

```powershell
# start and follow logs
.\scripts\start_enterprise.ps1 -action start -FollowLogs

# start in background (no logs)
.\scripts\start_enterprise.ps1 -action start

# stream logs
.\scripts\start_enterprise.ps1 -action logs

# stop and remove volumes
.\scripts\start_enterprise.ps1 -action stop
```

Notes:
- Ensure Docker Desktop (or Docker Engine) is running.
- Review `.env.enterprise` (copied from `.env.enterprise.example` by the script on first run).
- Use `-action status` to see container state.
