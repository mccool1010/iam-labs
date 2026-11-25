import os
from urllib.parse import urlencode

from flask import Flask, redirect, session, url_for
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import jwt

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=(
        "https://" + os.getenv("AUTH0_DOMAIN")
        + "/.well-known/openid-configuration"
    ),
)


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        audience=os.getenv("AUTH0_AUDIENCE"),
    )


@app.route("/callback")
def callback():
    token = oauth.auth0.authorize_access_token()
    session["token"] = token
    return redirect("/")


@app.route("/")
def home():
    token = session.get("token")
    if not token:
        return '<a href="/login">Login</a>'

    access_token = token["access_token"]
    # Display only. A real API must verify the signature, issuer and audience.
    claims = jwt.decode(access_token, options={"verify_signature": False})
    permissions = claims.get("permissions", [])
    email = token["userinfo"]["email"]

    return f"""
        <h2>{email}</h2>
        <p>Permissions: {permissions}</p>
        <a href="/logout">Logout</a>
    """


@app.route("/logout")
def logout():
    session.clear()
    params = urlencode({
        "client_id": os.getenv("AUTH0_CLIENT_ID"),
        "returnTo": "http://127.0.0.1:5000/",
    })
    return redirect(
        "https://" + os.getenv("AUTH0_DOMAIN") + "/v2/logout?" + params
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)