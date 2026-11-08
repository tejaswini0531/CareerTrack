import os
import mysql.connector
from dotenv import load_dotenv
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from database import get_db_connection


# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing from the .env file")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Gmail SMTP configuration
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").strip().lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)


def send_verification_email(email, full_name):
    token = serializer.dumps(email, salt="email-verification")
    verification_url = url_for("verify_email", token=token, _external=True)

    message = Message(
        subject="Verify your CareerTrack account",
        recipients=[email],
        body=f"""Hello {full_name},

Thank you for registering with CareerTrack.

Please click the link below to verify your email address:

{verification_url}

This link will expire in 1 hour.

If you did not create this account, you can ignore this email.

Regards,
CareerTrack Team
"""
    )
    mail.send(message)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("home.html")


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        if not full_name or not email or not password:
            error = "All fields are required."

        elif len(password) < 8:
            error = "Password must contain at least 8 characters."

        else:

            hashed_password = generate_password_hash(password)

            connection = None
            cursor = None

            try:
                connection = get_db_connection()
                cursor = connection.cursor()

                query = """
                    INSERT INTO users (full_name, email, password, is_verified)
                    VALUES (%s, %s, %s, 0)
                """

                cursor.execute(
                    query,
                    (full_name, email, hashed_password)
                )

                connection.commit()

                try:
                    send_verification_email(email, full_name)
                    return render_template("verification_pending.html", email=email)
                except Exception as mail_error:
                    print("Email sending error:", mail_error)
                    error = (
                        "Your account was created, but the verification email "
                        "could not be sent. Please check the mail settings and "
                        "contact the administrator."
                    )

            except mysql.connector.IntegrityError:
                error = "This email is already registered."

            except mysql.connector.Error as e:
                error = "Database error. Please try again."
                print("Database error:", e)

            finally:
                if cursor:
                    cursor.close()

                if connection and connection.is_connected():
                    connection.close()

    return render_template("register.html", error=error)


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT *
                FROM users
                WHERE email = %s
            """

            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):

                if not user.get("is_verified"):
                    error = "Please verify your email address before logging in."
                    return render_template("login.html", error=error)

                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]

                return redirect(url_for("dashboard"))

            else:
                error = "Invalid email or password."

        except mysql.connector.Error as e:
            error = "Unable to connect to the database."
            print("Database error:", e)

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("login.html", error=error)


# --------------------------------------------------
# ADD APPLICATION
# --------------------------------------------------



# --------------------------------------------------
# EMAIL VERIFICATION
# --------------------------------------------------

@app.route("/verify-email/<token>")
def verify_email(token):
    try:
        email = serializer.loads(token, salt="email-verification", max_age=3600)
    except SignatureExpired:
        return render_template(
            "verification_result.html",
            message="This verification link has expired. Please contact support."
        )
    except BadSignature:
        return render_template(
            "verification_result.html",
            message="This verification link is invalid."
        )

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET is_verified = 1 WHERE email = %s",
            (email,)
        )
        connection.commit()

        if cursor.rowcount == 0:
            message = "We could not find an account for this verification link."
        else:
            message = "Your email has been verified successfully. You can now log in."

    except mysql.connector.Error as e:
        print("Email verification database error:", e)
        message = "Unable to verify your email right now. Please try again."

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return render_template("verification_result.html", message=message)




# --------------------------------------------------
# RESEND VERIFICATION EMAIL
# --------------------------------------------------

@app.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    message = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            message = "Please enter your email address."
        else:
            connection = None
            cursor = None

            try:
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)

                cursor.execute(
                    "SELECT full_name, is_verified FROM users WHERE email = %s",
                    (email,)
                )
                user = cursor.fetchone()

                # Use a general response so the page does not reveal
                # whether an email address is registered.
                if user and not user["is_verified"]:
                    send_verification_email(email, user["full_name"])

                message = (
                    "If this email belongs to an account that still needs "
                    "verification, a new verification link has been sent."
                )

            except Exception as e:
                print("Resend verification error:", e)
                message = "Unable to send the verification email right now. Please try again."

            finally:
                if cursor:
                    cursor.close()
                if connection and connection.is_connected():
                    connection.close()

    return render_template("resend_verification.html", message=message)


@app.route("/add-application", methods=["GET", "POST"])
def add_application():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        company_name = request.form["company_name"].strip()
        job_role = request.form["job_role"].strip()
        job_location = request.form.get("job_location")
        job_type = request.form.get("job_type")
        application_date = request.form.get("application_date") or None
        status = request.form.get("status") or "Applied"
        interview_date = request.form.get("interview_date") or None
        job_description = request.form.get("job_description")
        job_link = request.form.get("job_link")

        if interview_date:
            interview_date = interview_date.replace("T", " ")

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO applications
                (
                    user_id,
                    company_name,
                    job_role,
                    job_location,
                    job_type,
                    application_date,
                    status,
                    interview_date,
                    job_description,
                    job_link
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                session["user_id"],
                company_name,
                job_role,
                job_location,
                job_type,
                application_date,
                status,
                interview_date,
                job_description,
                job_link
            )

            cursor.execute(query, values)
            connection.commit()

            return redirect(url_for("dashboard"))

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

    return render_template("add_application.html")


# --------------------------------------------------
# EDIT APPLICATION
# --------------------------------------------------

@app.route("/edit-application/<int:application_id>", methods=["GET", "POST"])
def edit_application(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == "POST":

            company_name = request.form["company_name"].strip()
            job_role = request.form["job_role"].strip()
            job_location = request.form.get("job_location")
            job_type = request.form.get("job_type")
            application_date = request.form.get("application_date") or None
            status = request.form.get("status") or "Applied"
            interview_date = request.form.get("interview_date") or None
            job_description = request.form.get("job_description")
            job_link = request.form.get("job_link")

            if interview_date:
                interview_date = interview_date.replace("T", " ")

            query = """
                UPDATE applications
                SET
                    company_name = %s,
                    job_role = %s,
                    job_location = %s,
                    job_type = %s,
                    application_date = %s,
                    status = %s,
                    interview_date = %s,
                    job_description = %s,
                    job_link = %s
                WHERE application_id = %s
                AND user_id = %s
            """

            values = (
                company_name,
                job_role,
                job_location,
                job_type,
                application_date,
                status,
                interview_date,
                job_description,
                job_link,
                application_id,
                session["user_id"]
            )

            cursor.execute(query, values)
            connection.commit()

            return redirect(url_for("dashboard"))

        query = """
            SELECT *
            FROM applications
            WHERE application_id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (application_id, session["user_id"])
        )

        application = cursor.fetchone()

        if not application:
            return "Application not found.", 404

        return render_template(
            "edit_application.html",
            application=application
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# --------------------------------------------------
# DELETE APPLICATION
# --------------------------------------------------

@app.route("/delete-application/<int:application_id>", methods=["POST"])
def delete_application(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            DELETE FROM applications
            WHERE application_id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (application_id, session["user_id"])
        )

        connection.commit()

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Dashboard statistics
        query = """
            SELECT
                COUNT(*) AS total,

                COALESCE(
                    SUM(status = 'Interview'), 0
                ) AS interviews,

                COALESCE(
                    SUM(status = 'Selected'), 0
                ) AS offers,

                COALESCE(
                    SUM(status = 'Rejected'), 0
                ) AS rejected

            FROM applications
            WHERE user_id = %s
        """

        cursor.execute(query, (session["user_id"],))
        stats = cursor.fetchone()

        # Fetch all applications of the logged-in user
        query = """
            SELECT *
            FROM applications
            WHERE user_id = %s
            ORDER BY application_id DESC
        """

        cursor.execute(query, (session["user_id"],))
        applications = cursor.fetchall()

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return render_template(
        "dashboard.html",
        stats=stats,
        applications=applications
    )


# --------------------------------------------------
# ABOUT
# --------------------------------------------------

@app.route("/about")
def about():
    return render_template("about.html")



# --------------------------------------------------
# CONTACT
# --------------------------------------------------

@app.route("/contact", methods=["GET", "POST"])
def contact():

    error = None
    success = None

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not all([full_name, email, subject, message]):
            error = "Please fill in all fields."

        else:
            connection = None
            cursor = None

            try:
                connection = get_db_connection()
                cursor = connection.cursor()

                query = """
                    INSERT INTO contact_messages
                    (full_name, email, subject, message)
                    VALUES (%s, %s, %s, %s)
                """

                values = (full_name, email, subject, message)

                cursor.execute(query, values)
                connection.commit()

                success = "Thank you! Your message has been submitted successfully."

            except mysql.connector.Error as e:
                error = "Unable to submit your message. Please try again."
                print("Contact form database error:", e)

            finally:
                if cursor:
                    cursor.close()

                if connection and connection.is_connected():
                    connection.close()

    return render_template(
        "contact.html",
        error=error,
        success=success
    )




# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
