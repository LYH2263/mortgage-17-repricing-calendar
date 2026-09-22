from pydantic import BaseModel, Field, model_validator
from app.engines.repricing import valid_month_day


class ScheduleRequest(BaseModel):
    principal: float = Field(gt=0)
    annual_rate: float = Field(ge=0)
    months: int = Field(gt=0, le=600)
    loan_id: int | None = None
    persist: bool = True
    preview_rows: int = Field(default=12, ge=1, le=120)
    start_month: int | None = Field(default=None, ge=1, le=12)
    start_day: int | None = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def _check_start_month_day(self):
        if (self.start_month is None) != (self.start_day is None):
            raise ValueError("起息月日须同时提交月与日")
        if self.start_month is not None and not valid_month_day(self.start_month, self.start_day):
            raise ValueError("起息月日不合法")
        return self
