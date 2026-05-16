from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


def test_home_page_renders_hackathon_ui():
    response = client.get("/contact-us")

    assert response.status_code == 200
    assert "UAReady Email and Domain Validation System" in response.text
    assert "Hackathon Nepal 2026" in response.text
    assert 'input type="text" id="email"' in response.text
    assert 'input type="submit" value="Contact us" id="submit"' in response.text


def test_submission_shows_validation_error_for_invalid_email():
    response = client.post("/contact-us", data={"email": "plainaddress"})

    assert response.status_code == 400
    assert "Please enter a valid international email address" in response.text
    assert "Syntax Error" in response.text
    assert "Email must contain exactly one @ symbol." in response.text


def test_submission_redirects_to_different_url_when_validation_passes():
    response = client.post("/contact-us", data={"email": "राम@नेपाल.नेपाल"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/thank-you"


def test_thank_you_page_renders_after_redirect():
    response = client.get("/thank-you")

    assert response.status_code == 200
    assert "Your UA-ready email passed" in response.text
