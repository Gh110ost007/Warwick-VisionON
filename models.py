from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_superuser = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    about = db.Column(db.Text)
    
    profile_photo_url = db.Column(db.String(200))

    artworks = db.relationship('Artwork', backref='artist', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Artwork(db.Model):
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    image_file = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    moderation_status = db.Column(db.String(20), default='unmoderated')
    location = db.Column(db.String(50), default='none')
    archived = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    archived_by = db.Column(db.String(80), nullable=True)
    archived_date = db.Column(db.DateTime, nullable=True)
    pixel_data = db.Column(db.LargeBinary, nullable=True)
    identifier = db.Column(db.String(50), nullable=True)
    qr_code = db.Column(db.String(120), nullable=True)
    
    votes = db.relationship('Vote', backref='artwork', lazy='dynamic')
    
    def vote_total(self):
        return sum(vote.value for vote in self.votes)


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)  # +1 for upvote, -1 for downvote
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    # Ensure each user can vote only once per artwork
    __table_args__ = (db.UniqueConstraint('user_id', 'artwork_id', name='unique_vote'),)


class VoteResetLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artwork_id = db.Column(db.Integer, db.ForeignKey('artwork.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    reset_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    artwork = db.relationship('Artwork', backref='reset_logs')

class TransactionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)