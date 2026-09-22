from pydantic import BaseModel, Field, model_validator
from app.engines.repricing import valid_month_day


class RepricingRuleIn(BaseModel):
    start_month: int = Field(ge=1, le=12)
    start_day: int = Field(ge=1, le=31)
    end_month: int = Field(ge=1, le=12)
    end_day: int = Field(ge=1, le=31)
    in_window_rate: float = Field(ge=0)
    out_window_rate: float = Field(ge=0)
    enabled: bool = True

    @model_validator(mode="after")
    def _check_month_day(self):
        if not valid_month_day(self.start_month, self.start_day):
            raise ValueError("窗起月日不合法")
        if not valid_month_day(self.end_month, self.end_day):
            raise ValueError("窗止月日不合法")
        return self
