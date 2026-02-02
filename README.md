# Academic Session Tracker Dashboard

This dashboard provides a visual overview of the academic session progress for the "Naan Mudhalvan" program. It allows users to track key metrics and filter data to gain insights into the performance of different universities and colleges.

## Features

- **Key Performance Indicators (KPIs):** At a glance, view important metrics such as:
  - Total Enrolled Students
  - Number of Batches In Progress
  - Average Completion Rate
  - Total Number of Batches

- **Dynamic Filtering:** Interactively filter the dashboard by:
  - University
  - College Name

- **Visualizations:**
  - **Top 10 Colleges by Progress:** A bar chart showcasing the colleges with the highest average completion rates.
  - **Student Progress Distribution:** A bar chart that categorizes and displays the number of batches in different progress brackets (e.g., 0-19%, 20-50%, 51-100%).

## Data Source

The dashboard is powered by the `Academic_Session_Tracker - Naan Mudhalvan.xlsx` Excel file. It reads data from two sheets:
- `Intervention Tracker`: Contains detailed data for each batch.
- `Summary`: Contains overall summary statistics.

## How to Run the Dashboard

1.  **Prerequisites:**
    - Python 3.x
    - An Excel file named `Academic_Session_Tracker - Naan Mudhalvan.xlsx` in the root directory with the required sheets.

2.  **Setup:**
    - Clone this repository.
    - It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
    - Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run:**
    - Start the Streamlit application:
    ```bash
    streamlit run dashboard.py
    ```
    - The dashboard will open in your web browser.
