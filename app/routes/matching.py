from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import GoalType, MatchRequest, MentorProfile, User, UserGoal
from app.schemas import MatchRequestIn, MatchRequestOut, MentorOut

router = APIRouter(prefix='/matching', tags=['matching'])


@router.get('/mentors', response_model=list[MentorOut])
def list_mentors(
    goal_type_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    goal = db.query(GoalType).filter(GoalType.id == goal_type_id, GoalType.school_id == user.school_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail='Goal not found')

    achieved = db.query(UserGoal).filter(
        UserGoal.goal_type_id == goal_type_id,
        UserGoal.achieved.is_(True),
    ).all()
    mentor_user_ids = [g.user_id for g in achieved if g.user_id != user.id]
    if not mentor_user_ids:
        return []
    profiles = db.query(MentorProfile).filter(MentorProfile.user_id.in_(mentor_user_ids)).all()
    users = {u.id: u for u in db.query(User).filter(User.id.in_(mentor_user_ids), User.school_id == user.school_id).all()}
    return [MentorOut(mentor_user_id=p.user_id, full_name=users[p.user_id].full_name, bio=p.bio) for p in profiles if p.user_id in users]


@router.post('/requests', response_model=MatchRequestOut, status_code=201)
def create_request(payload: MatchRequestIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mentor = db.query(User).filter(User.id == payload.mentor_id).first()
    goal = db.query(GoalType).filter(GoalType.id == payload.goal_type_id).first()
    if not mentor or not goal:
        raise HTTPException(status_code=404, detail='Mentor or goal not found')
    if mentor.school_id != user.school_id or goal.school_id != user.school_id:
        raise HTTPException(status_code=403, detail='Cross-school matching forbidden')

    mentor_goal = db.query(UserGoal).filter(
        UserGoal.user_id == mentor.id,
        UserGoal.goal_type_id == payload.goal_type_id,
        UserGoal.achieved.is_(True),
    ).first()
    if not mentor_goal:
        raise HTTPException(status_code=400, detail='Mentor has not achieved this goal')

    request = MatchRequest(
        requester_id=user.id,
        mentor_id=mentor.id,
        goal_type_id=payload.goal_type_id,
        note=payload.note,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get('/requests/{request_id}', response_model=MatchRequestOut)
def get_request(request_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    request = db.query(MatchRequest).filter(MatchRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail='Request not found')
    if user.id not in (request.requester_id, request.mentor_id):
        raise HTTPException(status_code=403, detail='Participants only')
    return request
