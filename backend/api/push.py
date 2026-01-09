import json
import os
from typing import Iterable

from api.models import DeviceToken


class PushSendError(RuntimeError):
    pass


def _load_firebase_credentials():
    """Load Firebase Admin credentials.

    Supported env vars:
    - FIREBASE_SERVICE_ACCOUNT_JSON: full JSON string for the service account
    - FIREBASE_SERVICE_ACCOUNT_FILE: path to a JSON file

    Returns a firebase_admin.credentials.Base or None if not configured.
    """

    sa_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    sa_file = os.getenv('FIREBASE_SERVICE_ACCOUNT_FILE')

    if sa_json:
        return json.loads(sa_json)

    if sa_file:
        with open(sa_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    return None


def send_test_push(*, tokens: Iterable[str], title: str, body: str) -> int:
    """Send a test push notification to a set of device tokens.

    Returns number of messages attempted.
    Raises PushSendError if Firebase isn't configured.

    Note: requires `firebase-admin` and valid service account config.
    """

    tokens = [t for t in tokens if t]
    if not tokens:
        return 0

    creds_dict = _load_firebase_credentials()
    if creds_dict is None:
        raise PushSendError('Firebase credentials not configured')

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
        )
        resp = messaging.send_multicast(message)
        return resp.success_count + resp.failure_count
    except Exception as e:  # noqa: BLE001
        raise PushSendError(str(e)) from e


def active_tokens_for_user(user) -> list[str]:
    qs = DeviceToken.objects.filter(user=user, is_active=True)
    return list(qs.values_list('token', flat=True))
