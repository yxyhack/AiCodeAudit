from pydantic import BaseModel, Field
from typing import List, Optional

class SourceFile(BaseModel):
    path: str
    name: str
    source_code: str
    extension: str

class SourceDir(BaseModel):
    path: str
    name: str
    source_dirs: Optional[List['SourceDir']] = Field(default_factory=list)
    source_files: Optional[List[SourceFile]] = Field(default_factory=list)


class OpenAIConfig(BaseModel):
    api_key: str
    base_url: str
    max_per_tokens: int
    model: str

class ProjectConfig(BaseModel):
    config_file_ext: List[str] = []
    exclude_dir: List[str] = []
    exclude_max_file_size: float
    source_file_ext: List[str] = []

class Config(BaseModel):
    openai: OpenAIConfig
    project: ProjectConfig


class CodeUnit(BaseModel):
    source_code:str
    start_code_line:int
    end_code_line:int
    name:str
    path:str
    source_name:str
    target_name:str
    source_desc:str


