import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const _accessTokenKey = 'access_token';

abstract class AccessTokenStore {
  Future<void> saveAccessToken(String token);
  Future<String?> readAccessToken();
  Future<void> clear();
}

class SecureTokenStorage implements AccessTokenStore {
  SecureTokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  @override
  Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }

  @override
  Future<String?> readAccessToken() async {
    return _storage.read(key: _accessTokenKey);
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _accessTokenKey);
  }
}

class InMemoryTokenStorage implements AccessTokenStore {
  InMemoryTokenStorage({String? initialToken}) : _token = initialToken;

  String? _token;

  @override
  Future<void> saveAccessToken(String token) async {
    _token = token;
  }

  @override
  Future<String?> readAccessToken() async {
    return _token;
  }

  @override
  Future<void> clear() async {
    _token = null;
  }
}
