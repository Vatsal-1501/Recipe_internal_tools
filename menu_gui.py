import json
import tkinter as tk
from tkinter import filedialog, messagebox ,ttk
import pygame 
import os
import threading
import time
import io
import zipfile

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

def check_for_errors(data_table, frame):
    error_cells = []
    for i, row in enumerate(data_table):
        if i == 0:  # Skip header row
            continue
        for j, value in enumerate(row):
            is_error = False
            if frame == instructions_frame and j == 10:  # Stirrer column
                if value not in ["0", "1", "2", "3", "4", ""]:
                    is_error = True
            elif frame == instructions_frame and j == 20:  # Skip column
                if value.lower() not in ["true", "false", ""]:
                    is_error = True
            elif frame == instructions_frame and j == 7:  # Lid status column
                if value.lower() not in ["open", "close", ""]:
                    is_error = True
            elif frame == instructions_frame and j== 3:
                if value.lower() not in ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", ""]:
                    is_error = True

            elif frame == instructions_frame and j== 12:
                if value.lower() not in ["0", "20", "40", "60", "80", "100", ""]:
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
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Function to format the ingredients data into a table-like format
def format_ingredients(data):
    rows = []
    ingredients = data.get("Ingredients", [])
    
    # Column names: Name, Weight, and Action
    column_names = ['Name', 'Weight', 'Action','audio','audioI','audioP','audioQ','audioU']
    
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
        rows.append([name, weight, action,audio,audioI,audioP,audioQ,audioU])
    
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
                    'Mag On Time', 'Mag Power', 'Action', 'Mag Serv', 'Pump','AudioI','AudioP','AudioQ','AudioU','skip']
    
    # Loop through the instructions and format the data
    for i, instruction in enumerate(instructions):
        step = f"Step {i + 1}"
        procedure = instruction.get("Audio", "")  # Fetch 'audio' as 'procedure'
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
              
        # Append row data
        rows.append([step, procedure, ind_on_time, ind_power, text, weight, 
                     duration, lid_status, wait_time, warm_time, stirrer, 
                     mag_on_time, mag_power, action, mag_serv, pump,AudioI,AudioP,AudioQ,AudioU,skip])
    
    # Include headers in the first row
    return [column_names] + rows


# Function to clear a specific table frame
def clear_table(frame):
    for widget in frame.winfo_children():
        widget.destroy()
def add_ingredient():
    ingredient_data.append(["New Ingredient", "0", "","","","","0",""])  # Add a new ingredient row
    clear_table(ingredients_frame)  # Clear the current table
    display_ingredients_table(ingredient_data)  # Refresh the ingredients table

# Function to add a new instruction step
def add_instruction():
    # Determine the next step number
    next_step_number = len(instruction_data)  # Current length gives the next step number
    instruction_data.append([f"Step {next_step_number}", "", 0, 0, "", "0", 0, "N/A", 0, 0, 0, 0, 0, "", "", 0,"","","","",""])  # Add a new instruction row
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
            
            # Determine if the cell should be underlined (audio-related columns)
            underline = (j in [16, 17, 18, 19] and i > 0)  # AudioI, AudioP, AudioQ, AudioU columns
            
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
            cell = tk.Frame(ingredients_frame, bg=default_color if i != selected_row else highlight_color, relief="solid", borderwidth=1)
            cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)

            
            # Determine if the cell should be underlined (audio-related columns)
            underline = (j in [4, 5, 6, 7] and i > 0)  # audio, audioI, audioP, audioQ, audioU columns
            
            label = tk.Label(cell, text=str(value), font=('Arial', 10, 'underline' if underline else ''),
                             bg=default_color if i != selected_row else highlight_color, anchor='center')
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
def update_duration_and_audioU(row, new_duration):
   
    try:
        # Convert the new duration to an integer
        duration_seconds = int(new_duration)

        # Update the duration column
        duration_str = str(duration_seconds)
        instruction_data[row][6] = duration_str  # Assuming duration is in the 6th column

        # Update the audioU column based on duration
        if duration_seconds >= 60:
            minutes = duration_seconds // 60
            seconds_remainder = duration_seconds % 60
            if seconds_remainder == 0:
                audioU_str = f"{minutes}Minute"
            else:
                audioU_str = f"{minutes}Minute {seconds_remainder}Seconds"
        else:
            audioU_str = f"{duration_seconds}Seconds"

        instruction_data[row][19] = audioU_str  # Update audioU column (assuming it's in the 19th column)

        # Refresh the instruction table to display the updated data
        clear_table(instructions_frame)
        display_instructions_table(instruction_data)
    
    except ValueError:
        print("Invalid duration value entered!")
    except IndexError:
        print("Row index out of bounds or columns missing!")



