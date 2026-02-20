import logging

from fastapi import FastAPI

from app.database import Base, engine
from app.routes import auth, goals, groups, matching, progress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title='Meetheman API', version='0.1.0')


@app.on_event('startup')
def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info('Database schema ensured')


@app.get('/health')
def health():
    return {'status': 'ok'}


app.include_router(auth.router)
app.include_router(goals.router)
app.include_router(progress.router)
app.include_router(matching.router)
app.include_router(groups.router)
