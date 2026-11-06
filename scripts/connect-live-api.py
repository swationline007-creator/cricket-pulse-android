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

# Apply requested product branding in the Android UI and launcher label.
manifest = Path("CricketPulseAndroid/app/src/main/AndroidManifest.xml")
manifest_text = manifest.read_text()
import re
manifest_text, label_count = re.subn(
    r"""android:label\s*=\s*["'][^"']*["']""",
    'android:label="SB CricketNow"',
    manifest_text,
    count=1,
)
if label_count == 0 and "<application" in manifest_text:
    manifest_text = manifest_text.replace("<application", '<application android:label="SB CricketNow"', 1)
manifest.write_text(manifest_text)
for kotlin_file in Path("CricketPulseAndroid/app/src/main").rglob("*.kt"):
    text = kotlin_file.read_text()
    text = text.replace('"CRICKET PULSE"', '"SB CRICKETNOW"')
    text = text.replace('"Cricket Pulse"', '"SB CricketNow"')
    kotlin_file.write_text(text)
gradle_file = Path("CricketPulseAndroid/app/build.gradle.kts")
gradle_text = gradle_file.read_text().replace('versionCode = 1', 'versionCode = 2').replace('versionName = "0.1.0"', 'versionName = "0.2.0"')
gradle_file.write_text(gradle_text)
print("SB CricketNow app name and version applied.")


# SB CricketNow Match Centre, full scorecard and honest commentary availability.
# This post-processing patch is intentionally idempotent: the cloud build reconstructs
# the starter project on every run before applying these edits.
src = p.read_text()

# Preserve the provider's match UUID for the scorecard endpoint.
if "val id: String, val status: String" not in src:
    src = src.replace(
        "data class MatchCard(\n    val status: String, val competition: String,",
        "data class MatchCard(\n    val id: String, val status: String, val competition: String,"
    )
src = src.replace(
    "add(MatchCard(status, title, a, score(0), b, score(1),",
    "add(MatchCard(item.optString(\"id\", \"\"), status, title, a, score(0), b, score(1),"
)

# Add selected match state and load scorecard only after a user taps a match.
src = src.replace(
    '    var selectedTab by remember { mutableStateOf("Home") }',
    '''    var selectedTab by remember { mutableStateOf("Home") }
    var selectedMatch by remember { mutableStateOf<MatchCard?>(null) }
    var scorecardText by remember { mutableStateOf<String?>(null) }
    var scorecardLoading by remember { mutableStateOf(false) }
    var scorecardError by remember { mutableStateOf<String?>(null) }
    LaunchedEffect(selectedMatch?.id) {
        val chosen = selectedMatch
        scorecardText = null
        scorecardError = null
        if (chosen != null) {
            if (chosen.id.isBlank()) {
                scorecardError = "इस मैच का provider match ID उपलब्ध नहीं है।"
            } else {
                scorecardLoading = true
                try { scorecardText = fetchMatchScorecard(chosen.id) }
                catch (e: Exception) { scorecardError = e.message ?: "Scorecard उपलब्ध नहीं है।" }
                scorecardLoading = false
            }
        }
    }'''
)

# Add a Results tab and keep Fixtures and Results filters independent.
src = src.replace('listOf("Home", "Live", "Fixtures", "News")',
                  'listOf("Home", "Live", "Fixtures", "Results", "News")')
src = src.replace(
    'Icons.Default.CalendarMonth, Icons.Default.Article)',
    'Icons.Default.CalendarMonth, Icons.Default.EmojiEvents, Icons.Default.Article)'
)
src = src.replace(
    '''            when (selectedTab) {
                "Home" -> HomeScreen(matches, loading, error, { reload++ }, Modifier.padding(padding))
                "Live" -> MatchListScreen("Live Matches", matches.filter { it.status.startsWith("LIVE") }, loading, error, { reload++ }, Modifier.padding(padding))
                "Fixtures" -> MatchListScreen("Fixtures & Results", matches.filter { !it.status.startsWith("LIVE") }, loading, error, { reload++ }, Modifier.padding(padding))
                else -> NewsScreen(Modifier.padding(padding))
            }''',
    '''            if (selectedMatch != null) {
                MatchDetailsScreen(selectedMatch!!, scorecardText, scorecardLoading, scorecardError,
                    onBack = { selectedMatch = null }, modifier = Modifier.padding(padding))
            } else when (selectedTab) {
                "Home" -> HomeScreen(matches, loading, error, { reload++ }, { selectedMatch = it }, Modifier.padding(padding))
                "Live" -> MatchListScreen("Live Matches", matches.filter { it.status.startsWith("LIVE") }, loading, error, { reload++ }, { selectedMatch = it }, Modifier.padding(padding))
                "Fixtures" -> MatchListScreen("Upcoming Fixtures", matches.filter { it.status.startsWith("UPCOMING") }, loading, error, { reload++ }, { selectedMatch = it }, Modifier.padding(padding))
                "Results" -> MatchListScreen("Match Results", matches.filter { it.status.startsWith("RESULT") }, loading, error, { reload++ }, { selectedMatch = it }, Modifier.padding(padding))
                else -> NewsScreen(Modifier.padding(padding))
            }'''
)