def edit_cell(row, col, data_table, frame):
    current_value = data_table[row][col]

    # Create an entry widget for inline editing
    entry = tk.Entry(frame, font=('Arial', 10))
    entry.insert(0, current_value)
    entry.grid(row=row, column=col, sticky="nsew")

    # Define validation functions as previously
    def validate_skip(value):
        return value.lower() in ["true", "false", ""]

    def validate_Stirrer(value):
        return value.lower() in ["0", "1", "2", "3", "4", ""]

    def validate_Lid(value):
        return value.lower() in ["close", "open", ""]

    def validate_induction(value):
        return value.lower() in ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", ""]

    def validate_magnetron(value):
        return value.lower() in ["0", "20", "40", "60", "80", "100"]

    # Define save function to update the value and clear the entry
    def save_value():
        new_value = entry.get()
        old_value = data_table[row][col]
        data_table[row][col] = new_value
        if frame == instructions_frame and col == 6:  # Assuming duration is in column 6
            try:
                duration = int(new_value)
                if duration < 0 or duration > 5999:  # 99 minutes 59 seconds
                    raise ValueError("Duration must be between 0 and 5999 seconds")
                
                # Update duration
                data_table[row][col] = str(duration)
                
                # Update AudioU (assuming it's in column 7)
                if duration < 60:
                    audio_u = f"{duration}Second"
                else:
                    minutes = duration // 60
                    seconds = duration % 60
                    if seconds == 0:
                        audio_u = f"{minutes}Minute"
                    else:
                        audio_u = f"{minutes}Minute{seconds}Second"
                
                data_table[row][19] = audio_u
            except ValueError as e:
                messagebox.showerror("Invalid Input", str(e))
                return
        else:
            data_table[row][col] = new_value
        
        # Apply validation if this is the instruction table
    
        if frame == instructions_frame:
            if col == 20:  
                if not validate_skip(new_value):
                    messagebox.showerror("Invalid Value", "The 'Skip' column can only accept 'true', 'false', or be blank.")
                    return  # Do not save if validation fails
            if col == 10:  
                if not validate_Stirrer(new_value):
                    messagebox.showerror("Invalid Value", "The 'Stirrer' column can only accept values from '0 to 4' or be blank.")
                    return  # Do not save if validation fails
            if col == 7:  
                if not validate_Lid(new_value):
                    messagebox.showerror("Invalid Value", "The 'Lid_status' column can only accept 'open', 'close' or be blank.")
                    return  # Do not save if validation fails
            if col == 3: 
                if not validate_induction(new_value):
                    messagebox.showerror("Invalid Value", "The 'Induction' column can only accept value in terms 10x or be blank.")
                    return  # Do not save if validation fails
            if col == 12:  
                if not validate_magnetron(new_value):
                    messagebox.showerror("Invalid Value", "The 'Magnetron' column can only accept value in terms of 20x or be blank.")
                    return  # Do not save if validation fails
        
        # Update corresponding weight in the opposite table if the edited column is weight
        if frame == ingredients_frame:
            if col == 0:  # Name in Ingredients
                update_name_in_instructions(old_value, new_value)
                # Sync Name, Action middle word, and AudioI
                sync_ingredient_columns(row, new_value, data_table)
            elif col == 1:  # Weight in Ingredients
                update_weight_in_instructions(data_table[row][0], new_value)
            elif col in [3, 5]:  # audio or audioI column
                data_table[row][3] = new_value  # Update audio
                data_table[row][5] = new_value  # Update audioI
                
                # Update the first word of the action column
                action_parts = data_table[row][2].split()
                if len(action_parts) >= 3:
                    action_parts[0] = new_value
                    data_table[row][2] = ' '.join(action_parts)
                else:
                    # If action doesn't have enough parts, just prepend the new value
                    data_table[row][2] = f"{new_value} {data_table[row][2]}"

            elif col == 2:  # action column
                action_parts = new_value.split()
                if len(action_parts) >= 3:
                    data_table[row][0] = action_parts[1]  # Update Name
                    data_table[row][3] = action_parts[0]  # Update audio
                    data_table[row][5] = action_parts[1]  # Update audioI
                elif len(action_parts) >= 1:
                    data_table[row][3] = action_parts[0]  # Update audio
                    data_table[row][5] = action_parts[0]  # Update audioI
        
        elif frame == instructions_frame:
            if col == 4:  # Text in Instructions
                update_name_in_ingredients(old_value, new_value)
            elif col == 5:  # Weight in Instructions
                update_weight_in_ingredients(data_table[row][4], new_value)
            if col in [1, 17]:  # procedure or AudioP column
                print("Syncing procedure/AudioP in instructions")
                data_table[row][1] = new_value  # Update procedure
                data_table[row][17] = new_value  # Update AudioP
                
                # Update the first word of the action column
                action_parts = data_table[row][13].split()
                if action_parts:
                    action_parts[0] = new_value
                    data_table[row][13] = ' '.join(action_parts)
                else:
                    data_table[row][13] = new_value
                print(f"Updated action to: {data_table[row][13]}")

            elif col == 13:  # action column
                print("Syncing action in instructions")
                action_parts = new_value.split()
                if action_parts:
                    first_word = action_parts[0]
                    data_table[row][1] = first_word  # Update procedure
                    data_table[row][17] = first_word  # Update AudioP
                print(f"Updated procedure to: {data_table[row][1]}, AudioP to: {data_table[row][17]}")
        # Clear the current table and refresh both tables
        clear_table(ingredients_frame)
        clear_table(instructions_frame)
        display_ingredients_table(ingredient_data)
        display_instructions_table(instruction_data)

    # Bind the return key to save the new value
    entry.bind("<Return>", lambda event: save_value())
    entry.focus_set()  # Focus on the entry widget
