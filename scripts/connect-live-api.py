from pathlib import Path
p=Path("CricketPulseAndroid/app/src/main/java/com/cricketpulse/app/MainActivity.kt")
s=p.read_text()
s=s.replace("import android.os.Bundle","import android.os.Bundle\nimport kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.withContext\nimport org.json.JSONObject\nimport java.net.HttpURLConnection\nimport java.net.URL")
s=s.replace('    val note: String\n)', '    val note: String\n)')
start=s.index("private val sampleMatches = listOf(")
end=s.index("\n\nclass MainActivity", start)
s=s[:start]+s[end+2:]
s=s.replace('fun CricketPulseApp() {\n    var selectedTab by remember { mutableStateOf("Home") }', '''fun CricketPulseApp() {
    var selectedTab by remember { mutableStateOf("Home") }
    var matches by remember { mutableStateOf<List<MatchCard>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf<String?>(null) }
    var reload by remember { mutableIntStateOf(0) }
    LaunchedEffect(reload) {
        loading = true
        error = null
        try { matches = fetchCricketMatches() }
        catch (e: Exception) { error = e.message ?: "Unable to load live matches" }
        loading = false
    }''')
s=s.replace('HomeScreen(Modifier.padding(padding))','HomeScreen(matches, loading, error, { reload++ }, Modifier.padding(padding))')
s=s.replace('MatchListScreen("Live Matches", Modifier.padding(padding))','MatchListScreen("Live Matches", matches.filter { it.status.startsWith("LIVE") }, loading, error, { reload++ }, Modifier.padding(padding))')
s=s.replace('MatchListScreen("Upcoming Fixtures", Modifier.padding(padding))','MatchListScreen("Fixtures & Results", matches.filter { !it.status.startsWith("LIVE") }, loading, error, { reload++ }, Modifier.padding(padding))')
s=s.replace('fun HomeScreen(modifier: Modifier = Modifier) {','fun HomeScreen(matches: List<MatchCard>, loading: Boolean, error: String?, refresh: () -> Unit, modifier: Modifier = Modifier) {')
s=s.replace('item { SectionHeading("MATCH CENTRE", "See all") }\n        items(sampleMatches) { MatchTile(it) }','''item { Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            SectionHeading("MATCH CENTRE", if (loading) "Updating…" else "LIVE DATA")
            TextButton(onClick = refresh) { Text("Refresh", color = Accent) }
        } }
        if (loading && matches.isEmpty()) item { CircularProgressIndicator(color = Accent) }
        if (error != null) item { Text("Feed error: $error", color = Muted) }
        if (!loading && matches.isEmpty() && error == null) item { Text("No current matches available right now.", color = Muted) }
        items(matches) { MatchTile(it) }''')
s=s.replace('fun MatchListScreen(title: String, modifier: Modifier = Modifier) {','fun MatchListScreen(title: String, matches: List<MatchCard>, loading: Boolean, error: String?, refresh: () -> Unit, modifier: Modifier = Modifier) {')
s=s.replace('Text(title, color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Bold)\n        Spacer(Modifier.height(14.dp))','''Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text(title, color = Color.White, fontSize = 25.sp, fontWeight = FontWeight.Bold)
            TextButton(onClick = refresh) { Text("Refresh", color = Accent) }
        }
        if (loading && matches.isEmpty()) CircularProgressIndicator(color = Accent)
        if (error != null) Text(error, color = Muted)
        if (!loading && matches.isEmpty() && error == null) Text("No matches available.", color = Muted)
        Spacer(Modifier.height(14.dp))''')
