import streamlit as st
import mysql.connector
import subprocess
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Vedic Dynamics", layout="wide")

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          # Ensure this matches your local MySQL
        password="1@Abhinav",  # Ensure this matches your local MySQL
        database="vedic_dynamics"
    )

st.title("Vedic Dynamics: Control Center")

# --- CREATE TABS ---
tab1, tab2 = st.tabs(["Physics Controller", "Animated Equation Grapher"])

# ==========================================
# TAB 1: PHYSICS CONTROLLER
# ==========================================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Create New Simulation")
        sim_name = st.text_input("Simulation Name", "Kinematics Test 1")
        gravity = st.slider("Gravity", 0.1, 10.0, 9.8)
        bounce = st.slider("Bounciness", 0.1, 1.0, 0.7)

        if st.button("Save to Database"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO simulations (sim_name, gravity, bounce) VALUES (%s, %s, %s)",
                (sim_name, gravity, bounce)
            )
            conn.commit()
            conn.close()
            st.success(f"Saved '{sim_name}' to database!")

    with col2:
        st.header("Saved Simulations")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM simulations ORDER BY id DESC")
            saved_sims = cursor.fetchall()
            conn.close()

            for sim in saved_sims:
                st.write(f"**{sim['sim_name']}** (Gravity: {sim['gravity']})")
                if st.button("Launch Engine", key=f"launch_{sim['id']}"):
                    subprocess.Popen(["python", "game.py", str(sim['id'])])
                st.divider()
        except Exception as e:
            st.error("Database connection failed. Ensure MySQL is running.")

# ==========================================
# TAB 2: 4-QUADRANT ANIMATED GRAPHER
# ==========================================
with tab2:
    st.header("Animated Equation Grapher")
    st.write("Type standard math equations (using `x`) to watch them draw live, detect intersections, and graph derivatives.")
    
    # 1. User Controls
    col_eq, col_ctrl = st.columns([2, 1])
    
    with col_eq:
        eq1 = st.text_input("Line 1 Equation ( y = )", "sin(x) * x")
        eq2 = st.text_input("Line 2 Equation ( y = )", "x / 2")

    with col_ctrl:
        x_val = st.slider("X-Axis Range (-X to +X)", 10, 100, 20)
        draw_speed = st.slider("Drawing Speed (ms)", 5, 100, 20)

    # 2. Math Calculations
    x = np.linspace(-x_val, x_val, 400)
    
    allowed_math = {
        'x': x,
        'sin': np.sin, 'cos': np.cos, 'tan': np.tan,
        'pi': np.pi, 'e': np.e,
        'sqrt': np.sqrt, 'abs': np.abs, 'exp': np.exp,
        'log': np.log
    }

    try:
        y1 = eval(eq1, {"__builtins__": None}, allowed_math)
        if isinstance(y1, (int, float)): y1 = np.full_like(x, y1)
    except Exception:
        y1 = np.zeros_like(x)

    try:
        y2 = eval(eq2, {"__builtins__": None}, allowed_math)
        if isinstance(y2, (int, float)): y2 = np.full_like(x, y2)
    except Exception:
        y2 = np.zeros_like(x)

    # --- CALCULUS LOGIC: DERIVATIVE OF LINE 1 ---
    # np.gradient calculates the exact numerical slope at every point
    dy1_dx = np.gradient(y1, x)

    # Axis limit logic
    y_max = max(np.max(y1), np.max(y2))
    y_min = min(np.min(y1), np.min(y2))
    limit = max(abs(y_max), abs(y_min), 5)
    limit = min(limit, x_val * 2) 

    # --- INTERSECTION DETECTION LOGIC ---
    diff = y1 - y2
    cross_indices = np.where(np.diff(np.sign(diff)) != 0)[0]
    
    int_x = []
    int_y = []
    for idx in cross_indices:
        if abs(y1[idx] - y1[idx+1]) < (limit / 2):
            int_x.append(x[idx])
            int_y.append(y1[idx])

    # --- POPULATE THE SIDEBAR ---
    st.sidebar.title("Graph Data 📊")
    st.sidebar.subheader("Intersection Coordinates")
    
    if len(int_x) > 0:
        st.sidebar.success(f"Detected {len(int_x)} intersection(s) in range.")
        for i in range(len(int_x)):
            st.sidebar.markdown(f"**Point {i+1}:** `({int_x[i]:.2f}, {int_y[i]:.2f})`")
    else:
        st.sidebar.info("No intersections detected in the current X-axis range.")

    # 3. Create the Animation Frames
    frames = []
    step = max(1, len(x) // 50) 
    for i in range(1, len(x) + step, step):
        end_idx = min(i, len(x))
        frames.append(go.Frame(
            data=[
                go.Scatter(x=x[:end_idx], y=y1[:end_idx], mode='lines', line=dict(color='#00ffcc', width=2.5)),
                go.Scatter(x=x[:end_idx], y=y2[:end_idx], mode='lines', line=dict(color='#ff00ff', width=2.5)),
                go.Scatter(x=x[:end_idx], y=dy1_dx[:end_idx], mode='lines', line=dict(color='#ffaa00', width=2, dash='dot'))
            ],
            traces=[0, 1, 2], # Instruct Plotly to animate all three line traces
            name=str(i)
        ))

    # 4. Build the 4-Quadrant Plotly Figure
    fig = go.Figure(
        data=[
            go.Scatter(x=[x[0]], y=[y1[0]], mode='lines', line=dict(color='#00ffcc', width=2.5), name="Line 1"),
            go.Scatter(x=[x[0]], y=[y2[0]], mode='lines', line=dict(color='#ff00ff', width=2.5), name="Line 2"),
            go.Scatter(x=[x[0]], y=[dy1_dx[0]], mode='lines', line=dict(color='#ffaa00', width=2, dash='dot'), name="Derivative (Line 1)"),
            go.Scatter(x=int_x, y=int_y, mode='markers', 
                       marker=dict(color='#ffff00', size=10, line=dict(color='#ffffff', width=2)), 
                       name=f"Intersections ({len(int_x)})")
        ],
        layout=go.Layout(
            template="plotly_dark",
            plot_bgcolor='rgba(15, 18, 22, 1)',
            paper_bgcolor='rgba(15, 18, 22, 1)',
            xaxis=dict(
                range=[-x_val, x_val],
                zeroline=True, zerolinewidth=2, zerolinecolor='white', 
                showgrid=True, gridwidth=1, gridcolor='#333333'
            ),
            yaxis=dict(
                range=[-limit, limit],
                zeroline=True, zerolinewidth=2, zerolinecolor='white', 
                showgrid=True, gridwidth=1, gridcolor='#333333',
                scaleanchor="x", scaleratio=1 
            ),
            height=600,
            margin=dict(l=20, r=20, t=40, b=20),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                x=0.05, y=1.1,
                buttons=[
                    dict(label="▶ Draw Graph",
                         method="animate",
                         args=[None, {"frame": {"duration": draw_speed, "redraw": True}, "fromcurrent": True}]),
                    dict(label="⏸ Pause",
                         method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}])
                ]
            )]
        ),
        frames=frames
    )
    
    st.write("💡 *Tip: The dashed orange line represents the instantaneous slope (derivative) of Line 1.*")
    st.plotly_chart(fig, use_container_width=True)