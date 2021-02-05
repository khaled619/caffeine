import os #interating with the operating system
from time import strftime,localtime # date
import pytz
import re #patterns
import secrets
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, Markup, get_flashed_messages
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from tempfile import mkdtemp #for current time
from datetime import datetime #for age
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, send_email

#make sure user is using corrent email and has access user's email
#from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import URLSafeTimedSerializer, SignatureExpired



from cs50 import SQL
#link to database
#db = SQL("sqlite:///finance.db")
#replaced:
db = SQL("sqlite:///coffee.db")
#db = SQL(os.getenv("DATABASE_URL"))
#ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Configure application
app = Flask(__name__)

csrf = CSRFProtect()
secret_key = os.environ.get('secret_key')
app.config['SECRET_KEY'] = secret_key
app.config['WTF_CSRF_SECRET_KEY'] = secret_key
csrf.init_app(app)

print("key:", secret_key)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
#global variables that will be used throughout
drinks = db.execute("SELECT Drink From caffeine")
contents = db.execute("SELECT * FROM caffeine")
#secret key

s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
@app.route('/')
def home():
    #always by get
    return render_template("main.html")
'''
@app.route('/about')
def about():
    return render_template("about.html")
'''

def calculateAge(DOB):
    if DOB == None or DOB == '':
        return None
    b_date = datetime.strptime(DOB, '%Y-%m-%d')
    date = ((datetime.today() - b_date).days/365)
    return date

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    #user trying to register for first time
    DOB = request.form.get("birthday")
    email = request.form.get("email")
    #form = EmailPasswordForm()
    if not DOB:
        flash('Must provide birthday', 'error')
        return render_template("register.html")
    age = calculateAge(DOB)
    if age < 4:
        flash('Must be at least 4 years old to register!', 'error')
        return render_template("register.html")
    if not request.form.get("username"):
        flash('Must provide username', 'error')
        return render_template("register.html")
    elif not email:
        flash('Must provide email', 'error')
        return render_template("register.html")
    elif not request.form.get("password"):
        flash('Must provide password', 'error')
        return render_template("register.html")

    elif not request.form.get("password") == request.form.get("confirmation"):
        flash('Passwords are not identical', 'error')
        return render_template("register.html")
    #elif len(request.form.get("password")) < 8 or re.search('[0-9]', request.form.get("password")) is None or re.search('[A-Z]', request.form.get("password")) is None:
    #    return apology("Password must be at least 8 characters and contain at least one number and and least uppercase character")
    #if user name is provided make sure it is unique
    elif request.form.get("username"):
    # Check database for username
        username_exists = db.execute("SELECT username FROM users WHERE username = :username", username = request.form.get("username"))
        email_exists = db.execute("SELECT email FROM users WHERE email = :email", email = request.form.get("email"))
        if username_exists:
            flash('Username already exists', 'error')
            return render_template("register.html")
        elif email_exists:
            flash('Email already exists', 'error')
            return render_template("register.html")
    #add to database user just registerd 
    rows = db.execute("INSERT INTO users (username,hash,email, age) VALUES(:username, :hash, :email, :age)", username = request.form.get("username"),
                hash = generate_password_hash(request.form.get("password")), email = request.form.get("email"), age = age)
    db.execute("INSERT INTO email_confirmation (user) VALUES (:user)", user = request.form.get("username"))
    username = request.form.get("username")
    sending_confirmation(username, email)
    #send email confirmation
    '''
    subject = "Confirm Your Email"
    token = s.dumps(email, salt='email-confirm-key')
    confirm_url = url_for('confirm_email', token=token, username=request.form.get("username"), _external=True)
    #html confirmation formatd
    html = render_template('activate.html', confirm_url=confirm_url)
    send_email(email, subject, html)
    '''
    #confirm_email(token, request.form.get("username"))
    # Redirect user to home page
    flash('You successfully registered! a confirmation link was sent to your email.')
    flash(Markup('if you have not recieved your confirmation link, you can request a new one by clicking <a href="/newConfirmationEmail" class="alert-link">here</a>'), 'primary')
    print("user number, ", rows)
    session["user_id"] = rows
    return redirect('/dashboard')

