from flask import Flask, render_template, redirect, url_for, flash
from flask_assets import Environment, Bundle
from flask import session
from flask_bcrypt import Bcrypt
from forms import RegistrationForm  # Adjusted import statement
import mysql.connector
from forms import LoginForm
from forms import ClassRegistrationForm
from datetime import datetime  # Import datetime module
from wtforms import SelectField, SubmitField, TextAreaField  # Added import for TextAreaField
from forms import RegistrationForm, LoginForm, ClassRegistrationForm, FeedbackForm, EditFeedbackForm
from flask import session, g
from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy


# Initialize the Flask app
app = Flask(__name__)

# Configure the SECRET_KEY
app.config['SECRET_KEY'] = b'\xe7t\xf6\x8d\xf4\xc4\x8f\x12\x95N\x94\x81\x94\xa2\xc5\xb9~C,\x1c9r\xe7S\x16\x8d\x91\x84\xd3\xa7\xb3'

# Initialize Flask Extensions
assets = Environment(app)
bcrypt = Bcrypt(app)

# Define asset bundles
css = Bundle('css/style.css', output='gen/packed.css')
assets.register('css_all', css)

def get_db_connection():
    return mysql.connector.connect(
        host='database1.cpe6w2mw6aei.us-east-1.rds.amazonaws.com', 
        database='gym', 
        user='admin', 
        password='12345678'
    )

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:12345678@database1.cpe6w2mw6aei.us-east-1.rds.amazonaws.com/gym'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/classes')
def classes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM OfferedClasses')
    classes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('classes.html', classes=classes)

@app.route('/diet-plan')
def diet_plan():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM DietPlan')
    plans = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('diet_plan.html', plans=plans)
#register route 

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        # Insert the new user into the Registration table
        try:
            cursor.execute("INSERT INTO Registration (Username, EmailAddress, DisplayName, Password) VALUES (%s, %s, %s, %s)",
                           (form.username.data, form.email.data, form.display_name.data, hashed_password))

            # Insert Username into the Account table
            cursor.execute("INSERT INTO Account (Registration_Username) VALUES (%s)", [form.username.data])

            conn.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            conn.rollback()  # Rollback in case of error
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html', title='Register', form=form)

#login route

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Registration WHERE Username = %s", (form.username.data,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['Password'], form.password.data):
            session['username'] = user['Username']
            flash('You have been logged in!', 'success')
            return redirect(url_for('index'))  
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html', title='Login', form=form)


# for logout

@app.route('/logout')
def logout():
    # Your existing logout logic here.
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# route for register


@app.route('/register-class', methods=['GET', 'POST'])
def register_class():
    if 'username' not in session:
        flash('Please login to register for classes.', 'danger')
        return redirect(url_for('login'))

    form = ClassRegistrationForm()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT class_id, class_name, class_days, class_timings FROM OfferedClasses")
    classes = cursor.fetchall()

    # Populate the dropdown with class names and corresponding class days and times
    class_choices = [(c['class_id'], f"{c['class_name']} - {c['class_days']} {c['class_timings']}") for c in classes]
    form.available_classes.choices = class_choices

    if form.validate_on_submit():
        selected_class_id = form.available_classes.data

        # Fetch the class name, timings, and days based on the selected class ID
        cursor.execute("SELECT class_name, class_timings, class_days FROM OfferedClasses WHERE class_id = %s", (selected_class_id,))
        class_info = cursor.fetchone()

        if class_info:
            class_name = class_info['class_name']
            class_timings = class_info['class_timings']
            class_days = class_info['class_days']
            username = session['username']
            
            # Before attempting to insert the new registration, check for duplicates
            query = """
                SELECT COUNT(*) as count
                FROM register_class
                WHERE Username = %s AND TypeOfClass = %s
            """
            cursor.execute(query, (username, class_name))
            result = cursor.fetchone()
            
            if result['count'] > 0:
                # If the count is greater than 0, the user is already registered for the class
                flash('You are already registered for this class.', 'info')
                return redirect(url_for('my_schedule'))

            # Proceed with registration if no duplicate is found
            try:
                cursor.execute("""
                    INSERT INTO register_class (TypeOfClass, ClassTime, Username, Day)
                    VALUES (%s, %s, %s, %s)
                """, (class_name, class_timings, username, class_days))
                conn.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('my_schedule'))
            except mysql.connector.Error as err:
                # Handle possible insertion errors
                flash(f'Error registering for class: {err}', 'danger')
        else:
            flash('Class not found.', 'danger')

    cursor.close()
    conn.close()
    return render_template('register_class.html', title='Register for Class', form=form)


### see schadule route for thst

