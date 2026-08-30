from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    users = [
        {
            "name": "Ankit",
            "email": "ankit@demo.com",
            "password": "Ankit@7828",
            "role": "supervisor",
        },
        {
            "name": "Riya",
            "email": "riya@demo.com",
            "password": "riya@123",
            "role": "agent",
        },
        {
            "name": "Shivam",
            "email": "shivam@demo.com",
            "password": "shivam@123",
            "role": "agent",
        },
        {
            "name": "Raghav",
            "email": "raghav@demo.com",
            "password": "raghav@123",
            "role": "agent",
        },
    ]

    for data in users:
        existing_user = User.query.filter_by(
            email=data["email"]
        ).first()

        if existing_user:
            print(f"Already exists: {data['email']}")
            continue

        user = User(
            name=data["name"],
            email=data["email"],
            role=data["role"],
        )

        user.set_password(data["password"])
        db.session.add(user)
    db.session.commit()
    print("Demo users created successfully!")