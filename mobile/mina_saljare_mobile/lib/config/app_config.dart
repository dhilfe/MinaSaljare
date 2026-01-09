class AppConfig {
  /// Base URL for the backend API.
  ///
  /// Default is set for local development, override with:
  /// `--dart-define=API_BASE_URL=http://<host>:<port>/api`
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api',
  );
}
