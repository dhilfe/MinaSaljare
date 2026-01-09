class AppConfig {
  /// Base URL for the backend API.
  ///
  /// Default is set for local development, override with:
  /// `--dart-define=API_BASE_URL=http://<host>:<port>/api`
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api',
  );

  /// Enable Firebase Cloud Messaging integration.
  ///
  /// Default is off. Enable with:
  /// `--dart-define=ENABLE_PUSH_NOTIFICATIONS=true`
  static const bool enablePushNotifications = bool.fromEnvironment(
    'ENABLE_PUSH_NOTIFICATIONS',
    defaultValue: false,
  );
}
