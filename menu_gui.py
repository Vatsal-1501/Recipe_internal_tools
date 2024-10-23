
import tkinter as tk
from tkinter import filedialog, messagebox ,ttk
import pygame 
import os
import threading
import time
import io
import zipfile
import json
from tkinter import ttk


# Global variables
ingredient_data = None  # Data for the ingredients table
instruction_data = None  # Data for the instructions table
data = None
selected_row = None  # Store the currently selected row
highlight_color = "yellow"  # Color for highlighting the selected row
default_color = "white"  # Default background color
long_press_duration = 500  # Duration in milliseconds to detect long press
long_press_active = False  # To track if long press is active

pygame.mixer.init()
AUDIO_FOLDER_PATH = r"D:\Recipe_internal_tools\mp3"
SELECT_FOLDER_PATHS = r"D:\Recipe_internal_tools\Recipee's\Aloo Samosa"
global error_cells
error_cells = [] 

def change_cell_color(row, col, frame, color):
    for widget in frame.grid_slaves(row=row, column=col):
        if isinstance(widget, tk.Frame):
            for label in widget.winfo_children():
                if isinstance(label, tk.Label):
                    if color:
                        label.config(bg=color)
                    else:
                        # Reset to default color and style
                        label.config(bg=default_color, font=('Arial', 10, 'underline'))
def play_audio(file_name, row, col, frame):
    audio_file = os.path.join(AUDIO_FOLDER_PATH, file_name)
    
    if os.path.exists(audio_file):
        # Change cell color to light green
        change_cell_color(row, col, frame, "light green")
        
        def play_and_reset():
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            # Reset cell color after audio finishes
            root.after(0, lambda: change_cell_color(row, col, frame, None))
        
        # Start audio playback in a separate thread
        threading.Thread(target=play_and_reset, daemon=True).start()
    else:
        print(f"Audio file {audio_file} not found!")
        # Change cell color to red
        change_cell_color(row, col, frame, "red") 
        # Reset cell color after 2 seconds
        root.after(1500, lambda: change_cell_color(row, col, frame, None))

# Function to handle left-click on the audioP column (column index 5)
def on_audio_click(row, col):
    audio_value = ingredient_data[row][col]
    if audio_value:
        audio_file_name = f"{audio_value}.mp3"
        play_audio(audio_file_name, row, col, ingredients_frame)

def on_instruction_audio_click(row, col):
    audio_value = instruction_data[row][col]
    if audio_value:
        audio_file_name = f"{audio_value}.mp3"
        play_audio(audio_file_name, row, col, instructions_frame)

def audio_file_exists(file_name):
    return os.path.exists(os.path.join(AUDIO_FOLDER_PATH, f"{file_name}.mp3"))

def check_for_errors(data_table, frame):
    error_cells = []
    for i, row in enumerate(data_table):
        if i == 0:  # Skip header row
            continue
        for j, value in enumerate(row):
            is_error = False
            if frame == instructions_frame:
                if j == 10:  # Stirrer column
                    if str(value).strip() not in ["0", "1", "2", "3", "4", ""]:
                        is_error = True
                elif j == 20:  # Skip column
                    if str(value).strip().lower() not in ["true", "false", ""]:
                        is_error = True
                elif j == 7:  # Lid status column
                    if str(value).strip().lower() not in ["open", "close", ""]:
                        is_error = True
                elif j == 3:  # Induction power column
                    if str(value).strip() not in ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", ""]:
                        is_error = True
                elif j == 12:  # Magnetron power column
                    if str(value).strip() not in ["0", "20", "40", "60", "80", "100", ""]:
                        is_error = True

            if is_error:
                error_cells.append((i, j))
    return error_cells
    

# Function to load JSON file and display both tables
def load_json():
    global ingredient_data, instruction_data  # Declare ingredient_data and instruction_data as global
    
    # Open file dialog to select JSON file
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"),("Zip Files","*.zip")])
    
    if not file_path:
        return
    
    try:
        if file_path.lower().endswith('.zip'):
            # Handle ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                json_files = [f for f in zip_ref.namelist() if f.lower().endswith('.txt')]
                if not json_files:
                    raise ValueError("No JSON file found in the ZIP archive")
                
                # Use the first JSON file found
                json_file = json_files[0]
                with zip_ref.open(json_file) as file:
                    data = json.load(io.TextIOWrapper(file))
        else:
            # Handle regular JSON file
            with open(file_path, 'r') as file:
                data = json.load(file)


        # Set recipe name at the heading
        recipe_name = data.get("name", ["Unknown Recipe"])[0]
        title_label.config(text=f"Recipe: {recipe_name}")
        
        # Extract ingredient and instruction data for the tables
        ingredient_data = format_ingredients(data)
        instruction_data = format_instructions(data)
        
        # Clear the existing table frames before adding new data
        clear_table(ingredients_frame)
        clear_table(instructions_frame)
        
        # Display the data in both tables
        display_ingredients_table(ingredient_data)
        display_instructions_table(instruction_data)
        # check_audio_files()
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Function to format the ingredients data into a table-like format
def format_ingredients(data):
    rows = []
    ingredients = data.get("Ingredients", [])
    
    # Column names: Name, Weight, and Action
    column_names = ['Name', 'Weight', 'Action','audio','audioI','audioP','audioQ','audioU','Image','Text']
    
    # Loop through the ingredients and extract the relevant fields
    for ingredient in ingredients:
        name = ingredient.get("title", "")
        weight = ingredient.get("weight", "")
        action = ingredient.get("app_audio", "")
        audio = ingredient.get("audio", "")
        audioI = ingredient.get("audioI", "")
        audioP = ingredient.get("audioP", "")
        audioQ = ingredient.get("audioQ", "")
        audioU = ingredient.get("audioU", "")
        Image = ingredient.get("image","")
        Text = ingredient.get("text","")
        rows.append([name, weight, action,audio,audioI,audioP,audioQ,audioU,Image,Text])
    
    # Include headers in the first row
    return [column_names] + rows

