from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, make_response
from extensions import db  # Import the db instance from extensions.py
import os
import qrcode
from datetime import datetime
from werkzeug.utils import secure_filename
from models import User, Artwork, Vote, VoteResetLog, TransactionLog
from PIL import Image
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

app = Flask(__name__)

# Configuration for Heroku deployment
if os.environ.get('DATABASE_URL'):
    # Heroku configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    app.config['MAIL_SUPPRESS_SEND'] = True  # Disable email on Heroku for demo
else:
    # Local configuration
    app.config.from_pyfile('config.py')
    app.config['MAIL_SUPPRESS_SEND'] = False

db.init_app(app)  # Initialize the database with the app
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

# Email configuration
if not os.environ.get('DATABASE_URL'):  # Only for local development
    app.config.update(
        MAIL_SERVER='smtp.dcs.warwick.ac.uk',
        MAIL_PORT=25,
        MAIL_USE_TLS=False,
        MAIL_USERNAME='',
        MAIL_PASSWORD='',
        MAIL_DEFAULT_SENDER=("NOREPLY", f"{os.getlogin()}@dcs.warwick.ac.uk")
    )



@app.route('/send')
def send():
    recipients = ["a.hague@warwick.ac.uk"]
    sender = f"{os.getlogin()}@dcs.warwick.ac.uk"
    mail.send_message(
        sender=("NOREPLY", sender),
        subject="FLASK-MAIL TEST",
        body="Testing",
        recipients=recipients
    )

    return make_response(f"<html><body><p>Sending your message to {recipients}</p></body></html>", 200)

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except Exception as e:
        flash("The verification link is invalid or has expired.", "danger")
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
        db.session.commit()
        flash("Email verified successfully! You can now log in.", "success")
    else:
        flash("User not found.", "danger")
    
    return redirect(url_for('login'))

def log_event(event_type, description):
    from models import TransactionLog  # Import here to avoid circular imports
    log = TransactionLog(event_type=event_type, description=description)
    db.session.add(log)
    db.session.commit()


@app.route('/transaction_logs')
def transaction_logs():
    # Only allow superusers to view logs
    user = User.query.get(session.get('user_id'))
    if not user or not user.is_superuser:
        flash("You are not authorized to view the transaction logs.", "danger")
        return redirect(url_for('home'))
    logs = TransactionLog.query.order_by(TransactionLog.timestamp.desc()).all()
    return render_template('log_dashboard.html', logs=logs)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if username or email already exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Username or email already exists!")
            return redirect(url_for('register'))
        
        # Create new user and set email_verified to False initially
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.email_verified = False
        db.session.add(new_user)
        db.session.commit()

        log_event("User Registration", f"User '{username}' registered with email '{email}'.")

        # Define mail sender using university settings
        mail_sender = f"{os.getlogin()}@dcs.warwick.ac.uk"

        # Generate a token for email verification
        token = s.dumps(new_user.email, salt='email-confirm')
        verify_url = url_for('verify_email', token=token, _external=True)

        # Create and send the verification email
        msg = Message(
            subject="Please verify your email",
            sender=("NOREPLY", mail_sender),
            recipients=[new_user.email]
        )
        msg.body = f"Click the link to verify your email: {verify_url}"
        mail.send(msg)
        
        flash("Registration successful! Please check your email to verify your account.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return {'current_user': user}
    return {'current_user': None}


@app.route('/debug/artworks')
def debug_artworks():
    artworks = Artwork.query.all()
    return '<br>'.join(
        [f"ID: {art.id}, Name: {art.name}, File: {art.image_file}, Status: {art.moderation_status}, Archived: {art.archived}, Archived Date: {art.archived_date}, Archived By: {art.archived_by}, Identifier: {art.identifier}, QR Code: {art.qr_code},  Location: {art.location}" for art in artworks]
    )

@app.route('/debug/users')
def debug_users():
    users = User.query.all()
    return '<br>'.join([f"ID: {user.id}, Username: {user.username}, Email: {user.email}" for user in users])

@app.route('/test_flash')
def test_flash():
    flash("This is a test flash message!")
    return render_template("test.html")

@app.route('/')
def home():
    return render_template("index.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form.get('login')
        password = request.form.get('password')
        
        user = User.query.filter((User.username == login_identifier) | (User.email == login_identifier)).first()
        
        # Enforce email verification: if the user's email is not verified, don't allow login.
        if user and not user.email_verified:
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for('login'))
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            log_event("User Login", f"User '{user.username}' logged in.")  # Log the login event
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid login credentials. Please try again.", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/send_reset_password', methods=['POST'])
def send_reset_password():
    if 'user_id' not in session:
        flash("Please log in to reset your password.", "warning")
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))
    
    # Generate token and URL (using your serializer 's')
    token = s.dumps(user.email, salt='password-reset-salt')
    reset_url = url_for('reset_password', token=token, _external=True)
    
    msg = Message(
        subject="Reset Your Password",
        sender=("NOREPLY", f"{os.getlogin()}@dcs.warwick.ac.uk"),
        recipients=[user.email],
        body=f"Please click the following link to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour."
    )
    mail.send(msg)
    flash("A password reset link has been sent to your email.", "info")
    return redirect(url_for('profile'))


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception as e:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for('login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('reset_password', token=token))
        user.set_password(new_password)
        db.session.commit()
        flash("Your password has been updated. Please log in.", "success")
        return redirect(url_for('profile'))
    
    return render_template('reset_password.html', token=token)


@app.route('/logout')
def logout():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        log_event("User Logout", f"User '{user.username}' logged out.")
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))


