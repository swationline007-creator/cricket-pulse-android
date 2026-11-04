# Cricket Pulse API

Vercel Node.js serverless API for the Cricket Pulse Android app.

## Routes
- GET /api/health
- GET /api/current-matches

Set the Vercel project environment variable CRICKETDATA_API_KEY (server-side secret). Never expose it in Android code or commit it.

Current matches are cached at the edge for 30 seconds. Provider credentials are never returned to clients.