def sending_confirmation(username, email):
    subject = "Confirm Your Email"
    token = s.dumps(email, salt='email-confirm-key')
    confirm_url = url_for('confirm_email', token=token, username=username, _external=True)
    #html confirmation formatd
    html = render_template('activate.html', confirm_url=confirm_url)
    send_email(email, subject, html)
    #handle confirmation link 
@app.route('/confirm/<token>/<username>')
def confirm_email(token, username):
    print("im in confirm email")
    try:
        email = s.loads(token, salt="email-confirm-key", max_age = 3600)
    except SignatureExpired:
        flash("Your confirmation link was expired to request a new one, fill the following form", 'error')
        return redirect('/newConfirmationEmail')
    #confirm email, set database confirmation to true
    print("user name is: ", username)
    #once confirmed update if user has confriemd their email
    db.execute("UPDATE email_confirmation SET confirmed = :confirmed WHERE user = :user", confirmed = 'TRUE', user = username)
    flash('Email successfully confirmed!')
    return redirect("/")


@app.route('/newConfirmationEmail', methods=["GET", "POST"])
def new_email():        
    if request.method == "GET":
        return render_template("newEmail.html")
    to_send = request.form.get("newConfirmationEmail")
    if not to_send:
        flash("Must provide reset email!", "error")
        return redirect('/newConfirmationEmail')
    email_exists = db.execute("SELECT email FROM users where email = :email", email = to_send)
    if not email_exists:
        flash('Email does not exist!', 'error')
        return redirect('/newConfirmationEmail')
    #check if user is logged in if logged in use cookies to get their username
    '''
    if 'logged_in' in session:
        print("using sessions")
        username = session["user_id"]
        isConfirmed = db.execute("SELECT confirmed FROM email_confirmation where user = :user", userId)
    else:
    '''
    #else get username by asking the database. 
    print("using database")
    username = db.execute("SELECT username FROM users where email = :email", email = to_send)
    isConfirmed = db.execute("SELECT confirmed FROM email_confirmation where user = :username", username = username[0]['username'])
    if isConfirmed[0]['confirmed'] == 'TRUE':
        flash('Email Already Confirmed', 'primary')
        return redirect('/newConfirmationEmail')
    else:
        sending_confirmation(username, to_send)
        flash('Confirmation Link was sent to your email.')
        return redirect('/newConfirmationEmail')
@app.route('/forgot', methods=["GET", "POST"])
def forgot():
    if request.method == "GET":
        return render_template("forgot.html")
    #get email user registered with 
    reset_email = request.form.get("emailReset")
    if not reset_email:
        flash("Must provide reset email!", "error")
        return redirect('/forgot')
    email_exists = db.execute("SELECT email FROM users where email = :email", email = reset_email)
    if not email_exists:
        flash('Email does not exist!', 'error')
        return redirect('/forgot')
    #if not confirmed send confirmation link then reset password link
    #get username for that email
    user = db.execute("SELECT username FROM users where email = :email", email = reset_email)
    username = user[0]['username'] 
    #is confirmed returns TRUE or FALSE
    isConfirmed = db.execute("SELECT confirmed FROM email_confirmation where user = :user", user = user[0]['username'])
    if isConfirmed[0]['confirmed'] == 'TRUE':
        #check if email is confirmed, if confirmed send only link to reset password
        subject = 'Reset Your Password'
        token = s.dumps(reset_email, salt = 'reset-key')
        reset_url = url_for('confirmPasswordReset', token=token, username=username, _external= True)
        html = render_template('recover.html', reset_url = reset_url)
        send_email(reset_email, subject, html)
        flash('Password Reset Email Sent')
        return redirect("/forgot")
    flash('Email not confirmed', 'error')
    return redirect("/forgot")
    #if not confirmed send confirmation link then reset password link
