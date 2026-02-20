from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    CheckinPost,
    GoalTemplateStep,
    Group,
    GroupMembership,
    MentorProfile,
    UserGoal,
    UserStep,
)


def ensure_school_scope(actor_school_id: int, target_school_id: int):
    if actor_school_id != target_school_id:
        raise HTTPException(status_code=403, detail='Cross-school access is forbidden')


def create_goal_steps(db: Session, user_goal: UserGoal) -> None:
    templates = (
        db.query(GoalTemplateStep)
        .filter(GoalTemplateStep.goal_type_id == user_goal.goal_type_id)
        .order_by(GoalTemplateStep.week_number.asc(), GoalTemplateStep.id.asc())
        .all()
    )
    if not templates:
        raise HTTPException(status_code=400, detail='Goal has no template steps')
    for template in templates:
        db.add(UserStep(user_goal_id=user_goal.id, week_number=template.week_number, title=template.title))


def recalculate_progress(db: Session, user_goal: UserGoal) -> UserGoal:
    steps = db.query(UserStep).filter(UserStep.user_goal_id == user_goal.id).all()
    total = len(steps)
    completed = sum(1 for s in steps if s.is_completed)
    user_goal.progress_percent = int((completed / total) * 100) if total else 0
    weekly = {}
    for step in steps:
        weekly.setdefault(step.week_number, []).append(step.is_completed)
    user_goal.streak_weeks = 0
    for week in sorted(weekly.keys()):
        if all(weekly[week]):
            user_goal.streak_weeks += 1
        else:
            break
    user_goal.achieved = user_goal.progress_percent == 100
    db.flush()
    if user_goal.achieved:
        existing = db.query(MentorProfile).filter(MentorProfile.user_id == user_goal.user_id).first()
        if not existing:
            db.add(MentorProfile(user_id=user_goal.user_id, bio='Achieved goal mentor'))
    return user_goal


def ensure_group_for_goal(db: Session, school_id: int, goal_type_id: int) -> Group:
    group = db.query(Group).filter(Group.school_id == school_id, Group.goal_type_id == goal_type_id).first()
    if group:
        return group
    group = Group(school_id=school_id, goal_type_id=goal_type_id, name=f'Goal {goal_type_id} Cohort')
    db.add(group)
    db.flush()
    return group


def ensure_group_membership(db: Session, group_id: int, user_id: int):
    membership = db.query(GroupMembership).filter(
        GroupMembership.group_id == group_id,
        GroupMembership.user_id == user_id,
    ).first()
    if not membership:
        db.add(GroupMembership(group_id=group_id, user_id=user_id))


def assert_group_member(db: Session, group_id: int, user_id: int):
    membership = db.query(GroupMembership).filter(
        GroupMembership.group_id == group_id,
        GroupMembership.user_id == user_id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail='Group members only')


def create_checkin(db: Session, group_id: int, user_id: int, week_start, content: str) -> CheckinPost:
    post = CheckinPost(group_id=group_id, author_id=user_id, week_start=week_start, content=content)
    db.add(post)
    db.flush()
    return post


def mark_step_complete(step: UserStep):
    step.is_completed = True
    step.completed_at = datetime.utcnow()