# Pass a click callback from each match list to the match card.
src = src.replace(
    'fun HomeScreen(matches: List<MatchCard>, loading: Boolean, error: String?, refresh: () -> Unit, modifier: Modifier = Modifier)',
    'fun HomeScreen(matches: List<MatchCard>, loading: Boolean, error: String?, refresh: () -> Unit, onMatchClick: (MatchCard) -> Unit, modifier: Modifier = Modifier)'
)
src = src.replace(
    'fun MatchListScreen(title: String, matches: List<MatchCard>, loading: Boolean, error: String?, refresh: () -> Unit, modifier: Modifier = Modifier)',
    'fun MatchListScreen(title: String, matches: List<MatchCard>, loading: Boolean, error: String?, refresh: () -> Unit, onMatchClick: (MatchCard) -> Unit, modifier: Modifier = Modifier)'
)
src = src.replace('items(matches) { MatchTile(it) }',
                  'items(matches) { match -> MatchTile(match) { onMatchClick(match) } }')

# Make each match card visibly tappable.
src = src.replace(
    'fun MatchTile(match: MatchCard) {',
    'fun MatchTile(match: MatchCard, onClick: () -> Unit) {'
)
tile_start = src.index("fun MatchTile(match: MatchCard, onClick: () -> Unit) {")
tile_end = src.find("\nprivate suspend fun fetchCricketMatches", tile_start)
if tile_start < 0 or tile_end < 0:
    raise SystemExit("Could not locate MatchTile for clickable update")
tile_src = src[tile_start:tile_end]
tile_src = tile_src.replace(
    "modifier = Modifier.fillMaxWidth()) {",
    "modifier = Modifier.fillMaxWidth().clickable(onClick = onClick)) {",
    1
)
src = src[:tile_start] + tile_src + src[tile_end:]

