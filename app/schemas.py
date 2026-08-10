from typing import Literal

from pydantic import BaseModel, Field


class DependencyInput(BaseModel):
    ecosystem: Literal["PyPI", "npm"] = Field(
        description="Écosystème auquel appartient le paquet."
    )
    name: str = Field(
        min_length=1,
        examples=["requests"],
        description="Nom exact du paquet.",
    )
    version: str = Field(
        min_length=1,
        examples=["2.19.0"],
        description="Version exacte du paquet.",
    )