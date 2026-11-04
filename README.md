# Cricket Pulse Android

Phone-first native Android cricket app starter (Kotlin + Jetpack Compose).

## Status
- Phase 1 UI scaffold: Home, Live, Fixtures, News
- Demo match cards only; no real-time data is connected
- No ads, subscriptions, payment collection, or login in this starter
- Android target API 36

## Cloud build
The GitHub Actions workflow decodes `starter.zip.base64`, extracts the Android project, and builds a debug APK. See `PHONE-ONLY-BUILD-GUIDE.md` after extraction.

## Important
This is an early development build, not a Play Store release. Real cricket data requires a provider whose licence permits the intended app use. Never commit API secrets.
