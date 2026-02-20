from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import GoalType, User, UserGoal, UserStep
from app.schemas import CreateUserGoalIn, GoalTypeOut, UserGoalOut, UserStepOut
from app.services import create_goal_steps, ensure_group_for_goal, ensure_group_membership, recalculate_progress

router = APIRouter(prefix='/goals', tags=['goals'])


@router.get('/catalog', response_model=list[GoalTypeOut])
def list_goal_catalog(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    return (
        db.query(GoalType)
        .filter(GoalType.school_id == user.school_id)
        .offset(offset)
        .limit(page_size)
        .all()
    )


@router.post('/user', response_model=UserGoalOut, status_code=201)
def create_user_goal(payload: CreateUserGoalIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal_type = db.query(GoalType).filter(GoalType.id == payload.goal_type_id).first()
    if not goal_type or goal_type.school_id != user.school_id:
        raise HTTPException(status_code=404, detail='Goal not found')

    existing = db.query(UserGoal).filter(UserGoal.user_id == user.id, UserGoal.goal_type_id == goal_type.id).first()
    if existing:
        raise HTTPException(status_code=409, detail='Goal already chosen')

    user_goal = UserGoal(user_id=user.id, goal_type_id=goal_type.id)
    db.add(user_goal)
    db.flush()
    create_goal_steps(db, user_goal)
    group = ensure_group_for_goal(db, user.school_id, goal_type.id)
    ensure_group_membership(db, group.id, user.id)
    recalculate_progress(db, user_goal)
    db.commit()
    db.refresh(user_goal)
    return user_goal


@router.get('/user/{user_goal_id}', response_model=UserGoalOut)
def get_user_goal(user_goal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_goal = db.query(UserGoal).filter(UserGoal.id == user_goal_id).first()
    if not user_goal or user_goal.user_id != user.id:
        raise HTTPException(status_code=404, detail='Goal not found')
    return user_goal


@router.get('/user/{user_goal_id}/steps', response_model=list[UserStepOut])
def list_user_goal_steps(user_goal_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_goal = db.query(UserGoal).filter(UserGoal.id == user_goal_id).first()
    if not user_goal or user_goal.user_id != user.id:
        raise HTTPException(status_code=404, detail='Goal not found')
    return db.query(UserStep).filter(UserStep.user_goal_id == user_goal.id).order_by(UserStep.week_number.asc()).all()
