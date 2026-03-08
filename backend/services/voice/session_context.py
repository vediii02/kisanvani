from contextvars import ContextVar, Token


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
