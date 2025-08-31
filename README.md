# CFMS - College Fest Management System

A comprehensive Flask-based web application for managing college festivals, events, participant registrations, accommodation bookings, and more.

## Features

### User Management
- **Student Registration & Login**: Students can register with roll numbers and access student-specific features
- **External Participant Registration & Login**: External participants can register with college information
- **Organizer Registration & Login**: Event organizers can register and manage events
- **Admin Dashboard**: Comprehensive admin panel for system management

### Event Management
- **Event Registration**: Students and external participants can register for events
- **Volunteer Registration**: Students can volunteer for events
- **Event Details**: View participants, volunteers, and organizers for each event
- **Winner Management**: Automatic winner determination and management

### Accommodation System
- **Hall Management**: Multiple halls with different locations and prices
- **Booking System**: External participants can book accommodation
- **Vacancy Tracking**: Real-time vacancy updates
- **Payment Processing**: Payment confirmation system

### Additional Features
- **Contact Information**: Comprehensive contact details
- **Sponsor Information**: Sponsor showcase and details
- **Responsive Design**: Modern, mobile-friendly interface
- **Session Management**: Secure user sessions

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript
- **Templates**: Jinja2
- **Authentication**: Session-based authentication

## Database Schema

### Core Tables

#### CustomUser
- `email` (VARCHAR(100), PRIMARY KEY)
- `password` (VARCHAR(100))
- `role` (VARCHAR(20)) - STUDENT, EXTERNAL, ORGANIZER, ADMIN

#### Student
- `email` (VARCHAR(100), PRIMARY KEY, FOREIGN KEY to CustomUser)
- `name` (VARCHAR(100))
- `roll_number` (VARCHAR(20))
- `password` (VARCHAR(100))

#### ExternalParticipant
- `email` (VARCHAR(100), PRIMARY KEY, FOREIGN KEY to CustomUser)
- `name` (VARCHAR(100))
- `college_name` (VARCHAR(100))
- `password` (VARCHAR(100))

#### Organiser
- `email` (VARCHAR(100), PRIMARY KEY, FOREIGN KEY to CustomUser)
- `name` (VARCHAR(100))
- `password` (VARCHAR(100))

#### Event
- `name` (VARCHAR(200), PRIMARY KEY)
- `description` (TEXT)
- `date` (DATE)
- `time` (TIME)
- `location` (VARCHAR(200))

#### EventRegistration
- `event` (VARCHAR(200), FOREIGN KEY to Event)
- `student_email` (VARCHAR(100), FOREIGN KEY to CustomUser)
- UNIQUE constraint on (event, student_email)

#### Hall
- `name` (VARCHAR(100), PRIMARY KEY)
- `location` (VARCHAR(200))
- `vacancy` (INTEGER)
- `price` (INTEGER)

#### Accomadation
- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `name_par` (VARCHAR(100))
- `email` (VARCHAR(100), FOREIGN KEY to ExternalParticipant)
- `date` (DATE)
- `name_hall` (VARCHAR(100), FOREIGN KEY to Hall)
- `price` (INTEGER)

#### Volunteer
- `event_name` (VARCHAR(100), FOREIGN KEY to Event)
- `student_name` (VARCHAR(100))
- `student_email` (VARCHAR(100), FOREIGN KEY to Student)
- PRIMARY KEY (event_name, student_email)

#### Event_has_organiser
- `event_name` (VARCHAR(100), FOREIGN KEY to Event)
- `org_name` (VARCHAR(100))
- `org_email` (VARCHAR(100), FOREIGN KEY to Organiser)
- PRIMARY KEY (event_name, org_email)

#### Winners
- `event` (VARCHAR(200), PRIMARY KEY)
- `name_par` (VARCHAR(100))
- `email` (VARCHAR(100))

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step-by-Step Installation

1. **Clone or download the project**
   ```bash
   cd flask_app
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:8000`

## Usage Guide

### For Students
1. Register as a student with your email, name, roll number, and password
2. Login to access the student dashboard
3. View available events and register for them
4. Volunteer for events if interested
5. Logout when done

### For External Participants
1. Register as an external participant with your email, name, college name, and password
2. Login to access the external participant dashboard
3. Register for events
4. Book accommodation if needed
5. View hall availability and make bookings

### For Organizers
1. Register as an organizer with your email, name, and password
2. Login to access the organizer dashboard
3. View events and manage them
4. Coordinate with participants and volunteers

### For Administrators
1. Access admin features (requires admin role)
2. Manage all users (students, external participants, organizers)
3. Monitor event registrations and volunteer signups
4. Track hall bookings and vacancies
5. Manage event winners
6. Delete users if necessary

