from flask import redirect, render_template, request, session
from functools import wraps #wraps for login decorarter
from flask_mail import Message
from email.message import EmailMessage
from email.mime.text import MIMEText
import smtplib
import os
EMAIL_ADDRESS = os.environ.get('DB_USER')
EMAIL_PASSWORD = os.environ.get('DB_PASS')
def error(message, code=400):
    def escape(s):
        for old, new in [("-", "--"), ("-", " "), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("error.html", top=code, bottom=escape(message)), code


def login_required(f):
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

