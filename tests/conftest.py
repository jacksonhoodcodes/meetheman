import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['JWT_SECRET'] = 'test-secret'
os.environ['ALLOWED_SCHOOL_DOMAINS'] = 'school.edu,other.edu'

from app.database import Base, get_db
from app.main import app
from app.models import GoalTemplateStep, GoalType, School

SQLALCHEMY_DATABASE_URL = 'sqlite:///./test.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    school = School(name='School', domain='school.edu')
    other = School(name='Other', domain='other.edu')
    db.add_all([school, other])
    db.flush()

    goal = GoalType(school_id=school.id, name='Get Internship', description='Internship goal')
    other_goal = GoalType(school_id=other.id, name='Other Goal', description='Other')
    db.add_all([goal, other_goal])
    db.flush()

    for week in range(1, 5):
        db.add(GoalTemplateStep(goal_type_id=goal.id, week_number=week, title=f'Week {week} step'))
        db.add(GoalTemplateStep(goal_type_id=other_goal.id, week_number=week, title=f'Other week {week}'))

    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
