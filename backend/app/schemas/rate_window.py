from pydantic import BaseModel, Field, model_validator
from app.modules.rate_float import valid_month_day


class RateWindowRuleBody(BaseModel):
    start_month: int = Field(ge=1, le=12)
    start_day: int = Field(ge=1, le=31)
    end_month: int = Field(ge=1, le=12)
    end_day: int = Field(ge=1, le=31)
    in_rate: float = Field(ge=0)
    out_rate: float = Field(ge=0)
    enabled: bool = False

    @model_validator(mode="after")
    def _check_days(self):
        for label, m, d in (("窗起", self.start_month, self.start_day),
                            ("窗止", self.end_month, self.end_day)):
            if not valid_month_day(m, d):
                raise ValueError(f"{label}月日不合法：{m}-{d}（允许 2-29）")
        return self
