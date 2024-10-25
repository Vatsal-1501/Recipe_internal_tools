import numpy as np
import matplotlib.pyplot as plt

# Define rice quantities (in grams) ranging from 100g to 500g
rice_quantities = np.arange(100, 501, 50)

# Define the formulas for water and time
water_needed = rice_quantities * 2.625  # Water formula
time_needed = 7 + 0.5 * (rice_quantities - 100) / 100  # Time formula

# Create a figure and axis for plotting
fig, ax1 = plt.subplots()

# Plot the water needed (left y-axis)
color = 'tab:blue'
ax1.set_xlabel('Rice (g)')
ax1.set_ylabel('Water (ml)', color=color)
ax1.plot(rice_quantities, water_needed, color=color, marker='o', label='Water')
ax1.tick_params(axis='y', labelcolor=color)

# Create a second y-axis for the time needed
ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Time (minutes)', color=color)
ax2.plot(rice_quantities, time_needed, color=color, marker='x', label='Time')
ax2.tick_params(axis='y', labelcolor=color)

# Add a title and grid for better readability
plt.title('Water and Time Required for Cooking Rice')
fig.tight_layout()
plt.grid(True)

# Show the plot
plt.show()