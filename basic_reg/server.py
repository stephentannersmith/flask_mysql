from flask import Flask, render_template, request, redirect, flash, session
from mysqlconnection import connectToMySQL
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
strongRegex = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])(?=.{8,})")
app = Flask(__name__)
app.secret_key = "mysecretkeyissupersecret"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/process', methods=["POST"])
def process():
    
    is_valid = True
    if len(request.form['first_name']) < 1:
        is_valid = False
        flash("Please enter a first name.")
    if len(request.form['last_name']) < 1:
        is_valid = False
        flash("Please enter a last name.")
    if len(request.form['email']) < 2:
        is_valid = False
        flash("Email needs to be valid.")
    if not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        flash("Invalid email address!")
    if len(request.form["password"]) < 5:
        is_valid = False
        flash("Password must be at least 5 characters.")
    if not strongRegex.match(request.form['password']):
        flash("Password must contain at least one lowercase, one uppercase, one numeric, one special character, grandma's banana bread recipe, and a blood sacrifice.")
        is_valid = False
    if request.form["password"] != request.form["conf_password"]:
        is_valid = False
        flash("Passwords must match.")
    
    if is_valid:
        #let user register
        flash("You've successfully registered.")
        mysql = connectToMySQL("users_reg")
        data = {
            "fn": request.form["first_name"],
            "ln": request.form["last_name"],
            "em": request.form["email"],
            "pw": request.form["password"]
            }
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, %(pw)s, NOW(), NOW());"
        new_user = mysql.query_db(query,data) #pylint: disable=unused-variable

    return redirect('/')


if __name__  == "__main__":
    app.run(debug=True)