import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';

class ApiClient {
  ApiClient({http.Client? httpClient}) : _httpClient = httpClient ?? http.Client();

  final http.Client _httpClient;

  Uri _uri(String path) {
    final base = AppConfig.apiBaseUrl.replaceAll(RegExp(r'/*$'), '');
    final p = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$base$p');
  }

  Future<String> fetchHealthStatus() async {
    final response = await _httpClient.get(_uri('/health/'));
    if (response.statusCode != 200) {
      throw Exception('Health check failed (${response.statusCode})');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final status = data['status'];
    if (status is String) return status;
    throw Exception('Unexpected health response');
  }

  Future<String> login({required String email, required String password}) async {
    final response = await _httpClient.post(
      _uri('/v1/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode != 200) {
      throw Exception('Login failed (${response.statusCode})');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final token = data['access_token'];
    if (token is String && token.isNotEmpty) return token;
    throw Exception('Unexpected login response');
  }
}
