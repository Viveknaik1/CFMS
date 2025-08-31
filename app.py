import os
from datetime import date
from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'dbms', 'project', 'myapp', 'static')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config.from_object(Config)

db = SQLAlchemy(app)
mail = Mail(app)


class CustomUser(db.Model):
    __tablename__ = 'customuser'
    email = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # STUDENT/EXTERNAL/ORGANIZER/ADMIN


class Student(db.Model):
    __tablename__ = 'student'
    email = db.Column(db.String(100), db.ForeignKey('customuser.email', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), nullable=False, unique=True)


class ExternalParticipant(db.Model):
    __tablename__ = 'externalparticipant'
    email = db.Column(db.String(100), db.ForeignKey('customuser.email', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    college_name = db.Column(db.String(100), nullable=False)


class Organiser(db.Model):
    __tablename__ = 'organiser'
    email = db.Column(db.String(100), db.ForeignKey('customuser.email', ondelete='CASCADE'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, default=date.today)
    location = db.Column(db.String(200))


class EventRegistration(db.Model):
    __tablename__ = 'eventregistration'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    student_email = db.Column(db.String(100), db.ForeignKey('customuser.email', ondelete='CASCADE'), nullable=False)
    __table_args__ = (db.UniqueConstraint('event_id', 'student_email', name='uq_event_user'),)


class Hall(db.Model):
    __tablename__ = 'hall'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(200))
    vacancy = db.Column(db.Integer, default=50)
    price = db.Column(db.Integer, default=200)


class Accommodation(db.Model):
    __tablename__ = 'accommodation'
    id = db.Column(db.Integer, primary_key=True)
    participant_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), db.ForeignKey('externalparticipant.email', ondelete='CASCADE'), nullable=False)
    hall_id = db.Column(db.Integer, db.ForeignKey('hall.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.Date, default=date.today)
    price = db.Column(db.Integer)


@app.route('/')
def homepage():
    events = Event.query.order_by(Event.date).all()
    return render_template('homepage.html', events=events)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = CustomUser.query.get(email)
        if user and check_password_hash(user.password, password):
            session['user_email'] = user.email
            session['user_role'] = user.role
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')


@app.route('/logout/')
def logout_view():
    session.clear()
    return redirect(url_for('homepage'))


@app.route('/student_registration/', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email', '').strip().lower()
        roll_number = request.form.get('roll_number')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        if password != password1:
            return render_template('register_student.html', error='Passwords do not match')
        if CustomUser.query.get(email):
            return render_template('register_student.html', error='Email already exists')
        hashed = generate_password_hash(password)
        db.session.add(CustomUser(email=email, password=hashed, role='STUDENT'))
        db.session.add(Student(email=email, name=name, roll_number=roll_number))
        db.session.commit()
        send_email(email, 'Welcome to CFMS', 'You have registered as Student.')
        flash('Student registered successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_student.html', error='')


@app.route('/external_registration/', methods=['GET', 'POST'])
def external_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email', '').strip().lower()
        college_name = request.form.get('college_name')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        if password != password1:
            return render_template('register_external.html', error='Passwords do not match')
        if CustomUser.query.get(email):
            return render_template('register_external.html', error='Email already exists')
        hashed = generate_password_hash(password)
        db.session.add(CustomUser(email=email, password=hashed, role='EXTERNAL'))
        db.session.add(ExternalParticipant(email=email, name=name, college_name=college_name))
        db.session.commit()
        send_email(email, 'Welcome to CFMS', 'You have registered as External Participant.')
        flash('External participant registered successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_external.html', error='')


@app.route('/organiser_registration/', methods=['GET', 'POST'])
def organiser_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        password1 = request.form.get('password1')
        if password != password1:
            return render_template('register_organiser.html', error='Passwords do not match')
        if CustomUser.query.get(email):
            return render_template('register_organiser.html', error='Email already exists')
        hashed = generate_password_hash(password)
        db.session.add(CustomUser(email=email, password=hashed, role='ORGANIZER'))
        # organiser row auto-created by Postgres trigger (init.sql)
        db.session.commit()
        send_email(email, 'Welcome to CFMS', 'You have registered as Organizer.')
        flash('Organizer registered successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register_organiser.html', error='')


@app.route('/dashboard/')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    role = session.get('user_role')
    events = Event.query.order_by(Event.date).all()
    if role == 'STUDENT':
        return render_template('student.html', events=events)
    if role == 'EXTERNAL':
        return render_template('external.html', events=events)
    if role == 'ORGANIZER':
        return render_template('organiser.html', events=events)
    if role == 'ADMIN':
        return render_template('admin.html')
    return redirect(url_for('homepage'))


@app.route('/event/register/', methods=['POST'])
def event_registration():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    event_id = int(request.form.get('event_id'))
    email = session['user_email']
    exists = EventRegistration.query.filter_by(event_id=event_id, student_email=email).first()
    if not exists:
        db.session.add(EventRegistration(event_id=event_id, student_email=email))
        db.session.commit()
        send_email(email, 'Event Registration', 'Registered for event.')
        flash('Registered successfully for the event!', 'success')
    else:
        flash('Already registered for this event.', 'warning')
    return redirect(url_for('dashboard'))


@app.route('/accommodation/book/', methods=['POST'])
def book_accommodation():
    if session.get('user_role') != 'EXTERNAL':
        return redirect(url_for('login'))
    hall_id = int(request.form.get('hall_id'))
    email = session['user_email']
    hall = Hall.query.get(hall_id)
    if not hall or hall.vacancy <= 0:
        flash('No vacancy available', 'error')
        return redirect(url_for('dashboard'))
    ep = ExternalParticipant.query.get(email)
    db.session.add(Accommodation(participant_name=ep.name, email=email, hall_id=hall_id, price=hall.price))
    hall.vacancy -= 1
    db.session.commit()
    send_email(email, 'Accommodation Booked', f'Hall: {hall.name}')
    flash('Accommodation booked', 'success')
    return redirect(url_for('dashboard'))


def send_email(recipient, subject, body):
    try:
        if not app.config.get('MAIL_USERNAME'):
            print(f'[EMAIL-DEV] To: {recipient} | {subject} | {body}')
            return
        msg = Message(subject=subject, recipients=[recipient], body=body)
        mail.send(msg)
    except Exception as e:
        print('Email send failed:', e)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')), debug=True)
import os
import datetime
import sqlite3
import re
from flask import Flask, request, session, redirect, url_for, render_template, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # psycopg2 is optional
    psycopg2 = None
    RealDictCursor = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), 'dbms', 'project', 'myapp', 'static')
DATABASE = os.path.join(BASE_DIR, 'cfms.db')
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DATABASE}')
IS_POSTGRES = DATABASE_URL.startswith('postgres')