# Function to update the name in the instructions table
def sync_ingredient_columns(row, new_value, data_table):
    # Update Name
    data_table[row][0] = new_value
    
    # Update middle word of Action
    action_parts = data_table[row][2].split()
    if len(action_parts) >= 3:
        action_parts[1] = new_value
        data_table[row][2] = ' '.join(action_parts)
    else:
        # If action doesn't have enough parts, just append the new value
        data_table[row][2] += f" {new_value}"
    
    # Update AudioI
    data_table[row][5] = new_value
def update_name_in_instructions(old_name, new_name):
    for instruction in instruction_data[1:]:  # Skip header
        if instruction[4] == old_name:  # Match the text column
            instruction[4] = new_name  # Update text in Instructions
            break

def update_name_in_ingredients(old_name, new_name):
    for ingredient in ingredient_data[1:]:  # Skip header
        if ingredient[0] == old_name:  # Match the name column
            ingredient[0] = new_name  # Update name in Ingredients
            break

def update_weight_in_instructions(ingredient_name, new_weight):
    for instruction in instruction_data[1:]:  # Skip header
        if instruction[4] == ingredient_name:  # Match the text column
            instruction[5] = new_weight  # Update weight in Instructions
            # Update related fields
            update_action_and_audio(ingredient_name, new_weight, instructions_frame)
            break

def update_weight_in_ingredients(instruction_text, new_weight):
    for ingredient in ingredient_data[1:]:  # Skip header
        if ingredient[0] == instruction_text:  # Match the name column
            ingredient[1] = new_weight  # Update weight in Ingredients
            # Update related fields
            update_action_and_audio(instruction_text, new_weight, ingredients_frame)
            break

