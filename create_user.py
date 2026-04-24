from app import db, User, app

with app.app_context():
    existing_user = User.query.filter_by(username="admin").first()
    if not existing_user:
        admin = User(username="admin", password="admin")
        db.session.add(admin)
        db.session.commit()
        print("Default user created: admin/admin")
    else:
        print("User 'admin' already exists, skipping creation.")