## API Endpoints

### Authentication & Registration
- `GET/POST /login/` - User login
- `GET/POST /student_registration/` - Student registration
- `GET/POST /external_registration/` - External participant registration
- `GET/POST /organiser_registration/` - Organizer registration
- `GET /logout/` - User logout

### Dashboards
- `GET /student/` - Student dashboard
- `GET /external/` - External participant dashboard
- `GET /organizer/` - Organizer dashboard
- `GET /admin_url/` - Admin dashboard

### Event Management
- `GET /admin_event_dashboard/` - Admin event management
- `POST /event_registration/` - Student event registration
- `POST /event_ext_registration/` - External participant event registration
- `POST /volunteer_registration/` - Volunteer registration
- `GET/POST /event_details/` - Event details view

### Accommodation
- `GET /accomadation_portal/` - Accommodation portal
- `GET /hall_portal/` - Hall availability
- `POST /mybooking_portal/` - Book accommodation
- `GET /hall_admin_portal/` - Hall administration
- `POST /hall_details/` - Hall details view

### Admin Functions
- `POST /delete/` - Delete user
- `GET/POST /winner/` - Winner management

### Information Pages
- `GET /` - Homepage
- `GET /contact.html` - Contact information
- `GET /sponsors.html` - Sponsor information

## Database Operations

### Key SQLite Queries Used

#### User Authentication
```sql
SELECT email, password, role FROM CustomUser WHERE email = ?
```

#### Event Registration
```sql
INSERT INTO EventRegistration (event, student_email) VALUES (?, ?)
```

#### Accommodation Booking
```sql
INSERT INTO Accomadation (name_par, email, date, name_hall, price) VALUES (?, ?, ?, ?, ?)
UPDATE Hall SET vacancy = vacancy - 1 WHERE name = ?
```

#### Winner Determination
```sql
SELECT student_email FROM EventRegistration WHERE event = ?
SELECT name FROM Student WHERE email = ?
SELECT name FROM ExternalParticipant WHERE email = ?
```

## Security Features

- **Session Management**: Secure user sessions with Flask sessions
- **Input Validation**: Form validation and sanitization
- **SQL Injection Prevention**: Parameterized queries using SQLite
- **Access Control**: Role-based access control for different user types
- **Password Security**: Password confirmation during registration

## File Structure

```
flask_app/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── cfms.db               # SQLite database (created on first run)
└── templates/            # HTML templates
    ├── base.html         # Base template with navigation
    ├── homepage.html     # Homepage
    ├── login.html        # Login page
    ├── register_student.html      # Student registration
    ├── register_external.html     # External participant registration
    ├── register_organiser.html    # Organizer registration
    ├── student.html      # Student dashboard
    ├── external.html     # External participant dashboard
    ├── organiser.html    # Organizer dashboard
    ├── admin.html        # Admin dashboard
    ├── admin_event.html  # Admin event management
    ├── admin_event_details.html   # Event details for admin
    ├── accomodation.html # Accommodation portal
    ├── bookedhalls.html  # Hall availability
    ├── hall_admin.html   # Hall administration
    ├── hall_details.html # Hall details
    ├── event_details.html # Event details
    ├── winner.html       # Winner management
    ├── payment.html      # Payment confirmation
    ├── contact.html      # Contact information
    └── sponsors.html     # Sponsor information
```

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key (defaults to 'dev-secret-key-change-in-production')
- `PORT`: Server port (defaults to 8000)

### Database Configuration
- Database file: `cfms.db` (SQLite)
- Location: Same directory as `app.py`
- Auto-created on first run with sample data

## Sample Data

The application comes with pre-loaded sample data:

### Events
- Battle of Bands
- Dance Competition
- Coding Contest
- Art Exhibition
- Sports Meet

### Halls
- LBS HALL (Old Hijili)
- MT HALL (Main Building)
- SNVH HALL (Pepsi Cut)
- VS HALL (Jhan Ghosh)
- JCB HALL (Gymkhana)

## Troubleshooting

### Common Issues

1. **Port already in use**
   - Change the port in `app.py` or kill the process using the port

2. **Database errors**
   - Delete `cfms.db` and restart the application
   - Check file permissions

3. **Template errors**
   - Ensure all template files are in the `templates/` directory
   - Check for syntax errors in HTML templates

4. **Import errors**
   - Activate virtual environment
   - Install requirements: `pip install -r requirements.txt`

### Debug Mode
The application runs in debug mode by default. For production:
- Set `debug=False` in `app.py`
- Change the secret key
- Use a production WSGI server

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request


