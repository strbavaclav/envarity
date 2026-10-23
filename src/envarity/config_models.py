from pydantic import BaseModel


class EnvironmentConfig(BaseModel):
    branch: str
    tier: str


class RepoConfig(BaseModel):
    name: str
    path: str
    environments: list[EnvironmentConfig]


class Rule(BaseModel):
    key_pattern: str
    expect: str
