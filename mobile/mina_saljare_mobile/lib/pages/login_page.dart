import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../auth/token_storage.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.api, required this.tokenStorage});

  final ApiClient api;
  final AccessTokenStore tokenStorage;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isSubmitting = false;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final email = _emailController.text.trim();
    final password = _passwordController.text;

    if (email.isEmpty || password.isEmpty) return;

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      final token = await widget.api.login(email: email, password: password);
      await widget.tokenStorage.saveAccessToken(token);
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed('/home');
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _error = 'Invalid credentials or server error.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final canSubmit =
        _emailController.text.trim().isNotEmpty &&
        _passwordController.text.isNotEmpty &&
        !_isSubmitting;

    return Scaffold(
      appBar: AppBar(title: const Text('Log in')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              decoration: const InputDecoration(labelText: 'Email'),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passwordController,
              obscureText: true,
              autofillHints: const [AutofillHints.password],
              decoration: const InputDecoration(labelText: 'Password'),
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: canSubmit ? _submit : null,
              child: Text(_isSubmitting ? 'Logging in…' : 'Log in'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Colors.red)),
            ],
          ],
        ),
      ),
    );
  }
}
