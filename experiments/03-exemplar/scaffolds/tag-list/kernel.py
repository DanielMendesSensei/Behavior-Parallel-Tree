"""The kernel of the fixture codebase: cross-cutting infrastructure.

Read only. A behavior imports from here; nothing here knows a behavior by name.
This is the whole kernel: there is no other shared code.
"""


class AppError(Exception):
    """Every error a behavior raises carries a contract error code."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require_session(session):
    """Raise UNAUTHORIZED when there is no usable session. Returns the session."""
    if not session or not session.get("user_id"):
        raise AppError("UNAUTHORIZED")
    return session


class Store:
    """In-memory storage. Behaviors read through it and never touch the rows."""

    def __init__(self, notes=None, tags=None):
        self._notes = list(notes or [])
        self._tags = list(tags or [])

    def notes(self):
        return [dict(n) for n in self._notes]

    def note(self, note_id):
        for n in self._notes:
            if n["id"] == note_id:
                return dict(n)
        return None

    def tags(self):
        return [dict(t) for t in self._tags]

    def save_note(self, note):
        for i, n in enumerate(self._notes):
            if n["id"] == note["id"]:
                self._notes[i] = dict(note)
                return dict(note)
        raise AppError("NOT_FOUND")
