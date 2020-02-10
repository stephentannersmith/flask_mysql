from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
strongRegex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})")

app = Flask(__name__)
app.secret_key = "fSD;fkljsf;ldskfjSD:GLiwougerafvbcv872t3riwegDSklfJHD"
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect('/')
    
    return render_template('success.html')

@app.route('/users/create', methods=["POST"])
def process():
    
    valid = True
    if len(request.form['first_name']) < 1:
        valid = False
        flash("First name must be at least 2 characters long.")

    if len(request.form['last_name']) < 1:
        valid = False
        flash("Last name must be at least 2 characters long.")

    if len(request.form['email']) < 2:
        valid = False
        flash("Email needs to be valid.")

    if not EMAIL_REGEX.match(request.form['email']): # test whether a field matches the pattern
        flash("Invalid email address!")

    if len(request.form["password"]) < 8:
        valid = False
        flash("Password must be at least 8 characters.")

    if not strongRegex.match(request.form['password']):
        flash("Password must contain at least one lowercase, one uppercase, one numeric, one special character, grandma's banana bread recipe, and a blood sacrifice.")
        valid = False

    if request.form["password"] != request.form["conf_password"]:
        valid = False
        flash("Passwords must match.")

    db = connectToMySQL('users_reg')
    validate_email_query = 'SELECT id FROM users WHERE email=%(email)s;'
    form_data = {
        'email': request.form['email']
    }
    existing_users = db.query_db(validate_email_query, form_data)

    if existing_users:
        flash("Email already in use")
        valid = False

    if not valid:
        # redirect to the form page, don't create user
        flash("Something went wrong.")
        return redirect('/')

    pw_hash = bcrypt.generate_password_hash(request.form['password'])
    
    db = connectToMySQL("users_reg")
    create_query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(password_hash)s, NOW(), NOW());"
    create_data = {
        "fn": request.form["first_name"],
        "ln": request.form["last_name"],
        "em": request.form["email"],
        "password_hash": pw_hash
        }

    user_id = db.query_db(create_query, create_data)
    session['user_id'] = user_id
    return redirect('/success')


@app.route('/login', methods=["POST"])
def login():
    db = connectToMySQL("users_reg")
    query = "SELECT id, email, password FROM users WHERE email = %(le)s;"
    stored_user = {
        "le": request.form["lemail"]
    }
    selected_users = db.query_db(query,stored_user)
    print(selected_users)
    is_correct_login = bcrypt.check_password_hash(selected_users[0]["password"], request.form["lpassword"])
    print(is_correct_login)
    if len(selected_users) < 1:
        flash("Email is incorrect")
        return redirect('/')
    elif is_correct_login:
        session['user_id'] = selected_users[0]["id"]
        print(session)
        return redirect('/success')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__  == "__main__":
    app.run(debug=True)