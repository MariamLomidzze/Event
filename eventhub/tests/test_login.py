from tests.conftest import login


def test_register_creates_user(client, app, db):
    response = client.post('/register', data={
        'name': 'New Person',
        'email': 'newperson@example.com',
        'password': 'securepass1',
        'confirm_password': 'securepass1',
    }, follow_redirects=True)

    assert response.status_code == 200

    from models import User
    with app.app_context():
        assert User.query.filter_by(email='newperson@example.com').first() is not None


def test_login_with_correct_credentials_succeeds(client, sample_user):
    response = login(client, 'test@example.com', 'password123')
    assert response.status_code == 200
    assert 'Add Event'.encode('utf-8') in response.data


def test_login_with_wrong_password_fails(client, sample_user):
    response = login(client, 'test@example.com', 'wrongpassword')
    assert response.status_code == 200
    assert 'იმეილი ან პაროლი არასწორია'.encode('utf-8') in response.data


def test_logout_clears_session(client, sample_user):
    login(client, 'test@example.com', 'password123')
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert 'Login'.encode('utf-8') in response.data
