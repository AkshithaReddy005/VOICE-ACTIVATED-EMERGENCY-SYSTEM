import os
import json
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from twilio.rest import Client
import speech_recognition as sr
import pyttsx3
import requests
from datetime import datetime

# Twilio credentials
account_sid = 'sid'  # Replace with your Account SID
auth_token = 'auth_token'      # Replace with your Auth Token
client = Client(account_sid, auth_token)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

PHONE_NUMBERS_FILE = "phone_numbers.json"
USERS_FILE = "users.json"

# Ensure JSON files exist
def ensure_file(file_name):
    if not os.path.exists(file_name):
        with open(file_name, 'w') as file:
            json.dump({}, file)

# Load data from JSON file
def load_data(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

# Save data to JSON file
def save_data(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

engine = pyttsx3.init()

def speak(text):
    """Function to convert text to speech."""
    engine.say(text)
    engine.runAndWait()

def get_location():
    """Retrieve the user's current location with both latitude and longitude using ip-api."""
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        if 'lat' in data and 'lon' in data:
            latitude = data['lat']
            longitude = data['lon']
            return latitude, longitude
        else:
            return None
    except Exception as e:
        print(f"Failed to retrieve location: {e}")
        return None

def send_message_and_location(message_text):
    """Send the message and location via SMS."""
    location = get_location()
    if location:
        latitude, longitude = location
        map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        ensure_file(PHONE_NUMBERS_FILE)
        data = load_data(PHONE_NUMBERS_FILE)

        user = session['user']
        user_numbers = data.get(user, [])

        # Extract 'number' values from the list of phone numbers
        to_phone_numbers = [number['number'] for number in user_numbers]
        print(to_phone_numbers)
        from_phone_number = 'xxxxxxxx'  # Your Twilio phone number
        full_message = f"{message_text}\nHere is my current location: {map_link}"

        for to_phone_number in to_phone_numbers:
            try:
                client.messages.create(
                    body=full_message,
                    from_=from_phone_number,
                    to=to_phone_number
                )
                print(f"Message sent to {to_phone_number}")
            except Exception as e:
                print(f"Failed to send message to {to_phone_number}: {e}")

@app.route('/listen', methods=['GET', 'POST'])
def listen_and_recognize():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=30, phrase_time_limit=5)
            print("Processing audio...")
            text = recognizer.recognize_google(audio).lower()  # Convert to lowercase for consistent comparison
            print(f"Recognized text: {text}")

            # Check if the recognized text contains the keywords
            keywords = ["emergency", "alertify"]
            if any(keyword in text for keyword in keywords):
                send_message_and_location(text)  # Send SMS if keywords are present
                return jsonify({"message": "Message and location sent successfully!", "recognized_text": text}), 200
            else:
                return jsonify({"message": "No relevant keywords detected. No message sent.", "recognized_text": text}), 200
    except sr.WaitTimeoutError:
        return jsonify({"error": "Listening timed out."}), 408
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand the audio."}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech recognition service error: {e}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route('/signup', methods=['POST'])
def signup():
    ensure_file(USERS_FILE)
    users = load_data(USERS_FILE)

    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    if username in users:
        return jsonify({"error": "Username already exists."}), 400

    users[username] = password
    save_data(USERS_FILE, users)

    return jsonify({"message": "User signed up successfully."}), 200

@app.route('/login', methods=['POST'])
def login():
    ensure_file(USERS_FILE)
    users = load_data(USERS_FILE)

    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    if username not in users or users[username] != password:
        return jsonify({"error": "Invalid username or password."}), 401

    session['user'] = username
    return redirect(url_for('ma'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return redirect(url_for("index"))

@app.route('/')
def index():
    return render_template('signin.html')

@app.route('/ma')
def ma():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('main.html')

@app.route('/register_contacts', methods=['POST'])
def register_contacts():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing data'}), 400

    username = session['user']
    contacts = data.get('contacts')

    if not contacts or len(contacts) == 0:
        return jsonify({'error': 'At least one contact is required.'}), 400

    ensure_file(PHONE_NUMBERS_FILE)
    current_data = load_data(PHONE_NUMBERS_FILE)

    valid_contacts = []
    for contact in contacts:
        name = contact.get('name')
        number = contact.get('number')

        if not name or not number:
            return jsonify({'error': 'Both name and number are required for each contact.'}), 400

        if not number.startswith('+') or not number[1:].isdigit():
            return jsonify({'error': 'Invalid phone number format.'}), 400

        valid_contacts.append({'name': name, 'number': number})

    if username in current_data:
        existing_numbers = {contact['number'] for contact in current_data[username]}
        for contact in valid_contacts:
            if contact['number'] not in existing_numbers:
                current_data[username].append(contact)
    else:
        current_data[username] = valid_contacts

    save_data(PHONE_NUMBERS_FILE, current_data)
    return jsonify({'message': 'Registration successful', 'user': {'username': username, 'contacts': valid_contacts}}), 200

@app.route('/get_numbers', methods=['GET'])
def get_numbers():
    ensure_file(PHONE_NUMBERS_FILE)
    data = load_data(PHONE_NUMBERS_FILE)

    if 'user' not in session:
        return jsonify({"error": "User not logged in."}), 403

    user = session['user']
    user_numbers = data.get(user, [])

    extracted_numbers = [number['number'] for number in user_numbers]
    print(extracted_numbers)

    return jsonify({"numbers": extracted_numbers}), 200

def get_location():
    """Retrieve the user's current location with both latitude and longitude using ip-api."""
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()

        if 'lat' in data and 'lon' in data:
            latitude = data['lat']
            longitude = data['lon']
            return latitude, longitude
        else:
            print("Error: Latitude and/or longitude data missing in the response.")
            return None
    except Exception as e:
        print(f"Error retrieving location: {e}")
        return None


def send_message_and_location(message_text):
    """Send the message and location via SMS."""
    
    location = get_location()
    if location:
        latitude, longitude = location
        map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        ensure_file(PHONE_NUMBERS_FILE)
        data = load_data(PHONE_NUMBERS_FILE)

        user = session['user']
        user_numbers = data.get(user, [])

        # Extract 'number' values from the list of phone numbers
        to_phone_numbers = [number['number'] for number in user_numbers]
        print(to_phone_numbers)
        from_phone_number = '+17754380831'  # Your Twilio phone number
        full_message = f"{message_text}\nHere is my current location-----SMS------: {map_link}"

        for to_phone_number in to_phone_numbers:
            try:
                client.messages.create(
                    body=full_message,
                    from_=from_phone_number,
                    to=to_phone_number
                )
                sent_messages_info = []  # To collect information about sent messages
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                sent_message = f"Message sent to {to_phone_number} at {timestamp}!"
                sent_messages_info.append(sent_message)
                print(sent_message)
               # print(f"Message sent to {to_phone_number}")
           
            except Exception as e:
                print(f"Failed to send message to {to_phone_number}: {e}")


@app.route('/send', methods=['POST'])
def send_message():
    message_text = "EMERGENCY HELP ME!!"
    result_message = send_message_and_location(message_text)
    return jsonify({"message": result_message}), 200


if __name__ == '__main__':
    ensure_file(PHONE_NUMBERS_FILE)
    ensure_file(USERS_FILE)
    app.run(host='127.0.0.1', port=5002, debug=True)