@app.route('/reset_password/<token>/<username>', methods=["GET", "POST"])
def confirmPasswordReset(token, username):
    try:
        token = s.loads(token, salt = 'reset-key', max_age = 500)
    except SignatureExpired:
        return '<h1>The token is expired</h1>'
    #resetPassword()
    if request.method == "GET":
        return render_template("resetPass.html")
    new_password = request.form.get("new_password")
    new_pass_confirmation = request.form.get("new_password_confirmaton")
    if new_password != new_pass_confirmation:
        flash("Must be same password", 'error')
        return redirect('/resetPass')
    else:
        db.execute("UPDATE users SET hash = :hash WHERE username = :username", hash = generate_password_hash(new_password), username = username)
        flash("Password Reset Was Successful!")
        #get_flashed_messages()
        return redirect("/")
'''
@app.route('/reset_my_pass', methods=["GET", "POST"])
def resetPassword():
    if request.method == "GET":
        return render_template("resetPass.html")
    new_password = request.form.get("new_password")
    new_pass_confirmation = request.form.get("new_password_confirmaton")
    if new_password != new_pass_confirmation:
        flash("Must be same password", 'error')
        return redirect('/resetPass')
    else:
        print("new_password", new_password)
'''
#user already registerd
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        if not request.form.get("username"):
            flash('Must Provide Username', 'error')
            return render_template("login.html")
        elif not request.form.get("password"):
            flash('Must Provide Password', 'error')
            return render_template("login.html")
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password", 'error')
            return render_template("login.html")
        session["user_id"] = rows[0]["id"]
        return redirect("/dashboard")
    else:
        return render_template("login.html")

'''       
def get_reset_token(secret_, expires_sec = 1800):
    #expiration time is 30 seconds 
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id': session["user_id"]}).decode('utf-8')
def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return User.query.get(user_id)
'''

@app.route("/lookup", methods=["GET", "POST"])
def lookup():
    # if request method is just get, display lookup page
    #global drinks
    #drinks = db.execute("SELECT Drink From caffeine")
    if request.method == "GET":
        return render_template("lookup.html", drinks=drinks)
    if request.form['lookup_add'] == 'lookup_drink':
        #check if drink is in the database
        global drink_chosen
        drink_chosen = request.form.get("drink") #get drink user chose
        global caffeine
        caffeine = db.execute("SELECT Caffeine_mg, fl_oz, mg_floz  From caffeine WHERE Drink = :drink_chosen", drink_chosen=drink_chosen)

        isDrink = db.execute("SELECT Drink From caffeine WHERE Drink = :drink_chosen", drink_chosen = drink_chosen)
        if not isDrink:
            flash('Not found! please enter an item from the list', 'error')
            return render_template("lookup.html", drink_chosen=drink_chosen, caffeine=caffeine, drinks=drinks)
        return render_template("lookup.html", drink_chosen=drink_chosen, caffeine=caffeine, drinks=drinks)
    elif request.form['lookup_add'] == 'add_drink':
        #login_required
        if session.get("user_id"):
            user_id = session["user_id"]
            Intake = caffeine[0]['Caffeine_mg']
            db.execute("INSERT INTO history (user_id,date_added,Intake, Drink) VALUES (:user_id, :date_added, :Intake, :Drink )"
            , user_id = user_id, date_added = strftime("%Y-%m-%d %H:%M:%S", localtime()), Intake = caffeine[0]['Caffeine_mg'], Drink = drink_chosen)
            flash("Your drink was added!")
            return render_template("lookup.html", drink_chosen=drink_chosen, caffeine=caffeine, drinks=drinks, add=request.form['lookup_add'] == 'add_drink')
        return redirect("/login")

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    session.clear()
    return redirect("/")




