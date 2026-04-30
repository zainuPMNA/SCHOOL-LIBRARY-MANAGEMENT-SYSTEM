# 📚 School Library Management System

A comprehensive, full-stack Python web application designed exclusively for **YES PA INAMDAR ENGLISH MEDIUM SCHOOL AND JUNIOR COLLEGE**. This system digitizes and streamlines the entire library administration process, featuring a modern, responsive Glassmorphism user interface.

**Developed by:** Zain (@zainuPMNA)

## ✨ Core Features

*   👥 **Student Data Management:** Add, edit, delete, and search students. Includes a robust bulk CSV import engine with strict duplication validation (Name, Roll No, Class, and Division).
*   📖 **Book Inventory:** Complete digital cataloging of books. Includes a multi-field advanced search engine (Title, Subject, Category, Publisher, Year) and CSV import/export capabilities.
*   🔄 **Circulation Engine:** Track book issuances and returns. Automatically calculates 7-day due dates and tracks late returns.
*   📊 **Advanced Analytics Dashboard:** Interactive data visualizations (powered by Chart.js) tracking monthly reading trends, most active classes, popular subjects, and top 50 student readers.
*   📄 **Comprehensive Reporting:** Instantly generate and download library data reports in **CSV**, **PDF**, and **Microsoft Word (.docx)** formats.
*   🎓 **Bulk Student Promotion:** Interactive UI to fetch students by class and use checkboxes to either promote them to a new grade or securely delete their records upon graduation.
*   💾 **Backup & Restore:** One-click SQLite database backup and restoration system for ultimate data security.

## 💻 Technology Stack

*   **Backend:** Python 3, Flask, SQLAlchemy (ORM)
*   **Database:** SQLite (`database.db`)
*   **Frontend:** HTML5, Vanilla CSS3 (Glassmorphism aesthetics), JavaScript
*   **Data Visualization:** Chart.js
*   **Document Generation:** `python-docx` (Word), `xhtml2pdf` (PDF), `csv` (Excel)

## 🚀 How to Run Locally

1. Clone this repository:
   ```bash
   git clone https://github.com/zainuPMNA/SCHOOL-LIBRARY-MANAGEMENT-SYSTEM.git
   cd SCHOOL-LIBRARY-MANAGEMENT-SYSTEM
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows use: env\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the Flask application:
   ```bash
   python app.py
   ```
5. Open your web browser and navigate to `http://127.0.0.1:5000`

## 📜 License
Proprietary Software. Unauthorized copying, modification, or distribution is strictly prohibited.
