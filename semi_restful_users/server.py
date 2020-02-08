from flask import Flask, redirect, render_template, request
from mysqlconnection import connectToMySQL
app = Flask(__name__)

#renders template for web app
@app.route('/')
def index():
    return render_template("add_user.html")

#route that saves user info to DB            
@app.route('/add_user', methods=["POST"])
def add_user():
    query= "INSERT INTO users (first_name, last_name, email, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, NOW(), NOW());" 
    data = {
        "fn": request.form["first_name"],
        "ln": request.form["last_name"],
        "em": request.form["email"],
    }

    mysql = connectToMySQL("users")
    user_id = mysql.query_db(query,data) # pylint: disable=unused-variable
    return redirect('/users/{}'.format(user_id))

#this route displays stored user info and is redirected from the add_user route
@app.route("/users/<user_id>")
def view_user(user_id):
    query = "SELECT * FROM users WHERE id = %(id)s"
    data = {
        'id': user_id
    }
    mysql = connectToMySQL('users')
    user = mysql.query_db(query, data)
    print(user)
    return render_template("user_details.html", user=user[0])

#route deletes user from DB and redirects to all users
@app.route("/delete/<user_id>")
def delete_user(user_id):
    query = "DELETE FROM users WHERE id = %(id)s"
    data = {
        'id': user_id
    }
    mysql = connectToMySQL('users')
    user = mysql.query_db(query, data) # pylint: disable=unused-variable
    return redirect("/users")

#this route GETS the requested data and displays it on a new page with form
@app.route('/edit_user/<user_id>')
def edit_user(user_id):
    query = "SELECT * FROM users WHERE id = %(id)s"
    data = {
        'id': user_id
    }
    mysql = connectToMySQL('users')
    user = mysql.query_db(query,data)
    return render_template("edit_user.html", user=user[0])

#this updates user information and redirects back to view_user
@app.route('/update_user/<user_id>', methods=["POST"])
def update_user(user_id):
    query = "UPDATE users SET first_name=%(fn)s, last_name=%(ln)s, email=%(em)s, updated_at=NOW()"
    data = {
        "fn": request.form["first_name"],
        "ln": request.form["last_name"],
        "em": request.form["email"],
    }
    mysql = connectToMySQL('users')
    mysql.query_db(query,data)
    return redirect('/users/{}'.format(user_id))

#this route is used for selecting and logging console information for every page load and action
@app.route("/users")
def all_users():
    query = "SELECT * FROM users"
    mysql = connectToMySQL('users')
    all_users = mysql.query_db(query)
    print(all_users)
    return render_template("all_users.html", all_users=all_users)

if __name__ == "__main__":
    app.run(debug=True)