@app.route('/upload_artwork', methods=['GET', 'POST'])
def upload_artwork():
    if 'user_id' not in session:
        flash("You need to be logged in to upload artwork.", "warning")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        file = request.files.get('artwork')

        if not file or file.filename == '':
            flash("No file selected!", "danger")
            return redirect(request.url)
        
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        allowed_extensions = ['.gif', '.png', '.webp', '.jpg', '.jpeg']
        if ext not in allowed_extensions:
            flash("Only GIF, PNG, WEBP, or JPEG images are allowed.", "danger")
            return redirect(request.url)

        try:
            # Open the image using PIL to enforce the mode if needed
            image = Image.open(file)
        except Exception as e:
            flash("Error opening image: " + str(e), "danger")
            return redirect(request.url)
        
        # Enforce RGBA mode (32-bit) if necessary
        if image.mode != 'RGBA':
            flash("Image is not in 32-bit RGBA mode. Converting automatically.", "info")
            image = image.convert('RGBA')

        # Optionally, if you want to force a particular format, you can convert JPEGs to PNG
        if ext in ['.jpg', '.jpeg']:
            ext = '.png'
            filename = os.path.splitext(filename)[0] + ext

        # Get the binary data from the image.
        # You can choose to save it as PNG or another format.
        from io import BytesIO
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)
        binary_data = img_io.read()

        # Create a new Artwork record and store the binary data.
        # (Optionally, you can still store the filename in image_file if needed)
        request_mod = request.form.get('request_moderation')
        status = 'pending' if request_mod == 'yes' else 'unmoderated'

        new_artwork = Artwork(
            name=name,
            image_file=filename,  # optional
            pixel_data=binary_data,
            user_id=session['user_id'],
            moderation_status=status
        )
        db.session.add(new_artwork)
        db.session.commit()

        log_event("Artwork Uploaded", f"Artwork '{name}' uploaded by user ID {session['user_id']}.")
        flash("Artwork uploaded successfully!", "success")
        return redirect(url_for('home'))
    
    return render_template('upload_artwork.html')


@app.route('/artwork_image/<int:artwork_id>')
def artwork_image(artwork_id):
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.pixel_data:
        # Here, 'image/png' is used since we saved the image in PNG format.
        return Response(artwork.pixel_data, mimetype='image/png')
    else:
        # Return a default image or a 404 response if no image data is available.
        return Response("No image data found", status=404)




@app.route('/my_artworks')
def my_artworks():
    if 'user_id' not in session:
        flash("You need to be logged in to view your artworks.", "warning")
        return redirect(url_for('login'))
    
    # Get all artworks for the current user
    artworks = Artwork.query.filter_by(user_id=session['user_id']).all()
    return render_template('my_artworks.html', artworks=artworks)


@app.route('/request_moderation/<int:artwork_id>', methods=['POST'])
def request_moderation(artwork_id):
    # Ensure the user is logged in
    if 'user_id' not in session:
        flash("You need to be logged in to request moderation.", "warning")
        return redirect(url_for('login'))
    
    # Get the artwork record and ensure the current user is its owner
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.user_id != session.get('user_id'):
        flash("You are not authorized to request moderation for this artwork.", "danger")
        return redirect(request.referrer or url_for('home'))
    
    # Update the artwork status to 'pending'
    artwork.moderation_status = 'pending'
    db.session.commit()
    
    flash("Moderation requested successfully.", "success")
    return redirect(request.referrer or url_for('home'))


@app.route('/moderate_artworks')
def moderate_artworks():
    if 'user_id' not in session:
        flash("Please log in to access the moderation dashboard.", "warning")
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user.is_superuser:
        flash("You are not authorized to access this page.", "danger")
        return redirect(url_for('home'))
    
    # Include artworks with statuses unmoderated, pending, or moderated
    artworks = Artwork.query.filter(
        Artwork.moderation_status.in_(['unmoderated', 'pending', 'moderated'])
    ).all()
    return render_template('moderate_artworks.html', artworks=artworks)



