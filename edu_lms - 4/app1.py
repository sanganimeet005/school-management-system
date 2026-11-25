import os
from flask import Flask, render_template, request, redirect, url_for
import pymysql

app = Flask(__name__)

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
@app.route('/admin')
@app.route('/admin/dashboard')
def admin_dashboard():
    conn, cur = get_db()
    cur.execute("SELECT COUNT(*) AS total FROM tbl_reg")
    res_users = cur.fetchone()
    students_count = res_users['total'] if res_users else 0
    cur.execute("SELECT COUNT(*) AS total FROM tbl_course")
    res_courses = cur.fetchone()
    courses_count = res_courses['total'] if res_courses else 0
    return render_template('admin_dashboard.html', students_count=students_count, courses_count=courses_count)

@app.route('/admin/users')
def admin_users():
    return render_template('admin_users.html')

@app.route('/admin/courses')
def admin_courses():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_course")
    courses = cur.fetchall()
    return render_template('admin_courses.html', courses=courses)

@app.route('/add-course', methods=['GET', 'POST'])
def add_course():
    conn, cur = get_db()
    if request.method == 'POST':
        cat_name = request.form.get('Category')
        course_name = request.form.get('course_name')
        price = request.form.get('price') or 0
        description = request.form.get('description')
        file = request.files.get('course_img')
        filename = 'appdev.png'
        if file and file.filename:
            filename = file.filename
            upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'images')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))

        cur.execute("SELECT cat_id FROM tbl_category WHERE cat_name = %s", (cat_name,))
        cat_row = cur.fetchone()
        cat_id = cat_row['cat_id'] if cat_row else 1

        sql = "INSERT INTO tbl_course (cat_id, cat_name, course_name, price, image_path, course_img, description) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cur.execute(sql, (cat_id, cat_name, course_name, price, filename, filename, description))
        # also keep tbl_courses in sync
        cur.execute("INSERT INTO tbl_courses (course_id, cat_id, cat_name, course_name, price, image_path, course_img, description) VALUES (LAST_INSERT_ID(), %s, %s, %s, %s, %s, %s, %s)",
                    (cat_id, cat_name, course_name, price, filename, filename, description))
        conn.commit()

        return redirect(url_for('admin_courses'))

    return render_template('add_course.html')

@app.route('/delete_course/<int:course_id>')
def delete_course(course_id):
    conn, cur = get_db()
    cur.execute("DELETE FROM tbl_course WHERE course_id = %s", (course_id,))
    cur.execute("DELETE FROM tbl_courses WHERE course_id = %s", (course_id,))
    conn.commit()
    return redirect(url_for('admin_courses'))

@app.route('/manage_category')
def manage_category():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_category")
    categories = cur.fetchall()
    return render_template('manage_category.html', cat=categories)

@app.route('/delete_category/<int:cat_id>')
def delete_category(cat_id):
    conn, cur = get_db()
    # Delete courses belonging to this category so they don't remain as orphans
    cur.execute("DELETE FROM tbl_course WHERE cat_id = %s", (cat_id,))
    cur.execute("DELETE FROM tbl_courses WHERE cat_id = %s", (cat_id,))
    # Delete the category
    cur.execute("DELETE FROM tbl_category WHERE cat_id = %s", (cat_id,))
    conn.commit()
    return redirect(url_for('manage_category'))

@app.route('/manage_user')
def manage_user():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_reg")
    users = cur.fetchall()
    return render_template('manage_user.html', cat=users)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    conn, cur = get_db()
    cur.execute("DELETE FROM tbl_reg WHERE reg_id = %s", (user_id,))
    conn.commit()
    return redirect(url_for('manage_user'))

@app.route('/manage_contact')
def manage_contact():
    conn, cur = get_db()
    cur.execute("SELECT * FROM tbl_contact")
    contacts = cur.fetchall()
    return render_template('manage_contact.html', cat=contacts)

@app.route('/delete_contact/<int:contact_id>')
def delete_contact(contact_id):
    conn, cur = get_db()
    cur.execute("DELETE FROM tbl_contact WHERE contact_id = %s", (contact_id,))
    conn.commit()
    return redirect(url_for('manage_contact'))

@app.route('/admin/add-category', methods=['GET', 'POST'])
def add_category():
    conn, cur = get_db()
    if request.method == 'POST':
        cat_name = request.form.get('cat_name')
        if cat_name:
            sql = "INSERT INTO tbl_category (cat_name) VALUES (%s)"
            cur.execute(sql, (cat_name,))
            conn.commit()
            return redirect(url_for('add_category'))

    return render_template('add_category.html')

if __name__ == '__main__':
    app.run(port=5001, debug=True)
