import 'package:flutter/material.dart';

import 'api/api_client.dart';
import 'config/app_config.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MinaSäljare',
      theme: ThemeData(useMaterial3: true),
      home: const HealthPage(),
    );
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
