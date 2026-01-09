import 'package:flutter/material.dart';

import 'api/api_client.dart';
import 'auth/token_storage.dart';
import 'config/app_config.dart';
import 'pages/app_shell.dart';
import 'pages/login_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key, this.api, this.tokenStorage});

  final ApiClient? api;
  final AccessTokenStore? tokenStorage;

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    final store = tokenStorage ?? SecureTokenStorage();
    final apiClient = api ?? ApiClient(tokenStore: store);

    return MaterialApp(
      title: 'MinaSäljare',
      theme: ThemeData(useMaterial3: true),
      routes: {
        '/login': (_) => LoginPage(api: apiClient, tokenStorage: store),
        '/home': (_) => AppShell(api: apiClient, tokenStorage: store),
        '/health': (_) => const HealthPage(),
      },
      home: StartPage(tokenStorage: store),
    );
  }
}

class StartPage extends StatefulWidget {
  const StartPage({super.key, required this.tokenStorage});

  final AccessTokenStore tokenStorage;

  @override
  State<StartPage> createState() => _StartPageState();
}

class _StartPageState extends State<StartPage> {
  @override
  void initState() {
    super.initState();
    _decide();
  }

  Future<void> _decide() async {
    final token = await widget.tokenStorage.readAccessToken();
    if (!mounted) return;
    Navigator.of(
      context,
    ).pushReplacementNamed(token == null ? '/login' : '/home');
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(body: Center(child: Text('Loading…')));
  }
}

class HealthPage extends StatefulWidget {
  const HealthPage({super.key});

  @override
  State<HealthPage> createState() => _HealthPageState();
}

class _HealthPageState extends State<HealthPage> {
  final _api = ApiClient();

  bool _loading = false;
  String? _status;
  String? _error;

  Future<void> _refresh() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final status = await _api.fetchHealthStatus();
      if (!mounted) return;
      setState(() {
        _status = status;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _status = null;
      });
    } finally {
      if (mounted) {
        setState(() {
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Health Check')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('API base URL: ${AppConfig.apiBaseUrl}'),
            const SizedBox(height: 12),
            if (_loading) const Text('Loading…'),
            if (_status != null) Text('Status: $_status'),
            if (_error != null) Text('Error: $_error'),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _loading ? null : _refresh,
              child: const Text('Refresh'),
            ),
          ],
        ),
      ),
    );
  }
}
