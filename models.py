from typing import Optional

from pydantic import conint, field_validator
from redis_om import (
    Field,
    HashModel,
)



class Player(HashModel):
    id: str = Field(primary_key=True)
    name: str = Field(max_length=20)
    description: str = Field(max_length=1024)
    gold: int = conint(ge=0, le=1000000000)  # 1 billion
    silver: int = conint(ge=0, le=1000000000)  # 1 billion
    attack: int = Field(ge=0, default=0)
    hit_points: int = Field(ge=0, default=0)
    luck: float = Field(default=0.0)
    score: int = Field(ge=0, default=0)

    @classmethod
    @field_validator('name')
    def validate_name_unique(cls, v):
        exists = Player.find(Player.name == v)
        if exists:
            raise ValueError("Name already exists. Please choose a unique name.")
        return v


class Battle(HashModel):
    battle_id: str
    attacker_id: str
    defender_id: str
    winner_id: Optional[str]
    battle_log: str = ""


class Leaderboard(HashModel):
    player_id: str = Field(index=True)
    total_resources_stolen: int = Field(index=True)

    class Index:
        fields = ('rank',)