import 'package:flutter/material.dart';

import '../auth/token_storage.dart';
import '../notifications/push_notifications.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({
    super.key,
    required this.tokenStorage,
    required this.pushNotifications,
  });

  final AccessTokenStore tokenStorage;
  final PushNotifications pushNotifications;

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

  Future<void> _toggleNotifications(bool enabled) async {
    setState(() => _notificationsEnabled = enabled);

    if (!enabled) return;

    final ok = await widget.pushNotifications.enable();
    if (!mounted) return;

    if (!ok) {
      setState(() => _notificationsEnabled = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Could not enable notifications (missing config?)'),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Notifications enabled')),
      );
    }
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
              onChanged: _toggleNotifications,
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