# Function to format the instructions data into a table-like format
def format_instructions(data):
    rows = []
    instructions = data.get("Instruction", [])
    
    # Column names for the instruction table
    column_names = ['Step', 'Procedure', 'Induction On Time', 'Induction Power', 
                    'Text', 'Weight', 'Duration (s)', 'Lid Status', 
                    'Wait Time (s)', 'Warm Time (s)', 'Stirrer', 
                    'Mag On Time', 'Mag Power', 'Action', 'Mag Serv', 'Pump','AudioI','AudioP','AudioQ','AudioU','skip','Ind_lid_con', 'threshold', 'Purge on']
    
    # Loop through the instructions and format the data
    for i, instruction in enumerate(instructions):
        step = f"Step {i + 1}"
        procedure = instruction.get("Audio", "")  # Fetch 'audio' as 'procedure'
        ind_lid_con = instruction.get("Indtime_lid_con","")
        ind_on_time = instruction.get("Induction_on_time", 0)
        ind_power = instruction.get("Induction_power", 0)
        mag_on_time = instruction.get("Magnetron_on_time", 0)
        mag_power = instruction.get("Magnetron_power", 0)
        text = instruction.get("Text", "")
        weight = instruction.get("Weight", "")
        duration = instruction.get("durationInSec", 0)
        lid_status = instruction.get("lid", "N/A")
        wait_time = instruction.get("wait_time", 0)
        warm_time = instruction.get("warm_time", 0)
        stirrer = instruction.get("stirrer_on", 0)
        action = instruction.get("app_audio", 0)
        mag_serv = instruction.get("mag_severity")
        pump = instruction.get("pump_on", 0)
        AudioI = instruction.get("audioI",0)
        AudioP = instruction.get("audioP",0)
        AudioQ = instruction.get("audioQ",0)
        AudioU = instruction.get("audioU",0)
        skip = instruction.get("skip",0)
        ind_lid_con = instruction.get("Indtime_lid_con","")   
        threshold = instruction.get("threshold","")   
        purge_on = instruction.get("purge_on","") 
        # Append row data
        rows.append([step, procedure,ind_on_time, ind_power, text, weight, 
                     duration, lid_status, wait_time, warm_time, stirrer, 
                     mag_on_time, mag_power, action, mag_serv, pump,AudioI,AudioP,AudioQ,AudioU,skip,ind_lid_con,threshold,purge_on])
    
    # Include headers in the first row
    return [column_names] + rows


# Function to clear a specific table frame
def clear_table(frame):
    for widget in frame.winfo_children():
        widget.destroy()
def add_ingredient():
    ingredient_data.append(["New Ingredient", "0", "","","","","0","","",""])  # Add a new ingredient row
    clear_table(ingredients_frame)  # Clear the current table
    display_ingredients_table(ingredient_data)  # Refresh the ingredients table

# Function to add a new instruction step
def add_instruction():
    # Determine the next step number
    next_step_number = len(instruction_data)  # Current length gives the next step number
    instruction_data.append([f"Step {next_step_number}", "", 0, 0, "", "0", 0, "N/A", 0, 0, 0, 0, 0, "", "", 0,"","","","","","","",""])  # Add a new instruction row
    clear_table(instructions_frame)  # Clear the current table
    display_instructions_table(instruction_data)  # Refresh the instructions table
  
