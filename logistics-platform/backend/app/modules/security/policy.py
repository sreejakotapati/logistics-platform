"""Password policy — configurable strength rules applied at register / provision / reset.

This only ever *strengthens* validation (the Pydantic min_length=10 still applies first); it never
weakens an existing control. The policy is data-driven from Settings so deployments can tune it.
"""
from __future__ import annotations

from app.core.config import Settings
from app.core.exceptions import ValidationError

# A small embedded deny-list of obviously-weak passwords. Real deployments point at a larger list
# (e.g. HaveIBeenPwned k-anonymity) — this is the safe floor, not the whole defence.
_COMMON = {
    "password", "password1", "password123", "12345678", "123456789", "1234567890",
    "qwerty123", "letmein123", "welcome123", "admin1234", "iloveyou1", "changeme123",
    "passw0rd", "p@ssw0rd", "p@ssword1", "logistics1", "qwertyuiop",
}


def _char_classes(value: str) -> int:
    has_lower = any(c.islower() for c in value)
    has_upper = any(c.isupper() for c in value)
    has_digit = any(c.isdigit() for c in value)
    has_symbol = any(not c.isalnum() for c in value)
    return sum((has_lower, has_upper, has_digit, has_symbol))


class PasswordPolicy:
    def __init__(self, settings: Settings) -> None:
        self.s = settings

    def describe(self) -> dict:
        return {
            "min_length": self.s.password_min_length,
            "max_length": self.s.password_max_length,
            "min_character_classes": self.s.password_min_char_classes,
            "character_classes": ["lowercase", "uppercase", "digit", "symbol"],
            "blocks_common_passwords": self.s.password_block_common,
        }

    def check(self, password: str) -> list[str]:
        """Return a list of human-readable failures (empty == OK)."""
        problems: list[str] = []
        if len(password) < self.s.password_min_length:
            problems.append(f"must be at least {self.s.password_min_length} characters")
        if len(password) > self.s.password_max_length:
            problems.append(f"must be at most {self.s.password_max_length} characters")
        classes = _char_classes(password)
        if classes < self.s.password_min_char_classes:
            problems.append(
                f"must include at least {self.s.password_min_char_classes} of: "
                "lowercase, uppercase, digit, symbol"
            )
        if self.s.password_block_common and password.lower() in _COMMON:
            problems.append("is too common")
        return problems

    def validate(self, password: str) -> None:
        problems = self.check(password)
        if problems:
            raise ValidationError("Password " + "; ".join(problems), code="weak_password")