def update_action_and_audio(item_name, new_weight, frame):
    print(f"Updating '{item_name}' in frame '{frame}' with new weight '{new_weight}'")
    
    # Split the weight into numeric and unit parts
    weight_parts = new_weight.split()
    numeric_weight = weight_parts[0] if weight_parts else "0"
    unit = weight_parts[1] if len(weight_parts) > 1 else ""

    if frame == ingredients_frame:
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == item_name:
                print(f"Found ingredient '{item_name}'. Updating weight and action.")
                ingredient[1] = new_weight
                ingredient[2] = f"{item_name} {numeric_weight} {unit}"
                ingredient[6] = numeric_weight
                ingredient[7] = unit

                for instruction in instruction_data[1:]:
                    if instruction[4] == item_name:
                        instruction[5] = new_weight
                        instruction[18] = numeric_weight
                        print(f"Updated Weight and AudioQ for Instruction '{instruction[0]}' to {new_weight} and {numeric_weight}")
        return

    elif frame == instructions_frame:
        for instruction in instruction_data[1:]:
            if instruction[4] == item_name:
                print(f"Found instruction '{item_name}'. Updating weight and related fields.")
                instruction[5] = new_weight
                
                # Preserve the first word of the action
                action_parts = instruction[13].split()
                first_word = action_parts[0] if action_parts else instruction[1]  # Use procedure as fallback
                instruction[13] = f"{first_word} {numeric_weight} {unit}"
                
                instruction[18] = numeric_weight
                instruction[19] = unit
                print(f"Updated instruction action to: {instruction[13]}")

                for ingredient in ingredient_data[1:]:
                    if ingredient[0] == item_name:
                        ingredient[1] = new_weight
                        ingredient[2] = f"{ingredient[2].split()[0]} {numeric_weight} {unit}"
                        ingredient[6] = numeric_weight
                        ingredient[7] = unit
                        print(f"Updated Weight and Action for Ingredient '{ingredient[0]}' to {new_weight} and {ingredient[2]}")
        return
# Function to save the updated data back to the JSON file
def save_json():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    
    if not file_path:
        return
    
    try:
        # Start with the existing data to preserve metadata
        updated_data = data.copy() if data else {}

        # Update or add the main recipe metadata
        updated_data.update({
            "name": [data.get("name", ["Unknown Recipe"])[0]],
            "audio1": data.get("audio1", [""]),
            "audio2": data.get("audio2", [""]),
            "category": data.get("category", "0"),
            "description": data.get("description", ""),
            "difficulty": data.get("difficulty", "Easy"),
            "id": data.get("id", 0),
            "imageUrl": data.get("imageUrl", ""),
            "isSelected": data.get("isSelected", False),
            "subCategories": data.get("subCategories", ""),
            "tags": data.get("tags", ""),
            "Ingredients": [],
            "Instruction": []
        })

        # Save changes made to the Ingredients
        for i in range(1, len(ingredient_data)):  # Skip the header (row 0)
            ingredient = {
                "app_audio": "",
                "audio": "",
                "audioI": "",
                "audioP": "",
                "audioQ": "",
                "audioU": "",
                "id": i,
                "image": "",
                "text": "",
                "title": "",
                "weight": ""
            }
            
            ingredient["title"] = ingredient_data[i][0]
            ingredient["weight"] = ingredient_data[i][1]
            weight_parts = ingredient["weight"].split()
            ingredient["audioQ"] = weight_parts[0] if weight_parts else ""
            ingredient["audioU"] = weight_parts[1] if len(weight_parts) > 1 else ""
            ingredient["app_audio"] = f"Add {ingredient['title']} {ingredient['weight']}"
            ingredient["audioI"] = ingredient["title"]
            ingredient["audioP"] = "Add"
            ingredient["audio"] = ingredient_data[i][3] if len(ingredient_data[i]) > 3 else ""
            ingredient["audioI"] = ingredient_data[i][4] if len(ingredient_data[i]) > 4 else ingredient["title"]
            ingredient["audioP"] = ingredient_data[i][5] if len(ingredient_data[i]) > 5 else "Add"
            
            updated_data["Ingredients"].append(ingredient)

        # Save changes made to the Instructions
        for i in range(1, len(instruction_data)):  # Skip the header (row 0)
            instruction = {
                "Audio": "",
                "Indtime_lid_con": "",
                "Induction_on_time": "",
                "Induction_power": "",
                "Magnetron_on_time": "",
                "Magnetron_power": "",
                "Text": "",
                "Weight": "",
                "app_audio": "",
                "audioI": "",
                "audioP": "",
                "audioQ": "",
                "audioU": "",
                "durationInSec": 0,
                "id": i,
                "image": "",
                "lid": "",
                "mag_severity": "",
                "pump_on": "",
                "skip": "",
                "stirrer_on": "",
                "wait_time": "",
                "warm_time": "",
                "threshold": "0",
                "purge_on": ""
            }
            
            # Map instruction_data to instruction dict
            field_mapping = {
                1: "Audio", 2: "Induction_on_time", 3: "Induction_power", 4: "Text", 5: "Weight",
                6: "durationInSec", 7: "lid", 8: "wait_time", 9: "warm_time", 10: "stirrer_on",
                11: "Magnetron_on_time", 12: "Magnetron_power", 13: "app_audio", 14: "mag_severity",
                15: "pump_on", 16: "audioI", 17: "audioP", 18: "audioQ", 19: "audioU", 20: "skip"
            }
            
            for idx, field in field_mapping.items():
                if idx < len(instruction_data[i]):
                    instruction[field] = instruction_data[i][idx]
            
            # Convert durationInSec to int
            instruction["durationInSec"] = int(instruction["durationInSec"]) if instruction["durationInSec"] else 0
            
            updated_data["Instruction"].append(instruction)

        # Write the updated data back to the JSON file
        with open(file_path, 'w') as file:
            json.dump(updated_data, file, indent=2)

        messagebox.showinfo("Success", "Data saved successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving: {str(e)}")