@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    poundsToKilos = 2.205
    if request.method =="GET":
        firstname = db.execute("SELECT firstname FROM users WHERE id = :user_id", user_id = user_id)
        lastname = db.execute("SELECT lastname FROM users WHERE id = :user_id", user_id = user_id)
        weight = db.execute("SELECT weight FROM users WHERE id = :user_id", user_id = user_id)
        age = db.execute("SELECT age FROM users WHERE id = :user_id", user_id = user_id)
        return render_template("profile.html", firstname = firstname[0]['firstname'], weight = weight[0]['weight'], lastname= lastname[0]['lastname'], age = age[0]['age'])
    else:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        #check if user inputs kilos or pounds
        initialWeight = request.form.get("weight")
        if initialWeight:
            if initialWeight.isdigit() == False:
                flash("Weight must be a positive number!", "error")
                return redirect("/profile")
        DOB = request.form.get("birthday")
        if DOB:
             age = calculateAge(DOB)
             if age < 4:
                flash('Must be at least 4 years old!', 'error')
                return render_template("profile.html")
             db.execute("UPDATE users SET age = :age WHERE id = :user_id", user_id= user_id, age = age)
        unitSelected = request.form['customRadioInline1']
        weight = 0
        print("unit: ", unitSelected, "initial weight is : ", initialWeight)
        print("weight: ", weight)
        #convert to kilos if user selects pounds else keep in kilos
        if initialWeight:
            if unitSelected == 'pounds':
                weight = round((float(initialWeight) / poundsToKilos), 2)
            else:
                weight = initialWeight
        db.execute("Select weight from users WHERE id = :user_id", user_id = user_id)
        #print("Age : %d" % age)
        db.execute("UPDATE users SET firstname = :firstname, lastname= :lastname, weight = :weight WHERE id = :user_id", firstname = firstname,
                    lastname = lastname, user_id = user_id, weight = weight)
        flash('You successfully updated your profile!')
        return redirect('/dashboard')



