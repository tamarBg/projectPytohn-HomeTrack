from datetime import datetime, timedelta
from io import BytesIO
from time import strftime
from flask import Flask, redirect, render_template, send_file,request, url_for
import numpy as np
from models import Purchase, db,User
import pandas as pd
import os
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests



app = Flask(__name__) # אובייקט ראשי שינהל את האפליקציה

# הגדרת מיקום קובץ ה-SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
# ביטול אזהרות מיותרות
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# עכשיו מקשרים את db לאפליקציה
db.init_app(app)
# with app.app_context():
#     db.drop_all()  # מוחק את כל הטבלאות
#     db.create_all()  # יוצר את הטבלאות מחדש
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup',methods=['GET','POST'])
def signup():
    error = None
    form_data = {'name':'','email':'','password':'','confirm':''}
    if request.method == 'GET':
        return render_template('signup.html',form_data=form_data)
    name=request.form['name']
    email=request.form['email']
    password=request.form['password']
    confirm=request.form['confirm']
    existing_email = User.query.filter_by(email=email).first()
    if confirm!=password:
        form_data = {'name':name,'email':email,'password':password,'confirm':''}
        error = 'אימות הסיסמה נכשל'
        return render_template('signup.html',error=error,form_data=form_data)
    elif existing_email:
        form_data = {'name':name,'email':'','password':'','confirm':''}
        error = 'המייל כבר קיים במערכת'
        return render_template('signup.html',error=error,form_data=form_data)
    else:
        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()        
        return redirect(url_for('profile',id=new_user.id))

@app.route('/signin',methods=['GET','POST'])
def signin():
    error = None
    form_data = {'email':'','password':''}
    if request.method == 'GET':
        return render_template('signin.html',form_data=form_data)
    email=request.form['email']
    password=request.form['password']
    existing_email=User.query.filter_by(email=email).first()
    if existing_email is None:
        form_data = {'email':'','password':password}
        error = 'המייל לא קיים במערכת'
        return render_template('signin.html',error=error,form_data=form_data)
    elif password != existing_email.password:
        form_data = {'email':email,'password':''}
        error = 'הסיסמא שגויה'
        return render_template('signin.html',error=error,form_data=form_data)
    else:   
        return redirect(url_for('profile',id=existing_email.id))
@app.route('/profile/<id>')
def profile(id):
    flag=1
    message="מהישן לחדש"
    user=User.query.get(id)
    purchases=Purchase.query.filter_by(user_id=id).order_by(Purchase.date.desc()).all()
    return render_template('profile.html',user=user,purchases=purchases,message=message,flag=flag)

@app.route('/profile2/<user_id>')
def profile2(user_id):
    flag=2
    message="מהחדש לישן"
    user=User.query.get(user_id)
    purchases=Purchase.query.filter_by(user_id=user_id).order_by(Purchase.date.asc()).all()
    return render_template('profile.html',user=user,purchases=purchases,message=message,flag=flag)

@app.route('/signout')
def signout():
    return redirect('/')

@app.route('/add/<id>',methods=['GET','POST'])
def add(id):
    if request.method=='GET':
        return render_template('add.html',id=id)

    nameP=request.form['nameP']
    qty=request.form['qty']
    price=request.form['price']
    category=request.form['category']
    date_str=request.form['date']
    date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
 
    purchases=[]

    if id == '9000':
        # כל פעם שמוסיפים:
        new_purchase = Purchase(
            user_id=1,
            nameP=nameP,
            qty=qty,
            price=price,
            category=category,
            date=date
        )
        purchases.append(new_purchase)
        return redirect(url_for('demoProfile.html',purchases=purchases))
    else:
        new_purchase=Purchase(user_id=id,nameP=nameP,qty=qty,price=price,category=category,date=date)
        db.session.add(new_purchase)
        db.session.commit()
        return redirect(url_for('profile',id=id))

