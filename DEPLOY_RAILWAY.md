# Deploy / update MineNova 8.0 on Railway

MineNova serves the website, FastAPI API, WebSocket matchmaking server, and SQLite-backed account system from one Railway service.

## Updating an existing MineNova deployment

If your game is already online, **do not create a new Railway project**.

1. Extract the MineNova 8.0 ZIP.
2. Replace the old files in the **same GitHub repository** with the 8.0 files.
3. Commit the changes to the branch Railway is connected to (usually `main`).
4. Wait for Railway to build/deploy the new commit.
5. Keep the existing `minenova-volume`, `/data` mount, public domain, and `MINENOVA_SECRET`.
6. Do **not** wipe the volume.
7. When the deployment is Active, open `/health` and verify it reports `"version":"8.0"`.
8. Hard-refresh the game once with `Ctrl + Shift + R`.

The 8.0 update does not require a destructive database migration. New keybind/profile/cosmetic fields are stored in existing account progress JSON.

## New installation

### 1. Put the project in GitHub
Upload the project files to a repository. Do not upload `minenova.db` or a real `.env` file.

### 2. Deploy the repository on Railway
Create a Railway project and choose **Deploy from GitHub repo**. The included `Dockerfile` handles the build/start command.

### 3. Attach persistent storage
Attach a Railway Volume to the MineNova service with mount path:

```text
/data
```

MineNova stores SQLite at `/data/minenova.db` on Railway unless `MINENOVA_DB` explicitly overrides it.

### 4. Add the production secret
In Railway → MineNova → Variables, add:

```text
MINENOVA_SECRET=<a-long-random-private-value>
```

Keep it private and never commit it to GitHub.

### 5. Health check
Set Railway's Healthcheck Path to:

```text
/health
```

### 6. Public networking
Generate a public domain in Railway's Networking settings. HTTPS is provided by Railway and MineNova automatically uses secure `wss://` WebSockets on HTTPS.

## Realtime multiplayer
MineNova prefers WebSockets for ranked play and automatically uses its authenticated HTTP-sync fallback when WebSockets are unavailable. Both transports use server-authoritative boards/actions.

Test deployment with two different accounts in two different browsers/devices, queueing the same difficulty.

## Scaling note
Keep **one replica** for this version. Persistent account/rating/history data is in SQLite, but active queues and live matches are held in the server process. Scaling to multiple replicas would require shared realtime state (for example Redis) plus a shared production database.


## 8.0 database note

MineNova 8.0 creates a new `shared_replays` table automatically for replay links. Keep the existing `/data` volume. Do not wipe or replace the database.
