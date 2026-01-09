import 'package:flutter/material.dart';

import '../auth/token_storage.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.tokenStorage});

  final AccessTokenStore tokenStorage;

  Future<void> _logout(BuildContext context) async {
    await tokenStorage.clear();
    if (!context.mounted) return;
    Navigator.of(context).pushReplacementNamed('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Logged in.'),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: () => _logout(context),
              child: const Text('Log out'),
            ),
          ],
        ),
      ),
    );
  }
}
