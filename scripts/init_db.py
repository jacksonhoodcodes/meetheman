from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import GoalTemplateStep, GoalType, School

DEFAULT_GOALS = [
    (
        'Data Structures Mastery',
        'Become fluent with core data structures and interview usage.',
        ['Arrays & Strings drills', 'Hash maps and sets', 'Trees & graphs basics', 'Weekly mock interview'],
    ),
    (
        'System Design Foundations',
        'Build practical system design instincts.',
        ['Requirements and APIs', 'Database and indexing choices', 'Caching and queues', 'Design walkthrough'],
    ),
]


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        domains = [d.strip().lower() for d in settings.allowed_school_domains.split(',') if d.strip()]
        for domain in domains:
            school = db.query(School).filter(School.domain == domain).first()
            if not school:
                school = School(name=domain.split('.')[0].title(), domain=domain)
                db.add(school)
                db.flush()

            for name, description, steps in DEFAULT_GOALS:
                goal = db.query(GoalType).filter(GoalType.school_id == school.id, GoalType.name == name).first()
                if not goal:
                    goal = GoalType(school_id=school.id, name=name, description=description)
                    db.add(goal)
                    db.flush()

                if db.query(GoalTemplateStep).filter(GoalTemplateStep.goal_type_id == goal.id).count() == 0:
                    for i, step in enumerate(steps, start=1):
                        db.add(GoalTemplateStep(goal_type_id=goal.id, week_number=i, title=step))
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    run()
