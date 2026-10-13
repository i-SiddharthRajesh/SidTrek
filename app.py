from flask import Flask, g, session
from werkzeug.security import generate_password_hash
from models import db, User
from routes import auth_bp, admin_bp, staff_bp, user_bp, api_bp
import os

app = Flask(__name__)

# Config
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise RuntimeError(
        "SECRET_KEY is required. Set it in your environment before starting SidTrek."
    )
app.config["SECRET_KEY"] = secret_key
database_url = os.environ.get("DATABASE_URL", "").strip()
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # SQLite is convenient for local development. Use DATABASE_URL for hosted PostgreSQL.
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "instance", "trekking.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ── Database ─────────────────────────────────────────────────────────
os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)
db.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role="admin").first():
        admin_password = os.environ.get("ADMIN_BOOTSTRAP_PASSWORD")
        if admin_password:
            admin = User(
                username="admin",
                email="admin@trekking.com",
                password=generate_password_hash(admin_password),
                full_name="System Administrator",
                phone="",
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
        else:
            app.logger.warning(
                "No admin account exists yet. Set ADMIN_BOOTSTRAP_PASSWORD "
                "before the first startup to create the initial admin."
            )

# ── Blueprints ───────────────────────────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(user_bp)
app.register_blueprint(api_bp)

# ── Global before-request ────────────────────────────────────────────
@app.before_request
def before_request():
    g.user = None
    if "user_id" in session:
        g.user = User.query.get(session["user_id"])

# ── Run ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
