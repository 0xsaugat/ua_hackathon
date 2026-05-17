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


def test_submission_sends_email_and_redirects_to_different_url_when_validation_passes(monkeypatch):
    captured = {}

    def fake_sender(recipient_email, validation):
        captured["recipient_email"] = recipient_email
        captured["validation"] = validation
        return f"Email sent to {recipient_email} using test-host:587."

    monkeypatch.setattr(main.app.state, "mail_sender", fake_sender, raising=False)

    response = client.post("/contact-us", data={"email": "राम@नेपाल.नेपाल"}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/thank-you"
    assert captured["recipient_email"] == "राम@नेपाल.नेपाल"
    assert captured["validation"].valid is True


def test_submission_shows_smtp_error_when_delivery_fails(monkeypatch):
    def failing_sender(recipient_email, validation):
        raise RuntimeError("SMTP_HOST is not configured.")

    monkeypatch.setattr(main.app.state, "mail_sender", failing_sender, raising=False)

    response = client.post("/contact-us", data={"email": "mkandel.yy@gmail.com"})

    assert response.status_code == 502
    assert "SMTP Error" in response.text
    assert "Email is valid, but SMTP delivery failed" in response.text


def test_thank_you_page_renders_after_redirect():
    response = client.get("/thank-you")

    assert response.status_code == 200
    assert "Your UA-ready email passed" in response.text