# Function to display the ingredients table
def display_instructions_table(data):
    global selected_row, error_cells
    error_cells = check_for_errors(data, instructions_frame)
    
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            cell = tk.Frame(instructions_frame, relief="solid", borderwidth=1)
            cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
            
            if (i, j) in error_cells:
                bg_color = "red"
            elif i == selected_row:
                bg_color = highlight_color
            else:
                bg_color = default_color
            
            # Check if it's an audio column and the audio file is missing
            if i > 0 and j in [16, 17, 18, 19] and value and not audio_file_exists(value):
                bg_color = "red"
            
            underline = (j in [16, 17, 18, 19] and i > 0)
            
            label = tk.Label(cell, text=str(value), font=('Arial', 10, 'underline' if underline else ''),
                             bg=bg_color, anchor='center')
            label.pack(side='left', fill='both', expand=True)

            if j in [16, 17, 18, 19]:  # AudioI, AudioP, AudioQ, AudioU columns
              label.bind("<Button-1>", lambda event, r=i, c=j: on_instruction_audio_click(r, c))
            
            if i > 0:  # Skip the header
                label.bind("<Double-1>", lambda event, r=i, c=j: edit_cell(r, c, instruction_data, instructions_frame))
                
                # Detect long press (right-click hold) for selecting row
                label.bind("<ButtonPress-3>", lambda event, r=i: start_long_press(r, instructions_frame))
                label.bind("<ButtonRelease-3>", lambda event, r=i: end_long_press(r, instructions_frame))
            if j == 16:  # AudioI column
                label.bind("<Button-1>", lambda event, r=i, c=j: on_instruction_audio_click(r, c))
            elif j == 17:  # AudioP column
                label.bind("<Button-1>", lambda event, r=i, c=j: on_instruction_audio_click(r, c))
            elif j == 18:  # AudioQ column
                label.bind("<Button-1>", lambda event, r=i, c=j: on_instruction_audio_click(r, c))
            elif j == 19:  # AudioU column
                label.bind("<Button-1>", lambda event, r=i, c=j: on_instruction_audio_click(r, c))
            
    # Make the columns resize equally
    for j in range(len(data[0])):
        instructions_frame.grid_columnconfigure(j, weight=1)

def display_ingredients_table(data):
    global selected_row
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            cell = tk.Frame(ingredients_frame, relief="solid", borderwidth=1)
            cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
            
            bg_color = default_color if i != selected_row else highlight_color
            
            # Check if it's an audio column and the audio file is missing
            if i > 0 and j in [4, 5, 6, 7] and value and not audio_file_exists(value):
                bg_color = "red"
            
            underline = (j in [4, 5, 6, 7] and i > 0)
            
            label = tk.Label(cell, text=str(value), font=('Arial', 10, 'underline' if underline else ''),
                             bg=bg_color, anchor='center')
            label.pack(side='left', fill='both', expand=True)
            
            if j in [4, 5, 6, 7]:  # audio, audioI, audioP, audioQ, audioU columns
              label.bind("<Button-1>", lambda event, r=i, c=j: on_audio_click(r, c))

            if i > 0:  # Skip the header
                label.bind("<Double-1>", lambda event, r=i, c=j: edit_cell(r, c, ingredient_data, ingredients_frame))
                
                # Detect long press (right-click hold) for selecting row
            if j == 4:  # Index of the audioP column
                    label.bind("<Button-1>", lambda event, r=i, c=j: on_audio_click(r, c))
            elif j == 5:  # Index of the audioP column
               label.bind("<Button-1>", lambda event, r=i, c=j: on_audio_click(r, c))
            elif j == 6:  # Index of the audioQ column
               label.bind("<Button-1>", lambda event, r=i, c=j: on_audio_click(r, c))
            elif j == 7:  # Index of the audioU column
               label.bind("<Button-1>", lambda event, r=i, c=j: on_audio_click(r, c))    

    # Make the columns resize equally
    for j in range(len(data[0])):
        ingredients_frame.grid_columnconfigure(j, weight=1)



def start_long_press(row, frame):
    global long_press_active
    long_press_active = True
    root.after(long_press_duration, lambda: select_row_long_press(row, frame))  # Set a timer for the long press

# Function to end long press detection
def end_long_press(row, frame):
    global long_press_active
    long_press_active = False  # Reset the long press active state

# Function to handle row selection on long press
def select_row_long_press(row, frame):
    global selected_row, long_press_active
    if long_press_active:  # Ensure the long press is still active when timer expires
        if selected_row == row:
            selected_row = None  # Deselect the row if it was already selected
        else:
            selected_row = row  # Select the new row
        clear_table(frame)  # Clear the table and re-draw to update the highlight
        if frame == ingredients_frame:
            display_ingredients_table(ingredient_data)
        else:
            display_instructions_table(instruction_data)

