from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql

app = Flask(__name__)
app.secret_key = 'secret123'

connection = None
cursor = None

def get_db():
    global connection, cursor
    try:
        if connection is not None:
            connection.ping(reconnect=True)
        else:
            raise Exception("Init connection")
    except Exception:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="",          
            database="db_education",      
            port=3306,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = connection.cursor()
    return connection, cursor

@app.route('/')
def home():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_category")
    categories = cur.fetchall()
    return render_template('index.html', categories=categories)

@app.route('/categories')
def categories():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_category")
    categories = cur.fetchall()
    return render_template('categories.html', cat=categories)

@app.route('/category-courses')
@app.route('/category-courses/<int:cat_id>')
def category_courses(cat_id=None):
    conn, cur = get_db()
    if cat_id is None:
        cat_id = request.args.get('cat_id', type=int)

    selected_category = None
    if cat_id is not None:
        cur.execute("SELECT * FROM tbl_category WHERE cat_id = %s", (cat_id,))
        selected_category = cur.fetchone()
        cur.execute("SELECT * FROM tbl_course WHERE cat_id = %s", (cat_id,))
        courses = cur.fetchall()
    else:
        cur.execute("SELECT * FROM tbl_course")
        courses = cur.fetchall()

    return render_template('category_courses.html', courses=courses, selected_category=selected_category, cat_id=cat_id)

@app.route('/course-detail')
@app.route('/course-detail/<int:course_id>')
def course_detail(course_id=None):
    conn, cur = get_db()
    if course_id is None:
        course_id = request.args.get('course_id', type=int)

    cat_id = request.args.get('cat_id', type=int)
    course_type = request.args.get('type')

    course = None
    if course_id:
        cur.execute("SELECT * FROM tbl_course WHERE course_id = %s", (course_id,))
        course = cur.fetchone()
    elif cat_id:
        cur.execute("SELECT * FROM tbl_course WHERE cat_id = %s", (cat_id,))
        course = cur.fetchone()
    elif course_type:
        type_mapping = {
            'web_dev': 1,
            'app_dev': 2,
            'ai_ml': 3
        }
        mapped_id = type_mapping.get(course_type)
        if mapped_id:
            cur.execute("SELECT * FROM tbl_course WHERE course_id = %s", (mapped_id,))
            course = cur.fetchone()

    # If course is not found, redirect to categories with a friendly message
    if not course:
        flash("The requested course is not available or has been removed.", "warning")
        return redirect(url_for('categories'))

    return render_template('course_detail.html', course=course)

@app.route('/manage_category')
def manage_category():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_category")
    categories = cur.fetchall()
    return render_template('manage_category.html', cat=categories)

@app.route('/delete_category/<int:cat_id>')
def delete_category(cat_id):
    conn, cur = get_db()
    cur.execute("DELETE FROM tbl_course WHERE cat_id = %s", (cat_id,))
    cur.execute("DELETE FROM tbl_courses WHERE cat_id = %s", (cat_id,))
    cur.execute("DELETE FROM tbl_category WHERE cat_id = %s", (cat_id,))
    conn.commit()
    flash("Category and its associated courses deleted successfully!", "success")
    return redirect(url_for('manage_category'))

@app.route('/delete_course/<int:course_id>')
def delete_course(course_id):
    conn, cur = get_db()
    cur.execute("DELETE FROM tbl_course WHERE course_id = %s", (course_id,))
    cur.execute("DELETE FROM tbl_courses WHERE course_id = %s", (course_id,))
    conn.commit()
    flash("Course deleted successfully!", "success")
    return redirect(url_for('categories'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    conn, cur = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        sql = "INSERT INTO tbl_contact (contact_name, contact_email, contact_message) VALUES (%s, %s, %s)"
        cur.execute(sql, (name, email, message))
        conn.commit()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    conn, cur = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        cur.execute("SELECT * FROM tbl_reg WHERE reg_email = %s", (email,))
        user = cur.fetchone()

        if user:
            flash("Email is already registered!", "danger")
            return redirect(url_for('register'))

        sql = "INSERT INTO tbl_reg (reg_name, reg_email, reg_password) VALUES (%s, %s, %s)"
        cur.execute(sql, (name, email, password))
        conn.commit()

        flash("Registration successful!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn, cur = get_db()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        sql = "SELECT * FROM tbl_reg WHERE reg_email = %s AND reg_password = %s"
        cur.execute(sql, (email, password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user['reg_id']
            session['user_name'] = user['reg_name']
            session['user_email'] = user['reg_email']

            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid Email or Password!", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
