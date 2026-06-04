# Monthly Budget Planner 💰

A modern, full-featured web application for managing personal finances built with Flask and SQLite.

![Budget Planner](https://via.placeholder.com/800x400/667eea/ffffff?text=Monthly+Budget+Planner)

## ✨ Features

### 🎨 Modern UI/UX
- Full-screen gradient background with animated particles
- Glassmorphism design with blur effects
- Smooth animations and transitions
- Fully responsive design for all devices

### 📊 Dashboard
- **Total Income** - View all your income sources
- **Total Expenses** - Track your spending
- **Remaining Balance** - See what's left
- **Monthly Budget Tracker** - Set and monitor your budget with progress bars

### 💰 Transaction Management
- **Add Income** - Record income from various sources (Salary, Freelance, Business, etc.)
- **Add Expense** - Log expenses by category (Food, Transport, Utilities, etc.)
- **View Transactions** - See all your financial records
- **Edit/Delete** - Modify or remove any transaction

### 📈 Visual Analytics
- **Expense Breakdown Chart** - Doughnut chart showing spending by category
- **Monthly Trend Chart** - Line chart showing income vs expenses over 6 months

### 🔐 User Authentication
- Secure user registration and login
- Password hashing with PBKDF2
- Session management

### 📥 Export Data
- Download monthly records as CSV file
- Includes all income, expenses, and summary

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/likhith0501/monthly-buget-planner.git
   cd monthly-buget-planner
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   - Navigate to: http://127.0.0.1:5000

## 📁 Project Structure

```
monthly-buget-planner/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── instance/
│   └── budget_planner.db # SQLite database (auto-created)
├── static/
│   └── style.css         # Additional CSS styles
└── templates/
    ├── base.html         # Base template
    ├── index.html        # Main dashboard (SPA)
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── add_income.html   # Add income form
    ├── add_expense.html  # Add expense form
    ├── transactions.html # View all transactions
    ├── edit_income.html  # Edit income
    └── edit_expense.html # Edit expense
```

## 🛠️ Technologies Used

- **Flask** - Web framework
- **Flask-SQLAlchemy** - Database ORM
- **Flask-Login** - User authentication
- **SQLite** - Database
- **Chart.js** - Interactive charts
- **Bootstrap 5** - UI components
- **Font Awesome** - Icons

## 📸 Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x400/11998e/ffffff?text=Dashboard+View)

### Add Transaction
![Add Transaction](https://via.placeholder.com/800x400/4facfe/ffffff?text=Add+Transaction)

### Transactions List
![Transactions](https://via.placeholder.com/800x400/4f46e5/ffffff?text=Transactions+List)

## 🔒 Security Features

- Password hashing using PBKDF2 algorithm
- CSRF protection via Flask-WTF
- Secure session management
- User-specific data isolation

## 📊 Database Schema

### Users Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| username | String | Unique username |
| email | String | Unique email |
| password | String | Hashed password |
| created_at | DateTime | Account creation date |

### Income Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key (User) |
| amount | Float | Income amount |
| source | String | Income source |
| date | Date | Transaction date |

### Expense Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key (User) |
| amount | Float | Expense amount |
| category | String | Expense category |
| date | Date | Transaction date |

### Budget Table
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key (User) |
| monthly_budget | Float | Budget amount |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Likhith**
- GitHub: [@likhith0501](https://github.com/likhith0501)
- Repository: [Monthly Budget Planner](https://github.com/likhith0501/monthly-buget-planner)

## 🙏 Acknowledgments

- Flask community
- Chart.js team
- Bootstrap team
- Font Awesome icons

## 📧 Contact

If you have any questions or suggestions, feel free to reach out!

---

**Made with ❤️ using Flask**