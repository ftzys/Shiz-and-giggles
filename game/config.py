from dataclasses import dataclass


@dataclass
class MatchSettings:
    """Server-configurable knobs for the match lifecycle."""

    time_limit_seconds: int = 10 * 60
    frag_limit: int = 25
    item_respawn_seconds: int = 30
    invulnerability_seconds: float = 2.5

    def validate(self) -> None:
        if self.time_limit_seconds <= 0:
            raise ValueError("time_limit_seconds must be positive")
        if self.frag_limit <= 0:
            raise ValueError("frag_limit must be positive")
        if self.item_respawn_seconds <= 0:
            raise ValueError("item_respawn_seconds must be positive")
        if self.invulnerability_seconds < 0:
            raise ValueError("invulnerability_seconds cannot be negative")
