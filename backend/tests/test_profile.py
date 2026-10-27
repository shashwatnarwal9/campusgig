import io

PROFILE = "/api/v1/profile"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff" + b"\x00" * 64
PDF = b"%PDF-1.7\n" + b"\x00" * 64


def error_code(response) -> str:
    return response.json()["detail"]["code"]


def upload(client, path: str, content: bytes, filename: str, content_type: str):
    return client.post(path, files={"file": (filename, io.BytesIO(content), content_type)})


def test_profile_returns_signup_details(client, logged_in):
    logged_in()
    body = client.get(PROFILE).json()
    assert body["email"] == "student@thapar.edu"
    assert body["roll_no"] == "102103999"
    assert body["dept"] == "Computer Science"
    assert body["batch"] == 2026
    assert body["bio"] is None
    assert body["avatar_url"] is None
    assert body["resume_url"] is None


def test_profile_never_exposes_credentials(client, logged_in):
    logged_in()
    body = client.get(PROFILE).text
    assert "password" not in body.lower()
    assert "hash" not in body.lower()


def test_profile_requires_authentication(client):
    assert client.get(PROFILE).status_code == 401
    assert client.patch(PROFILE, json={"bio": "hi"}).status_code == 401
    assert upload(client, f"{PROFILE}/avatar", PNG, "a.png", "image/png").status_code == 401


def test_update_bio(client, logged_in):
    logged_in()
    body = client.patch(PROFILE, json={"bio": "  Final year CSE, I build web things.  "}).json()
    assert body["bio"] == "Final year CSE, I build web things."
    assert client.get(PROFILE).json()["bio"] == "Final year CSE, I build web things."


def test_blank_bio_clears_it(client, logged_in):
    logged_in()
    client.patch(PROFILE, json={"bio": "something"})
    assert client.patch(PROFILE, json={"bio": "   "}).json()["bio"] is None


def test_overlong_bio_is_rejected(client, logged_in):
    logged_in()
    assert client.patch(PROFILE, json={"bio": "x" * 1001}).status_code == 422


def test_upload_avatar(client, logged_in):
    logged_in()
    body = upload(client, f"{PROFILE}/avatar", PNG, "me.png", "image/png").json()
    assert body["avatar_url"].startswith("/media/avatars/")
    assert body["avatar_url"].endswith(".png")
    # the client's filename is never reused
    assert "me.png" not in body["avatar_url"]


def test_upload_resume(client, logged_in):
    logged_in()
    body = upload(client, f"{PROFILE}/resume", PDF, "cv.pdf", "application/pdf").json()
    assert body["resume_url"].startswith("/media/resumes/")
    assert body["resume_url"].endswith(".pdf")


def test_content_type_header_is_not_trusted(client, logged_in):
    """A file's first bytes decide what it is, not the label the browser sends."""
    logged_in()
    response = upload(client, f"{PROFILE}/avatar", b"MZ\x90\x00 not an image", "x.png", "image/png")
    assert response.status_code == 415
    assert error_code(response) == "unsupported_file_type"


def test_pdf_rejected_as_avatar_and_image_rejected_as_resume(client, logged_in):
    logged_in()
    assert upload(client, f"{PROFILE}/avatar", PDF, "a.pdf", "image/png").status_code == 415
    assert upload(client, f"{PROFILE}/resume", JPEG, "a.jpg", "application/pdf").status_code == 415


def test_oversized_upload_is_rejected(client, logged_in, monkeypatch):
    from app.core.config import settings

    logged_in()
    monkeypatch.setattr(settings, "max_avatar_bytes", 128, raising=False)
    response = upload(client, f"{PROFILE}/avatar", PNG + b"\x00" * 500, "big.png", "image/png")
    assert response.status_code == 413
    assert error_code(response) == "file_too_large"


def test_replacing_an_avatar_removes_the_old_file(client, logged_in):
    from pathlib import Path

    from app.core.config import settings

    logged_in()
    first = upload(client, f"{PROFILE}/avatar", PNG, "one.png", "image/png").json()["avatar_url"]
    second = upload(client, f"{PROFILE}/avatar", JPEG, "two.jpg", "image/jpeg").json()["avatar_url"]
    assert first != second

    old_file = Path(settings.media_root) / first.removeprefix("/media/")
    assert not old_file.exists()
    assert (Path(settings.media_root) / second.removeprefix("/media/")).exists()