@app.route('/my_schedule')
def my_schedule():
    if 'username' not in session:
        flash('Please log in to view your schedule.', 'danger')
        return redirect(url_for('login'))

    username = session['username']
    print(f"Username from session: {username}")  # Debug print

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT TypeOfClass, ClassTime, Day
        FROM register_class
        WHERE Username = %s
    """, (username,))
    schedule = cursor.fetchall()
    print(f"Schedule fetched: {schedule}")  # Debug print
    cursor.close()
    conn.close()

    return render_template('my_schedule.html', schedule=schedule)

# delete

@app.route('/delete-class/<type_of_class>', methods=['POST'])
def delete_class(type_of_class):
    if 'username' not in session:
        flash('Please log in to delete classes.', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use placeholders and tuple to prevent SQL injection
    query = "DELETE FROM register_class WHERE Username = %s AND TypeOfClass = %s"
    cursor.execute(query, (username, type_of_class))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Class deleted successfully!', 'success')
    return redirect(url_for('my_schedule'))

#feedback

from flask import redirect, url_for
@app.route('/give-feedback', methods=['GET', 'POST'])
def give_feedback():
    print("Session Username:", session.get('username'))  # Debug print to check if the username is in session

    if 'username' not in session:
        flash('Please log in to give feedback.', 'danger')
        return redirect(url_for('login'))
    
    form = FeedbackForm()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch classes for the dropdown and concatenate class name, day, and time
    cursor.execute("""
        SELECT class_id, 
               CONCAT(class_name, ' - ', class_days, ' at ', class_timings) AS class_info 
        FROM OfferedClasses
    """)
    classes = cursor.fetchall()
    form.class_id.choices = [(c['class_id'], c['class_info']) for c in classes]
    
    if form.validate_on_submit():
        class_id = form.class_id.data
        feedback = form.feedback.data
        username = session['username']
        
        # Fetch the class name based on the class_id
        cursor.execute("SELECT class_name FROM OfferedClasses WHERE class_id = %s", (class_id,))
        class_info = cursor.fetchone()
        if class_info:
            class_name = class_info['class_name']
            # Insert using class_name instead of class_id
            cursor.execute("""
                INSERT INTO ClassFeedback (ClassName, Username, FeedbackText) 
                VALUES (%s, %s, %s)
            """, (class_name, username, feedback))
            conn.commit()
            flash('Feedback submitted successfully!', 'success')
        else:
            flash('Class not found.', 'danger')
    
        # Make sure to close the cursor and connection within the if block
        cursor.close()
        conn.close()
        return redirect(url_for('view_feedback'))  # Redirect to view_feedback route
    
    # Close the cursor and connection if form is not submitted or if there's an error
    cursor.close()
    conn.close()
    
    return render_template('give_feedback.html', form=form)






# view feedback 

@app.route('/view-feedback', methods=['GET', 'POST'])
def view_feedback():
    if 'username' not in session:
        flash('Please log in to view your feedback.', 'danger')
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT FeedbackID, ClassName, FeedbackText, CreatedAt
        FROM ClassFeedback
        WHERE Username = %s
    """, (username,))
    feedback_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('view_feedback.html', feedback_list=feedback_list)


#Edit feedback 

@app.route('/edit-feedback/<int:feedback_id>', methods=['GET', 'POST'])
def edit_feedback(feedback_id):
    if 'username' not in session:
        flash('Please log in to edit feedback.', 'danger')
        return redirect(url_for('login'))
    
    form = EditFeedbackForm()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch the specific feedback entry
    cursor.execute("SELECT * FROM ClassFeedback WHERE FeedbackID = %s", (feedback_id,))
    feedback = cursor.fetchone()

    if feedback['Username'] != session['username']:
        flash('You can only edit your own feedback.', 'danger')
        return redirect(url_for('view_feedback'))
    
    if form.validate_on_submit():
        feedback_text = form.feedback.data
        
        # Update the specific feedback entry
        cursor.execute("UPDATE ClassFeedback SET FeedbackText = %s WHERE FeedbackID = %s",
                       (feedback_text, feedback_id))
        conn.commit()
        flash('Feedback updated successfully!', 'success')
        return redirect(url_for('view_feedback'))
    
    # Pre-populate form with existing feedback
    form.feedback.data = feedback['FeedbackText']
    
    cursor.close()
    conn.close()
    
    return render_template('edit_feedback.html', form=form)



# delete feedback 


@app.route('/delete-feedback/<int:feedback_id>', methods=['POST'])
def delete_feedback(feedback_id):
    if 'username' not in session:
        flash('Please log in to delete feedback.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch the specific feedback entry to confirm ownership
    cursor.execute("SELECT * FROM ClassFeedback WHERE FeedbackID = %s", (feedback_id,))
    feedback = cursor.fetchone()

    if feedback['Username'] != session['username']:
        flash('You can only delete your own feedback.', 'danger')
        return redirect(url_for('view_feedback'))
    
    # Delete the specific feedback entry
    cursor.execute("DELETE FROM ClassFeedback WHERE FeedbackID = %s", (feedback_id,))
    conn.commit()
    flash('Feedback deleted successfully!', 'success')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('view_feedback'))


# join Account and Registration 



@app.route('/my_profile')
def my_profile():
    if 'username' not in session:
        flash('Please log in to view your profile.', 'danger')
        return redirect(url_for('login'))
    
    username = session['username']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Ensure that the join condition uses the correct column names from both tables
    cursor.execute("""
        SELECT 
            a.MemberID, 
            r.Username, 
            r.EmailAddress, 
            r.DisplayName
        FROM 
            Account a
        JOIN 
            Registration r ON a.Registration_Username = r.Username
        WHERE 
            a.Registration_Username = %s;
    """, (username,))
    profile = cursor.fetchone()

    cursor.close()
    conn.close()

    if profile:
        return render_template('my_profile.html', profile=profile)
    else:
        flash('Profile not found.', 'danger')
        return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
