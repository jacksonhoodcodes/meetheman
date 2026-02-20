from datetime import date


def signup_and_login(client, email='alice@school.edu', password='password123', full_name='Alice'):
    r = client.post('/auth/signup', json={'email': email, 'password': password, 'full_name': full_name})
    assert r.status_code == 201
    r = client.post('/auth/login', json={'email': email, 'password': password})
    assert r.status_code == 200
    token = r.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def test_signup_domain_allowlist_and_login(client):
    denied = client.post('/auth/signup', json={'email': 'bad@gmail.com', 'password': 'password123', 'full_name': 'Bad'})
    assert denied.status_code == 400

    headers = signup_and_login(client)
    assert headers['Authorization'].startswith('Bearer ')


def test_create_goal_generates_steps_and_progress_updates(client):
    headers = signup_and_login(client)

    catalog = client.get('/goals/catalog', headers=headers)
    goal_id = catalog.json()[0]['id']

    created = client.post('/goals/user', json={'goal_type_id': goal_id}, headers=headers)
    assert created.status_code == 201
    user_goal_id = created.json()['id']

    steps = client.get(f'/goals/user/{user_goal_id}/steps', headers=headers)
    assert steps.status_code == 200
    assert len(steps.json()) == 4

    step_id = steps.json()[0]['id']
    updated = client.post(f'/progress/steps/{step_id}/complete', headers=headers)
    assert updated.status_code == 200
    assert updated.json()['progress_percent'] == 25


def test_matching_and_group_checkins(client):
    mentor_headers = signup_and_login(client, 'mentor@school.edu', full_name='Mentor')
    learner_headers = signup_and_login(client, 'learner@school.edu', full_name='Learner')

    goal_id = client.get('/goals/catalog', headers=mentor_headers).json()[0]['id']
    mentor_goal = client.post('/goals/user', json={'goal_type_id': goal_id}, headers=mentor_headers).json()
    steps = client.get(f"/goals/user/{mentor_goal['id']}/steps", headers=mentor_headers).json()
    for step in steps:
        resp = client.post(f"/progress/steps/{step['id']}/complete", headers=mentor_headers)
        assert resp.status_code == 200

    learner_goal = client.post('/goals/user', json={'goal_type_id': goal_id}, headers=learner_headers)
    assert learner_goal.status_code == 201

    mentors = client.get(f'/matching/mentors?goal_type_id={goal_id}', headers=learner_headers)
    assert mentors.status_code == 200
    assert len(mentors.json()) >= 1
    mentor_id = mentors.json()[0]['mentor_user_id']

    match = client.post('/matching/requests', json={'mentor_id': mentor_id, 'goal_type_id': goal_id, 'note': 'Help me!'}, headers=learner_headers)
    assert match.status_code == 201

    groups = client.get('/groups/mine', headers=learner_headers)
    assert groups.status_code == 200
    group_id = groups.json()[0]['id']

    checkin = client.post(
        f'/groups/{group_id}/checkins',
        json={'content': 'Made progress this week', 'week_start': str(date.today())},
        headers=learner_headers,
    )
    assert checkin.status_code == 201

    feed = client.get(f'/groups/{group_id}/checkins', headers=learner_headers)
    assert feed.status_code == 200
    assert len(feed.json()) == 1


def test_access_control_for_goals_groups_and_match_threads(client):
    alice = signup_and_login(client, 'alice@school.edu', full_name='Alice')
    bob = signup_and_login(client, 'bob@school.edu', full_name='Bob')

    goal_id = client.get('/goals/catalog', headers=alice).json()[0]['id']
    alice_goal = client.post('/goals/user', json={'goal_type_id': goal_id}, headers=alice).json()
    bob_goal = client.post('/goals/user', json={'goal_type_id': goal_id}, headers=bob).json()

    denied_goal = client.get(f"/goals/user/{alice_goal['id']}", headers=bob)
    assert denied_goal.status_code == 404

    bob_group = client.get('/groups/mine', headers=bob).json()[0]['id']
    outsider = signup_and_login(client, 'outsider@other.edu', full_name='Outsider')
    denied_group = client.get(f'/groups/{bob_group}/checkins', headers=outsider)
    assert denied_group.status_code == 403

    # setup match thread visibility
    steps = client.get(f"/goals/user/{bob_goal['id']}/steps", headers=bob).json()
    for step in steps:
        client.post(f"/progress/steps/{step['id']}/complete", headers=bob)

    req = client.post('/matching/requests', json={'mentor_id': 2, 'goal_type_id': goal_id, 'note': 'yo'}, headers=alice)
    assert req.status_code == 201
    request_id = req.json()['id']

    denied_match = client.get(f'/matching/requests/{request_id}', headers=outsider)
    assert denied_match.status_code == 403
