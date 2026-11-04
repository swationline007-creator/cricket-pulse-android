module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "s-maxage=30, stale-while-revalidate=60");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") return res.status(405).json({ ok: false, error: "Method not allowed" });
  const key = process.env.CRICKETDATA_API_KEY;
  if (!key) return res.status(503).json({ ok: false, error: "Cricket data provider is not configured" });
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const url = new URL("https://api.cricapi.com/v1/currentMatches");
    url.searchParams.set("apikey", key);
    url.searchParams.set("offset", "0");
    const upstream = await fetch(url.toString(), { signal: controller.signal, headers: { Accept: "application/json" } });
    const payload = await upstream.json().catch(() => null);
    if (!upstream.ok) return res.status(502).json({ ok: false, error: "Cricket data provider request failed", providerStatus: upstream.status });
    if (!payload || payload.status !== "success") return res.status(502).json({ ok: false, error: "Cricket data provider returned an unsuccessful response", providerMessage: payload && payload.reason ? String(payload.reason).slice(0, 180) : undefined });
    return res.status(200).json({ ok: true, source: "cricketdata", data: payload.data || [], info: payload.info || null, fetchedAt: new Date().toISOString() });
  } catch (error) {
    return res.status(502).json({ ok: false, error: error && error.name === "AbortError" ? "Cricket data provider timed out" : "Unable to reach cricket data provider" });
  } finally {
    clearTimeout(timeout);
  }
};