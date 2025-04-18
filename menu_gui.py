import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
import pygame
import os
import threading
import time
import io
import zipfile
import json
import shutil

# Global variables
ingredient_data = None  # Data for the ingredients table
instruction_data = None  # Data for the instructions table
data = None
selected_row = None  # Store the currently selected row index
selected_table = None  # Store the table with the selected row ("ingredients" or "instructions")
highlight_color = "yellow"  # Color for highlighting the selected row
default_color = "white"  # Default background color
copied_row = None
error_cells = []
water_used_label = None  # Label for displaying water used
time_used_label  = None

pygame.mixer.init()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_FOLDER_PATH = os.path.join(BASE_DIR, "mp3")
SELECT_FOLDER_PATHS = os.path.join(BASE_DIR, "Recipee's", "Aloo Samosa")

def change_cell_color(row, col, frame, color):
    for widget in frame.grid_slaves(row=row, column=col):
        if isinstance(widget, tk.Frame):
            for label in widget.winfo_children():
                if isinstance(label, tk.Label):
                    if color:
                        label.config(bg=color)
                    else:
                        label.config(bg=default_color, font=('Arial', 10, 'underline'))

def play_audio(file_name, row, col, frame):
    audio_file = os.path.join(AUDIO_FOLDER_PATH, file_name)
    if os.path.exists(audio_file):
        change_cell_color(row, col, frame, "light green")
        def play_and_reset():
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            root.after(0, lambda: change_cell_color(row, col, frame, None))
        threading.Thread(target=play_and_reset, daemon=True).start()

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
    audio_path = os.path.join(AUDIO_FOLDER_PATH, f"{file_name}.mp3")
    return os.path.exists(audio_path)

def handle_missing_audio(file_name):
    audio_path = os.path.join(AUDIO_FOLDER_PATH, f"{file_name}.mp3")
    if not os.path.exists(audio_path):
        response = messagebox.askquestion("Audio File Not Found",
                                         f"The audio file '{file_name}.mp3' was not found. Would you like to add it?")
        if response == 'yes':
            file_path = filedialog.askopenfilename(title="Select Audio File", filetypes=[("MP3 files", "*.mp3")])
            if file_path:
                try:
                    os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)
                    shutil.copy2(file_path, audio_path)
                    messagebox.showinfo("Success", f"Audio file '{file_name}.mp3' has been added successfully.")
                    return True
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred while copying the file: {str(e)}")
    return False

def check_for_errors(data_table, frame):
    error_cells = []
    for i, row in enumerate(data_table):
        if i == 0:
            continue
        for j, value in enumerate(row):
            is_error = False
            if frame == instructions_frame:
                if j == 9:  # stirrer
                    if str(value).strip() not in ["0", "1", "2", "3", "4", ""]:
                        is_error = True
                elif j == 17:  # skip
                    if str(value).strip().lower() not in ["true", "false", ""]:
                        is_error = True
                elif j == 11:  # lid status
                    if str(value).strip().lower() not in ["open", "close", ""]:
                        is_error = True
                elif j == 5:  # induction power
                    if str(value).strip() not in ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100", ""]:
                        is_error = True
                elif j == 7:  # mag power
                    if str(value).strip() not in ["0", "20", "40", "60", "80", "100", ""]:
                        is_error = True
            if is_error:
                error_cells.append((i, j))
    return error_cells

def update_water_used():
    global water_used_label, instruction_data
    if water_used_label is None:
        return
    try:
        pump_sum = 0
        for row in instruction_data[1:]:  # Skip header row
            pump_value = str(row[10]).strip()  # Pump column at index 10
            if pump_value and pump_value.isdigit():
                pump_sum += int(pump_value)
        water_used = pump_sum * 10
        water_used_label.config(text=f"Water Used: {water_used} ml")
    except Exception as e:
        water_used_label.config(text="Water Used: 0 ml")
def update_total_time():
    global time_used_label, instruction_data
    if time_used_label is None:
        return
    try :
        time_sum = 0
        for row in instruction_data[1:]:  # Skip header row
            time_value = str(row[8]).strip()  # duration column at index 8
            if time_value and time_value.isdigit():
                time_sum += int(time_value)
        time_used = time_sum 
        time_used_label.config(text=f"Total Time: {time_used} Secs")
    except Exception as e:
        time_used_label.config(text="Total Time: 0 Sec")

    

