import 'package:flutter/material.dart';

import '../auth/token_storage.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key, required this.tokenStorage});

  final AccessTokenStore tokenStorage;

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool _notificationsEnabled = false;

  Future<void> _logout() async {
    await widget.tokenStorage.clear();
    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SwitchListTile(
              title: const Text('Notifications (placeholder)'),
              value: _notificationsEnabled,
              onChanged: (v) => setState(() => _notificationsEnabled = v),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _logout,
                child: const Text('Log out'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
