from flask import Flask, render_template, request, session, redirect, url_for  # Importing Flask modules
from flask_socketio import join_room, leave_room, send, SocketIO  # Importing Flask-SocketIO for WebSocket support
import random  # Importing random module for generating room codes
from string import ascii_uppercase  # Importing ascii_uppercase for generating room codes

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"  # Secret key for session encryption
socketio = SocketIO(app)

rooms = {}  # Dictionary to store room information


# Function to generate a unique room code
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)  # Generate a random code using uppercase letters

        if code not in rooms:  # Check if the code is unique
            break

    return code


# Route for home page
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()  # Clear session data
    if request.method == "POST":  # If form is submitted
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        is_public = request.form.get("public", False) 

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name, public_room_list=get_public_rooms())

        if join!= False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name, public_room_list=get_public_rooms())

        room = code
        if create!= False:  # If user wants to create a new room
            room = generate_unique_code(4)  # Generate a unique room code
            rooms[room] = { "members": 0, "messages": [], "public": is_public, "creator": name}  # Initialize room
            # data

        elif code not in rooms:  # If joining an existing room
            return render_template("home.html", error="Room does not exist.", code=code, name=name, public_room_list=get_public_rooms())

        session["room"] = room  # Store room code in session
        session["name"] = name  # Store user's name in session
        return redirect(url_for("room"))  # Redirect to the room page
    
    return render_template("home.html", public_room_list=get_public_rooms())

def get_public_rooms():
    return [{"code": code, "creator": details["creator"]} for code, details in rooms.items() if details["public"]]



# Route for room page
@app.route("/room")
def room():
    room = session.get ("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])  # Render the room page template

# Event handler for receiving messages
@socketio.on("message")
def message(data):
    room = session.get ("room")
    name = session.get ("name")
    if room not in rooms:
        return  # If room does not exist, ignore the message
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)  # Broadcast the message to all clients in the room
    rooms[room]["messages"].append(content)  # Store the message in the room's message history
    print(f"{session.get('name')} said: {data['data']}")  # Print the message to the console

# Event handler for client connection
@socketio.on("connect")
def connect(auth):
    room = session.get ("room")
    name = session.get ("name")
    if not room or not name:
        return  # If session data is missing, do nothing
    if room not in rooms:
        leave_room(room)  # If room does not exist, leave the current room
        return

    join_room(room)  # Join the specified room
    send({"name": name, "message": "has entered the room"}, to=room)  # Broadcast entry message to room
    rooms[room]["members"] += 1  # Increment member count for the room
    print(f"{name} joined room {room}")  # Print to console

# Event handler for client disconnection
@socketio.on("disconnect")
def disconnect():
    room  = session.get ("room")
    name  = session.get ("name")
    leave_room(room)  # Leave the current room

    if room in rooms:
        rooms[room]["members"] -= 1  # Decrement member count for the room
        if rooms[room]["members"] <= 0:
            del rooms[room]  # If no members left, delete the room

    send({"name": name, "message": "has left the room"}, to=room)  # Broadcast exit message to room
    print(f"{name} has left the room {room}")  # Print to console

# Start the Flask app with SocketIO support
if __name__ == "__main__":
    socketio.run(app,host='172.20.10.6',port=5000, debug=True, allow_unsafe_werkzeug=True, use_reloader=False)
	