def load_json():
    global ingredient_data, instruction_data, data, selected_row, selected_table
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("Zip Files", "*.zip")])
    if not file_path:
        return
    try:
        if file_path.lower().endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                json_files = [f for f in zip_ref.namelist() if f.lower().endswith('.txt')]
                if not json_files:
                    raise ValueError("No JSON file found in the ZIP archive")
                json_file = json_files[0]
                with zip_ref.open(json_file) as file:
                    data = json.load(io.TextIOWrapper(file))
        else:
            with open(file_path, 'r') as file:
                data = json.load(file)
        recipe_name = data.get("name", ["Unknown Recipe"])[0]
        title_label.config(text=f"Recipe: {recipe_name}")
        ingredient_data = format_ingredients(data)
        instruction_data = format_instructions(data)
        selected_row = None
        selected_table = None
        clear_table(ingredients_frame)
        clear_table(instructions_frame)
        display_ingredients_table(ingredient_data)
        display_instructions_table(instruction_data)
        update_water_used()
        update_total_time()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def format_ingredients(data):
    rows = []
    ingredients = data.get("Ingredients", [])
    column_names = ['Name', 'Weight', 'Action', 'audio', 'audioI', 'audioP', 'audioQ', 'audioU', 'Image', 'Text']
    for ingredient in ingredients:
        name = ingredient.get("title", "")
        weight = ingredient.get("weight", "")
        action = ingredient.get("app_audio", "")
        audio = ingredient.get("audio", "")
        audioI = ingredient.get("audioI", "")
        audioP = ingredient.get("audioP", "")
        audioQ = ingredient.get("audioQ", "")
        audioU = ingredient.get("audioU", "")
        Image = ingredient.get("image", "")
        Text = ingredient.get("text", "")
        rows.append([name, weight, action, audio, audioI, audioP, audioQ, audioU, Image, Text])
    return [column_names] + rows

def format_instructions(data):
    rows = []
    instructions = data.get("Instruction", [])
    column_names = ['Step', 'Procedure', 'Text', 'Weight', 'Induction On Time', 'Induction Power',
                    'Mag On Time', 'Mag Power', 'Duration (s)', 'Stirrer', 'Pump', 'Lid Status',
                    'Action', 'AudioI', 'AudioP', 'AudioQ', 'AudioU', 'Skip', 'Mag Serv',
                    'Ind_lid_con', 'Threshold', 'Purge', 'Wait Time (s)', 'Warm Time (s)']
    for i, instructions in enumerate(instructions):
        step = f"Step {i + 1}"
        procedure = instructions.get("Audio", "")
        text = instructions.get("Text", "")
        weight = instructions.get("Weight", "")
        ind_on_time = instructions.get("Induction_on_time", 0)
        ind_power = instructions.get("Induction_power", 0)
        mag_on_time = instructions.get("Magnetron_on_time", 0)
        mag_power = instructions.get("Magnetron_power", 0)
        duration = instructions.get("durationInSec", 0)
        stirrer = instructions.get("stirrer_on", 0)
        pump = instructions.get("pump_on", 0)
        lid_status = instructions.get("lid", "N/A")
        action = instructions.get("app_audio", 0)
        audio_i = instructions.get("audioI", 0)
        audio_p = instructions.get("audioP", 0)
        audio_q = instructions.get("audioQ", 0)
        audio_u = instructions.get("audioU", 0)
        skip = instructions.get("skip", 0)
        mag_serv = instructions.get("mag_severity", "")
        ind_lid_con = instructions.get("Indtime_lid_con", "")
        threshold = instructions.get("threshold", "")
        purge = instructions.get("purge_on", "")
        wait_time = instructions.get("wait_time", 0)
        warm_time = instructions.get("warm_time", 0)
        rows.append([step, procedure, text, weight, ind_on_time, ind_power, mag_on_time, mag_power,
                     duration, stirrer, pump, lid_status, action, audio_i, audio_p, audio_q, audio_u,
                     skip, mag_serv, ind_lid_con, threshold, purge, wait_time, warm_time])
    return [column_names] + rows