# Function to clear the table before refreshing
def clear_table(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def update_step_numbers(data_table):
    # Reassign step numbers with the "Step" prefix
    for i in range(1, len(data_table)):  # Skip header (index 0)
        data_table[i][0] = f"Step {i}"  # Assuming the step number is in the first column (index 0)

def move_row_up(data_table, frame):
    global selected_row
    if selected_row is None or selected_row == 1:  # Ensure the header row (index 0) is not selected
        return
    
    # Swap the selected row with the one above it
    data_table[selected_row], data_table[selected_row - 1] = data_table[selected_row - 1], data_table[selected_row]
    
    # Update the selected row index to reflect the new position
    selected_row -= 1
    
    # Update step numbers after the move
    update_step_numbers(data_table)
    
    # Clear and refresh the table to reflect the changes
    clear_table(frame)
    if frame == ingredients_frame:
        display_ingredients_table(data_table)
    else:
        display_instructions_table(data_table)

# Function to move a row down
def move_row_down(data_table, frame):
    global selected_row
    if selected_row is None or selected_row == len(data_table) - 1:  # Ensure it's not the last row
        return
    
    # Swap the selected row with the one below it
    data_table[selected_row], data_table[selected_row + 1] = data_table[selected_row + 1], data_table[selected_row]
    
    # Update the selected row index to reflect the new position
    selected_row += 1
    
    # Update step numbers after the move
    update_step_numbers(data_table)
    
    # Clear and refresh the table to reflect the changes
    clear_table(frame)
    if frame == ingredients_frame:
        display_ingredients_table(data_table)
    else:
        display_instructions_table(data_table)


# Modify the display functions to detect row selection

def edit_cell(row, col, data_table, frame):
    current_value = data_table[row][col]

    # Create an entry widget for inline editing
    entry = tk.Entry(frame, font=('Arial', 10))
    entry.insert(0, current_value)
    entry.grid(row=row, column=col, sticky="nsew")
    
    def save_value():
        new_value = entry.get()
        old_value = data_table[row][col]
        
        if frame == instructions_frame and col == 6:  # Duration column
            try:
                duration_seconds = int(new_value)

                if duration_seconds < 0 or duration_seconds > 6000:
                    messagebox.showerror("Error", "Duration must be between 0 and 6000 seconds.")
                    return
                # Update duration
                data_table[row][col] = str(duration_seconds)
                
                # Convert duration to minutes and seconds for audioU
                if duration_seconds >= 60:
                    minutes = duration_seconds // 60
                    seconds = duration_seconds % 60
                    if seconds == 0:
                        audioU_text = f"{minutes}Minute"
                    else:
                        audioU_text = f"{minutes}Minute {seconds}Seconds"
                else:
                    audioU_text = f"{duration_seconds}Seconds"
                
                # Update audioU column (index 19)
                data_table[row][19] = audioU_text
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for duration")
                return
            
        if frame == ingredients_frame:
            if col == 0:  # Name
                update_name(old_value, new_value, ingredients_frame)
            elif col == 1:  # Weight
                update_weight(data_table[row][0], new_value, ingredients_frame)
            elif col in [2, 3, 5]:  # Action, audio, audioP
                update_action_audio(row, col, new_value, ingredients_frame)
        
        elif frame == instructions_frame:
            if col == 4:  # Text
                update_name(old_value, new_value, instructions_frame)
            elif col == 5:  # Weight
                update_weight(data_table[row][4], new_value, instructions_frame)
            elif col in [1, 13, 17]:  # Procedure, Action, audioP
                update_action_audio(row, col, new_value, instructions_frame)
            
            # Apply validation for instruction table
            if not validate_instruction_input(col, new_value):
                entry.delete(0, tk.END)
                entry.insert(0, old_value)
                return

        data_table[row][col] = new_value
        
        # Clear and refresh both tables
        clear_table(ingredients_frame)
        clear_table(instructions_frame)
        display_ingredients_table(ingredient_data)
        display_instructions_table(instruction_data)

        # Remove the entry widget
        entry.destroy()

    # Bind the return key to save the new value
    entry.bind("<Return>", lambda event: save_value())
    entry.bind("<FocusOut>", lambda event: save_value())
    entry.focus_set()

def validate_instruction_input(col, value):
    value_str = str(value).strip()
    if col == 20 and not validate_skip(value_str):
        messagebox.showerror("Invalid Value", "The 'Skip' column can only accept 'true', 'false', or be blank.")
        return False
    if col == 10 and not validate_Stirrer(value_str):
        messagebox.showerror("Invalid Value", "The 'Stirrer' column can only accept values from '0 to 4' or be blank.")
        return False
    if col == 7 and not validate_Lid(value_str):
        messagebox.showerror("Invalid Value", "The 'Lid_status' column can only accept 'open', 'close' or be blank.")
        return False
    if col == 3 and not validate_induction(value_str):
        messagebox.showerror("Invalid Value", "The 'Induction' column can only accept value in terms 10x or be blank.")
        return False
    if col == 12 and not validate_magnetron(value_str):
        messagebox.showerror("Invalid Value", "The 'Magnetron' column can only accept value in terms of 20x or be blank.")
        return False
    return True

def validate_skip(value):
    return value.lower() in ["true", "false", ""]

def validate_Stirrer(value):
    return value in ["0", "1", "2", "3", "4", ""]

def validate_Lid(value):
    return value.lower() in ["open", "close", ""]

def validate_induction(value):
    return value in ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", ""]

def validate_magnetron(value):
    return value in ["0", "20", "40", "60", "80", "100", ""]

def update_name(old_name, new_name, frame):
    if frame == ingredients_frame:
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == old_name:
                ingredient[0] = new_name  # Name
                ingredient[2] = update_middle_word(ingredient[2], new_name)  # Action
                ingredient[4] = new_name  # AudioI
        
        for instruction in instruction_data[1:]:
            if instruction[4] == old_name:
                instruction[4] = new_name  # Text
                instruction[13] = update_last_word(instruction[13], new_name)  # Action
                instruction[16] = new_name  # AudioI
    
    elif frame == instructions_frame:
        for instruction in instruction_data[1:]:
            if instruction[4] == old_name:
                instruction[4] = new_name  # Text
                instruction[13] = update_last_word(instruction[13], new_name)  # Action
                instruction[16] = new_name  # AudioI
        
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == old_name:
                ingredient[0] = new_name  # Name
                ingredient[2] = update_middle_word(ingredient[2], new_name)  # Action
                ingredient[4] = new_name  # AudioI

def update_middle_word(action, new_word):
    words = action.split()
    if len(words) >= 3:
        words[1] = new_word
    return ' '.join(words)

def update_weight(item_name, new_weight, frame):
    weight_parts = new_weight.split()
    numeric_weight = weight_parts[0] if weight_parts else "0"
    unit = weight_parts[1] if len(weight_parts) > 1 else ""

    if frame == ingredients_frame:
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == item_name:
                ingredient[1] = new_weight  # Weight
                ingredient[2] = update_last_two_words(ingredient[2], numeric_weight, unit)  # Action
                ingredient[6] = numeric_weight  # AudioQ
                ingredient[7] = unit  # AudioU
        
        for instruction in instruction_data[1:]:
            if instruction[4] == item_name:
                instruction[5] = new_weight  # Weight
                instruction[13] = update_last_two_words(instruction[13], numeric_weight, unit)  # Action
                instruction[18] = numeric_weight  # AudioQ
                
    
    elif frame == instructions_frame:
        for instruction in instruction_data[1:]:
            if instruction[4] == item_name:
                instruction[5] = new_weight  # Weight
                instruction[13] = update_last_two_words(instruction[13], numeric_weight, unit)  # Action
                instruction[18] = numeric_weight  # AudioQ
                
        
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == item_name:
                ingredient[1] = new_weight  # Weight
                ingredient[2] = update_last_two_words(ingredient[2], numeric_weight, unit)  # Action
                ingredient[6] = numeric_weight  # AudioQ
                ingredient[7] = unit  # AudioU

def update_last_two_words(action, numeric_weight, unit):
    words = action.split()
    if len(words) >= 3:
        words[-2] = numeric_weight
        words[-1] = unit
    return ' '.join(words)
def update_last_word(action, new_word):
    words = action.split()
    if words:
        words[-1] = new_word
    return ' '.join(words)
def update_action_audio(row, col, new_value, frame):
    if frame == ingredients_frame:
        if col == 2:  # Action
            words = new_value.split()
            if len(words) >= 3:
                ingredient_data[row][3] = words[0]  # audio
                ingredient_data[row][0] = words[1]  # Name
                ingredient_data[row][5] = words[0]  # audioP
                update_name(ingredient_data[row][0], words[1], ingredients_frame)
        elif col in [3, 5]:  # audio or audioP
            ingredient_data[row][3] = new_value  # audio
            ingredient_data[row][5] = new_value  # audioP
            action_words = ingredient_data[row][2].split()
            if action_words:
                action_words[0] = new_value
                ingredient_data[row][2] = ' '.join(action_words)
    
    elif frame == instructions_frame:
        if col == 13:  # Action
            words = new_value.split()
            if words:
                instruction_data[row][1] = words[0]  # Procedure
                instruction_data[row][17] = words[0]  # audioP
                if len(words) > 1:
                    instruction_data[row][4] = words[-1]  # Text
                    instruction_data[row][16] = words[-1]  # AudioI
                    update_name(instruction_data[row][4], words[-1], instructions_frame)
        elif col in [1, 17]:  # Procedure or audioP
            instruction_data[row][1] = new_value  # Procedure
            instruction_data[row][17] = new_value  # audioP
            action_words = instruction_data[row][13].split()
            if action_words:
                action_words[0] = new_value
                instruction_data[row][13] = ' '.join(action_words)


# Function to save the updated data back to the JSON file
def save_json():
    global data, ingredient_data, instruction_data
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    
    if not file_path:
        return
    
    try:
        # Initialize the updated data structure
        updated_data = {
            "name": ["Unknown Recipe"],
            "audio1": [""],
            "audio2": [""],
            "category": "0",
            "description": "",
            "difficulty": "Easy",
            "id": 0,
            "imageUrl": "",
            "isSelected": False,
            "subCategories": "",
            "tags": "",
            "Ingredients": [],
            "Instruction": []
        }

        # Update recipe metadata if 'data' exists
        if isinstance(data, dict):
            updated_data["name"] = [data.get("name", ["Unknown Recipe"])[0]] if isinstance(data.get("name"), list) else [data.get("name", "Unknown Recipe")]
            updated_data["audio1"] = data.get("audio1", [""])
            updated_data["audio2"] = data.get("audio2", [""])
            updated_data["category"] = str(data.get("category", "0"))
            updated_data["description"] = str(data.get("description", ""))
            updated_data["difficulty"] = str(data.get("difficulty", "Easy"))
            updated_data["id"] = int(data.get("id", 0))
            updated_data["imageUrl"] = str(data.get("imageUrl", ""))
            updated_data["isSelected"] = bool(data.get("isSelected", False))
            updated_data["subCategories"] = str(data.get("subCategories", ""))
            updated_data["tags"] = str(data.get("tags", ""))

        # Process Ingredients
        current_id = 1  # Keep track of actual ID for valid ingredients
        if isinstance(ingredient_data, list) and len(ingredient_data) > 1:
            for i in range(1, len(ingredient_data)):  # Skip header row
                row = ingredient_data[i]
                
                # Skip if the row is invalid or name is empty or "New Ingredient"
                if not isinstance(row, list) or len(row) == 0:
                    continue
                    
                ingredient_name = str(row[0]).strip()
                if not ingredient_name or ingredient_name == "New Ingredient":
                    continue
                
                ingredient = {
                    "app_audio": "",
                    "audio": "",
                    "audioI": "",
                    "audioP": "",
                    "audioQ": "",
                    "audioU": "",
                    "id": current_id,  # Use current_id instead of i
                    "image": "",
                    "text": "",
                    "title": "",
                    "weight": ""
                }
                
                ingredient["title"] = ingredient_name
                ingredient["weight"] = str(row[1]) if len(row) > 1 else ""
                ingredient["app_audio"] = str(row[2]) if len(row) > 2 else ""
                ingredient["audio"] = str(row[3]) if len(row) > 3 else ""
                ingredient["audioI"] = str(row[4]) if len(row) > 4 else ""
                ingredient["audioP"] = str(row[5]) if len(row) > 5 else ""
                
                # Safely split weight
                weight_parts = ingredient["weight"].split()
                ingredient["audioQ"] = weight_parts[0] if len(weight_parts) > 0 else ""
                ingredient["audioU"] = weight_parts[1] if len(weight_parts) > 1 else ""
                
                ingredient["image"] = str(row[8]) if len(row) > 8 else ""
                ingredient["text"] = str(row[9]) if len(row) > 9 else ""
                
                updated_data["Ingredients"].append(ingredient)
                current_id += 1

        # Process Instructions
        current_id = 1  # Reset current_id for instructions
        if isinstance(instruction_data, list) and len(instruction_data) > 1:
            for i in range(1, len(instruction_data)):  # Skip header row
                row = instruction_data[i]
                
                # Skip if row doesn't exist or Text column is empty
                if not isinstance(row, list) or len(row) <= 4 or not row[4].strip():
                    continue
                
                instruction = {
                    "Audio": "",
                    "Indtime_lid_con": "",
                    "Induction_on_time": "0",
                    "Induction_power": "0",
                    "Magnetron_on_time": "0",
                    "Magnetron_power": "0",
                    "Text": "",
                    "Weight": "",
                    "app_audio": "",
                    "audioI": "",
                    "audioP": "",
                    "audioQ": "",
                    "audioU": "",
                    "durationInSec": 0,
                    "id": current_id,  # Use current_id instead of i
                    "image": "",
                    "lid": "",
                    "mag_severity": "",
                    "pump_on": "0",
                    "skip": "false",
                    "stirrer_on": "0",
                    "wait_time": "0",
                    "warm_time": "0",
                    "threshold": "0",
                    "purge_on": "0"
                }
                
                field_mapping = {
                    1: "Audio", 2: "Induction_on_time", 3: "Induction_power", 4: "Text", 5: "Weight",
                    6: "durationInSec", 7: "lid", 8: "wait_time", 9: "warm_time", 10: "stirrer_on",
                    11: "Magnetron_on_time", 12: "Magnetron_power", 13: "app_audio", 14: "mag_severity",
                    15: "pump_on", 16: "audioI", 17: "audioP", 18: "audioQ", 19: "audioU", 20: "skip",
                    21: "Indtime_lid_con", 22: "threshold", 23: "purge_on"
                }
                
                for idx, field in field_mapping.items():
                    if idx < len(row):
                        if field == "durationInSec":
                            instruction[field] = int(row[idx]) if str(row[idx]).isdigit() else 0
                        else:
                            instruction[field] = str(row[idx])
                
                updated_data["Instruction"].append(instruction)
                current_id += 1

        # Write the updated data to the JSON file
        with open(file_path, 'w') as file:
            json.dump(updated_data, file, indent=2)

        messagebox.showinfo("Success", "Data saved successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving: {str(e)}")
        # Print the full error traceback for debugging
        import traceback
        traceback.print_exc()

def prt_action(part_name):
    print(f"{part_name} button clicked")
def new_recipe():
    global ingredient_data, instruction_data, data, selected_row, error_cells

    # Reset selection and errors
    selected_row = None
    error_cells = []

    # Initialize default recipe metadata
    data = {
        "name": ["New Recipe"],
        "Ingredients": [
            {
                "title": "Water",
                "weight": "500 ml",
                "app_audio": "add water 500 ml",
                "audio": "add",
                "audioI": "Water",
                "audioP": "add",
                "audioQ": "500",
                "audioU": "ml",
                "image": "",
                "text": "Add water"
            },
            {
                "title": "Oil",
                "weight": "30 ml",
                "app_audio": "add oil 30 ml",
                "audio": "add",
                "audioI": "Oil",
                "audioP": "add",
                "audioQ": "30",
                "audioU": "ml",
                "image": "",
                "text": "Add oil"
            },
            {
                "title": "Salt",
                "weight": "10 g",
                "app_audio": "add salt 10 g",
                "audio": "add",
                "audioI": "Salt",
                "audioP": "add",
                "audioQ": "10",
                "audioU": "g",
                "image": "",
                "text": "Add salt"
            }
        ],
        "Instruction": [
            {
                "Audio": "heat",
                "Induction_on_time": "120",
                "Induction_power": "80",
                "Text": "Water",
                "Weight": "500 ml",
                "durationInSec": "120",
                "lid": "close",
                "wait_time": "0",
                "warm_time": "0",
                "stirrer_on": "1",
                "Magnetron_on_time": "0",
                "Magnetron_power": "0",
                "app_audio": "heat water 500 ml",
                "mag_severity": "",
                "pump_on": "0",
                "audioI": "Water",
                "audioP": "heat",
                "audioQ": "500",
                "audioU": "2Minutes",
                "skip": "false",
                "Indtime_lid_con": "120",
                "threshold": "0",
                "purge_on": "0"
            },
            {
                "Audio": "add",
                "Induction_on_time": "0",
                "Induction_power": "0",
                "Text": "Oil",
                "Weight": "30 ml",
                "durationInSec": "30",
                "lid": "open",
                "wait_time": "30",
                "warm_time": "0",
                "stirrer_on": "0",
                "Magnetron_on_time": "0",
                "Magnetron_power": "0",
                "app_audio": "add oil 30 ml",
                "mag_severity": "",
                "pump_on": "0",
                "audioI": "Oil",
                "audioP": "add",
                "audioQ": "30",
                "audioU": "30Seconds",
                "skip": "false",
                "Indtime_lid_con": "",
                "threshold": "0",
                "purge_on": "0"
            },
            {
                "Audio": "stir",
                "Induction_on_time": "60",
                "Induction_power": "40",
                "Text": "Salt",
                "Weight": "",
                "durationInSec": "60",
                "lid": "close",
                "wait_time": "0",
                "warm_time": "0", # Changed from "30" to "0"
                "stirrer_on": "1",
                "Magnetron_on_time": "30",
                "Magnetron_power": "30",
                "app_audio": "stir mixture",
                "mag_severity": "medium",
                "pump_on": "1",
                "audioI": "Mixture",
                "audioP": "stir",
                "audioQ": "",
                "audioU": "1Minute",
                "skip": "false",
                "Indtime_lid_con": "60",
                "threshold": "0",
                "purge_on": "0"
            }
        ]
    }

    # Format the ingredients data into a table-like format
    ingredient_data = format_ingredients(data)

    # Format the instructions data into a table-like format
    instruction_data = format_instructions(data)

    # Update the recipe name in the title
    title_label.config(text="Recipe: New Recipe")

    # Clear existing tables
    for widget in ingredients_frame.winfo_children():
        widget.destroy()
    for widget in instructions_frame.winfo_children():
        widget.destroy()

    # Create new tables with default data
    display_ingredients_table(ingredient_data)
    display_instructions_table(instruction_data)
    for i in range(1, len(ingredient_data)):
        for j in range(len(ingredient_data[i])):
            cell = ingredients_frame.grid_slaves(row=i, column=j)
            if cell:
                cell[0].bind('<Double-Button-1>', 
                    lambda e, row=i, col=j: edit_cell(row, col, ingredient_data, ingredients_frame))

    # Add cell editing functionality to instructions table
    for i in range(1, len(instruction_data)):
        for j in range(len(instruction_data[i])):
            cell = instructions_frame.grid_slaves(row=i, column=j)
            if cell:
                cell[0].bind('<Double-Button-1>', 
                    lambda e, row=i, col=j: edit_cell(row, col, instruction_data, instructions_frame))
    # Enable all buttons
    save_button.config(state='normal')
    add_ingredient_button.config(state='normal')
    add_step_button.config(state='normal')
    move_up_button.config(state='normal')
    move_down_button.config(state='normal')
    
def load_text_files():
    # List all text files in the specified directory
    return [f for f in os.listdir(SELECT_FOLDER_PATHS) if f.endswith('.txt')]

def select_recipe(event=None):  # Accept an optional event argument
    # Logic for selecting a recipe
    title_label.config(text="Recipe: Selected Recipe")
    print("Select Recipe button clicked")
    
    # Load and display text files in the combo box
    text_files = load_text_files()
    if text_files:
        recipe_combobox['values'] = text_files  # Populate the combo box with text files
        recipe_combobox.pack(pady=10)  # Show the combo box
    else:
        print("No text files available.")

def load_file(event=None):
    global ingredient_data, instruction_data  # Declare ingredient_data and instruction_data as global
    
    selected_file = recipe_combobox.get()  # Get the selected file from the combo box
    if selected_file:
        file_path = os.path.join(SELECT_FOLDER_PATHS, selected_file)
        
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                
                # Set recipe name at the heading
                recipe_name = data.get("name", ["Unknown Recipe"])[0]
                title_label.config(text=f"Recipe: {recipe_name}")
                
                # Extract ingredient and instruction data for the tables
                ingredient_data = format_ingredients(data)
                instruction_data = format_instructions(data)
                
                # Clear the existing table frames before adding new data
                clear_table(ingredients_frame)
                clear_table(instructions_frame)
                
                # Display the data in both tables
                display_ingredients_table(ingredient_data)
                display_instructions_table(instruction_data)
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    hide_combobox()  # Hide the combo box after loading

def hide_combobox():
    recipe_combobox.pack_forget()  # Hide the combo box

root = tk.Tk()
root.title("Recipe Editor")

# Create a frame to hold the canvas and scrollbars
container = tk.Frame(root)
container.pack(fill='both', expand=True)

# Create a canvas that will hold all the content with scrollbars
main_canvas = tk.Canvas(container)
main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Add vertical and horizontal scrollbars for the entire window
y_scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=main_canvas.yview)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

