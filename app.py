from flask import Flask, render_template_string, request

app = Flask(__name__)

# רשימה זמנית לשמירת התלמידים (במציאות נשתמש בבסיס נתונים)
students_list = []

# דף הבית - מציג טופס ורשימת תלמידים
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # אם התלמיד לחץ על כפתור "שלח"
        student_name = request.form.get('student_name')
        if student_name:
            students_list.append(student_name)
    
    # HTML פשוט מאוד ישירות בתוך הקוד (רק לצורך הלמידה)
    html = """
    <h1>מערכת הזמנות לשיעורים פרטיים - צבי רכל</h1>
    <form method="POST">
        <input type="text" name="student_name" placeholder="הכנס את שמך" required>
        <button type="submit">הזמן שיעור</button>
    </form>
    <hr>
    <h3>תלמידים שנרשמו היום:</h3>
    <ul>
        {% for name in students %}
            <li>{{ name }}</li>
        {% endfor %}
    </ul>
    """
    return render_template_string(html, students=students_list)

if __name__ == '__main__':
    app.run(debug=True)