# VisionON! - Digital Art Gallery Platform

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.38-red.svg)](https://sqlalchemy.org/)

A comprehensive digital art gallery platform designed for pixel artists and art enthusiasts, featuring role-based access control, artwork moderation, and community voting systems.

## Features

### User Management

- **Dual User Classes**: Superusers and Pixel Artists with distinct permissions
- **Email Verification**: Secure account activation via Flask-Mail
- **Flexible Authentication**: Login with email or username
- **Password Management**: Secure password reset and change functionality
- **Profile Management**: Complete user profiles with photo uploads

### Artwork System

- **Pixel Art Upload**: Support for 64×64 pixel artworks (GIF, PNG, WEBP, JPEG)
- **Automatic Processing**: 32-bit RGBA conversion and format optimization
- **Moderation Workflow**: Complete approval system with status tracking
- **Location Assignment**: Display locations (DCSAtrium, MSB, Piazza)
- **Unique Identification**: QR codes and barcodes for each artwork
- **Voting System**: Community-driven upvote/downvote functionality

### Superuser Features

- **Artwork Moderation**: Approve, reject, and manage submissions
- **Location Management**: Assign display locations to approved artworks
- **Archive System**: Archive/unarchive artworks while preserving votes
- **Vote Management**: Reset votes with detailed logging and reasoning
- **Transaction Logging**: Comprehensive audit trail of all system activities

### Pixel Artist Features

- **Artwork Submission**: Upload and manage personal artwork collections
- **Moderation Requests**: Request review for artwork approval
- **Community Interaction**: Vote on other artists' works
- **Status Tracking**: Monitor moderation status and unique identifiers
- **Self-Management**: Archive personal artworks

### Public Access

- **Gallery Viewing**: Browse approved artworks by location
- **Location Filtering**: Filter by specific display areas
- **No Registration Required**: Public access to approved content

## Additional Features (Bonus Implementation)

### Enhanced User Experience

- **Email Verification System**: Complete email verification workflow
- **Profile Photo Upload**: 90×90px profile picture support
- **Transaction Logging**: Detailed logging of all significant events
- **Modern UI/UX**: Beautiful, responsive design with animations
- **Mobile Responsive**: Optimized for all device sizes
- **QR Code Generation**: Unique QR codes for each moderated artwork

## Technology Stack

- **Backend**: Python 3.9+, Flask 3.1.0
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **Email**: Flask-Mail integration
- **Image Processing**: Pillow (PIL)
- **QR Codes**: qrcode library
- **Security**: Werkzeug password hashing

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)

## Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Gh110ost007/Warwick-VisionON.git
   cd Warwick-VisionON
   ```

2. **Run the setup script**

   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. **Initialize the database**

   ```bash
   python create_db.py
   ```

4. **Start the application**

   ```bash
   ./flask-server.sh
   ```

5. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:5000`
   - Default superuser credentials: `admin` / `admin`

## Project Structure

```
Warwick-VisionON/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── config.py              # Configuration settings
├── extensions.py          # Flask extensions
├── create_db.py           # Database initialization
├── start.sh               # Setup script
├── clean.sh               # Cleanup script
├── requirements.txt       # Python dependencies
├── demo.mp4              # Demo video
├── static/               # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   ├── images/           # Image assets
│   ├── uploads/          # User uploads
│   ├── profile_photos/   # Profile pictures
│   └── qr_codes/         # Generated QR codes
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── index.html        # Home page
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── gallery.html      # Artwork gallery
    ├── profile.html      # User profile
    └── moderate_artworks.html # Moderation dashboard
```

## Demo Video

A comprehensive demo video (`demo.mp4`) is included showcasing:

- User registration and email verification
- Artwork upload and moderation workflow
- Voting system functionality
- Superuser moderation features
- Public gallery access
- All additional features

## Security Features

- **Password Hashing**: Secure password storage using Werkzeug
- **Email Verification**: Account activation via email links
- **Input Validation**: Comprehensive form validation
- **Session Management**: Secure user session handling
- **Access Control**: Role-based permission system

## Database Schema

### Core Tables

- **Users**: User accounts with role-based permissions
- **Artworks**: Artwork metadata and binary data
- **Votes**: User voting records
- **VoteResetLog**: Audit trail for vote resets
- **TransactionLog**: System activity logging


This is a coursework project for CS139 Web Application Development. While contributions are welcome, please note this is an academic project.

## Acknowledgments

- University of Warwick Computer Science Department
- Flask and SQLAlchemy communities
- All open-source libraries used in this project

---

**Note**: This project was developed as part of the CS139 Web Application Development module at the University of Warwick. The application demonstrates proficiency in web development technologies, database design, and user interface development.
