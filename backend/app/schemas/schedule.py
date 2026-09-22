from pydantic import BaseModel, Field, model_validator
from app.modules.rate_float import valid_month_day

class ScheduleRequest(BaseModel):
    principal: float = Field(gt=0)
    annual_rate: float = Field(ge=0)          # 回退年利率（百分比），如 3.5 表示 3.5%
    months: int = Field(gt=0, le=600)
    loan_id: int | None = None
    persist: bool = True
    preview_rows: int = Field(default=12, ge=1, le=120)
    value_month: int | None = Field(default=None, ge=1, le=12)
    value_day: int | None = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def _check_value_date(self):
        if (self.value_month is None) != (self.value_day is None):
            raise ValueError("起息月与起息日必须同时提供或同时省略")
        if self.value_month is not None and not valid_month_day(self.value_month, self.value_day):
            raise ValueError(f"起息月日不合法：{self.value_month}-{self.value_day}（允许 2-29）")
        return self
