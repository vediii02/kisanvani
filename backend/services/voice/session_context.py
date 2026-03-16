from contextvars import ContextVar, Token


import asyncio

class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.is_interrupted = False
        self.turn_id = 0
        self.last_ai_audio_time = 0.0 # To avoid VAD triggering while AI is "thinking"

    def interrupt(self):
        if not self.is_interrupted:
            self.is_interrupted = True
            self.turn_id += 1
            return True
        return False

    def reset_interrupt(self):
        self.is_interrupted = False

    def new_turn(self):
        self.turn_id += 1
        self.is_interrupted = False
        return self.turn_id

class SessionStateManager:
    _instance = None
    _states: dict[str, SessionState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionStateManager, cls).__new__(cls)
        return cls._instance

    def get_state(self, session_id: str) -> SessionState:
        if session_id not in self._states:
            self._states[session_id] = SessionState(session_id)
        return self._states[session_id]

    def remove_state(self, session_id: str):
        self._states.pop(session_id, None)

session_state_manager = SessionStateManager()

_voice_organisation_id: ContextVar[int | None] = ContextVar(
    "voice_organisation_id",
    default=None,
)

_voice_company_id: ContextVar[int | None] = ContextVar(
    "voice_company_id",
    default=None,
)

_voice_phone_number: ContextVar[str | None] = ContextVar(
    "voice_phone_number",
    default=None,
)

_voice_session_id: ContextVar[str | None] = ContextVar(
    "voice_session_id",
    default=None,
)

_voice_farmer_row_id: ContextVar[int | None] = ContextVar(
    "voice_farmer_row_id",
    default=None,
)

def set_current_organisation_id(organisation_id: int | None) -> Token:
    return _voice_organisation_id.set(organisation_id)

def get_current_organisation_id() -> int | None:
    return _voice_organisation_id.get()

def reset_current_organisation_id(token: Token) -> None:
    _voice_organisation_id.reset(token)

def set_current_company_id(company_id: int | None) -> Token:
    return _voice_company_id.set(company_id)

def get_current_company_id() -> int | None:
    return _voice_company_id.get()

def reset_current_company_id(token: Token) -> None:
    _voice_company_id.reset(token)

def set_current_phone_number(phone_number: str | None) -> Token:
    return _voice_phone_number.set(phone_number)

def get_current_phone_number() -> str | None:
    return _voice_phone_number.get()

def reset_current_phone_number(token: Token) -> None:
    _voice_phone_number.reset(token)

def set_current_session_id(session_id: str | None) -> Token:
    return _voice_session_id.set(session_id)

def get_current_session_id() -> str | None:
    return _voice_session_id.get()

def reset_current_session_id(token: Token) -> None:
    _voice_session_id.reset(token)

def set_current_farmer_row_id(farmer_row_id: int | None) -> Token:
    return _voice_farmer_row_id.set(farmer_row_id)

def get_current_farmer_row_id() -> int | None:
    return _voice_farmer_row_id.get()

def reset_current_farmer_row_id(token: Token) -> None:
    _voice_farmer_row_id.reset(token)