@app.route('/delete/<id>/<p_id>')
def delete(id,p_id):
    purchase = Purchase.query.get_or_404(p_id)
    db.session.delete(purchase)
    db.session.commit()
    return redirect(url_for('profile',id=id))

@app.route('/saveData/<id>')
def save_data(id):
    purchases=Purchase.query.all()
    data=[{
        'User ID': p.user_id,
        'Name': p.nameP,
        'Quantity': p.qty,
        'Price': p.price,
        'Category': p.category,
        'Date': p.date.strftime("%Y-%m-%d")
    }for p in purchases]
    df=pd.DataFrame(data)
    file_path = 'backup.csv'
    df.to_csv(file_path, index=False)

    # שדרוג: הצגת משוב
    return render_template('backup_success.html', filepath=file_path,id=id)


# הורדת הקובץ
@app.route('/downloadData')
def download_data():
    file_path = 'backup.csv'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "הקובץ לא נמצא, בצעי קודם גיבוי.", 404


@app.route('/graph1')
def graph1():
    purchases=Purchase.query.all()
    data=[{
        'user_id': p.user_id,
        'nameP': p.nameP,
        'qty': p.qty,
        'price': p.price,
        'category': p.category,
        'date': p.date.strftime("%Y-%m-%d")
    }for p in purchases]
    df=pd.DataFrame(data)
        # סכום לפי קטגוריה
    category_sum = df.groupby('category')['qty'].sum()
        # יצירת הגרף
    plt.figure(figsize=(6, 6))
    category_sum.plot.pie(autopct='%1.1f%%', startangle=90)
    plt.title('התפלגות הוצאות לפי קטגוריה')
    plt.ylabel('')  # בלי תווית y
        # שמירה לקובץ זמני בזיכרון
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return send_file(img, mimetype='image/png')


 # גרף 2 - סכום הוצאות לפי שבוע