app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

class ParamCursor:
    """Cursor adapter that lets us keep '?' placeholders even on Postgres."""
    def __init__(self, real_cursor, is_postgres):
        self._cur = real_cursor
        self._is_pg = is_postgres

    def execute(self, query, params=None):
        if self._is_pg and query is not None:
            query = query.replace('?', '%s')
        return self._cur.execute(query, params or [])

    def executemany(self, query, seq_of_params):
        if self._is_pg and query is not None:
            query = query.replace('?', '%s')
        return self._cur.executemany(query, seq_of_params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def __getattr__(self, item):
        return getattr(self._cur, item)


class DbWrapper:
    def __init__(self, conn, is_postgres):
        self._conn = conn
        self._is_pg = is_postgres
        self.row_factory = sqlite3.Row if not is_postgres else None

    def cursor(self):
        if self._is_pg:
            return ParamCursor(self._conn.cursor(cursor_factory=RealDictCursor), True)
        cur = self._conn.cursor()
        return ParamCursor(cur, False)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    def executescript(self, script):
        if not self._is_pg:
            return self._conn.executescript(script)
        # Split on semicolons; execute non-empty statements
        statements = [s.strip() for s in script.split(';') if s.strip()]
        with self._conn.cursor() as c:
            for stmt in statements:
                c.execute(stmt)


def get_db():
    """Get database connection (SQLite default, optional Postgres via DATABASE_URL)."""
    if 'db' not in g:
        if IS_POSTGRES:
            if psycopg2 is None:
                raise RuntimeError('psycopg2-binary is required for PostgreSQL support')
            conn = psycopg2.connect(DATABASE_URL)
            g.db = DbWrapper(conn, True)
        else:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            g.db = DbWrapper(conn, False)
        g.is_postgres = IS_POSTGRES
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

def init_db():
    """Initialize database with tables and sample data"""
    db = get_db()

    # Create tables (differences for AUTOINCREMENT vs SERIAL)
    if IS_POSTGRES:
        schema = '''
        CREATE TABLE IF NOT EXISTS CustomUser (
            email VARCHAR(100) PRIMARY KEY,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Student (
            email VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(20) NOT NULL,
            password VARCHAR(100) NOT NULL,
            FOREIGN KEY (email) REFERENCES CustomUser (email) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ExternalParticipant (
            email VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            college_name VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            FOREIGN KEY (email) REFERENCES CustomUser (email) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Organiser (
            email VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            FOREIGN KEY (email) REFERENCES CustomUser (email) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Event (
            name VARCHAR(200) PRIMARY KEY,
            description TEXT,
            date DATE DEFAULT CURRENT_DATE,
            time TIME,
            location VARCHAR(200)
        );

        CREATE TABLE IF NOT EXISTS EventRegistration (
            event VARCHAR(200),
            student_email VARCHAR(100),
            FOREIGN KEY (event) REFERENCES Event (name) ON DELETE CASCADE,
            FOREIGN KEY (student_email) REFERENCES CustomUser (email) ON DELETE CASCADE,
            UNIQUE(event, student_email)
        );

        CREATE TABLE IF NOT EXISTS Hall (
            name VARCHAR(100) PRIMARY KEY,
            location VARCHAR(200),
            vacancy INTEGER DEFAULT 50,
            price INTEGER DEFAULT 200
        );

        CREATE TABLE IF NOT EXISTS Accomadation (
            id SERIAL PRIMARY KEY,
            name_par VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            name_hall VARCHAR(100) NOT NULL,
            price INTEGER,
            FOREIGN KEY (email) REFERENCES ExternalParticipant (email) ON DELETE CASCADE,
            FOREIGN KEY (name_hall) REFERENCES Hall (name) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Volunteer (
            event_name VARCHAR(100),
            student_name VARCHAR(100),
            student_email VARCHAR(100),
            FOREIGN KEY (event_name) REFERENCES Event (name) ON DELETE CASCADE,
            FOREIGN KEY (student_email) REFERENCES Student (email) ON DELETE CASCADE,
            PRIMARY KEY(event_name, student_email)
        );

        CREATE TABLE IF NOT EXISTS Event_has_organiser (
            event_name VARCHAR(100),
            org_name VARCHAR(100),
            org_email VARCHAR(100),
            FOREIGN KEY (event_name) REFERENCES Event (name) ON DELETE CASCADE,
            FOREIGN KEY (org_email) REFERENCES Organiser (email) ON DELETE CASCADE,
            PRIMARY KEY(event_name, org_email)
        );

        CREATE TABLE IF NOT EXISTS Winners (
            event VARCHAR(200) PRIMARY KEY,
            name_par VARCHAR(100),
            email VARCHAR(100)
        );
        '''
    else:
        schema = '''
        CREATE TABLE IF NOT EXISTS CustomUser (
            email VARCHAR(100) PRIMARY KEY,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Student (
            email VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(20) NOT NULL,
            password VARCHAR(100) NOT NULL,
            FOREIGN KEY (email) REFERENCES CustomUser (email) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ExternalParticipant (
            email VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            college_name VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            FOREIGN KEY (email) REFERENCES CustomUser (email) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Organiser (
            email VARCHAR(100) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            password VARCHAR(100) NOT NULL,
            FOREIGN KEY (email) REFERENCES CustomUser (email) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Event (
            name VARCHAR(200) PRIMARY KEY,
            description TEXT,
            date DATE DEFAULT CURRENT_DATE,
            time TIME,
            location VARCHAR(200)
        );

        CREATE TABLE IF NOT EXISTS EventRegistration (
            event VARCHAR(200),
            student_email VARCHAR(100),
            FOREIGN KEY (event) REFERENCES Event (name) ON DELETE CASCADE,
            FOREIGN KEY (student_email) REFERENCES CustomUser (email) ON DELETE CASCADE,
            UNIQUE(event, student_email)
        );

        CREATE TABLE IF NOT EXISTS Hall (
            name VARCHAR(100) PRIMARY KEY,
            location VARCHAR(200),
            vacancy INTEGER DEFAULT 50,
            price INTEGER DEFAULT 200
        );

        CREATE TABLE IF NOT EXISTS Accomadation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_par VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            name_hall VARCHAR(100) NOT NULL,
            price INTEGER,
            FOREIGN KEY (email) REFERENCES ExternalParticipant (email) ON DELETE CASCADE,
            FOREIGN KEY (name_hall) REFERENCES Hall (name) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS Volunteer (
            event_name VARCHAR(100),
            student_name VARCHAR(100),
            student_email VARCHAR(100),
            FOREIGN KEY (event_name) REFERENCES Event (name) ON DELETE CASCADE,
            FOREIGN KEY (student_email) REFERENCES Student (email) ON DELETE CASCADE,
            PRIMARY KEY(event_name, student_email)
        );

        CREATE TABLE IF NOT EXISTS Event_has_organiser (
            event_name VARCHAR(100),
            org_name VARCHAR(100),
            org_email VARCHAR(100),
            FOREIGN KEY (event_name) REFERENCES Event (name) ON DELETE CASCADE,
            FOREIGN KEY (org_email) REFERENCES Organiser (email) ON DELETE CASCADE,
            PRIMARY KEY(event_name, org_email)
        );

        CREATE TABLE IF NOT EXISTS Winners (
            event VARCHAR(200) PRIMARY KEY,
            name_par VARCHAR(100),
            email VARCHAR(100)
        );
        '''

    db.executescript(schema)
    
    # Insert sample data if tables are empty
    cursor = db.cursor()
    
    # Check if Hall table is empty and insert sample data
    cursor.execute("SELECT COUNT(*) FROM Hall")
    if cursor.fetchone()[0] == 0:
        halls_data = [
            ("LBS HALL", "Old Hijili", 50, 200),
            ("MT HALL", "Main Building", 50, 200),
            ("SNVH HALL", "Pepsi Cut", 50, 200),
            ("VS HALL", "Jhan Ghosh", 50, 200),
            ("JCB HALL", "Gymkhana", 50, 200)
        ]
        cursor.executemany("INSERT INTO Hall (name, location, vacancy, price) VALUES (?, ?, ?, ?)", halls_data)
    
    # Check if Event table is empty and insert sample data
    cursor.execute("SELECT COUNT(*) FROM Event")
    if cursor.fetchone()[0] == 0:
        events_data = [
            ("Battle of Bands", "Music competition between college bands", "2024-03-15", "18:00", "Main Auditorium"),
            ("Dance Competition", "Inter-college dance competition", "2024-03-16", "19:00", "Open Air Theatre"),
            ("Coding Contest", "Programming competition", "2024-03-17", "10:00", "Computer Lab"),
            ("Art Exhibition", "Student art showcase", "2024-03-18", "14:00", "Art Gallery"),
            ("Sports Meet", "Annual sports competition", "2024-03-19", "08:00", "Sports Ground")
        ]
        cursor.executemany("INSERT INTO Event (name, description, date, time, location) VALUES (?, ?, ?, ?, ?)", events_data)
    
    db.commit()

@app.route('/')
def homepage():
    """Homepage route"""
    init_db()
    return render_template('homepage.html')

@app.route('/login/', methods=['GET', 'POST'])
def login():
    """Login route for all user types"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT email, password, role FROM CustomUser WHERE email = ?", (email,))
        user_row = cursor.fetchone()
        
        if user_row and user_row['password'] == password:
            session['user_email'] = email
            session['user_role'] = user_row['role']
            
            if user_row['role'] == 'STUDENT':
                return redirect(url_for('student_dashboard'))
            elif user_row['role'] == 'EXTERNAL':
                return redirect(url_for('external_dashboard'))
            elif user_row['role'] == 'ORGANIZER':
                return redirect(url_for('organizer_dashboard'))
            elif user_row['role'] == 'ADMIN':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password', 'error')
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/student_registration/', methods=['GET', 'POST'])
def student_registration():
    """Student registration route"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        roll_number = request.form.get('roll_number')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        
        if password != password1:
            return render_template('register_student.html', error='Passwords do not match')
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Insert into CustomUser first
            cursor.execute("INSERT INTO CustomUser (email, password, role) VALUES (?, ?, ?)", 
                         (email, password, 'STUDENT'))
            
            # Insert into Student table
            cursor.execute("INSERT INTO Student (name, email, roll_number, password) VALUES (?, ?, ?, ?)", 
                         (name, email, roll_number, password))
            
            db.commit()
            flash('Student registered successfully! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            db.rollback()
            return render_template('register_student.html', error='Email already exists. Please use a different email.')
    
    return render_template('register_student.html', error='')

@app.route('/external_registration/', methods=['GET', 'POST'])
def external_registration():
    """External participant registration route"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        college_name = request.form.get('college_name')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        
        if password != password1:
            return render_template('register_external.html', error='Passwords do not match')
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Insert into CustomUser first
            cursor.execute("INSERT INTO CustomUser (email, password, role) VALUES (?, ?, ?)", 
                         (email, password, 'EXTERNAL'))
            
            # Insert into ExternalParticipant table
            cursor.execute("INSERT INTO ExternalParticipant (name, email, college_name, password) VALUES (?, ?, ?, ?)", 
                         (name, email, college_name, password))
            
            db.commit()
            flash('External participant registered successfully! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            db.rollback()
            return render_template('register_external.html', error='Email already exists. Please use a different email.')
    
    return render_template('register_external.html', error='')

@app.route('/organiser_registration/', methods=['GET', 'POST'])
def organiser_registration():
    """Organizer registration route"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        
        if password != password1:
            return render_template('register_organiser.html', error='Passwords do not match')
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Insert into CustomUser first
            cursor.execute("INSERT INTO CustomUser (email, password, role) VALUES (?, ?, ?)", 
                         (email, password, 'ORGANIZER'))
            
            # Insert into Organiser table
            cursor.execute("INSERT INTO Organiser (name, email, password) VALUES (?, ?, ?)", 
                         (name, email, password))
            
            db.commit()
            flash('Organizer registered successfully! Please login.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            db.rollback()
            return render_template('register_organiser.html', error='Email already exists. Please use a different email.')
    
    return render_template('register_organiser.html', error='')

@app.route('/student/')
def student_dashboard():
    """Student dashboard route"""
    if 'user_email' not in session or session['user_role'] != 'STUDENT':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Event")
    events = cursor.fetchall()
    
    return render_template('student.html', events=events)

@app.route('/external/')
def external_dashboard():
    """External participant dashboard route"""
    if 'user_email' not in session or session['user_role'] != 'EXTERNAL':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Event")
    events = cursor.fetchall()
    
    return render_template('external.html', events=events)

@app.route('/organizer/')
def organizer_dashboard():
    """Organizer dashboard route"""
    if 'user_email' not in session or session['user_role'] != 'ORGANIZER':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Event")
    events = cursor.fetchall()
    
    return render_template('organiser.html', events=events)

@app.route('/admin_url/')
def admin_dashboard():
    """Admin dashboard route"""
    if 'user_email' not in session or session['user_role'] != 'ADMIN':
        return redirect(url_for('login'))
    
    return render_template('admin.html')

@app.route('/admin_event_dashboard/')
def admin_event_dashboard():
    """Admin event dashboard route"""
    if 'user_email' not in session or session['user_role'] != 'ADMIN':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Event")
    events = cursor.fetchall()
    
    return render_template('admin_event.html', events=events)

@app.route('/event_registration/', methods=['POST'])
def event_registration():
    """Event registration for students"""
    if 'user_email' not in session or session['user_role'] != 'STUDENT':
        return redirect(url_for('login'))
    
    event_name = request.form.get('event')
    student_email = session['user_email']
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if already registered
    cursor.execute("SELECT * FROM EventRegistration WHERE student_email = ? AND event = ?", 
                  (student_email, event_name))
    
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO EventRegistration (event, student_email) VALUES (?, ?)", 
                      (event_name, student_email))
        db.commit()
        flash('Registered successfully for the event!', 'success')
    else:
        flash('Already registered for this event.', 'warning')
    
    return redirect(url_for('student_dashboard'))

@app.route('/event_ext_registration/', methods=['POST'])
def event_ext_registration():
    """Event registration for external participants"""
    if 'user_email' not in session or session['user_role'] != 'EXTERNAL':
        return redirect(url_for('login'))
    
    event_name = request.form.get('event')
    student_email = session['user_email']
    
    db = get_db()
    cursor = db.cursor()
    
    # Check if already registered
    cursor.execute("SELECT * FROM EventRegistration WHERE student_email = ? AND event = ?", 
                  (student_email, event_name))
    
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO EventRegistration (event, student_email) VALUES (?, ?)", 
                      (event_name, student_email))
        db.commit()
        flash('Registered successfully for the event!', 'success')
    else:
        flash('Already registered for this event.', 'warning')
    
    return redirect(url_for('external_dashboard'))

@app.route('/accomadation_portal/')
def accomadation_portal():
    """Accommodation portal for external participants"""
    if 'user_email' not in session or session['user_role'] != 'EXTERNAL':
        return redirect(url_for('login'))
    
    ep_mail = session['user_email']
    db = get_db()
    cursor = db.cursor()
    
    # Get booked accommodation details
    cursor.execute("SELECT name_par, email, date, name_hall, price FROM Accomadation WHERE email = ?", (ep_mail,))
    booked_accommodation = cursor.fetchone()
    
    booked_accommodation_details = None
    if booked_accommodation:
        booked_accommodation_details = {
            'name_par': booked_accommodation['name_par'],
            'email': booked_accommodation['email'],
            'date': booked_accommodation['date'],
            'name_hall': booked_accommodation['name_hall'],
            'price': booked_accommodation['price']
        }
    
    return render_template('accomodation.html', booked_accommodation=booked_accommodation_details)

@app.route('/hall_portal/')
def hall_portal():
    """Hall portal showing available halls"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM Hall")
    halls = cursor.fetchall()
    
    return render_template('bookedhalls.html', halls=halls)

@app.route('/volunteer_registration/', methods=['POST'])
def volunteer_registration():
    """Volunteer registration for students"""
    if 'user_email' not in session or session['user_role'] != 'STUDENT':
        return redirect(url_for('login'))
    
    student_email = session['user_email']
    event_name = request.form.get('event')
    
    db = get_db()
    cursor = db.cursor()
    
    # Get student name
    cursor.execute("SELECT name FROM Student WHERE email = ?", (student_email,))
    student_name = cursor.fetchone()['name']
    
    # Check if already volunteered
    cursor.execute("SELECT * FROM Volunteer WHERE student_email = ? AND event_name = ?", 
                  (student_email, event_name))
    
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO Volunteer (event_name, student_name, student_email) VALUES (?, ?, ?)", 
                      (event_name, student_name, student_email))
        db.commit()
        flash(f'Successfully volunteered for {event_name}!', 'success')
    else:
        flash('Already volunteered for this event.', 'warning')
    
    return redirect(url_for('student_dashboard'))

@app.route('/mybooking_portal/', methods=['POST'])
def mybooking_portal():
    """Booking accommodation for external participants"""
    if 'user_email' not in session or session['user_role'] != 'EXTERNAL':
        return redirect(url_for('login'))
    
    name_hall = request.form.get('name_hall')
    ep_mail = session['user_email']
    
    db = get_db()
    cursor = db.cursor()
    
    # Check vacancy
    cursor.execute("SELECT vacancy FROM Hall WHERE name = ?", (name_hall,))
    row = cursor.fetchone()
    
    if row is None:
        return 'Hall not found', 400
    
    # Check if already has accommodation
    cursor.execute("SELECT * FROM Accomadation WHERE email = ?", (ep_mail,))
    if cursor.fetchall():
        return 'More than one booking not allowed', 400
    
    vac = row['vacancy']
    if vac > 0:
        # Get external participant info
        cursor.execute("SELECT name, email FROM ExternalParticipant WHERE email = ?", (ep_mail,))
        ep_info = cursor.fetchone()
        
        # Get hall info
        cursor.execute("SELECT name, price FROM Hall WHERE name = ?", (name_hall,))
        hall_info = cursor.fetchone()
        
        current_date = datetime.date.today()
        
        # Insert accommodation booking
        cursor.execute("""INSERT INTO Accomadation (name_par, email, date, name_hall, price) 
                         VALUES (?, ?, ?, ?, ?)""", 
                      (ep_info['name'], ep_info['email'], current_date, hall_info['name'], hall_info['price']))
        
        # Update vacancy
        cursor.execute("UPDATE Hall SET vacancy = ? WHERE name = ?", (vac - 1, name_hall))
        
        db.commit()
        return render_template('payment.html')
    
    return 'No vacancies available', 400

@app.route('/logout/')
def logout_view():
    """Logout route"""
    session.clear()
    return redirect(url_for('homepage'))

@app.route('/event_details/', methods=['GET', 'POST'])
def event_details():
    """Event details route"""
    org_name = None
    participants = []
    volunteers = []
    
    if request.method == 'POST':
        event_name = request.form.get('event')
        db = get_db()
        cursor = db.cursor()
        
        # Get participants
        cursor.execute("""
            SELECT DISTINCT cu.email, s.name 
            FROM CustomUser cu 
            INNER JOIN EventRegistration er ON cu.email = er.student_email 
            INNER JOIN Student s ON s.email = er.student_email 
            WHERE er.event = ?
        """, (event_name,))
        participants = cursor.fetchall()
        
        # Get volunteers
        cursor.execute("""
            SELECT DISTINCT cu.email, s.name 
            FROM CustomUser cu 
            INNER JOIN Volunteer v ON cu.email = v.student_email 
            INNER JOIN Student s ON s.email = v.student_email 
            WHERE v.event_name = ?
        """, (event_name,))
        volunteers = cursor.fetchall()
        
        # Get organizer
        cursor.execute("SELECT org_name FROM Event_has_organiser WHERE event_name = ?", (event_name,))
        row = cursor.fetchone()
        org_name = row['org_name'] if row else "No organizer assigned"
        
        return render_template('admin_event_details.html', participants=participants, 
                             volunteers=volunteers, org_name=org_name)
    
    return render_template('event_details.html', participants=participants, 
                         volunteers=volunteers, org_name=org_name)

@app.route('/hall_admin_portal/')
def hall_admin_portal():
    """Hall admin portal"""
    if 'user_email' not in session or session['user_role'] != 'ADMIN':
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Hall")
    halls = cursor.fetchall()
    
    return render_template('hall_admin.html', halls=halls)

@app.route('/hall_details/', methods=['POST'])
def hall_details():
    """Hall details showing participants"""
    name_hall = request.form.get('name_hall')
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT email, name_par FROM Accomadation WHERE name_hall = ?", (name_hall,))
    participants = cursor.fetchall()
    
    return render_template('hall_details.html', name_hall=name_hall, participants=participants)

@app.route('/contact.html')
def contact():
    """Contact page"""
    return render_template('contact.html')

@app.route('/sponsors.html')
def sponsor():
    """Sponsors page"""
    return render_template('sponsors.html')

@app.route('/winner/', methods=['GET', 'POST'])
def winner():
    """Winner determination route"""
    winners = []
    
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        
        # Get all events
        cursor.execute("SELECT name FROM Event")
        events = [row['name'] for row in cursor.fetchall()]
        
        # Determine winners for each event
        for event in events:
            cursor.execute("SELECT student_email FROM EventRegistration WHERE event = ?", (event,))
            registrations = cursor.fetchall()
            
            if registrations:
                first_registration = registrations[0]['student_email']
                
                # Check if external participant
                cursor.execute("SELECT name FROM ExternalParticipant WHERE email = ?", (first_registration,))
                ep_check = cursor.fetchone()
                
                if ep_check:
                    winners.append([event, ep_check['name'], first_registration])
                else:
                    # Check if student
                    cursor.execute("SELECT name FROM Student WHERE email = ?", (first_registration,))
                    std_check = cursor.fetchone()
                    if std_check:
                        winners.append([event, std_check['name'], first_registration])
        
        # Insert winners into database
        cursor.execute("SELECT COUNT(*) FROM Winners")
        existing_winners = cursor.fetchone()[0]
        
        if existing_winners < len(events):
            for winner in winners:
                cursor.execute("INSERT OR IGNORE INTO Winners (event, name_par, email) VALUES (?, ?, ?)", 
                              (winner[0], winner[1], winner[2]))
        
        db.commit()
    
    return render_template('winner.html', winners=winners)

@app.route('/delete/', methods=['POST'])
def delete():
    """Delete user route for admin"""
    if 'user_email' not in session or session['user_role'] != 'ADMIN':
        return redirect(url_for('login'))
    
    email = request.form.get('email')
    db = get_db()
    cursor = db.cursor()
    
    # Get user role
    cursor.execute("SELECT role FROM CustomUser WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        return 'User not found', 404
    
    role = row['role']
    
    # Delete from CustomUser (cascade will handle related tables)
    cursor.execute("DELETE FROM CustomUser WHERE email = ?", (email,))
    
    # Handle specific cleanup for external participants
    if role == 'EXTERNAL':
        # Update hall vacancy if accommodation exists
        cursor.execute("SELECT name_hall FROM Accomadation WHERE email = ?", (email,))
        accommodation = cursor.fetchone()
        if accommodation:
            hall_name = accommodation['name_hall']
            cursor.execute("UPDATE Hall SET vacancy = vacancy + 1 WHERE name = ?", (hall_name,))
    
    db.commit()
    flash(f'User {email} deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    port = int(os.getenv('PORT', '8000'))
    app.run(host='0.0.0.0', port=port, debug=True)
