from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import CheckinPost, Group, GroupMembership, User
from app.schemas import CheckinIn, CheckinOut
from app.services import assert_group_member, create_checkin

router = APIRouter(prefix='/groups', tags=['groups'])


@router.get('/mine')
def my_groups(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(GroupMembership).filter(GroupMembership.user_id == user.id).all()
    group_ids = [m.group_id for m in memberships]
    groups = db.query(Group).filter(Group.id.in_(group_ids)).all() if group_ids else []
    return [{'id': g.id, 'goal_type_id': g.goal_type_id, 'name': g.name} for g in groups]


@router.get('/{group_id}/checkins', response_model=list[CheckinOut])
def list_checkins(group_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail='Group not found')
    if group.school_id != user.school_id:
        raise HTTPException(status_code=403, detail='Forbidden')
    assert_group_member(db, group_id, user.id)
    return db.query(CheckinPost).filter(CheckinPost.group_id == group_id).order_by(CheckinPost.created_at.desc()).all()


@router.post('/{group_id}/checkins', response_model=CheckinOut, status_code=201)
def create_checkin_post(group_id: int, payload: CheckinIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail='Group not found')
    if group.school_id != user.school_id:
        raise HTTPException(status_code=403, detail='Forbidden')
    assert_group_member(db, group_id, user.id)
    post = create_checkin(db, group_id, user.id, payload.week_start, payload.content)
    db.commit()
    db.refresh(post)
    return post
