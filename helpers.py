from flask import redirect, render_template, request, session
from functools import wraps #wraps for login decorarter
from flask_mail import Message
from email.message import EmailMessage
from email.mime.text import MIMEText
import smtplib
import os
EMAIL_ADDRESS = os.environ.get('DB_USER')
EMAIL_PASSWORD = os.environ.get('DB_PASS')
def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), ("-", " "), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def send_email(email, subject, html):
    my_email= MIMEText(html, "html")
    my_email['From'] = EMAIL_ADDRESS
    my_email['To'] = email
    my_email['Subject'] = subject
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        #idfentiy oursleves with the mail server
        smtp.ehlo()
        #encrypt traffic
        smtp.starttls()
        smtp.ehlo()
        #login to mail server
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_ADDRESS, email, my_email.as_string())

