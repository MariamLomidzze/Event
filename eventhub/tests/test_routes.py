def test_home_shows_events_list(client):
    response = client.get('/')
    assert response.status_code == 200


def test_about_page_accessible_without_login(client):
    response = client.get('/about')
    assert response.status_code == 200


def test_event_detail_shows_event(client, sample_event):
    response = client.get(f'/event/{sample_event.id}')
    assert response.status_code == 200
    assert 'Test Concert'.encode('utf-8') in response.data


def test_nonexistent_event_returns_404(client):
    response = client.get('/event/9999')
    assert response.status_code == 404


def test_add_event_requires_login(client):
    response = client.get('/event/new')
    assert response.status_code == 302
    assert '/login' in response.location


def test_profile_requires_login(client):
    response = client.get('/profile')
    assert response.status_code == 302
    assert '/login' in response.location