@app.route('/approve_artwork/<int:artwork_id>', methods=['POST'])
def approve_artwork(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_superuser:
        flash("You are not authorized.", "danger")
        return redirect(url_for('home'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    artwork.moderation_status = 'moderated'
    
    # Generate a unique identifier if not already set
    if not artwork.identifier:
        # For simplicity, we use the artwork ID as the identifier
        artwork.identifier = f"ART-{artwork.id}"
    
    # Generate QR code if not already generated
    if not artwork.qr_code:
        # Create the QR code image using the identifier
        qr = qrcode.make(artwork.identifier)
        qr_filename = f"qr_{artwork.id}.png"
        # Define the folder to store QR codes (e.g., static/qr_codes)
        qr_folder = os.path.join(app.root_path, 'static', 'qr_codes')
        os.makedirs(qr_folder, exist_ok=True)
        qr_path = os.path.join(qr_folder, qr_filename)
        qr.save(qr_path)
        artwork.qr_code = qr_filename

    db.session.commit()
    log_event("Artwork Approved", f"Artwork '{artwork.name}' (ID: {artwork.id}) approved by user '{user.username}'.")
    flash("Artwork approved and QR code generated successfully.", "success")
    return redirect(url_for('moderate_artworks'))


@app.route('/unmoderate_artwork/<int:artwork_id>', methods=['POST'])
def unmoderate_artwork(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_superuser:
        flash("You are not authorized.", "danger")
        return redirect(url_for('home'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    artwork.moderation_status = 'unmoderated'
    db.session.commit()
    flash("Artwork has been set to unmoderated.", "info")
    return redirect(url_for('moderate_artworks'))


# ... other routes remain the same ...

@app.route('/vote_artwork/<int:artwork_id>/<action>', methods=['POST'])
def vote_artwork(artwork_id, action):
    if 'user_id' not in session:
        flash("Please log in to vote.", "warning")
        return redirect(url_for('login'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    user_id = session['user_id']
    
    # Check if the user has already voted on this artwork
    existing_vote = Vote.query.filter_by(user_id=user_id, artwork_id=artwork_id).first()
    if existing_vote:
        flash("You have already voted on this artwork.", "info")
        return redirect(request.referrer or url_for('home'))
    
    # Determine vote value based on the action parameter
    if action == "up":
        vote_value = 1
    elif action == "down":
        vote_value = -1
    else:
        flash("Invalid vote action.", "danger")
        return redirect(request.referrer or url_for('home'))
    
    new_vote = Vote(value=vote_value, user_id=user_id, artwork_id=artwork_id)
    db.session.add(new_vote)
    db.session.commit()
    
    flash("Your vote has been recorded.", "success")
    return redirect(request.referrer or url_for('home'))


@app.route('/gallery')
def gallery():
    location_filter = request.args.get('location')
    
    # Check if the user is logged in
    if 'user_id' not in session:
        # Public view: only show moderated, non-archived artworks that have a valid location
        query = Artwork.query.filter(
            Artwork.moderation_status == 'moderated',
            Artwork.archived == False,
            Artwork.location != 'none'
        )
    else:
        # Logged-in users (pixel artists and superusers) can see all moderated artworks regardless of location
        query = Artwork.query.filter(
            Artwork.moderation_status == 'moderated',
            Artwork.archived == False
        )
    
    # If a location filter is provided, further filter the artworks
    if location_filter:
        query = query.filter(Artwork.location == location_filter)
    
    artworks = query.all()
    return render_template('gallery.html', artworks=artworks, location_filter=location_filter)




@app.route('/archive_artwork/<int:artwork_id>', methods=['POST'])
def archive_artwork(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    current_user = User.query.get(session['user_id'])
    
    # Allow archiving if the user is the owner or a superuser
    if artwork.user_id != current_user.id and not current_user.is_superuser:
        flash("You are not authorized to archive this artwork.", "danger")
        return redirect(request.referrer or url_for('home'))
    
    artwork.archived = True
    artwork.archived_by = current_user.username  # Record the username
    artwork.archived_date = datetime.utcnow()     # Record the current date/time
    db.session.commit()
    flash("Artwork archived.", "success")
    return redirect(request.referrer or url_for('home'))

@app.route('/unarchive_artwork/<int:artwork_id>', methods=['POST'])
def unarchive_artwork(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    current_user = User.query.get(session['user_id'])
    
    # Allow unarchiving if the user is the owner or a superuser
    if artwork.user_id != current_user.id and not current_user.is_superuser:
        flash("You are not authorized to unarchive this artwork.", "danger")
        return redirect(request.referrer or url_for('home'))
    
    artwork.archived = False
    artwork.archived_by = None
    artwork.archived_date = None
    db.session.commit()
    flash("Artwork unarchived.", "success")
    return redirect(request.referrer or url_for('home'))



@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash("Please log in to access your profile.", "warning")
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found. Please log in again.", "warning")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Update personal details
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        age_value = request.form.get('age')
        try:
            user.age = int(age_value) if age_value else None
        except ValueError:
            user.age = None
        user.about = request.form.get('about')
        
        # Handle password change
        new_password = request.form.get('new_password')
        old_password = request.form.get('old_password')
        if new_password:
            if not old_password:
                flash("Please enter your old password to change your password.", "warning")
                return redirect(url_for('profile'))
            if not user.check_password(old_password):
                flash("Old password is incorrect.", "danger")
                return redirect(url_for('profile'))
            user.set_password(new_password)
        
        # Handle profile photo update
        if 'profile_photo' in request.files:
            photo = request.files['profile_photo']
            if photo and photo.filename != '':
                filename = secure_filename(photo.filename)
                try:
                    image = Image.open(photo)
                    # Resize image to 90x90 px
                    image = image.resize((90, 90))
                    photo_folder = os.path.join(app.root_path, 'static', 'profile_photos')
                    os.makedirs(photo_folder, exist_ok=True)
                    file_path = os.path.join(photo_folder, filename)
                    image.save(file_path, format='PNG')
                    user.profile_photo_url = url_for('static', filename='profile_photos/' + filename)
                except Exception as e:
                    flash("Error processing profile photo: " + str(e), "danger")
                    return redirect(url_for('profile'))
        
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)


@app.route('/reset_votes/<int:artwork_id>', methods=['POST'])
def reset_votes(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    
    current_user = User.query.get(session['user_id'])
    if not current_user or not current_user.is_superuser:
        flash("You are not authorized.", "danger")
        return redirect(url_for('home'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    if artwork.moderation_status != 'moderated':
        flash("Votes can only be reset for moderated artwork.", "danger")
        return redirect(url_for('moderate_artworks'))
    
    reason = request.form.get('reason')
    if not reason:
        flash("Please provide a reason for resetting votes.", "warning")
        return redirect(url_for('moderate_artworks'))
    
    # Reset votes: delete all votes for this artwork.
    Vote.query.filter_by(artwork_id=artwork.id).delete()
    
    # Log the vote reset event.
    new_log = VoteResetLog(artwork_id=artwork.id, reason=reason)
    db.session.add(new_log)
    db.session.commit()
    
    flash("Votes have been reset to zero.", "success")
    return redirect(url_for('moderate_artworks'))

@app.route('/reject_artwork/<int:artwork_id>', methods=['POST'])
def reject_artwork(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user.is_superuser:
        flash("You are not authorized to perform this action.", "danger")
        return redirect(url_for('home'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    
    # Only allow rejecting if artwork is currently pending
    if artwork.moderation_status != 'pending':
        flash("Only pending artworks can be rejected.", "warning")
        return redirect(url_for('moderate_artworks'))
    
    artwork.moderation_status = 'unmoderated'
    db.session.commit()
    flash("Artwork has been rejected.", "info")
    return redirect(url_for('moderate_artworks'))

@app.route('/assign_location/<int:artwork_id>', methods=['POST'])
def assign_location(artwork_id):
    if 'user_id' not in session:
        flash("Please log in.", "warning")
        return redirect(url_for('login'))
    
    current_user = User.query.get(session['user_id'])
    if not current_user or not current_user.is_superuser:
        flash("You are not authorized to assign locations.", "danger")
        return redirect(url_for('home'))
    
    artwork = Artwork.query.get_or_404(artwork_id)
    
    # Only allow location assignment for moderated artworks
    if artwork.moderation_status != 'moderated':
        flash("Location can only be assigned to moderated artworks.", "warning")
        return redirect(url_for('moderate_artworks'))
    
    new_location = request.form.get('location')
    if not new_location:
        flash("Please select a valid location.", "warning")
        return redirect(url_for('moderate_artworks'))
    
    artwork.location = new_location
    db.session.commit()
    flash("Location assigned successfully.", "success")
    return redirect(url_for('moderate_artworks'))


# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Create superuser if it doesn't exist
    if not User.query.filter_by(is_superuser=True).first():
        superuser = User(username="admin", email="admin@example.com")
        superuser.set_password("admin")
        superuser.is_superuser = True
        superuser.email_verified = True
        db.session.add(superuser)
        db.session.commit()
        print("Superuser created!")

if __name__ == '__main__':
    app.run(debug=True)
