import hashlib
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from hashlib import md5
from flaskext.mysql import MySQL
# from flask_sqlalchemy import SQLAlchemy
# from flask_admin import Admin
# from flask_admin.contrib.sqla import ModelView
# from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# admin = Admin(app, name='microblog', template_mode='bootstrap3')
# admin.add_view(ModelView(User, db.session))
# admin.add_view(ModelView(Post, db.session))
# Add administrative views here

# MySQL configurations
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'lib_mngt'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# db = SQLAlchemy(app)


"""
Sequence of functions:
---------------------

Category: Authentication & redirect
1. sign_up()
2. sign_in()
3. sign_out()
4. register_user()
5. login_check()

Category: Landing Page & user Profile
6. home()
7. my_profile()

Category: Business Logic
8. check_issued_books()
9. view_books()
10. issue_book()
11. return_a_book()
12. return_multiple_book()

Category: Admin Functions
13. admin_view()
14. add_books()
15. delete_user()
 
"""


# -----------Category: Authentication & redirect-----------
@app.route('/sign_up_form')
def sign_up():
    """
    :return:
    """
    if 'username' in session:
        user_name = session['username']
        return render_template('home.html', user_name=user_name)
    else:
        return render_template('student_registration.html')


@app.route('/sign_in')
def sign_in():
    """
    :return:
    """
    if 'username' in session:
        user_name = session['username']
        return render_template('home.html', user_name=user_name)
    else:
        return render_template('sign_in.html')


@app.route('/sign_out')
def sign_out():
    session.pop('username')
    session.pop('email')
    return redirect(url_for('home'))


@app.route('/register_user', methods=['POST'])
def register_user():
    """
    :return:
    """
    try:
        if 'username' in session:
            return render_template('home.html', user_name=session["username"])
        _name = request.form['username']
        _email = request.form['email']
        _password = request.form['password']

        # validate the received values
        if _name and _email and _password:
            conn = mysql.connect()
            cursor = conn.cursor()
            _hashed_password = hashlib.md5(_password.encode()).hexdigest()
            # cursor.execute("INSERT INTO 'user' (user_email, user_name, user_pass)
            #                    VALUES (%s, %s, %s)", (_email, _name, _hashed_password))
            cursor.callproc('sp_createUser', (_name, _email, _hashed_password))
            data = cursor.fetchall()
            session['username'] = _name
            session['email'] = _email
            if len(data) is 0:
                conn.commit()
                cursor.close()
                conn.close()
                return render_template('home.html', user_name=_name)
            else:
                return render_template('student_registration.html', error=str(data[0]))
        else:
            content = "<span>Enter the required fields</span>"
            return render_template('student_registration.html', content=content)

    except Exception as e:
        content = {
            'error': str(e)
        }
        return render_template('student_registration.html', content=content)


@app.route('/login_check', methods=['POST'])
def login_check():
    error = None
    if 'username' in session:
        return render_template('home.html', user_name=session["username"])
    if request.method == 'POST':
        username_form = request.form['username']
        password_form = request.form['password']
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM tbl_user WHERE user_email = %s;", [username_form])  # CHECKS IF USERNAME EXSIST
        if cursor.fetchone()[0]:
            cursor.execute("SELECT user_pass, user_name, user_email FROM tbl_user WHERE user_email = %s;", [username_form])  # FETCH THE HASHED PASSWORD
            for row in cursor.fetchall():
                if md5(password_form).hexdigest() == row[0]:
                    user_name = row[1]
                    session['username'] = user_name
                    session['email'] = row[2]
                    if row[2] == "admin@gmail.com":
                        session['user'] = "Admin"
                    cursor.close()
                    conn.close()
                    return render_template('home.html', user_name=user_name)
                else:
                    cursor.close()
                    conn.close()
                    error = "Invalid Credential"
        else:
            cursor.close()
            conn.close()
            error = "Invalid Credential"
    return render_template('sign_in.html', error=error)


