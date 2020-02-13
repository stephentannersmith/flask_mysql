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
    return render_template("login_reg.html")

@app.route('/success')
def tweet_landing():
    if 'user_id' not in session:
        return redirect('/')
    
    query = "SELECT * FROM users WHERE id_user = %(uid)s"
    data = {"uid": session["user_id"]}
    mysql = connectToMySQL("dojo_tweets")
    result = mysql.query_db(query, data)
    if result:
        query = "SELECT tweets.id_tweet, tweets.authors, tweets.content, users.first_name, users.last_name FROM users JOIN tweets ON users.id_user = tweets.authors;"
        mysql = connectToMySQL("dojo_tweets")
        tweets = mysql.query_db(query)

        return render_template('tweet_landing.html', user_data = result[0], tweets=tweets)
    else:
        return redirect('/')

@app.route('/on_tweet', methods=["POST"])
def on_tweet():
    valid = True 
    tweet_content = request.form.get('tweet_content')
    if len(tweet_content) < 1:
        valid = False
        flash("Tweets must be at least 1 character long.")

    if valid:
        query = "INSERT INTO tweets (content, authors, created_at, updated_at) VALUES (%(tweet)s, %(user_fk)s, NOW(), NOW());"
        data = {
            "tweet": tweet_content,
            "user_fk": session['user_id']
        }
        mysql = connectToMySQL("dojo_tweets")
        mysql.query_db(query, data)
    
    return redirect('/success')

@app.route("/on_delete/<tweet_id>")
def on_delete(tweet_id):
    if 'user_id' not in session:
        return redirect('/')
    query = "DELETE FROM tweets WHERE tweets.id_tweet = %(tweet_id)s"
    data = {'tweet_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect('/success')

@app.route("/edit/<tweet_id>")
def edit_form(tweet_id):
    query = "SELECT tweets.id_tweet, tweets.content FROM tweet WHERE tweets.id_tweet = %(tweet_id)s"
    data = {"tweet_id": tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    tweet = mysql.query_db(query, data)
    if tweet:
        return render_template("tweet_edit.html", tweet_data=tweet[0])
    return redirect("/success")

@app.route("/on_edit/<tweet_id>", methods=["POST"])
def on_edit(tweet_id):
    query = "UPDATE tweets SET tweets.content = %(tweet)s WHERE tweets.id_tweet = %(tweet_id)s "
    data = { "tweet": request.form.get("tweet_edit"), "tweet_id": tweet_id }
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

@app.route('/like/<tweet_id>')
def like_tweet(tweet_id):
    query = "INSERT INTO liked_tweets (user_id, tweet_id) VALUES (%(u_id)s, %(t_id)s)"
    data = {'u_id': session['user_id'], 't_id': tweet_id}
    mysql = connectToMySQL("dojo_tweets")
    mysql.query_db(query, data)

    return redirect("/success")

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

    # if not strongRegex.match(request.form['password']):
    #     flash("Password must contain at least one lowercase, one uppercase, one numeric, one special character, grandma's banana bread recipe, and a blood sacrifice.")
    #     valid = False

    if request.form["password"] != request.form["conf_password"]:
        valid = False
        flash("Passwords must match.")

    db = connectToMySQL('dojo_tweets')
    validate_email_query = 'SELECT email FROM users WHERE email=%(email)s;'
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
    
    db = connectToMySQL("dojo_tweets")
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
    db = connectToMySQL("dojo_tweets")
    query = "SELECT users.id_user, users.email, users.password FROM users WHERE email = %(le)s;"
    stored_user = {
        "le": request.form["lemail"]
    }
    selected_users = db.query_db(query,stored_user)
    is_correct_login = bcrypt.check_password_hash(selected_users[0]["password"], request.form["lpassword"])
    if len(selected_users) < 1:
        flash("Email must be at least 1 character long.")
        return redirect('/')
    if len(request.form["lpassword"]) < 1:
        flash("Password must be at least 1 character long.")
        return redirect('/')
    if not is_correct_login:
        flash("Password is incorrect")
        return redirect('/')
    elif is_correct_login:
        session['user_id'] = selected_users[0]["id_user"]
    return redirect('/success')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__  == "__main__":
    app.run(debug=True)