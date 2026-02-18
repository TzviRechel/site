from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# הגדרת מסד הנתונים
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'lessons.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# מודל לשיעור זמין
class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(50), nullable=False)  # יום השבוע (שני, שלישי וכו')
    time = db.Column(db.String(5), nullable=False)  # השעה (14:00, 15:00 וכו')
    bookings = db.relationship('Booking', backref='slot', lazy=True, cascade='all, delete-orphan')
    
    def is_available(self):
        return len(self.bookings) == 0

# מודל להזמנה
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now)

# יצירת טבלאות
with app.app_context():
    db.create_all()
    
    # הוספת שיעורים זמינים (אם אין כבר)
    if TimeSlot.query.count() == 0:
        schedule = [
            ('שני', '14:00'), ('שני', '15:00'), ('שני', '16:00'),
            ('שלישי', '14:00'), ('שלישי', '15:00'), ('שלישי', '16:00'),
            ('רביעי', '14:00'), ('רביעי', '15:00'), ('רביעי', '16:00'),
            ('חמישי', '14:00'), ('חמישי', '15:00'), ('חמישי', '16:00'),
        ]
        for day, time in schedule:
            db.session.add(TimeSlot(day=day, time=time))
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        slot_id = request.form.get('time_slot_id')
        
        if student_name and email and phone and slot_id:
            slot = TimeSlot.query.get(slot_id)
            if slot and slot.is_available():
                booking = Booking(
                    student_name=student_name,
                    email=email,
                    phone=phone,
                    time_slot_id=slot_id
                )
                db.session.add(booking)
                db.session.commit()
    
    time_slots = TimeSlot.query.all()
    bookings = Booking.query.all()
    
    # ארגון השיעורים לפי יום
    days = {}
    for slot in time_slots:
        if slot.day not in days:
            days[slot.day] = []
        days[slot.day].append(
            {
                'id': slot.id,
                'time': slot.time,
                'available': slot.is_available(),
                'student': slot.bookings[0].student_name if slot.bookings else None
            }
        )
    
    html = """
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>שיעורים פרטיים - צבי רכל</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Hebrew, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 40px;
                font-size: 1.1em;
            }
            
            .content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 40px;
                margin-top: 30px;
            }
            
            .form-section h2, .schedule-section h2 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 1.5em;
            }
            
            form {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            input, select {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 1em;
                font-family: inherit;
                transition: border-color 0.3s;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
            }
            
            button {
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1em;
                font-weight: bold;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
            }
            
            .schedule-section {
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .day-schedule {
                background: #f9f9f9;
                padding: 15px;
                border-radius: 8px;
                border-right: 4px solid #667eea;
            }
            
            .day-schedule h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            
            .time-slots {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
            }
            
            .slot {
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .slot.available {
                background: #e8f5e9;
                color: #2e7d32;
                border: 2px solid #4caf50;
            }
            
            .slot.available:hover {
                background: #c8e6c9;
            }
            
            .slot.booked {
                background: #ffebee;
                color: #c62828;
                border: 2px solid #f44336;
                cursor: not-allowed;
            }
            
            .slot.selected {
                background: #667eea;
                color: white;
            }
            
            .student-info {
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
                border-right: 4px solid #2196f3;
            }
            
            .student-info h3 {
                color: #1976d2;
                margin-bottom: 8px;
            }
            
            .student-info p {
                color: #555;
                font-size: 0.95em;
            }
            
            @media (max-width: 768px) {
                .content {
                    grid-template-columns: 1fr;
                }
                
                .time-slots {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 שיעורים פרטיים</h1>
            <p class="subtitle">צבי רכל</p>
            
            <div class="content">
                <div class="form-section">
                    <h2>📝 הרשמה לשיעור</h2>
                    <form method="POST">
                        <input 
                            type="text" 
                            name="student_name" 
                            placeholder="שם מלא" 
                            required
                        >
                        <input 
                            type="email" 
                            name="email" 
                            placeholder="אימייל" 
                            required
                        >
                        <input 
                            type="tel" 
                            name="phone" 
                            placeholder="טלפון" 
                            required
                        >
                        <select name="time_slot_id" required>
                            <option value="">-- בחר זמן שיעור --</option>
                            {% for day, slots in schedule.items() %}
                                <optgroup label="{{ day }}">
                                {% for slot in slots %}
                                    {% if slot.available %}
                                        <option value="{{ slot.id }}">{{ day }} בשעה {{ slot.time }}</option>
                                    {% endif %}
                                {% endfor %}
                                </optgroup>
                            {% endfor %}
                        </select>
                        <button type="submit">✅ הזמן שיעור</button>
                    </form>
                </div>
                
                <div class="schedule-section">
                    <h2>📅 לוח זמנים</h2>
                    {% for day, slots in schedule.items() %}
                        <div class="day-schedule">
                            <h3>{{ day }}</h3>
                            <div class="time-slots">
                                {% for slot in slots %}
                                    <div class="slot {% if slot.available %}available{% else %}booked{% endif %}">
                                        <div>{{ slot.time }}</div>
                                        {% if not slot.available %}
                                            <div style="font-size: 0.85em; margin-top: 5px;">✓ תפוס</div>
                                        {% endif %}
                                    </div>
                                {% endfor %}
                            </div>
                        </div>
                    {% endfor %}
                </div>
            </div>
            
            {% if bookings %}
                <div class="student-info" style="margin-top: 30px;">
                    <h3>📋 הזמנות אחרונות</h3>
                    {% for booking in bookings[-5:] %}
                        <p style="margin-bottom: 8px;">
                            <strong>{{ booking.student_name }}</strong> - {{ booking.slot.day }} בשעה {{ booking.slot.time }}
                        </p>
                    {% endfor %}
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html, schedule=days, bookings=bookings)

@app.route('/admin')
def admin():
    """דף ניהול לצפיה בכל ההזמנות"""
    bookings = Booking.query.all()
    html = """
    <!DOCTYPE html>
    <html lang="he" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>ניהול הזמנות</title>
        <style>
            body {
                font-family: 'Segoe UI', Hebrew, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 12px;
                text-align: right;
                border-bottom: 1px solid #ddd;
            }
            th {
                background: #667eea;
                color: white;
            }
            tr:hover {
                background: #f9f9f9;
            }
            a {
                color: #667eea;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 ניהול הזמנות</h1>
            <p>סה"כ הזמנות: {{ count }}</p>
            <table>
                <tr>
                    <th>שם התלמיד</th>
                    <th>אימייל</th>
                    <th>טלפון</th>
                    <th>יום</th>
                    <th>שעה</th>
                    <th>תאריך הזמנה</th>
                </tr>
                {% for booking in bookings %}
                    <tr>
                        <td>{{ booking.student_name }}</td>
                        <td>{{ booking.email }}</td>
                        <td>{{ booking.phone }}</td>
                        <td>{{ booking.slot.day }}</td>
                        <td>{{ booking.slot.time }}</td>
                        <td>{{ booking.booking_date.strftime('%d.%m.%Y %H:%M') }}</td>
                    </tr>
                {% endfor %}
            </table>
            <br>
            <a href="/">← חזור לעמוד הבית</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, bookings=bookings, count=len(bookings))

if __name__ == '__main__':
    app.run(debug=True)