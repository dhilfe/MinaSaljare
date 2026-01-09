// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:mina_saljare_mobile/main.dart';
import 'package:mina_saljare_mobile/auth/token_storage.dart';

void main() {
  testWidgets('App starts on login when no token', (WidgetTester tester) async {
    await tester.pumpWidget(MyApp(tokenStorage: InMemoryTokenStorage()));

    // StartPage shows loading first, then redirects.
    expect(find.text('Loading…'), findsOneWidget);
    await tester.pumpAndSettle();

    expect(find.byType(AppBar), findsOneWidget);
    expect(find.widgetWithText(ElevatedButton, 'Log in'), findsOneWidget);
  });
}