def clear_table(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def add_ingredient():
    global ingredient_data, selected_row, selected_table
    ingredient_data.append(["New Ingredient", "0", "", "", "", "", "0", "", "", ""])
    selected_row = None
    selected_table = None
    clear_table(ingredients_frame)
    clear_table(instructions_frame)
    display_ingredients_table(ingredient_data)
    display_instructions_table(instruction_data)

def add_instruction():
    global instruction_data, selected_row, selected_table
    next_step_number = len(instruction_data)
    instruction_data.append([f"Step {next_step_number}", "", "", "0", 0, 0, 0, 0, 0, 0, 0, "N/A", "", "", "", "", "", "", "", "", "", "", 0, 0])
    selected_row = None
    selected_table = None
    clear_table(ingredients_frame)
    clear_table(instructions_frame)
    display_ingredients_table(ingredient_data)
    display_instructions_table(instruction_data)
    update_water_used()
    update_total_time()

def display_ingredients_table(data):
    global selected_row, selected_table
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            cell = tk.Frame(ingredients_frame, relief="solid", borderwidth=1)
            cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
            if i == 0:
                bg_color = "light blue"
            elif i == selected_row and selected_table == "ingredients":
                bg_color = highlight_color
            else:
                bg_color = default_color
            if i > 0 and j in [4, 5, 6, 7] and value and not audio_file_exists(value):
                bg_color = "red"
            underline = (j in [4, 5, 6, 7] and i > 0)
            label = tk.Label(cell, text=str(value), font=('Arial', 10, 'underline' if underline else ''),
                             bg=bg_color, anchor='center')
            label.pack(side='left', fill='both', expand=True)
            if j in [4, 5, 6, 7]:
                label.bind("<Button-1>", lambda event, r=i, c=j: on_audio_click(r, c))
            else:
                label.bind("<Button-1>", lambda event, r=i, c=j: handle_missing_audio(r, c))
            if i > 0:
                if j != 2:  # Skip Action column (index 2)
                    label.bind("<Double-1>", lambda event, r=i, c=j: edit_cell(r, c, ingredient_data, ingredients_frame))
                label.bind("<Button-3>", lambda event, r=i: toggle_row_selection(r, ingredients_frame))
    for j in range(len(data[0])):
        ingredients_frame.grid_columnconfigure(j, weight=1)

def display_instructions_table(data):
    global selected_row, selected_table, error_cells
    error_cells = check_for_errors(data, instructions_frame)
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            cell = tk.Frame(instructions_frame, relief="solid", borderwidth=1)
            cell.grid(row=i, column=j, sticky="nsew", padx=1, pady=1)
            if i == 0:
                bg_color = "light blue"
            elif (i, j) in error_cells:
                bg_color = "red"
            elif i == selected_row and selected_table == "instructions":
                bg_color = highlight_color
            else:
                bg_color = default_color
            if i > 0 and j in [13, 14, 15, 16] and value and not audio_file_exists(value):
                bg_color = "red"
            underline = (j in [13, 14, 15, 16] and i > 0)
            label = tk.Label(cell, text=str(value), font=('Arial', 10, 'underline' if underline else ''),
                             bg=bg_color, anchor='center')
            label.pack(side='left', fill='both', expand=True)
            if j in [13, 14, 15, 16]:
                label.bind("<Button-1>", lambda event, r=i, c=j: on_instruction_audio_click(r, c))
            if i > 0:
                if j != 12:  # Skip Action column (index 12)
                    label.bind("<Double-1>", lambda event, r=i, c=j: edit_cell(r, c, instruction_data, instructions_frame))
                label.bind("<Button-3>", lambda event, r=i: toggle_row_selection(r, instructions_frame))
    for j in range(len(data[0])):
        instructions_frame.grid_columnconfigure(j, weight=1)
    update_water_used()
    update_total_time()

def toggle_row_selection(row, frame):
    global selected_row, selected_table
    if frame == ingredients_frame:
        table_name = "ingredients"
        other_frame = instructions_frame
    elif frame == instructions_frame:
        table_name = "instructions"
        other_frame = ingredients_frame
    else:
        return
    if selected_row == row and selected_table == table_name:
        selected_row = None
        selected_table = None
    else:
        selected_row = row
        selected_table = table_name
    clear_table(ingredients_frame)
    clear_table(instructions_frame)
    display_ingredients_table(ingredient_data)
    display_instructions_table(instruction_data)


def update_step_numbers(data_table):
    for i in range(1, len(data_table)):
        data_table[i][0] = f"Step {i}"

def move_row_up(data_table, frame):
    global selected_row, selected_table
    if selected_row is None or selected_row == 1:
        return
    if (frame == ingredients_frame and selected_table != "ingredients") or \
       (frame == instructions_frame and selected_table != "instructions"):
        return
    data_table[selected_row], data_table[selected_row - 1] = data_table[selected_row - 1], data_table[selected_row]
    selected_row -= 1
    if frame == instructions_frame:
        update_step_numbers(data_table)
    clear_table(frame)
    if frame == ingredients_frame:
        display_ingredients_table(data_table)
    else:
        display_instructions_table(data_table)
    # Refresh the other table to update selection highlight
    other_frame = instructions_frame if frame == ingredients_frame else ingredients_frame
    clear_table(other_frame)
    if other_frame == ingredients_frame:
        display_ingredients_table(ingredient_data)
    else:
        display_instructions_table(instruction_data)

def move_row_down(data_table, frame):
    global selected_row, selected_table
    if selected_row is None or selected_row == len(data_table) - 1:
        return
    if (frame == ingredients_frame and selected_table != "ingredients") or \
       (frame == instructions_frame and selected_table != "instructions"):
        return
    data_table[selected_row], data_table[selected_row + 1] = data_table[selected_row + 1], data_table[selected_row]
    selected_row += 1
    if frame == instructions_frame:
        update_step_numbers(data_table)
    clear_table(frame)
    if frame == ingredients_frame:
        display_ingredients_table(data_table)
    else:
        display_instructions_table(data_table)
    # Refresh the other table to update selection highlight
    other_frame = instructions_frame if frame == ingredients_frame else ingredients_frame
    clear_table(other_frame)
    if other_frame == ingredients_frame:
        display_ingredients_table(ingredient_data)
    else:
        display_instructions_table(instruction_data)

def edit_cell(row, col, data_table, frame):
    if (frame == ingredients_frame and col == 2) or (frame == instructions_frame and col == 12):
        messagebox.showinfo("Non-Editable", "The Action column is non-editable and updates automatically.")
        return
    current_value = data_table[row][col]
    if frame == ingredients_frame:
        audio_columns = [4, 5, 6, 7]
    elif frame == instructions_frame:
        audio_columns = [13, 14, 15, 16]
    else:
        audio_columns = []
    if col in audio_columns:
        if not audio_file_exists(current_value):
            if handle_missing_audio(current_value):
                cell = frame.grid_slaves(row=row, column=col)[0]
                cell.config(bg='white')
            else:
                cell = frame.grid_slaves(row=row, column=col)[0]
                cell.config(bg='red')
    entry = tk.Entry(frame, font=('Arial', 10))
    entry.insert(0, current_value)
    entry.grid(row=row, column=col, sticky="nsew")
    def save_value():
        new_value = entry.get()
        old_value = data_table[row][col]
        if frame == instructions_frame and col in [4, 6, 8]:  # Induction On Time, Magnetron On Time, Duration
            try:
                if col in [4, 6]:  # Induction On Time or Magnetron On Time
                    if new_value.strip() and not new_value.isdigit():
                        messagebox.showerror("Error", f"{'Induction On Time' if col == 4 else 'Magnetron On Time'} must be a non-negative integer or blank.")
                        return
                    data_table[row][col] = new_value
                    # Update Duration based on max of Induction On Time and Magnetron On Time
                    ind_on_time = int(data_table[row][4]) if str(data_table[row][4]).strip().isdigit() else 0
                    mag_on_time = int(data_table[row][6]) if str(data_table[row][6]).strip().isdigit() else 0
                    duration_seconds = max(ind_on_time, mag_on_time)
                    if duration_seconds < 0 or duration_seconds > 6000:
                        messagebox.showerror("Error", "Duration must be between 0 and 6000 seconds.")
                        return
                    data_table[row][8] = str(duration_seconds)
                    # Update AudioU
                    if duration_seconds >= 60:
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        if seconds == 0:
                            audioU_text = f"{minutes}Minute"
                        else:
                            audioU_text = f"{minutes}Minute {seconds}Seconds"
                    else:
                        audioU_text = f"{duration_seconds}Seconds"
                    data_table[row][16] = audioU_text
                    # Magnetron safety rule
                    if col == 6 and new_value.strip() and new_value != "0":
                        data_table[row][11] = "close"  # Lid Status
                        data_table[row][7] = "100"  # Mag Power
                        data_table[row][18] = "high" #Mag Serv
                    
                elif col == 8:  # Duration
                    duration_seconds = int(new_value)
                    if duration_seconds < 0 or duration_seconds > 6000:
                        messagebox.showerror("Error", "Duration must be between 0 and 6000 seconds.")
                        return
                    data_table[row][col] = str(duration_seconds)
                    if duration_seconds >= 60:
                        minutes = duration_seconds // 60
                        seconds = duration_seconds % 60
                        if seconds == 0:
                            audioU_text = f"{minutes}Minute"
                        else:
                            audioU_text = f"{minutes}Minute{seconds}Seconds"
                    else:
                        audioU_text = f"{duration_seconds}Seconds"
                    data_table[row][16] = audioU_text
            except ValueError:
                messagebox.showerror("Error", f"{'Induction On Time' if col == 4 else 'Magnetron On Time' if col == 6 else 'Duration'} must be a valid number.")
                return
        if frame == instructions_frame and col == 9:  # Stirrer
            if not validate_Stirrer(new_value):
                messagebox.showerror("Error", "Stirrer value must be between 0 and 4 or blank.")
                return
            data_table[row][col] = new_value
            if new_value in ["1", "2", "3", "4"]:  # Safety rule: Stirrer > 0
                data_table[row][11] = "close"  # Lid Status
        if frame == instructions_frame and col == 10:  # Pump
            try:
                pump_value = str(new_value).strip()
                if pump_value and not pump_value.isdigit():
                    messagebox.showerror("Error", "Pump value must be a non-negative integer or blank.")
                    return
                data_table[row][col] = new_value
                if pump_value and int(pump_value) > 0:  # Safety rule: Pump > 0
                    data_table[row][11] = "close"  # Lid Status
            except ValueError:
                messagebox.showerror("Error", "Pump value must be a non-negative integer or blank.")
                return
        if frame == instructions_frame and col not in [4, 6, 8, 9, 10]:  # Validate other instruction inputs
            if not validate_instruction_input(col, new_value):
                entry.delete(0, tk.END)
                entry.insert(0, old_value)
                return
        if frame == ingredients_frame:
            if col == 0:
                update_name(old_value, new_value, ingredients_frame)
            elif col == 1:
                update_weight(data_table[row][0], new_value, ingredients_frame)
            elif col in [3, 5]:  # audio, audioP
                update_action_audio(row, col, new_value, ingredients_frame)
        elif frame == instructions_frame:
            if col == 2:  # Text
                update_name(old_value, new_value, instructions_frame)
            elif col == 3:  # Weight
                update_weight(data_table[row][2], new_value, instructions_frame)
            elif col in [1, 14]:  # Procedure, AudioP
                update_action_audio(row, col, new_value, instructions_frame)
        if col not in [4, 6, 8, 9, 10]:  # Update only if not already handled
            data_table[row][col] = new_value
        # Update Action column for Procedure, Text, or Weight edits
        if frame == instructions_frame and col in [1, 2, 3]:
            procedure = str(data_table[row][1]).strip()
            text = str(data_table[row][2]).strip()
            weight = str(data_table[row][3]).strip()
            data_table[row][12] = f"{procedure} {text} {weight}".strip()
            data_table[row][13] = text  # Update AudioI
            data_table[row][14] = procedure  # Update AudioP
        clear_table(ingredients_frame)
        clear_table(instructions_frame)
        display_ingredients_table(ingredient_data)
        display_instructions_table(instruction_data)
        entry.destroy()
    entry.bind("<Return>", lambda event: save_value())
    entry.bind("<FocusOut>", lambda event: save_value())
    entry.focus_set()

def validate_instruction_input(col, value):
    value_str = str(value).strip()
    if col == 17 and not validate_skip(value_str):  # Skip
        messagebox.showerror("Invalid Value", "The 'Skip' column can only accept 'true', 'false', or be blank.")
        return False
    if col == 11 and not validate_Lid(value_str):  # Lid status
        messagebox.showerror("Invalid Value", "The 'Lid_status' column can only accept 'open', 'close' or be blank.")
        return False
    if col == 5 and not validate_induction(value_str):  # Induction power
        messagebox.showerror("Invalid Value", "The 'Induction' column can only accept value in terms 10x or be blank.")
        return False
    if col == 7 and not validate_magnetron(value_str):  # Mag power
        messagebox.showerror("Invalid Value", "The 'Magnetron' column can only accept value in terms of 20x or be blank.")
        return False
    if col in [4, 6] and value_str and not value_str.isdigit():  # Induction On Time, Magnetron On Time
        messagebox.showerror("Invalid Value", f"{'Induction On Time' if col == 4 else 'Magnetron On Time'} must be a non-negative integer or blank.")
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
                ingredient[0] = new_name
                ingredient[2] = update_middle_word(ingredient[2], new_name)
                ingredient[4] = new_name
        for instruction in instruction_data[1:]:
            if instruction[2] == old_name:
                instruction[2] = new_name
                instruction[13] = new_name
                # Update Action
                procedure = str(instruction[1]).strip()
                weight = str(instruction[3]).strip()
                instruction[12] = f"{procedure} {new_name} {weight}".strip()
    elif frame == instructions_frame:
        for instruction in instruction_data[1:]:
            if instruction[2] == old_name:
                instruction[2] = new_name
                instruction[13] = new_name
                # Update Action
                procedure = str(instruction[1]).strip()
                weight = str(instruction[3]).strip()
                instruction[12] = f"{procedure} {new_name} {weight}".strip()
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == old_name:
                ingredient[0] = new_name
                ingredient[2] = update_middle_word(ingredient[2], new_name)
                ingredient[4] = new_name

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
                ingredient[1] = new_weight
                ingredient[2] = update_last_two_words(ingredient[2], numeric_weight, unit)
                ingredient[6] = numeric_weight
                ingredient[7] = unit
        for instruction in instruction_data[1:]:
            if instruction[2] == item_name:
                instruction[3] = new_weight
                instruction[15] = numeric_weight
                # Update Action
                procedure = str(instruction[1]).strip()
                text = str(instruction[2]).strip()
                instruction[12] = f"{procedure} {text} {new_weight}".strip()
    elif frame == instructions_frame:
        for instruction in instruction_data[1:]:
            if instruction[2] == item_name:
                instruction[3] = new_weight
                instruction[15] = numeric_weight
                # Update Action
                procedure = str(instruction[1]).strip()
                text = str(instruction[2]).strip()
                instruction[12] = f"{procedure} {text} {new_weight}".strip()
        for ingredient in ingredient_data[1:]:
            if ingredient[0] == item_name:
                ingredient[1] = new_weight
                ingredient[2] = update_last_two_words(ingredient[2], numeric_weight, unit)
                ingredient[6] = numeric_weight
                ingredient[7] = unit

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
                ingredient_data[row][3] = words[0]
                ingredient_data[row][0] = words[1]
                ingredient_data[row][5] = words[0]
                update_name(ingredient_data[row][0], words[1], ingredients_frame)
        elif col in [3, 5]:  # audio, audioP
            ingredient_data[row][3] = new_value
            ingredient_data[row][5] = new_value
            action_words = ingredient_data[row][2].split()
            if action_words:
                action_words[0] = new_value
                ingredient_data[row][2] = ' '.join(action_words)
    elif frame == instructions_frame:
        if col == 12:  # Action
            words = new_value.split()
            if len(words) >= 3:
                instruction_data[row][1] = words[0]  # Procedure
                instruction_data[row][14] = words[0]  # AudioP
                instruction_data[row][2] = words[1]  # Text
                instruction_data[row][13] = words[1]  # AudioI
                instruction_data[row][3] = ' '.join(words[2:])  # Weight
                instruction_data[row][15] = words[2] if len(words) > 2 else ""  # AudioQ
                update_name(instruction_data[row][2], words[1], instructions_frame)
        elif col == 1:  # Procedure
            instruction_data[row][1] = new_value
            instruction_data[row][14] = new_value
            # Update Action
            text = str(instruction_data[row][2]).strip()
            weight = str(instruction_data[row][3]).strip()
            instruction_data[row][12] = f"{new_value} {text} {weight}".strip()
        elif col == 14:  # AudioP
            instruction_data[row][1] = new_value
            instruction_data[row][14] = new_value
            # Update Action
            text = str(instruction_data[row][2]).strip()
            weight = str(instruction_data[row][3]).strip()
            instruction_data[row][12] = f"{new_value} {text} {weight}".strip()

def save_json():
    global data, ingredient_data, instruction_data
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if not file_path:
        return
    try:
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
        current_id = 1
        if isinstance(ingredient_data, list) and len(ingredient_data) > 1:
            for i in range(1, len(ingredient_data)):
                row = ingredient_data[i]
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
                    "id": current_id,
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
                weight_parts = ingredient["weight"].split()
                ingredient["audioQ"] = weight_parts[0] if len(weight_parts) > 0 else ""
                ingredient["audioU"] = weight_parts[1] if len(weight_parts) > 1 else ""
                ingredient["image"] = str(row[8]) if len(row) > 8 else ""
                ingredient["text"] = str(row[9]) if len(row) > 9 else ""
                updated_data["Ingredients"].append(ingredient)
                current_id += 1
        current_id = 1
        if isinstance(instruction_data, list) and len(instruction_data) > 1:
            for i in range(1, len(instruction_data)):
                row = instruction_data[i]
                if not isinstance(row, list) or len(row) <= 2 or not row[2].strip():
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
                    "id": current_id,
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
                    1: "Audio",
                    2: "Text",
                    3: "Weight",
                    4: "Induction_on_time",
                    5: "Induction_power",
                    6: "Magnetron_on_time",
                    7: "Magnetron_power",
                    8: "durationInSec",
                    9: "stirrer_on",
                    10: "pump_on",
                    11: "lid",
                    12: "app_audio",
                    13: "audioI",
                    14: "audioP",
                    15: "audioQ",
                    16: "audioU",
                    17: "skip",
                    18: "mag_severity",
                    19: "Indtime_lid_con",
                    20: "threshold",
                    21: "purge_on",
                    22: "wait_time",
                    23: "warm_time"
                }
                for idx, field in field_mapping.items():
                    if idx < len(row):
                        if field == "durationInSec":
                            instruction[field] = int(row[idx]) if str(row[idx]).isdigit() else 0
                        else:
                            instruction[field] = str(row[idx])
                updated_data["Instruction"].append(instruction)
                current_id += 1
        with open(file_path, 'w') as file:
            json.dump(updated_data, file, indent=2)
        messagebox.showinfo("Success", "Data saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving: {str(e)}")
        import traceback
        traceback.print_exc()

