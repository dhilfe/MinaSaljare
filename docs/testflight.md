# TestFlight (iOS) release flow

This repo contains a Flutter iOS app at `mobile/mina_saljare_mobile`.

## One-time setup (Apple)

1) **Apple Developer Program**
- Ensure you have access to a team that can create signing certificates/profiles.

2) **App Store Connect**
- Create an app in App Store Connect with bundle id: `se.minasaljare.minaSaljareMobile`.

3) **Xcode signing**
- Open `mobile/mina_saljare_mobile/ios/Runner.xcworkspace` in Xcode.
- In **Runner** target settings:
  - Set your **Team**.
  - Enable **Automatically manage signing** (recommended).
  - Ensure the bundle identifier matches App Store Connect.

## Local sanity checks

From repo root:

```bash
cd mobile/mina_saljare_mobile
flutter pub get
flutter analyze
flutter test
```

On macOS, you can also verify iOS builds without signing:

```bash
cd mobile/mina_saljare_mobile
flutter build ios --release --no-codesign
```

## Upload to TestFlight (Fastlane)

Fastlane is configured under `mobile/mina_saljare_mobile/ios/fastlane`.

### 1) Create an App Store Connect API key

In App Store Connect:
- Users and Access → Keys → App Store Connect API
- Create a key and download the `.p8` file.

You will need:
- `ASC_KEY_ID`
- `ASC_ISSUER_ID`
- a local path to the `.p8` file (`ASC_KEY_FILEPATH`)

### 2) Run the upload

From repo root (macOS):

```bash
cd mobile/mina_saljare_mobile/ios
bundle install

export ASC_KEY_ID="..."
export ASC_ISSUER_ID="..."
export ASC_KEY_FILEPATH="$HOME/keys/AuthKey_XXXX.p8"

bundle exec fastlane beta
```

Optional: specify build name/number (maps to `CFBundleShortVersionString` / `CFBundleVersion`):

```bash
bundle exec fastlane beta build_name:1.0.0 build_number:2
```

## Notes

- `fastlane beta` assumes iOS signing is already correctly configured in Xcode.
- If signing fails, fix it in Xcode first (Team / provisioning) and retry.
