from contextvars import ContextVar, Token


_voice_organisation_id: ContextVar[int | None] = ContextVar(
    "voice_organisation_id",
    default=None,
)

_voice_company_id: ContextVar[int | None] = ContextVar(
    "voice_company_id",
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