@app.route("/add_caffeine", methods=["GET", "POST"])
@login_required
def add_caffeine():
    if request.method == "GET":
        return render_template("add_caffeine.html", contents=contents)
    else:
        #get user
        user_id = session["user_id"]
        #update intake in database
        #dispaly new intake if request.form['lookup_add'] == 'lookup_drink':
        if request.form['addDrink'] == 'add_drink':
            print("user clicked on database")
            drink_chosen = request.form.get("drink") #get drink user chose
            caffeine = db.execute("SELECT Caffeine_mg From caffeine WHERE Drink = :drink_chosen", drink_chosen=drink_chosen)
            Intake = caffeine[0]['Caffeine_mg']
            db.execute("INSERT INTO history (user_id,date_added,Intake, Drink) VALUES (:user_id, :date_added, :Intake, :Drink )"
            , user_id = user_id, date_added = strftime("%Y-%m-%d %H:%M:%S", localtime()), Intake = caffeine[0]['Caffeine_mg'], Drink = drink_chosen)
        elif request.form['addDrink'] == 'add_custom_intake':
            #get drink name, caffeine per mg
            #add it to history
            print("user clicked on custom")
            drink_created = request.form.get("drink_created")
            custom_intake = request.form.get("add_quantity") #get custom intake user chose
            print("drink_created" , drink_created)
            print("custom_intake" , custom_intake)
            if not drink_created:
                flash("Drink name must be specified", 'error')
                return render_template("add_caffeine.html")
            if not custom_intake:
                flash("Drink caffeine content must be specified", 'error')
                return render_template("add_caffeine.html")
            caffeine = custom_intake
            drink_chosen = drink_created
            db.execute("INSERT INTO history (user_id,date_added,Intake, Drink) VALUES (:user_id, :date_added, :Intake, :Drink )"
            , user_id = user_id, date_added = strftime("%Y-%m-%d %H:%M:%S", localtime()), Intake = custom_intake, Drink = drink_created.title())
            

            
        daily_intake = db.execute("SELECT Sum(Intake) as daily_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
        print("daily intake so far", daily_intake[0]['daily_intake'])
        #this gives sum of intake of all days, get this then divide by number of days of week
        weekly_average_intake = db.execute("SELECT Sum(Intake) as weekly_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now','localtime', '-6 days') AND datetime('now', 'localtime')", user_id = user_id)
        print("weekly average intake", weekly_average_intake[0]['weekly_intake'] / 7)
        #check for limit
        #display if under limit or above
        flash("Your drink was added!")
        return redirect ('/add_caffeine')
        #return render_template("add_caffeine.html", drink_chosen=drink_chosen, caffeine=caffeine, contents=contents, add=request.form['lookup_add'] == 'add_drink')
        #average intake per week
        #intake per day so far


@app.route("/remove_caffeine", methods=["GET", "POST"])
@login_required
def remove_caffeine():
    user_id = session['user_id']
    daily_intake = db.execute("SELECT Sum(Intake) as daily_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
    daily_history = db.execute("SELECT Drink, date_added, Intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now','localtime', 'start of day') AND datetime('now', 'localtime') ", user_id = user_id)
    caffeine_consumed = db.execute("SELECT Drink FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
    if request.method == "GET":
        print("Drink:", caffeine_consumed)
        #quantity_consumed = db.execute("SELECT Intake FROM history WHERE user_id = :user_id AND AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
        return render_template("remove_caffeine.html", caffeine_consumed= caffeine_consumed, daily_intake=daily_intake[0]['daily_intake'], daily_history=daily_history)
    else:
    #update table
    #drink user wants to remove
        Drink = request.form.get("Caffeine_drop_down")
        #get how many of that drink user wants to delete
        #quantity_to_remove = request.form.get("quantity")
        #quantity_owned = db.execute("SELECT Sum(quantity) as sum_drinks WHERE user_id = :user_id AND Drink = :Drink", user_id=user_id, Drink:Drink)
        #delete most recent record SELECT MAX(Date_added)FROM history WHERE user_id=9;
        db.execute("DELETE FROM history WHERE user_id = :user_id AND Drink = :Drink ORDER BY date_added DESC LIMIT 1 ", user_id = user_id, Drink = Drink )
        daily_intake = db.execute("SELECT Sum(Intake) as daily_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
        daily_history = db.execute("SELECT Drink, date_added, Intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now','localtime', 'start of day') AND datetime('now', 'localtime') ", user_id = user_id)
        caffeine_consumed = db.execute("SELECT Drink FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
        #send back new table
        return render_template("remove_caffeine.html", caffeine_consumed= caffeine_consumed, daily_intake=daily_intake[0]['daily_intake'], daily_history=daily_history)



@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    user_id = session["user_id"]
    username = db.execute("SELECT username FROM users WHERE id = :user_id", user_id = user_id)
    danger = False
    isWeight = False
    inPounds = None
    send_intake = True
    #age = True;
    safeLimit = 0
    safeAdultNumber = 6 #6mg/kg of caffeine seems safe for adults
    safeTeensNumber = 2.5  #2.5mg/kg of caffeine seems safe for teens
    weightValue = db.execute("Select weight from users WHERE id = :user_id", user_id = user_id)
    if weightValue[0]['weight']:
        isWeight = True
    #get caffeine intake for today and last week
    isIntake = db.execute("Select Intake FROM history where user_id =:user_id", user_id = user_id)
    #welcome user, show their stats
    firstname= db.execute("SELECT firstname FROM users WHERE id = :user_id", user_id = user_id)
    lastname= db.execute("SELECT lastname FROM users WHERE id = :user_id", user_id = user_id)
    get_age = db.execute("SELECT age FROM users WHERE id = :user_id", user_id = user_id)
    checkConfirmation = db.execute("SELECT confirmed FROM email_confirmation WHERE user = :user", user = username[0]['username'])
    isConfirmed = checkConfirmation[0]['confirmed']
    print("is confrimed? ", isConfirmed)
    print("AGE IS : ", get_age[0]['age'])
    if get_age[0]['age']:
        age_person=int(get_age[0]['age'])
        print("AGE IS : ", get_age[0]['age'])
    else:
        age_person = 0
        print("not age")
    weight_person = db.execute("SELECT weight FROM users WHERE id = :user_id", user_id = user_id)
    #show user both weight in kg and pound
    if weight_person[0]['weight']:
        inPounds = round((weight_person[0]['weight'] * 2.205), 2)
        isWeight = True
        #heerree
     
    daily_intake = db.execute("SELECT Sum(Intake) as daily_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')", user_id = user_id)
    print("intake: ", daily_intake[0]['daily_intake'])
    daily_history = db.execute("SELECT Drink, date_added, Intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now','localtime', 'start of day') AND datetime('now', 'localtime') ", user_id = user_id)
    #this gives sum of intake of all days, get this then divide by number of days of week
    weekly_average_sum = db.execute("SELECT Sum(Intake) as weekly_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now','localtime', '-6 days') AND datetime('now', 'localtime')", user_id = user_id)
    print("Weekly Average Sum is :", weekly_average_sum[0]['weekly_intake'])
    if weekly_average_sum[0]['weekly_intake']:
        weekly_average_intake = int(weekly_average_sum[0]['weekly_intake'] / 7)
    else:
        weekly_average_intake = 0
    weekly_history = db.execute("SELECT Drink, date_added, Intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now','localtime', '-6 days') AND datetime('now', 'localtime') ", user_id = user_id)
    if not daily_intake[0]['daily_intake'] or daily_intake[0]['daily_intake'] == None:
        send_intake = False
        print("Your daily intake is :", daily_intake[0]['daily_intake'])
    #if no intake at all do not do calculations
    #print("intake: ", daily_intake[0]['daily_intake'], "weight:", weightValue[0]['weight'])
    if isWeight is True and age_person > 0:
        print("I'm inside calcualtions.")
        #if adult multiply by safeAdultNumber
        if age_person >= 18:
            safeLimit = weightValue[0]['weight'] * safeAdultNumber
        #if teen multiple by safeTeensNumber
        elif age_person >= 13 and age_person < 18:
            safeLimit = weightValue[0]['weight'] * safeTeensNumber
        #Ages 4-6 No more than 45mg of caffeine per day
        elif age_person >= 4 and age_person < 7:
            safeLimit = 45
        #Ages 7-9 No more than 62.5mg of caffeine per day
        elif age_person >= 7 and age_person <= 9:
            safeLimit = 62.5
        #Ages 10-12 No more than 85mg of caffeine per day
        elif age_person >= 10 and age_person <= 12:
            safeLimit = 85
        if send_intake is True:
            if safeLimit < daily_intake[0]['daily_intake']:
                danger = True
            else:
                danger = False
    '''
    else:
        safeLimit = 'unknown'
        if not daily_intake[0]['daily_intake']:
            danger = False
        elif 400 < daily_intake[0]['daily_intake']:
h    '''
    #ability to remove caffeine

    #ability to add caffeine
    
    print("your weight is : ", weight_person[0]['weight'], "your weekly sum: ", weekly_average_intake, "your safe limit is:", safeLimit)
    
    if firstname[0]['firstname']:
        firstname = firstname[0]['firstname'].capitalize()
    else:
        firstname = firstname[0]['firstname']
    if lastname[0]['lastname']:
        lastname = lastname[0]['lastname'].capitalize()
    else:
        lastname = lastname[0]['lastname']
    
    if not isIntake:
        #not only send name but also their age and weight
        if firstname and lastname:
            return render_template("dashboard.html", firstname=firstname.capitalize(), lastname=lastname.capitalize(), age_person = age_person, weight_person= weight_person[0]['weight'], inPounds = inPounds, safeLimit = safeLimit,isConfirmed=isConfirmed)
        elif firstname:
            return render_template("dashboard.html", firstname=firstname.capitalize(), age_person = age_person, weight_person= weight_person[0]['weight'], inPounds = inPounds, safeLimit = safeLimit, isConfirmed=isConfirmed)
        elif lastname:
            return render_template("dashboard.html", lastname=lastname.capitalize(), age_person = age_person, weight_person= weight_person[0]['weight'], inPounds = inPounds, safeLimit = safeLimit, isConfirmed=isConfirmed)
        return render_template("dashboard.html", firstname=firstname, age_person = age_person, weight_person= weight_person[0]['weight'], inPounds = inPounds, safeLimit = safeLimit, isConfirmed=isConfirmed)
    return render_template("dashboard.html", daily_intake = daily_intake[0]['daily_intake'], weekly_average_intake = weekly_average_intake, daily_history = daily_history, weekly_history = weekly_history,
    firstname=firstname, danger=danger, safeLimit=safeLimit, weekly_average_sum=weekly_average_sum[0]['weekly_intake'], age_person = age_person, weight_person= weight_person[0]['weight'],
    inPounds = inPounds, lastname=lastname, send_intake = send_intake, isConfirmed=isConfirmed)

'''
@app.route("/list", methods=["GET", "POST"])
def caffeine_list():
    caffeine = db.execute("SELECT * FROM caffeine")
    return render_template("list.html", caffeine = caffeine)
'''

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)