def prt_action(part_name):
    print(f"{part_name} button clicked")

def new_recipe():
    global ingredient_data, instruction_data, data, selected_row, selected_table, error_cells
    selected_row = None
    selected_table = None
    error_cells = []
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
                "app_audio": "heat Water 500 ml",
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
                "app_audio": "add Oil 30 ml",
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
                "warm_time": "0",
                "stirrer_on": "1",
                "Magnetron_on_time": "30",
                "Magnetron_power": "100",
                "app_audio": "stir Salt",
                "mag_severity": "medium",
                "pump_on": "1",
                "audioI": "Salt",
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
    ingredient_data = format_ingredients(data)
    instruction_data = format_instructions(data)
    title_label.config(text="Recipe: New Recipe")
    clear_table(ingredients_frame)
    clear_table(instructions_frame)
    display_ingredients_table(ingredient_data)
    display_instructions_table(instruction_data)
    update_water_used()
    update_total_time()
    for i in range(1, len(ingredient_data)):
        for j in range(len(ingredient_data[i])):
            cell = ingredients_frame.grid_slaves(row=i, column=j)
            if cell:
                if j != 2:  # Skip Action column
                    cell[0].bind('<Double-Button-1>',
                                 lambda e, row=i, col=j: edit_cell(row, col, ingredient_data, ingredients_frame))
                cell[0].bind('<Button-3>',
                             lambda e, row=i: toggle_row_selection(row, ingredients_frame))
    for i in range(1, len(instruction_data)):
        for j in range(len(instruction_data[i])):
            cell = instructions_frame.grid_slaves(row=i, column=j)
            if cell:
                if j != 12:  # Skip Action column
                    cell[0].bind('<Double-Button-1>',
                                 lambda e, row=i, col=j: edit_cell(row, col, instruction_data, instructions_frame))
                cell[0].bind('<Button-3>',
                             lambda e, row=i: toggle_row_selection(row, instructions_frame))
    save_button.config(state='normal')
    add_ingredient_button.config(state='normal')
    add_step_button.config(state='normal')
    move_up_button.config(state='normal')
    move_down_button.config(state='normal')

