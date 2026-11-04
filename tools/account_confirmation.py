"""Validate explicitly labeled user or trusted authenticated-client idle evidence."""
from __future__ import annotations

import re
from datetime import datetime,timezone


def confirmed_idle(owner: str, confirmation: dict, now: datetime | None = None) -> dict:
    if not isinstance(owner,str) or not re.fullmatch(r'[0-9]{17}',owner):
        raise ValueError('Expected an explicit Steam account ID')
    if not isinstance(confirmation,dict):
        raise ValueError('Expected a user confirmation object')
    if type(confirmation.get('schema_version')) is not int or confirmation['schema_version'] != 1:
        raise ValueError('Expected schema_version 1')
    if confirmation.get('owner') != owner or confirmation.get('authorized_by') != 'user':
        raise ValueError('Expected user confirmation for this account')
    if confirmation.get('source') != 'user_current_session_statement':
        raise ValueError('Expected a current-session user statement')
    statement=confirmation.get('statement')
    if not isinstance(statement,str) or not statement.strip():
        raise ValueError('Expected a nonempty user statement')
    received=confirmation.get('received_at_utc')
    if not isinstance(received,str):
        raise ValueError('Expected a UTC confirmation timestamp')
    try:
        timestamp=datetime.fromisoformat(received.replace('Z','+00:00'))
    except ValueError:
        raise ValueError('Invalid confirmation timestamp') from None
    current=now if now is not None else datetime.now(timezone.utc)
    if (timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0
            or current.tzinfo is None):
        raise ValueError('Expected timezone-aware UTC timestamps')
    age=(current-timestamp).total_seconds()
    if not -5 <= age <= 900:
        raise ValueError('User confirmation is expired or in the future')
    return dict(owner=owner,status='USER_CONFIRMED_IDLE',source=confirmation['source'],
                observed_at_utc=received,checked_at_utc=current.isoformat(),
                statement=statement,authorized_by='user',schema_version=1)


def confirmed_idle_client_persona(owner: str, receipt: dict, now: datetime | None = None) -> dict:
    """Validate a trusted background own authenticated Steam CEF query receipt."""
    if not isinstance(owner, str) or not re.fullmatch(r'[0-9]{17}', owner):
        raise ValueError('Expected an explicit Steam account ID')
    if not isinstance(receipt, dict):
        raise ValueError('Expected a client presence receipt object')

    # Schema and Source
    if type(receipt.get('schema_version')) is not int or receipt['schema_version'] != 1:
        raise ValueError('Expected schema_version 1')
    if receipt.get('source') != 'live_own_account_persona_on_authenticated_server_connection':
        raise ValueError('Expected source live_own_account_persona_on_authenticated_server_connection')
    if receipt.get('owner') != owner:
        raise ValueError('Receipt owner mismatch')

    # Connection State
    if receipt.get('offline') is not False:
        raise ValueError('Expected offline false (client must be connected)')

    bool_keys = ('server_connected', 'server_logged_on', 'initial_connection_complete', 'initialized', 'statusInitialized')
    for key in bool_keys:
        if receipt.get(key) is not True:
            raise ValueError(f'Expected {key} true')

    # Persona and App State
    persona = receipt.get('persona')
    if type(persona) is not int or not (1 <= persona <= 6):
        raise ValueError('Expected persona int 1..6')

    app = receipt.get('app')
    if type(app) is not int or app != 0:
        raise ValueError('Expected app int 0')

    gameid = receipt.get('gameid')
    if not isinstance(gameid, str) or gameid != '0':
        raise ValueError('Expected gameid string "0"')

    game = receipt.get('game')
    if not isinstance(game, str) or game != '':
        raise ValueError('Expected game empty string')

    # Timing
    age_ms = receipt.get('age_ms')
    if type(age_ms) not in (int, float) or not (0 <= age_ms <= 5000):
        raise ValueError('Expected age_ms 0..5000')

    observed = receipt.get('observed_at_utc')
    if not isinstance(observed, str):
        raise ValueError('Expected observed_at_utc timestamp')
    try:
        timestamp = datetime.fromisoformat(observed.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('Invalid observed_at_utc timestamp') from None

    current = now if now is not None else datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset().total_seconds() != 0:
        raise ValueError('Expected timezone-aware UTC timestamp')
    if current.tzinfo is None:
        raise ValueError('Expected timezone-aware current time')

    age_seconds = (current - timestamp).total_seconds()
    if not -5 <= age_seconds <= 30:
        raise ValueError('Client presence receipt is expired or in the future')

    return dict(receipt, status='CLIENT_PERSONA_IDLE', checked_at_utc=current.isoformat())
