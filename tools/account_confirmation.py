"""Check explicit live user evidence without relabeling it as public presence."""
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
