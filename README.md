Markdown
# Vedic Dynamics: Physics & Math Laboratory

Vedic Dynamics is a multi-functional, fully offline 2D physics engine and advanced mathematical grapher. Designed for rigorous secondary school foundation and competitive mathematics preparation (IOQM/JEE), it features a local Streamlit control dashboard, a Pygame/Pymunk kinematics engine, and a 4-quadrant Plotly coordinate geometry grapher. 

## Core Features
* **Kinematics Engine:** Interactive 2D projectile physics with real-time HUD (velocity, net speed, launch angle).
* **Live Parabola Calculator:** Automatically converts screen coordinates to Cartesian coordinates to display the exact quadratic equation ($y = ax^2 + bx + c$) of the projectile's flight path.
* **Target Collision System:** Dynamic target generation and wave-based score tracking using Pymunk collision handlers.
* **Animated Equation Grapher:** Type standard math equations to watch them draw live on a 4-quadrant plane.
* **Calculus & Geometry:** Real-time automatic derivative mapping (instantaneous slope) and numerical intersection detection between two curves.
* **Local Database:** MySQL integration to save and load different gravity and bounciness environments.

## Prerequisites
* Python 3.8+
* MySQL Server (Running locally)

## Installation & Setup

1. **Clone the Directory**
   Ensure all files (`app.py`, `game.py`, `requirements.txt`) are in the same folder.

2. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
Configure the MySQL Database
Open your MySQL command line or Workbench and run the following SQL commands to create the required database and table:

SQL
CREATE DATABASE vedic_dynamics;
USE vedic_dynamics;

CREATE TABLE simulations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sim_name VARCHAR(255) NOT NULL,
    gravity FLOAT NOT NULL,
    bounce FLOAT NOT NULL
);
Update Credentials
Open both app.py and game.py and ensure the MySQL connection block matches your local system credentials:

Python
user="root",          # Change to your MySQL username
password="password",  # Change to your MySQL password
How to Run
Open your terminal in the project folder.

Launch the Streamlit Control Center:

Bash
streamlit run app.py
Use the Physics Controller tab in your web browser to configure gravity and launch the standalone Pygame window.

Use the Animated Equation Grapher tab to plot mathematical functions and calculate intersections.


<FollowUp label="Need the exact MySQL setup commands?" query="Show me how to open the MySQL command line on Windows to quickly create the vedic_dynamics database and table."/>