@app.route('/graph2')
def graph2():
    purchases=Purchase.query.all()
    data=[{
        'user_id': p.user_id,
        'nameP': p.nameP,
        'qty': p.qty,
        'price': p.price,
        'category': p.category,
        'date': p.date.strftime("%Y-%m-%d")
    }for p in purchases]
    df=pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    # יצירת עמודת שבוע מתוך התאריך
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year

    # סכום שבועי לפי שנה
    weekly_sum = df.groupby(['year', 'week'])['price'].sum().reset_index()

    # מיזוג שנה ושבוע לטובת הצגה נוחה
    weekly_sum['label'] = weekly_sum['year'].astype(str) + '-שבוע ' + weekly_sum['week'].astype(str)

    # ציור גרף
    plt.figure(figsize=(10, 5))
    plt.bar(weekly_sum['label'], weekly_sum['price'], color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.title('סך הוצאות לפי שבוע')
    plt.xlabel('שבוע')
    plt.ylabel('סכום הוצאות')

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    return send_file(img, mimetype='image/png')

@app.route('/demoProfile')
def demo_profile():
    data = [
        {'user_id': 1,'nameP': 'כדור','qty': 20,'price': 77.90,'category': 'משחקים','date': '2024-12-01'},
        {'user_id': 1,'nameP': 'בובה','qty': 5,'price': 35.00,'category': 'צעצועים','date': '2024-12-15'},
        {'user_id': 1,'nameP': 'מחברת','qty': 10,'price': 12.50,'category': 'לימודים','date': '2025-01-05'},
        {'user_id': 1,'nameP': 'ספר','qty': 2,'price': 90.00,'category': 'לימודים','date': '2025-02-10'},
        {'user_id': 1,'nameP': 'פאזל','qty': 3,'price': 48.00,'category': 'משחקים','date': '2025-02-25'},
        {'user_id': 1,'nameP': 'בלונים','qty': 50,'price': 0.90,'category': 'מסיבות','date': '2025-03-01'}
    ]
        # מספר רשומות דמה
    num_records = 10

    # תכונות של רכישה
    names = np.random.choice(['כדור', 'בובה', 'פאזל', 'לגו', 'רכבת'], size=num_records)
    prices = np.round(np.random.uniform(20, 200, size=num_records), 2)
    qtys = np.random.randint(1, 5, size=num_records)
    categories = np.random.choice(['משחקים', 'צעצועים', 'לימוד'], size=num_records)
    days_ago = np.random.randint(0, 7, size=num_records)
    dates = [datetime.today() - timedelta(days=int(d)) for d in days_ago]
    dates = [d.strftime('%Y-%m-%d') for d in dates]
        # יצירת DataFrame עם הנתונים הדינמיים
    extra_data = pd.DataFrame({
        'user_id': 1,
        'nameP': names,
        'qty': qtys,
        'price': prices,
        'category': categories,
        'date': dates
    })

    # המרת רשומות הדמה למילונים והוספתם ל-data
    for _, row in extra_data.iterrows():
        data.append({
            'user_id': row['user_id'],
            'nameP': row['nameP'],
            'qty': row['qty'],
            'price': row['price'],
            'category': row['category'],
            'date': row['date']
        })

    # המרה לאובייקטי Purchase (רק לצורך תצוגה, לא מוסיפים לדאטאבייס)
    purchases = [Purchase(
        user_id=record['user_id'],
        nameP=record['nameP'],
        qty=record['qty'],
        price=record['price'],
        category=record['category'],
        date=datetime.strptime(record['date'], '%Y-%m-%d')
    ) for record in data]

    # יצירת משתמש דמה
    user = User(id=1, name="משתמשת הדגמה", email="demo@example.com", password="1234")

    return render_template('profile.html', user=user, purchases=purchases, message="תצוגת דמו", flag=1)
    # הצגת הנתונים בטמפלט



@app.route('/Shopping_cart/<id>')
def Shopping_cart(id):
    data = [
        {'user_id': 1,'name': 'כדור','qty': 20,'price': 77.90,'category': 'משחקים','date': '2024-12-01'},
        {'user_id': 1,'name': 'בובה','qty': 5,'price': 35.00,'category': 'צעצועים','date': '2024-12-15'},
        {'user_id': 1,'name': 'מחברת','qty': 10,'price': 12.50,'category': 'לימודים','date': '2025-01-05'},
        {'user_id': 1,'name': 'ספר','qty': 2,'price': 90.00,'category': 'לימודים','date': '2025-02-10'},
        {'user_id': 1,'name': 'פאזל','qty': 3,'price': 48.00,'category': 'משחקים','date': '2025-02-25'},
        {'user_id': 1,'name': 'בלונים','qty': 50,'price': 0.90,'category': 'מסיבות','date': '2025-03-01'}
    ]
       # יצירת DataFrame עם pandas
    user_purchases = pd.DataFrame(data)
    # שלב 1: פתיחת קובץ HTML וניתוחו
    with open("templates/store.html", encoding="utf-8") as file:
        soup = BeautifulSoup(file, 'html.parser')
    # שלב 2: שליפת שמות ומחירים מהחנות
    store_products = []
    for product in soup.find_all("div", class_="product"):
        name = product.find("span", class_="name").text.strip()
        price = float(product.find("span", class_="price").text.strip())
        store_products.append({'name': name, 'store_price': price})    
        
    store_df = pd.DataFrame(store_products)
    # שלב 3: מיזוג הנתונים לפי שם המוצר
    merged = pd.merge(user_purchases, store_df, on="name")

    # שלב 4: סינון רק של מוצרים שבהם המחיר בחנות זול יותר
    better_deals = merged[merged['store_price'] < merged['price']]
    to_print="מוצרים שהחנות מציעה במחיר זול יותר"
    return render_template('store.html',better_deals=better_deals,to_print=to_print,id=id)

if __name__== "__main__":  # הרצת האפליקציה
    app.run(debug=True)