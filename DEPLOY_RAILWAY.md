# Deploy MineNova Infinity on Railway

MineNova serves both the website and the FastAPI/WebSocket backend from one service.

## 1. Put the project in a GitHub repository
Upload the project files from this folder to a repository. Do not upload a generated `minenova.db` file or a real `.env` file.

## 2. Create a Railway project
- Create a new Railway project.
- Choose **Deploy from GitHub repo** and select the MineNova repository.
- Railway will see the included `Dockerfile` and build it.

## 3. Add persistent storage
Attach one Railway Volume to the MineNova service.

Recommended mount path:

```text
/data
```

The server automatically detects Railway's volume mount and uses `/data/minenova.db` unless `MINENOVA_DB` overrides it.

## 4. Add the production secret
In the service's Variables page, add:

```text
MINENOVA_SECRET=<your-random-secret>
```

Generate one locally with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not publish or commit the generated value.

`HOST` is already set to `0.0.0.0` in the Dockerfile. Railway supplies `PORT` automatically.

## 5. Configure health checking
Set the service Healthcheck Path to:

```text
/health
```

## 6. Generate the public URL
Open the service Settings page -> Networking -> Public Networking -> Generate Domain.

Open the generated HTTPS URL. The game automatically switches its WebSocket connection to `wss://` when served over HTTPS.

## 7. Test real matchmaking
- Open the public URL in two separate browser profiles/devices.
- Create two accounts.
- Queue the same ranked difficulty.
- Confirm both players enter the same match and the leaderboard updates afterward.

## Important scaling note
Keep the service at **one replica** for this version. Matchmaking and live match state are currently held in memory, while account/rating/history data live in SQLite. Multiple replicas would need a shared realtime state layer such as Redis plus a shared database.

## Updating the game
Push changes to the connected GitHub repository. Railway can redeploy from the new commit. The attached volume keeps the SQLite account database across deployments.

## Custom domain
After the Railway URL works, add a custom domain from Railway's Networking settings and follow the DNS records Railway gives you. TLS/HTTPS is handled by Railway.
