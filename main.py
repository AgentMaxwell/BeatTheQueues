import tkinter as tk
from tkinter import ttk
from pip._vendor import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

counter = 0

last_updated_time = None
recipient_email = ""

def fetch_queue_times(park_id):
    try:
        response = requests.get(f"https://queue-times.com/parks/{park_id}/queue_times.json")
        data = response.json()
        lands = data.get('lands', [])
        rides = []
        for land in lands:
            rides.extend(land.get('rides', []))
        return rides, lands
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return [], []

def categorize_rides(lands):
    categorized_rides = {}
    for land in lands:
        land_name = land['name']
        rides = land.get('rides', [])
        categorized_rides[land_name] = [{'name': ride['name'], 'wait_time': ride['wait_time'], 'is_open': ride['is_open'], 'last_updated': ride['last_updated']} for ride in rides]
    return categorized_rides

def update_timer_label():
    global update_timer
    timer_label.config(text=f"Next update in: {update_timer} seconds")
    if update_timer > 0:
        update_timer -= 1
        root.after(1000, update_timer_label)
    else:
        update_timer = 30
        root.after(1000,update_timer_label)

def update_ride_data():
    global rides, lands, categorized_rides, update_timer, counter
    print(f"Fetching queue times...{counter}")  # Debugging line
    counter += 1
    rides, lands = fetch_queue_times(selected_park.get())
    categorized_rides = categorize_rides(lands)
    update_ride_list(ride_categories[0])
    check_state_changes()
    check_wait_time_thresholds()
    root.after(60000, update_ride_data)

# Function to save the email address to a file
def save_email_address(email):
    with open('email_settings.json', 'w') as file:
        json.dump({'email': email}, file)
        # Update recipient_email after saving
        global recipient_email
        recipient_email = email

# Function to read the email address from the file
def load_email_address():
    try:
        with open('email_settings.json', 'r') as file:
            data = json.load(file)
            return data.get('email', None)  # Return email if exists, otherwise None
    except FileNotFoundError:
        return None

# Function to handle saving email address from the settings page
def save_email_address_from_settings():
    email = email_entry.get()
    save_email_address(email)
    # Update the recipient_email after saving
    global recipient_email
    recipient_email = email
    settings_window.destroy()

# Create a settings window
def open_settings_window():
    global email_entry, settings_window
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("300x100")
    settings_window.resizable(False, False)

    email_label = ttk.Label(settings_window, text="Email Address:")
    email_label.pack()

    email_entry = ttk.Entry(settings_window)
    email_entry.pack()

    save_button = ttk.Button(settings_window, text="Save", command=save_email_address_from_settings)
    save_button.pack()

# Load the email address from the file on startup
recipient_email = load_email_address()

# Use the loaded email address to send emails
if recipient_email:
    print("Recipient email loaded:", recipient_email)
else:
    print("No recipient email found.")

def check_state_changes():
    global ride_checkboxes
    for land_name, rides in categorized_rides.items():
        for ride in rides:
            ride_name = ride['name']
            is_open = ride['is_open']
            # Check if ride_name exists in ride_checkboxes, if not, initialize it
            if ride_name not in ride_checkboxes:
                ride_checkboxes[ride_name] = {'last_state': None, 'notify': False, 'threshold': False, 'threshold_value': 10}
            last_state = ride_checkboxes[ride_name].get('last_state', None)
            if ride_checkboxes.get(ride_name, {}).get('notify', False) and is_open != last_state:
                ride_checkboxes[ride_name]['last_state'] = is_open
                status_change = 'opened' if is_open else 'closed'
                print(f"{ride_name} has {status_change}")
                print("EMAIL WIBBLE WOBBLE")
                send_email(f"{ride_name} has {status_change}", "Thanks for using my service. Questions? Contact me on X @lqsonic. Powered by the API at https://queue-times.com")

email_sent_flag = {}

def check_wait_time_thresholds():
    global email_sent_flag
    
    for land_name, rides in categorized_rides.items():
        for ride in rides:
            ride_name = ride['name']
            wait_time = ride['wait_time']
            is_open = ride['is_open']
            if ride_checkboxes.get(ride_name, {}).get('threshold', False) and wait_time is not None and is_open:
                threshold_value = int(ride_checkboxes[ride_name].get('threshold_value', 10))
                
                if int(wait_time) < threshold_value:
                    if ride_name not in email_sent_flag or not email_sent_flag[ride_name]:
                        print(f"{ride_name}'s wait is now less than {threshold_value}")
                        send_email(f"{ride_name}'s wait time is less than {threshold_value}!",
                                   f"The wait time for {ride_name} is now less than {threshold_value} minutes.")
                        email_sent_flag[ride_name] = True
                else:
                    email_sent_flag[ride_name] = False