s=s.replace('items(sampleMatches) { MatchTile(it) }','items(matches) { MatchTile(it) }')
s += '''
private suspend fun fetchCricketMatches(): List<MatchCard> = withContext(Dispatchers.IO) {
    val connection = URL("https://cricket-pulse-android.vercel.app/api/current-matches").openConnection() as HttpURLConnection
    connection.connectTimeout = 15000
    connection.readTimeout = 15000
    try {
        val code = connection.responseCode
        val body = (if (code in 200..299) connection.inputStream else connection.errorStream).bufferedReader().use { it.readText() }
        check(code in 200..299) { "Cricket server HTTP $code" }
        val root = JSONObject(body)
        check(root.optBoolean("ok")) { root.optString("error", "Cricket feed unavailable") }
        val data = root.optJSONArray("data") ?: return@withContext emptyList()
        buildList {
            for (i in 0 until data.length()) {
                val item = data.optJSONObject(i) ?: continue
                val teams = item.optJSONArray("teams")
                val a = teams?.optString(0).orEmpty().ifBlank { "Team 1" }
                val b = teams?.optString(1).orEmpty().ifBlank { "Team 2" }
                val scores = item.optJSONArray("score")
                fun score(index: Int): String {
                    val x = scores?.optJSONObject(index) ?: return "—"
                    val runs = x.optString("r", "")
                    if (runs.isBlank()) return "—"
                    val wickets = x.optString("w", "")
                    val overs = x.optString("o", "")
                    return runs + (if (wickets.isNotBlank()) "/$wickets" else "") + (if (overs.isNotBlank()) " ($overs ov)" else "")
                }
                val started = item.optBoolean("matchStarted")
                val ended = item.optBoolean("matchEnded")
                val status = when { started && !ended -> "LIVE • " + item.optString("status", "In progress"); ended -> "RESULT • " + item.optString("status", "Finished"); else -> "UPCOMING • " + item.optString("status", "Scheduled") }
                val type = item.optString("matchType", "CRICKET").uppercase()
                val title = item.optString("name", type) + " • " + type
                val venue = item.optString("venue", "")
                add(MatchCard(status, title, a, score(0), b, score(1), item.optString("status", "Match details") + if (venue.isNotBlank()) " • $venue" else ""))
            }
        }
    } finally { connection.disconnect() }
}
'''
p.write_text(s)
# Ensure Android network permission exists.
manifest=Path("CricketPulseAndroid/app/src/main/AndroidManifest.xml")
m=manifest.read_text()
if "android.permission.INTERNET" not in m:
    at=m.find(">",m.find("<manifest"))
    m=m[:at+1]+'\n    <uses-permission android:name="android.permission.INTERNET" />'+m[at+1:]
    manifest.write_text(m)
print("Patched Compose screens to load real match records from secure Vercel API.")

# Keep status and competition on separate lines to prevent label overlap.
src = p.read_text()
a = src.find("@Composable fun MatchTile(")
if a < 0:
    a = src.find("@Composable\nfun MatchTile(")
b = src.find("\nprivate suspend fun fetchCricketMatches", a)
if a >= 0 and b > a:
    tile = """@Composable
fun MatchTile(match: MatchCard) {
    Surface(color = Panel, shape = RoundedCornerShape(18.dp), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(match.status, color = Accent, fontSize = 11.sp, fontWeight = FontWeight.Bold, maxLines = 2)
            Spacer(Modifier.height(5.dp))
            Text(match.competition, color = Muted, fontSize = 11.sp, maxLines = 2)
            Spacer(Modifier.height(16.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(match.teamA, color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.weight(1f))
                Text(match.scoreA, color = Color.White, fontSize = 14.sp)
            }
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(match.teamB, color = Color.White, fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, modifier = Modifier.weight(1f))
                Text(match.scoreB, color = Color.White, fontSize = 14.sp)
            }
            Spacer(Modifier.height(14.dp))
            HorizontalDivider(color = Color(0xFF29415B))
            Spacer(Modifier.height(10.dp))
            Text(match.note, color = Muted, fontSize = 11.sp)
        }
    }
}
"""
    p.write_text(src[:a] + tile + src[b:])
    print("Card text layout updated.")
else:
    raise SystemExit("Could not locate MatchTile boundaries")