x_scrollbar = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=main_canvas.xview)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

main_canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)

# Create a frame inside the canvas to hold all the content
content_frame = tk.Frame(main_canvas)

# Add the content_frame to the canvas window
main_canvas.create_window((0, 0), window=content_frame, anchor='nw')

# Ensure that the scroll region is updated when the content changes size
def on_frame_configure(event):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))

content_frame.bind("<Configure>", on_frame_configure)

# Create a frame for the buttons at the top left
button_frame = tk.Frame(content_frame)
button_frame.pack(side=tk.TOP, anchor='nw', padx=10, pady=10)

# New Recipe button
new_recipe_button = tk.Button(button_frame, text="New Recipe", command=new_recipe)
new_recipe_button.pack(side=tk.LEFT, padx=5)

# Select Recipe button
select_button = tk.Button(button_frame, text="Select the Recipe", command=select_recipe)
select_button.pack(side=tk.LEFT, padx=5)

# Create a combo box for displaying text files (initially hidden)
recipe_combobox = ttk.Combobox(root)
recipe_combobox.pack_forget()  # Hide the combo box initially

# Bind the combo box selection to load the file directly
recipe_combobox.bind("<<ComboboxSelected>>", load_file)

# Create a button to load the selected text file (initially hidden)
load_button = tk.Button(root, text="Load File", command=load_file)
load_button.pack_forget()  # Hide the load button initially

