from flask import Flask, request, jsonify
import pymysql
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'alertsdb.ct4kqsgsqpud.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Ctsnpn2024',
    'database': 'alertsdb',
    'port': 3306
}

# Twilio configuration
twilio_client = Client('ACb125c82d4f915652a10a4f42f5f0f85c', '0fe151c3a22ee7ce20ff923692281258')
twilio_from_number = '+12565884281'

def get_db_connection():
    return pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        port=db_config['port']
    )

def send_alert_message(alert):
    try:
        message = twilio_client.messages.create(
            body=alert['message'],
            from_=twilio_from_number,
            to=alert['phoneNumber']
        )
        print(f"Message sent: {message.sid}")
    except Exception as e:
        print(f"Failed to send message: {e}")

def fetch_and_send_alerts():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Define timezone
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    # Get current time in IST
    now_ist = datetime.now(ist_tz)
    
    # Convert IST to UTC for comparison
    now_utc = now_ist.astimezone(pytz.utc)
    
    cursor.execute("SELECT * FROM alerts WHERE time <= %s", (now_ist,))
    alerts = cursor.fetchall()
    
    for row in alerts:
        alert = {
            'alertID': row[0],
            'patientID': row[1],
            'phoneNumber': row[2],
            'message': row[3],
            'time': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None
        }
        send_alert_message(alert)
        
    cursor.close()
    connection.close()

@app.route('/create_table', methods=['POST'])
def create_table():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    create_alerts_table_query = """
    CREATE TABLE IF NOT EXISTS alerts (
        alertID INT AUTO_INCREMENT PRIMARY KEY,
        patientID INT,
        phoneNumber VARCHAR(15),
        message VARCHAR(50),
        time DATETIME
    );
    """
    cursor.execute(create_alerts_table_query)
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Alerts table created successfully"})

@app.route('/add_alert', methods=['POST'])
def add_alert():
    data = request.get_json()
    patientID = data['patientID']
    phoneNumber = data['phoneNumber']
    message = data['message']
    time = data['time']  # Expecting 'YYYY-MM-DD HH:MM:SS' format
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    insert_query = "INSERT INTO alerts (patientID, phoneNumber, message, time) VALUES (%s, %s, %s, %s)"
    cursor.execute(insert_query, (patientID, phoneNumber, message, time))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Alert added successfully"})

@app.route('/update_alert/<int:id>', methods=['PUT'])
def update_alert(id):
    data = request.get_json()
    phoneNumber = data['phoneNumber']
    message = data['message']
    time = data['time']  # Expecting 'YYYY-MM-DD HH:MM:SS' format
    
    connection = get_db_connection()
    cursor = connection.cursor()
    
    update_query = """
    UPDATE alerts
    SET phoneNumber = %s, message = %s, time = %s
    WHERE alertID = %s
    """
    cursor.execute(update_query, (phoneNumber, message, time, id))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Alert updated successfully"})

@app.route('/get_alerts', methods=['GET'])
def get_alerts():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM alerts")
    result = cursor.fetchall()
    
    alerts = []
    for row in result:
        alert = {
            'alertID': row[0],
            'patientID': row[1],
            'phoneNumber': row[2],
            'message': row[3],
            'time': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None
        }
        alerts.append(alert)
    
    cursor.close()
    connection.close()
    
    return jsonify(alerts)

@app.route('/delete_alert/<int:id>', methods=['DELETE'])
def delete_alert(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    delete_query = "DELETE FROM alerts WHERE alertID = %s"
    cursor.execute(delete_query, (id,))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return jsonify({"message": "Alert deleted successfully"})

@app.route('/display_all', methods=['GET'])
def display_all():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM alerts")
    result = cursor.fetchall()
    
    alerts = []
    for row in result:
        alert = {
            'alertID': row[0],
            'patientID': row[1],
            'phoneNumber': row[2],
            'message': row[3],
            'time': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else None
        }
        alerts.append(alert)
    
    cursor.close()
    connection.close()
    
    return jsonify(alerts)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_send_alerts, 'interval', minutes=1)  # Adjust the interval as needed
    scheduler.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
