module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "s-maxage=60, stale-while-revalidate=120");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") return res.status(405).json({ ok: false, error: "Method not allowed" });
  const id = typeof req.query.id === "string" ? req.query.id : "";
  if (!/^[0-9a-f-]{36}$/i.test(id)) return res.status(400).json({ ok: false, error: "A valid match id is required" });
  const key = process.env.CRICKETDATA_API_KEY;
  if (!key) return res.status(503).json({ ok: false, error: "Cricket data provider is not configured" });
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const url = new URL("https://api.cricapi.com/v1/match_scorecard");
    url.searchParams.set("apikey", key);
    url.searchParams.set("offset", "0");
    url.searchParams.set("id", id);
    const upstream = await fetch(url.toString(), { signal: controller.signal, headers: { Accept: "application/json" } });
    const payload = await upstream.json().catch(() => null);
    if (!upstream.ok) return res.status(502).json({ ok: false, error: "Cricket data provider request failed", providerStatus: upstream.status });
    if (!payload || payload.status !== "success" || !payload.data) {
      return res.status(502).json({ ok: false, error: "Scorecard is unavailable for this match", providerMessage: payload && payload.reason ? String(payload.reason).slice(0, 180) : undefined });
    }
    return res.status(200).json({ ok: true, source: "cricketdata", data: payload.data, fetchedAt: new Date().toISOString() });
  } catch (error) {
    return res.status(502).json({ ok: false, error: error && error.name === "AbortError" ? "Cricket data provider timed out" : "Unable to reach cricket data provider" });
  } finally {
    clearTimeout(timeout);
  }
};