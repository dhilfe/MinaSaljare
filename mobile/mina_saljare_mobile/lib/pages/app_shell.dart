import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../auth/token_storage.dart';
import '../notifications/push_notifications.dart';
import 'home_page.dart';
import 'settings_page.dart';
import 'team_status_page.dart';

class AppShell extends StatefulWidget {
  const AppShell({
    super.key,
    required this.api,
    required this.tokenStorage,
    required this.pushNotifications,
  });

  final ApiClient api;
  final AccessTokenStore tokenStorage;
  final PushNotifications pushNotifications;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      HomePage(api: widget.api),
      TeamStatusPage(api: widget.api),
      SettingsPage(
        tokenStorage: widget.tokenStorage,
        pushNotifications: widget.pushNotifications,
      ),
    ];

    return Scaffold(
      body: pages[_index],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _index,
        onTap: (i) => setState(() => _index = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.groups), label: 'Team'),
          BottomNavigationBarItem(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
