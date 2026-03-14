# Deployment Checklist

## Before Merge

- Backend tests are green
- Frontend build is green
- PR721 integration pages render without mock-only regressions
- additive Alembic migration `0020` reviewed
- no secrets in tracked files
- docs do not claim unsupported production status

## Before Staging

- `.env` values are present and rotated
- `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET` validated
- worker and beat are enabled if scheduler views are expected to be live
- health endpoints return green
- login and one core business flow were smoke-tested

## Before Production

- security review completed
- migration plan approved
- rollback plan documented
- monitoring and alerting destinations configured
- optional providers validated or explicitly disabled
