from flask import Flask, render_template, jsonify
import speech_recognition as sr
import pyttsx3
from twilio.rest import Client
import requests

app = Flask(__name__)

# Twilio credentials (Your Account SID and Auth Token)
account_sid = ''  # Replace with your Account SID
auth_token = ''      # Replace with your Auth Token
client = Client(account_sid, auth_token)

# Initialize the text-to-speech engine
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
        to_phone_numbers = [
            '+918247258785',
            '+919553000540',
            '+918121500540',
            '+918309056805',
            '+916303715976',
            '+919959583328',
            '+918919833054',
            '+916305864075'
        ]
        from_phone_number = '+12542523623'  # Your Twilio phone number
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

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')

@app.route('/listen', methods=['POST'])
def listen_and_recognize():
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            audio = recognizer.listen(source, timeout=30, phrase_time_limit=5)
            print("Processing audio...")
            text = recognizer.recognize_google(audio)
            print(f"Recognized text: {text}")
            send_message_and_location(text)
            return jsonify({"message": "Message and location sent successfully!", "recognized_text": text}), 200
    except sr.WaitTimeoutError:
        return jsonify({"error": "Listening timed out."}), 408
    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand the audio."}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech recognition service error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

if __name__ == '__main__':
        app.run(host='127.0.0.1', port=5001, debug=True)
