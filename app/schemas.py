from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    school_id: int

    class Config:
        from_attributes = True


class GoalTypeOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class CreateUserGoalIn(BaseModel):
    goal_type_id: int


class UserGoalOut(BaseModel):
    id: int
    user_id: int
    goal_type_id: int
    progress_percent: int
    streak_weeks: int
    achieved: bool

    class Config:
        from_attributes = True


class UserStepOut(BaseModel):
    id: int
    user_goal_id: int
    week_number: int
    title: str
    is_completed: bool

    class Config:
        from_attributes = True


class MentorOut(BaseModel):
    mentor_user_id: int
    full_name: str
    bio: str


class MatchRequestIn(BaseModel):
    mentor_id: int
    goal_type_id: int
    note: str = ''


class MatchRequestOut(BaseModel):
    id: int
    requester_id: int
    mentor_id: int
    goal_type_id: int
    status: str
    note: str

    class Config:
        from_attributes = True


class CheckinIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    week_start: date


class CheckinOut(BaseModel):
    id: int
    group_id: int
    author_id: int
    week_start: date
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
