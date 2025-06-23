# Emergency STEM Project

This project appears to be a Python-based server application, possibly for managing users and phone numbers, with template support. Below are setup instructions and a guide to push your project to GitHub.

## Project Structure
- `server.py` / `server2.py`: Main server scripts.
- `phone_numbers.json`: Stores phone number data.
- `users.json`: Stores user data.
- `templates/`: Contains HTML or other template files for the server.

## Getting Started
1. **Install Python** (if not already installed):
   - Download from https://www.python.org/downloads/
2. **Install required packages:**
   - Open a terminal in the project directory and run:
     ```bash
     pip install flask
     ```
   - (Add any other dependencies as needed, e.g., `pyttsx3`, `requests`, `twilio`, `speechrecognition`)
3. **Run both servers:**
   - Open two terminal windows/tabs in the project directory.
   - In the first terminal, run:
     ```bash
     python server.py
     ```
   - In the second terminal, run:
     ```bash
     python server2.py
     ```
   - Both servers need to be running for the full application to work.


## Pushing to GitHub
If you want to contribute or push this project to GitHub, please follow standard git procedures (initialize a repository, add your files, commit, and push to your own remote repository).

---

Feel free to update this README with more details about your project, dependencies, or usage instructions!
