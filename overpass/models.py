from typing import Optional
import pydantic

class User(pydantic.BaseModel):
    snowflake: int
    username: str
    avatar: Optional[str]
    last_login_date: str