def load_text_files():
    return [f for f in os.listdir(SELECT_FOLDER_PATHS) if f.endswith('.txt')]

def select_recipe(event=None):
    title_label.config(text="Recipe: Selected Recipe")
    print("Select Recipe button clicked")
    text_files = load_text_files()
    if text_files:
        recipe_combobox['values'] = text_files
        recipe_combobox.pack(pady=10)
    else:
        print("No text files available.")

def load_file(event=None):
    global ingredient_data, instruction_data, selected_row, selected_table
    selected_file = recipe_combobox.get()
    if selected_file:
        file_path = os.path.join(SELECT_FOLDER_PATHS, selected_file)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                recipe_name = data.get("name", ["Unknown Recipe"])[0]
                title_label.config(text=f"Recipe: {recipe_name}")
                ingredient_data = format_ingredients(data)
                instruction_data = format_instructions(data)
                selected_row = None
                selected_table = None
                clear_table(ingredients_frame)
                clear_table(instructions_frame)
                display_ingredients_table(ingredient_data)
                display_instructions_table(instruction_data)
                update_water_used()
                update_total_time()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    hide_combobox()

def hide_combobox():
    recipe_combobox.pack_forget()

def refresh_tables():
    global error_cells, selected_row, selected_table
    error_cells = []
    selected_row = None
    selected_table = None
    clear_table(ingredients_frame)
    clear_table(instructions_frame)
    display_ingredients_table(ingredient_data)
    display_instructions_table(instruction_data)
    error_cells = check_for_errors(instruction_data, instructions_frame)
    update_water_used()
    update_total_time()
    messagebox.showinfo("Refresh", "Tables have been refreshed and errors rechecked.")