# Append the detail screen and provider-backed scorecard fetch once.
if "private suspend fun fetchMatchScorecard" not in src:
    src += '''

@Composable
fun MatchDetailsScreen(
    match: MatchCard,
    scorecard: String?,
    loading: Boolean,
    error: String?,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier.fillMaxSize().padding(18.dp)) {
        TextButton(onClick = onBack) { Text("‹ Back to matches", color = Accent) }
        Text("MATCH CENTRE", color = Accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(6.dp))
        Text(match.competition, color = Color.White, fontSize = 21.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(12.dp))
        Surface(color = Panel, shape = RoundedCornerShape(16.dp)) {
            Column(Modifier.fillMaxWidth().padding(16.dp)) {
                Text(match.status, color = Accent, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(12.dp))
                Text(match.teamA + "    " + match.scoreA, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                Text(match.teamB + "    " + match.scoreB, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                Text(match.note, color = Muted, fontSize = 12.sp)
            }
        }
        Spacer(Modifier.height(18.dp))
        Text("FULL SCORECARD", color = Accent, fontSize = 13.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        when {
            loading -> CircularProgressIndicator(color = Accent)
            error != null -> Text(error, color = Muted)
            scorecard != null -> ScorecardSections(scorecard)
            else -> Text("इस मैच का scorecard अभी उपलब्ध नहीं है।", color = Muted)
        }
        Spacer(Modifier.height(18.dp))
        Text("BALL-BY-BALL COMMENTARY", color = Accent, fontSize = 13.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text(
            "इस provider/API response में verified ball-by-ball commentary feed उपलब्ध नहीं है। इसलिए यहाँ कोई अनुमानित या नकली commentary नहीं दिखाई जाएगी।",
            color = Muted, fontSize = 13.sp
        )
    }
}


@Composable
fun ScorecardSections(raw: String) {
    val root = remember(raw) { runCatching { JSONObject(raw) }.getOrNull() }
    val innings = root?.optJSONArray("scorecard")
        ?: root?.optJSONArray("innings")
        ?: root?.optJSONArray("data")
    if (innings == null || innings.length() == 0) {
        Text("Provider ने structured innings scorecard नहीं दिया। Raw response को scorecard की तरह दिखाने के बजाय इसे unavailable रखा गया है।", color = Muted, fontSize = 13.sp)
        return
    }
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        for (i in 0 until innings.length()) {
            val inning = innings.optJSONObject(i) ?: continue
            val inningName = inning.optString("inning", inning.optString("name", "Innings ${i + 1}"))
            Text(inningName, color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            val batting = inning.optJSONArray("batting") ?: inning.optJSONArray("batsmen")
            if (batting != null) {
                Text("BATTING", color = Accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Batter", color = Muted, fontSize = 11.sp, modifier = Modifier.weight(1f))
                    Text("R", color = Muted, fontSize = 11.sp, modifier = Modifier.width(28.dp))
                    Text("B", color = Muted, fontSize = 11.sp, modifier = Modifier.width(28.dp))
                    Text("4s", color = Muted, fontSize = 11.sp, modifier = Modifier.width(28.dp))
                    Text("6s", color = Muted, fontSize = 11.sp, modifier = Modifier.width(28.dp))
                    Text("SR", color = Muted, fontSize = 11.sp, modifier = Modifier.width(42.dp))
                }
                for (j in 0 until batting.length()) {
                    val player = batting.optJSONObject(j) ?: continue
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Column(Modifier.weight(1f)) {
                            Text(player.optString("batsman", player.optString("name", "Batter")), color = Color.White, fontSize = 12.sp)
                            val dismissal = player.optString("dismissal", player.optString("dismissal-text", ""))
                            if (dismissal.isNotBlank()) Text(dismissal, color = Muted, fontSize = 10.sp)
                        }
                        Text(player.optString("r", player.optString("runs", "—")), color = Color.White, fontSize = 12.sp, modifier = Modifier.width(28.dp))
                        Text(player.optString("b", player.optString("balls", "—")), color = Color.White, fontSize = 12.sp, modifier = Modifier.width(28.dp))
                        Text(player.optString("4s", "0"), color = Color.White, fontSize = 12.sp, modifier = Modifier.width(28.dp))
                        Text(player.optString("6s", "0"), color = Color.White, fontSize = 12.sp, modifier = Modifier.width(28.dp))
                        Text(player.optString("sr", player.optString("strikeRate", "—")), color = Color.White, fontSize = 12.sp, modifier = Modifier.width(42.dp))
                    }
                }
            }
            val bowling = inning.optJSONArray("bowling") ?: inning.optJSONArray("bowlers")
            if (bowling != null) {
                Spacer(Modifier.height(6.dp))
                Text("BOWLING", color = Accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text("Bowler", color = Muted, fontSize = 11.sp, modifier = Modifier.weight(1f))
                    listOf("O", "M", "R", "W", "Econ").forEach { Text(it, color = Muted, fontSize = 11.sp, modifier = Modifier.width(34.dp)) }
                }
                for (j in 0 until bowling.length()) {
                    val player = bowling.optJSONObject(j) ?: continue
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(player.optString("bowler", player.optString("name", "Bowler")), color = Color.White, fontSize = 12.sp, modifier = Modifier.weight(1f))
                        listOf("o", "m", "r", "w", "eco").forEach { key ->
                            Text(player.optString(key, "—"), color = Color.White, fontSize = 12.sp, modifier = Modifier.width(34.dp))
                        }
                    }
                }
            }
            val extras = inning.optJSONObject("extras")
            if (extras != null) {
                Spacer(Modifier.height(6.dp))
                Text("EXTRAS", color = Accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Text(extras.toString(), color = Color.White, fontSize = 12.sp)
            }
            val fall = inning.optJSONArray("fallOfWickets") ?: inning.optJSONArray("fall_of_wickets")
            if (fall != null) {
                Spacer(Modifier.height(6.dp))
                Text("FALL OF WICKETS", color = Accent, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                val entries = (0 until fall.length()).mapNotNull { idx ->
                    val item = fall.opt(idx)
                    when (item) {
                        is JSONObject -> item.optString("score", item.optString("wicket", item.toString()))
                        else -> item?.toString()
                    }
                }
                Text(entries.joinToString("  •  "), color = Color.White, fontSize = 12.sp)
            }
            val total = inning.optString("total", inning.optString("score", ""))
            if (total.isNotBlank()) Text("TOTAL  $total", color = Color.White, fontWeight = FontWeight.Bold)
            if (i < innings.length() - 1) HorizontalDivider(color = Color(0xFF29415B))
        }
    }
}

private suspend fun fetchMatchScorecard(matchId: String): String = withContext(Dispatchers.IO) {
    val url = URL("https://cricket-pulse-android.vercel.app/api/scorecard?id=" + java.net.URLEncoder.encode(matchId, "UTF-8"))
    val connection = url.openConnection() as HttpURLConnection
    connection.connectTimeout = 15000
    connection.readTimeout = 15000
    try {
        val code = connection.responseCode
        val body = (if (code in 200..299) connection.inputStream else connection.errorStream).bufferedReader().use { it.readText() }
        check(code in 200..299) { "Scorecard server HTTP $code" }
        val root = JSONObject(body)
        check(root.optBoolean("ok")) { root.optString("error", "Scorecard unavailable") }
        val data = root.optJSONObject("data") ?: error("Provider returned no scorecard data")
        data.toString(2)
    } finally { connection.disconnect() }
}
'''
p.write_text(src)
print("Applied SB CricketNow Match Centre navigation, provider scorecard, separate Results filter, and honest commentary fallback.")
