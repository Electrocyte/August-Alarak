from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Voice:
    id: str
    name: str
    category: str


@dataclass_json
@dataclass
class VoiceSetting:
    stability: float
    similarity_boost: float
