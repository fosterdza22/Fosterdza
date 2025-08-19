import click
from app import create_app, db
from app.models import User

app = create_app()

@app.cli.command("make-admin")
@click.argument("email")
def make_admin(email):
    """Gives a user admin privileges."""
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f"User {email} is now an admin.")
    else:
        print(f"User {email} not found.")

if __name__ == "__main__":
    app.run(debug=True)