def display_rides_based_on_checkbox():
    selected_rides = {'first_checkbox': [], 'second_checkbox': []}
    threshold_values = {}
    
    for ride_name, checkbox_info in ride_checkboxes.items():
        if checkbox_info.get('threshold', False):
            threshold_values[ride_name] = checkbox_info.get('threshold_value', 10)
    
    for land_name, rides in categorized_rides.items():
        for ride in rides:
            ride_name = ride['name']
            if ride_checkboxes.get(ride_name, {}).get('notify', False):
                selected_rides['first_checkbox'].append(ride)
            if ride_checkboxes.get(ride_name, {}).get('threshold', False):
                selected_rides['second_checkbox'].append(ride)
    
    return selected_rides, threshold_values

def update_ride_list_with_checkbox_selection(selected_category):
    selected_rides, threshold_values = display_rides_based_on_checkbox()
    
    for widget in rides_listbox.winfo_children():
        widget.destroy()

    for button in buttons:
        button.pack_forget()

    num_rides = len(selected_rides[selected_category])
    num_columns = 2 if num_rides > 20 else 1

    for i, ride_info in enumerate(selected_rides[selected_category]):
        ride_name = ride_info['name']
        ride_wait_time = ride_info['wait_time'] if ride_info['is_open'] else 'Closed'

        ride_button = ttk.Button(
            rides_listbox,
            text=f"{ride_name}: {ride_wait_time} minutes",
            command=lambda info=ride_info: open_ride_detail(info))
        ride_button.grid(row=i // num_columns,
                         column=i % num_columns,
                         padx=5,
                         pady=5)
    
    if selected_category == 'second_checkbox':
        threshold_label = ttk.Label(rides_listbox, text=f"Thresholds: {threshold_values}")
        threshold_label.grid(row=num_rides // num_columns + 1, column=0, columnspan=num_columns, padx=5, pady=5)


def open_ride_detail(ride_info):
    ride_name = ride_info['name']
    ride_wait_time = ride_info['wait_time'] if ride_info['is_open'] else 'Closed'
    ride_status = ride_wait_time if ride_wait_time != 'Closed' else 'Closed'

    detail_window = tk.Toplevel(root)
    detail_window.title(ride_name)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    detail_window.geometry(f"{screen_width}x{screen_height}")

    ride_label = ttk.Label(
        detail_window,
        text=f"Name: {ride_name}\nWait Time: {ride_wait_time} minutes")
    ride_label.pack()

    notify_label = ttk.Label(detail_window, text="Notify me")
    notify_label.pack(anchor=tk.W)

    notify_var = tk.BooleanVar(
        value=ride_checkboxes.get(ride_name, {}).get('notify', False))
    notify_checkbox = ttk.Checkbutton(detail_window,
                                      text="About the state changes",
                                      variable=notify_var)
    notify_checkbox.pack(anchor=tk.W)

    threshold_frame = tk.Frame(detail_window)
    threshold_frame.pack(anchor=tk.W)

    threshold_var = tk.BooleanVar(
        value=ride_checkboxes.get(ride_name, {}).get('threshold', False))
    threshold_checkbox = ttk.Checkbutton(
        threshold_frame,
        text="When the queue time goes below",
        variable=threshold_var)
    threshold_checkbox.pack(side=tk.LEFT)

    threshold_dropdown = ttk.Combobox(threshold_frame,
                                      values=[i for i in range(10, 121, 10)])
    threshold_dropdown.pack(side=tk.LEFT)

    if threshold_var.get():
        threshold_dropdown.set(
            ride_checkboxes.get(ride_name, {}).get('threshold_value', 10))

    def toggle_dropdown():
        if threshold_var.get():
            threshold_dropdown.pack()
        else:
            threshold_dropdown.pack_forget()

    threshold_var.trace_add('write', lambda *_: toggle_dropdown())

    space_label = ttk.Label(detail_window, text="")
    space_label.pack()

    def on_detail_window_close():
        ride_checkboxes[ride_name] = {
            'notify':
            notify_var.get(),
            'threshold':
            threshold_var.get(),
            'threshold_value':
            threshold_dropdown.get() if threshold_var.get() else None
        }
        detail_window.destroy()

    detail_window.protocol("WM_DELETE_WINDOW", on_detail_window_close)

def update_ride_list(selected_category):
    for widget in rides_listbox.winfo_children():
        widget.destroy()

    for button in buttons:
        button.pack_forget()

    num_rides = len(categorized_rides[selected_category])
    num_columns = 2 if num_rides > 20 else 1

    for i, ride_info in enumerate(categorized_rides[selected_category]):
        ride_name = ride_info['name']
        ride_wait_time = ride_info['wait_time'] if ride_info['is_open'] else 'Closed'

        ride_button = ttk.Button(
            rides_listbox,
            text=f"{ride_name}: {ride_wait_time} minutes",
            command=lambda info=ride_info: open_ride_detail(info))
        ride_button.grid(row=i // num_columns,
                         column=i % num_columns,
                         padx=5,
                         pady=5)

    for button, category in zip(buttons, ride_categories):
        if categorized_rides[category]:
            button.pack(side=tk.LEFT, padx=1, pady=5)

    for button, category in zip(buttons, ride_categories):
        if not categorized_rides[category]:
            button.pack_forget()

def switch_park(park_id):
    global rides, lands, categorized_rides, ride_categories
    rides, lands = fetch_queue_times(park_id)
    categorized_rides = categorize_rides(lands)
    ride_categories = list(categorized_rides.keys())
    print(f"Number of categories found: {len(ride_categories)}")
    update_ride_list(ride_categories[0])

    for button, category in zip(buttons, ride_categories):
        button.configure(text=category,
                         command=lambda cat=category: update_ride_list(cat))

def print_debug_info():
    global last_updated_time
    new_last_updated_time = max([ride.get('last_updated', 'Unknown') for rides in categorized_rides.values() for ride in rides])
    if new_last_updated_time != last_updated_time:
        last_updated_time = new_last_updated_time
        print("Last updated times:")
        for land_name, rides in categorized_rides.items():
            for ride in rides:
                ride_name = ride['name']
                last_updated = ride.get('last_updated', 'Unknown')
                print(f"- {ride_name}: Last updated at {last_updated}")
    root.after(5000, print_debug_info)

def read_sender_password():
    with open('pass.txt', 'r') as file:
        return file.read().strip()

def send_email(subject, message):
    # Set up the MIME
    sender_password = read_sender_password()

    email_message = MIMEMultipart()
    email_message['From'] = sender_email
    email_message['To'] = recipient_email
    email_message['Subject'] = subject

    # Attach the message to the email
    email_message.attach(MIMEText(message, 'plain'))

    # Connect to the SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()

    # Log in to the server
    server.login(sender_email, sender_password)

    # Send the email
    server.sendmail(sender_email, recipient_email, email_message.as_string())

    # Close the connection
    server.quit()

root = tk.Tk()
root.title("Queue Times")
root.geometry("360x680")

selected_park = tk.IntVar(value=2)
rides, lands = fetch_queue_times(selected_park.get())
categorized_rides = categorize_rides(lands)
ride_categories = list(categorized_rides.keys())

rides_listbox = tk.Frame(root)
rides_listbox.pack(fill=tk.BOTH, expand=False)

button_frame = tk.Frame(root)
button_frame.pack(side=tk.BOTTOM, fill=tk.X)
buttons = []
for category in ride_categories:
    button = ttk.Button(button_frame,
                        text=category,
                        command=lambda cat=category: update_ride_list(cat))
    button.pack(side=tk.LEFT, padx=5, pady=5)
    buttons.append(button)

ride_checkboxes = {}

update_ride_list(ride_categories[0])

menu = tk.Menu(root)
root.config(menu=menu)
park_menu = tk.Menu(menu)
menu.add_cascade(label="Parks", menu=park_menu)
park_menu.add_radiobutton(label="Thorpe Park",
                          variable=selected_park,
                          value=2,
                          command=lambda: switch_park(2))
# park_menu.add_radiobutton(label="Alton Towers",
#                           variable=selected_park,
#                           value=1,
#                           command=lambda: switch_park(1))
park_menu.add_radiobutton(label="Epcot (9am Email Expected)",
                          variable=selected_park,
                          value=5,
                          command=lambda: switch_park(5))
display_menu = tk.Menu(menu)
menu.add_cascade(label="Display Rides with Notifications", menu=display_menu)
display_menu.add_command(label="Status",
                         command=lambda: update_ride_list_with_checkbox_selection('first_checkbox'))
display_menu.add_command(label="Wait Time Threshold",
                         command=lambda: update_ride_list_with_checkbox_selection('second_checkbox'))
# Create a button to open the settings window
settings_button = ttk.Button(root, text="Settings", command=open_settings_window)
settings_button.pack()

timer_label = ttk.Label(root, text="Next update in: 30 seconds")
timer_label.pack(side=tk.BOTTOM, pady=5)

sender_email = 'significodettv@gmail.com'
subject = 'Test Email'
message = 'This is a test email sent from Python.'

update_timer = 30

root.after(5000, print_debug_info)
root.after(30000, update_ride_data)

root.mainloop()