# -----------Category: Landing Page & user Profile-----------
@app.route('/')
def home():
    """
    :return:
    """
    if 'username' in session:
        user_name = session['username']
        return render_template('home.html', user_name=user_name)
    else:
        return render_template('home.html')


@app.route('/my_profile')
def my_profile():
    """
    :return:
    """
    data = ""
    conn = mysql.connect()
    cursor = conn.cursor()
    if 'email' in session:
        email = session['email']
        cursor.execute("SELECT * FROM tbl_user WHERE user_email='" + email + "';")
        for row in cursor.fetchall():
            data = row
        return render_template('my_profile.html', data=data)
    else:
        return redirect(url_for('home'))


# -----------Category: Business Logic-----------
def check_issued_books(email):
    """
    just to return user related issued books
    :return:
    """
    issued_book_ids = []
    issued_books = []
    conn = mysql.connect()
    cursor = conn.cursor()
    if 'email' in session:
        cursor.execute("SELECT book_id_issued FROM tbl_user WHERE user_email='" + session['email'] + "';")
        for row in cursor.fetchall():
            issued_book_ids = row[0].split(';') if row[0] or len(row[0]) > 0 else []
            for i in issued_book_ids:
                issued_books.append(int(i) if i else None)

    return issued_books


@app.route('/view_books')
def view_books():
    """
    :return:
    """
    user_name = None
    issued_book_ids = []
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books;")
    books_obj = cursor.fetchall()
    if 'username' in session:
        user_name = session['username']
        issued_book_ids = check_issued_books(session['email'])

        # return jsonify({'books_obj': books_obj, 'user_name': user_name})
        return render_template('view_books.html', books_obj=books_obj,
                               user_name=user_name, issued_book_ids=issued_book_ids)
    else:
        return render_template('sign_in.html')


@app.route('/issue_book/<int:book_id>', methods=['GET', 'POST'])
def issue_book(book_id):
    """
    :param book_id:
    :return:
    """
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor2 = conn.cursor()
        if 'email' in session:
            email = session['email']
            cursor.execute("SELECT iduser, book_id_issued FROM tbl_user WHERE user_email='" + email + "';")
            rows = cursor.fetchall()
            for row in rows:
                if row[1]:
                    # assuming same book issuing won't be allowed from UI
                    updated_value = str(row[1]) + ";" + str(book_id)
                    cursor.execute("UPDATE tbl_user SET book_id_issued='%s' WHERE iduser=%d" % (updated_value, row[0]))
                else:
                    cursor.execute("UPDATE tbl_user SET book_id_issued="+str(book_id)+" WHERE user_email='"+email+"';")

            cursor2.execute("select total_available from books where id_books="+str(book_id)+";")
            for result in cursor2.fetchall():
                if int(result[0]) > 0:
                    available_books = int(result[0]) - 1
                    cursor2.execute("UPDATE books SET total_available=%d WHERE id_books=%d" % (available_books, book_id))

        conn.commit()
        cursor.close()
        cursor2.close()
        conn.close()

        # return jsonify({'available_books': available_books})
        return "DONE"
    except Exception as e:
        return "FULL"


@app.route('/return_book/<int:book_id>', methods=['POST'])
def return_a_book(book_id):
    """
    :return:
    """
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor2 = conn.cursor()
        if 'email' in session:
            email = session['email']
            cursor.execute("SELECT iduser, book_id_issued FROM tbl_user WHERE user_email='" + email + "';")
            rows = cursor.fetchall()
            for row in rows:
                if row[1]:
                    updated_value = row[1].split(';')
                    for i in updated_value:
                        updated_value.append(int(i) if i else "")
                    if book_id in updated_value:
                        del updated_value[book_id]
                        new_updated_values = ';'.join(updated_value)
                        cursor.execute(
                            "UPDATE tbl_user SET book_id_issued='%s' WHERE iduser=%d" % (new_updated_values, row[0]))

                    cursor2.execute("select total_available from books where id_books=" + str(book_id) + ";")
                    for result in cursor2.fetchall():
                        if result[0]:
                            available_books = int(result[0]) + 1
                            cursor2.execute(
                                "UPDATE books SET total_available=%d WHERE id_books=%d" % (available_books, book_id))

                else:
                    return "Book Not issued"

        conn.commit()
        cursor.close()
        cursor2.close()
        conn.close()

        return "DONE"
    except Exception as e:
        return "NOT ISSUED"