# Create a button to load the selected text file (initially hidden)
load_button = tk.Button(root, text="Load File", command=load_file)
load_button.pack_forget()  # Hide the load button initially

# Set up the title frame for "on2cook"
title_frame = tk.Frame(content_frame)
title_frame.pack(pady=10)

# Title labels
on_label = tk.Label(title_frame, text="on", font=('Arial', 24), fg='red')
on_label.pack(side=tk.LEFT)

two_cook_label = tk.Label(title_frame, text="2cook", font=('Arial', 24), fg='black')
two_cook_label.pack(side=tk.LEFT)

# Label for displaying the recipe name
recipe_name = "Your Recipe Name"  # Placeholder for the recipe name
title_label = tk.Label(content_frame, text=f"Recipe: {recipe_name}", font=('Arial', 16), anchor='center')
title_label.pack(pady=10, anchor='center')  # Center the recipe name

# Ingredients section
ingredients_label = tk.Label(content_frame, text="Ingredients", font=('Arial', 14, 'bold'), anchor='center')
ingredients_label.pack(pady=5, anchor='center')  # Center the ingredients label

ingredients_frame = tk.Frame(content_frame)
ingredients_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

# Instructions section
instructions_label = tk.Label(content_frame, text="Instructions", font=('Arial', 14, 'bold'), anchor='center')
instructions_label.pack(pady=5, anchor='center')  # Center the instructions label

