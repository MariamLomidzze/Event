from tests.conftest import login


def test_owner_can_access_edit_page(client, sample_user, sample_event):
    login(client, 'test@example.com', 'password123')
    response = client.get(f'/event/{sample_event.id}/update')
    assert response.status_code == 200


def test_other_user_cannot_edit_event(client, other_user, sample_event):
    login(client, 'other@example.com', 'password456')
    response = client.get(f'/event/{sample_event.id}/update')
    assert response.status_code == 403


def test_other_user_cannot_delete_event(client, other_user, sample_event):
    login(client, 'other@example.com', 'password456')
    response = client.post(f'/event/{sample_event.id}/delete')
    assert response.status_code == 403


def test_owner_can_delete_event(client, sample_user, sample_event, app, db):
    login(client, 'test@example.com', 'password123')
    response = client.post(f'/event/{sample_event.id}/delete', follow_redirects=True)
    assert response.status_code == 200

    from models import Event
    with app.app_context():
        assert Event.query.get(sample_event.id) is None
