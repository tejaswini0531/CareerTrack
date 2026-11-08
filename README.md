CareerTrack – Job Application Tracking System

CareerTrack is a web-based job application tracking system developed using Python and Flask. It helps job seekers organize job applications, track application statuses, manage interview schedules, and monitor their job search progress in one place.

Features

User Registration & Login: Secure account creation and password hashing.

Email Verification: Verify user accounts through Gmail verification links.

Resend Verification: Request a new verification email.

Dashboard: View application statistics and job search progress.

Application Management: Add, edit, and delete job applications.

Status Tracking: Track Applied, Interview, Selected, and Rejected applications.

Search & Filters: Search applications by company or job role and filter by status and job type.

Contact Form: Submit questions, suggestions, and feedback.

Technologies Used

Category

Technologies

Backend

Python, Flask

Frontend

HTML, CSS, JavaScript

Database

MySQL

Email Service

Gmail SMTP, Flask-Mail

Security

Werkzeug Password Hashing, Session Management

Version Control

Git, GitHub

Project Structure

CareerTrack/
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│
├── templates/
│   ├── about.html
│   ├── add_application.html
│   ├── base.html
│   ├── contact.html
│   ├── dashboard.html
│   ├── edit_application.html
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── resend_verification.html
│   ├── verification_pending.html
│   └── verification_result.html
│
├── app.py
├── database.py
├── requirements.txt
├── .gitignore
└── README.md

Installation and Setup

1. Clone the Repository

git clone https://github.com/tejaswini0531/CareerTrack.git
cd CareerTrack

2. Create a Virtual Environment

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure MySQL Database

Install and start MySQL.

Create the database named careertrack_db.

Configure the required application tables and columns.

Update your database connection settings using environment variables.

5. Configure Environment Variables

Create a .env file in the project root and provide your own configuration values. Use the variable names expected by app.py and database.py.

Configure:

MySQL connection credentials

Flask secret key

Gmail SMTP server settings

Gmail app password

Important: Never upload your .env file, database passwords, Gmail app passwords, or secret keys to GitHub.

6. Run the Application

python app.py

Open your browser and visit:

http://127.0.0.1:5000

Security Features

Passwords are stored using secure password hashing.

Email verification is required before login.

Verification links have a limited validity period.

Sensitive configuration values are stored in environment variables.

.gitignore prevents environment files and virtual environments from being committed.

Future Enhancements

Job application reminders.

Resume management.

Advanced analytics and visual reports.

Deployment with a production-ready hosting environment.