root = tk.Tk()
root.title("Recipe Editor")
container = tk.Frame(root)
container.pack(fill='both', expand=True)
main_canvas = tk.Canvas(container)
main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
y_scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=main_canvas.yview)
y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
x_scrollbar = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=main_canvas.xview)
x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
main_canvas.configure(xscrollcommand=x_scrollbar.set, yscrollcommand=y_scrollbar.set)
content_frame = tk.Frame(main_canvas)
main_canvas.create_window((0, 0), window=content_frame, anchor='nw')

def on_frame_configure(event):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))

content_frame.bind("<Configure>", on_frame_configure)
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X)
button_frame = tk.Frame(top_frame)
button_frame.pack(pady=10)
new_recipe_button = tk.Button(button_frame, text="New Recipe", command=new_recipe)
new_recipe_button.pack(side='left', padx=5)
select_button = tk.Button(button_frame, text="Select the Recipe", command=select_recipe)
select_button.pack(side='left', padx=5)
recipe_combobox = ttk.Combobox(root)
recipe_combobox.pack_forget()
recipe_combobox.bind("<<ComboboxSelected>>", load_file)
load_button = tk.Button(root, text="Load File", command=load_file)
load_button.pack_forget()
title_frame = tk.Frame(content_frame)
title_frame.pack(pady=10)
on_label = tk.Label(title_frame, text="on", font=('Arial', 24), fg='red')
on_label.pack(side=tk.LEFT)
two_cook_label = tk.Label(title_frame, text="2cook", font=('Arial', 24), fg='black')
two_cook_label.pack(side=tk.LEFT)
recipe_name = "Your Recipe Name"
title_label = tk.Label(content_frame, text=f"Recipe: {recipe_name}", font=('Arial', 16), anchor='center')
title_label.pack(pady=10, anchor='center')
ingredients_label = tk.Label(content_frame, text="Ingredients", font=('Arial', 14, 'bold'), anchor='center')
ingredients_label.pack(pady=5, anchor='center')
ingredients_frame = tk.Frame(content_frame)
ingredients_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
water_used_label = tk.Label(content_frame, text="Water Used: 0 ml", font=('Arial', 12), anchor='center')
water_used_label.pack(pady=5, anchor='center')
time_used_label = tk.Label(content_frame, text="Total Time: 0 Secs", font=('Arial', 12), anchor='center')
time_used_label.pack(pady=5, anchor='center')
instructions_label = tk.Label(content_frame, text="Instructions", font=('Arial', 14, 'bold'), anchor='center')
instructions_label.pack(pady=5, anchor='center')
instructions_frame = tk.Frame(content_frame)
instructions_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)
button_frame = tk.Frame(bottom_frame)
button_frame.pack(pady=10)
load_button = tk.Button(button_frame, text="Load Recipe", command=load_json)
load_button.pack(side='left', padx=5)
save_button = tk.Button(button_frame, text="Save Recipe", command=save_json)
save_button.pack(side='left', padx=5)
add_ingredient_button = tk.Button(button_frame, text="Add Ingredient", command=add_ingredient)
add_ingredient_button.pack(side='left', padx=5)
add_step_button = tk.Button(button_frame, text="Add Step", command=add_instruction)
add_step_button.pack(side='left', padx=5)
move_up_button = tk.Button(button_frame, text="Move Up",
                          command=lambda: move_row_up(ingredient_data if selected_table == "ingredients" else instruction_data,
                                                    ingredients_frame if selected_table == "ingredients" else instructions_frame))
move_up_button.pack(side='left', padx=5)
move_down_button = tk.Button(button_frame, text="Move Down",
                            command=lambda: move_row_down(ingredient_data if selected_table == "ingredients" else instruction_data,
                                                        ingredients_frame if selected_table == "ingredients" else instructions_frame))
move_down_button.pack(side='left', padx=5)
# -------------portion buttons------------------
# prt1_button = tk.Button(button_frame, text="prt1", command=lambda: prt_action("prt1"))
# prt1_button.pack(side='left', padx=5)
# prt2_button = tk.Button(button_frame, text="prt2", command=lambda: prt_action("prt2"))
# prt2_button.pack(side='left', padx=5)
# prt3_button = tk.Button(button_frame, text="prt3", command=lambda: prt_action("prt3"))
# prt3_button.pack(side='left', padx=5)
# prt4_button = tk.Button(button_frame, text="prt4", command=lambda: prt_action("prt 4"))
# prt4_button.pack(side='left', padx=5)
# ----------------------------------------------
refresh_button = tk.Button(button_frame, text="Refresh", command=refresh_tables)
refresh_button.pack(side=tk.LEFT, padx=5)
root.mainloop()
