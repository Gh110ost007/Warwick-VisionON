from app import app
from extensions import db
import models  
from models import User

with app.app_context():
    db.create_all()
    print("Database tables created!")    
    if not User.query.filter_by(is_superuser=True).first():
        superuser = User(username="admin", email="admin@gmail.com")
        superuser.set_password("admin")
        superuser.is_superuser = True
        superuser.email_verified = True
        db.session.add(superuser)
        db.session.commit()
        print("Superuser created!")
    else:
        print("Superuser already exists!")