instructions_frame = tk.Frame(content_frame)
instructions_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)



# Create a separate frame for buttons at the bottom of the main window
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Button frame inside the bottom frame
button_frame = tk.Frame(bottom_frame)
button_frame.pack(pady=10)

# Load button
load_button = tk.Button(button_frame, text="Load Recipe", command=load_json)
load_button.pack(side='left', padx=5)

# Save button
save_button = tk.Button(button_frame, text="Save Recipe", command=save_json)
save_button.pack(side='left', padx=5)

# Add ingredient button
add_ingredient_button = tk.Button(button_frame, text="Add Ingredient", command=add_ingredient)
add_ingredient_button.pack(side='left', padx=5)

# Add step button
add_step_button = tk.Button(button_frame, text="Add Step", command=add_instruction)
add_step_button.pack(side='left', padx=5)

# Move up button
move_up_button = tk.Button(button_frame, text="Move Up", command=lambda: move_row_up(instruction_data, instructions_frame))
move_up_button.pack(side='left', padx=5)

# Move down button
move_down_button = tk.Button(button_frame, text="Move Down", command=lambda: move_row_down(instruction_data, instructions_frame))
move_down_button.pack(side='left', padx=5)

# PRT buttons
prt1_button = tk.Button(button_frame, text="prt1", command=lambda: prt_action("prt1"))
prt1_button.pack(side='left', padx=5)

prt2_button = tk.Button(button_frame, text="prt2", command=lambda: prt_action("prt2"))
prt2_button.pack(side='left', padx=5)

prt3_button = tk.Button(button_frame, text="prt3", command=lambda: prt_action("prt3"))
prt3_button.pack(side='left', padx=5)

prt4_button = tk.Button(button_frame, text="prt4", command=lambda: prt_action("prt 4"))
prt4_button.pack(side='left', padx=5)

# Start the tkinter event loop
root.mainloop()