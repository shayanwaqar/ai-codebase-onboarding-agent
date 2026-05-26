from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "AI Codebase Onboarding Agent"
    app_env: str = "development"


settings = Settings()