def prt_action(part_name):
    print(f"{part_name} button clicked")

# Set up the tkinter window
root = tk.Tk()
root.title("Recipe Editor")

# Set up the title label
title_label = tk.Label(root, text="Recipe: Choose your recipe", font=('Arial', 14))
title_label.pack(pady=10)

# Set up the frame for the ingredients table
ingredients_label = tk.Label(root, text="Ingredients", font=('Arial', 12, 'bold'))
ingredients_label.pack(pady=5)

ingredients_frame = tk.Frame(root)
ingredients_frame.pack(fill='both', expand=True)

# Set up the frame for the instructions table
instructions_label = tk.Label(root, text="Instructions", font=('Arial', 12, 'bold'))
instructions_label.pack(pady=5)

instructions_frame = tk.Frame(root)
instructions_frame.pack(fill='both', expand=True)

# Add load and save buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

load_button = tk.Button(button_frame, text="Load Recipe", command=load_json)
load_button.pack(side='left', padx=5)

save_button = tk.Button(button_frame, text="Save Recipe", command=save_json)
save_button.pack(side='left', padx=5)

add_ingredient_button = tk.Button(button_frame, text="Add Ingredient", command=add_ingredient)
add_ingredient_button.pack(side='right', padx=5)

add_step_button = tk.Button(button_frame, text="Add Step", command=add_instruction)
add_step_button.pack(side='right', padx=5)

move_up_button = tk.Button(button_frame, text="Move Up", command=lambda: move_row_up(instruction_data, instructions_frame))
move_up_button.pack(side='right', padx=5)

move_down_button = tk.Button(button_frame, text="Move Down", command=lambda: move_row_down(instruction_data, instructions_frame))
move_down_button.pack(side='right', padx=5)

prt1_button = tk.Button(button_frame, text="prt1", command=lambda: prt_action("prt1"))
prt1_button.pack(side='left', padx=5)

prt2_button = tk.Button(button_frame, text="prt2", command=lambda: prt_action("prt2"))
prt2_button.pack(side='left', padx=5)

prt3_button = tk.Button(button_frame, text="prt3", command=lambda: prt_action("prt3"))
prt3_button.pack(side='left', padx=5)

prt4_button = tk.Button(button_frame, text="prt4", command=lambda: prt_action("prt4"))
prt4_button.pack(side='left', padx=5)
# Run the tkinter event loop
root.mainloop() 