# @app.route('/return_multiple_book/<list:book_ids>', methods=['POST'])
@app.route('/return_multiple_book', methods=['POST'])
def return_multiple_book():
    """
    :return:
    """
    try:
        book_ids = []
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor2 = conn.cursor()
        if request.method == 'POST':
            # Assuming UI will send a string of book ids seperated by (,)
            book_ids_string = request.form['book_ids']
            book_ids_string = book_ids_string.split(',')
            for i in book_ids_string:
                book_ids.append(int(i))

            if 'email' in session:
                email = session['email']
                cursor.execute("SELECT iduser, book_id_issued FROM tbl_user WHERE user_email='" + email + "';")
                rows = cursor.fetchall()
                for row in rows:
                    if row[1]:
                        updated_value = row[1].split(';')
                        for i in updated_value:
                            updated_value.append(int(i) if i else "")
                        for book_id in book_ids:
                            if book_id in updated_value:
                                del updated_value[book_id]
                                new_updated_values = ';'.join(updated_value)
                                cursor.execute("UPDATE tbl_user SET book_id_issued='%s' WHERE iduser=%d" % (
                                new_updated_values, row[0]))

                            cursor2.execute("select total_available from books where id_books=" + str(book_id) + ";")
                            for result in cursor2.fetchall():
                                if result[0]:
                                    available_books = int(result[0]) + 1
                                    cursor2.execute("UPDATE books SET total_available=%d WHERE id_books=%d" % (
                                    available_books, book_id))

                    else:
                        return "Book Not issued"

        conn.commit()
        cursor.close()
        cursor2.close()
        conn.close()

        return "DONE"
    except Exception as e:
        return "NOT ISSUED"


# -----------Category: Admin Functions-----------
@app.route('/admin_view')
def admin_view():
    """
    :return:
    """
    if 'username' in session:
        email = session['email']
        if email == "admin@gmail.com":
            return render_template('admin_home.html')
    else:
        return redirect(url_for('home'))


@app.route('/admin/add_books', methods=['GET'])
def add_books():
    """
    :return:
    """
    # Assuming on admin login user variable added in session with value admin
    if 'user' in session:
        data = ""
        book_name = request.form['book_name']
        book_author = request.form['book_author']
        total_count = request.form['total_count']

        conn = mysql.connect()
        cursor = conn.cursor()
        if book_name and book_author and total_count:
            cursor.execute("INSERT INTO books (book_name, book_author, total_count, total_available) VALUES (%s, %s, %d)",
                           (book_name, book_author, total_count, total_count))
        conn.commit()
        cursor.close()
        conn.close()
        return render_template('admin_templates/admin_home.html')
    else:
        return redirect(url_for('home'))


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    """
    :return:
    """
    # Assuming on admin login user variable added in session with value admin
    if 'user' in session:
        data = ""
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tbl_user WHERE iduser=" + str(user_id) + ";")
        conn.commit()
        cursor.close()
        conn.close()
        return render_template('admin_templates/admin_home.html')
    else:
        return redirect(url_for('home'))


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    # session.init_app(app)
    app.debug = True
    app.run()


# """ Remove user by admin"""
# @app.route('/admin/users/remove_group/<int:groupId>', methods=['DELETE'])
# def removeGroup(groupId):
#     """
#     :param groupId:
#     :return:
#     """
#     try:
#         if userGroup.query.filter_by(group_id=groupId).first() is not None:
#             userGroup.query.filter_by(group_id=groupId).delete()
#             message='Group removed succesfully\n'
#         else:
#             message='Group not found\n'
#     except HTTPException as error:
#         return error(os.version)
#     return message
