from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, UserGoal, UserStep
from app.schemas import UserGoalOut
from app.services import mark_step_complete, recalculate_progress

router = APIRouter(prefix='/progress', tags=['progress'])


@router.post('/steps/{step_id}/complete', response_model=UserGoalOut)
def complete_step(step_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    step = db.query(UserStep).filter(UserStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail='Step not found')

    user_goal = db.query(UserGoal).filter(UserGoal.id == step.user_goal_id).first()
    if not user_goal or user_goal.user_id != user.id:
        raise HTTPException(status_code=403, detail='Forbidden')

    if not step.is_completed:
        mark_step_complete(step)
    recalculate_progress(db, user_goal)
    db.commit()
    db.refresh(user_goal)
    return user_goal
