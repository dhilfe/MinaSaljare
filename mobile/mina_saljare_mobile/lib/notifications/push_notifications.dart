import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../api/api_client.dart';

abstract class PushNotifications {
  Future<bool> enable();
}

class NoopPushNotifications implements PushNotifications {
  @override
  Future<bool> enable() async {
    return false;
  }
}

/// Firebase Cloud Messaging implementation.
///
/// If Firebase isn't configured (missing GoogleService-Info.plist etc), this will
/// fail gracefully and return false.
class FirebasePushNotifications implements PushNotifications {
  FirebasePushNotifications({required this.api});

  final ApiClient api;

  StreamSubscription<String>? _tokenRefreshSub;

  @override
  Future<bool> enable() async {
    try {
      await Firebase.initializeApp();

      final settings = await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.denied) {
        return false;
      }

      final token = await FirebaseMessaging.instance.getToken();
      if (token == null || token.isEmpty) {
        return false;
      }

      await api.registerDeviceToken(
        token: token,
        platform: 'ios',
        provider: 'fcm',
      );

      await _tokenRefreshSub?.cancel();
      _tokenRefreshSub = FirebaseMessaging.instance.onTokenRefresh.listen(
        (newToken) async {
          if (newToken.isEmpty) return;
          try {
            await api.registerDeviceToken(
              token: newToken,
              platform: 'ios',
              provider: 'fcm',
            );
          } catch (_) {
            // best-effort
          }
        },
      );

      return true;
    } catch (e) {
      debugPrint('Push notifications init failed: $e');
      return false;
    }
  }
}
