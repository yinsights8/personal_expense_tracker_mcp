# Personal Expense Tracker MCP

A comprehensive Model Context Protocol (MCP) server for personal expense and income tracking with full CRUD functionality.

## 🌟 Features

- **Complete Expense Tracking**: Track expenses across multiple categories
- **Income/Credit Management**: Manage salary, freelance income, investments, and other credits
- **Full CRUD Operations**: Create, read, update, and delete expense and credit entries
- **Category Management**: Pre-defined categories for organized tracking
- **Date-based Queries**: Filter and summarize by date ranges
- **SQLite Database**: Local, fast, and reliable data storage
- **MCP Integration**: Seamlessly integrates with MCP-compatible applications

## 📁 Categories Supported

### Expense Categories
- **Food**: groceries, fruits_vegetables, dining_out, coffee_tea, snacks, delivery_fees
- **Transport**: fuel, public_transport, cab_ride_hailing, parking, tolls, vehicle_service
- **Housing**: rent, maintenance_hoa, property_tax, repairs_service, cleaning, furnishing
- **Utilities**: electricity, water, gas, internet_broadband, mobile_phone, tv_dth
- **Health**: medicines, doctor_consultation, diagnostics_labs, insurance_health, fitness_gym
- **Education**: books, courses, online_subscriptions, exam_fees, workshops
- **Family & Kids**: school_fees, daycare, toys_games, clothes, events_birthdays
- **Entertainment**: movies_events, streaming_subscriptions, games_apps, outing
- **Shopping**: clothing, footwear, accessories, electronics_gadgets, appliances, home_decor
- **Subscriptions**: saas_tools, cloud_ai, newsletters, music_video, storage_backup
- **Personal Care**: salon_spa, grooming, cosmetics, hygiene
- **Gifts & Donations**: gifts_personal, charity_donation, festivals
- **Finance Fees**: bank_charges, late_fees, interest, brokerage
- **Business**: software_tools, hosting_domains, marketing_ads, contractor_payments, travel_business, office_supplies
- **Travel**: flights, hotels, train_bus, visa_passport, local_transport, food_travel
- **Home**: household_supplies, cleaning_supplies, kitchenware, small_repairs, pest_control
- **Pet**: food, vet, grooming, supplies
- **Taxes**: income_tax, gst, professional_tax, filing_fees
- **Investments**: mutual_funds, stocks, fd_rd, gold, crypto, brokerage_fees

### Credit/Income Categories
- **Employment**: salary, freelance, business_income
- **Investments**: dividends, interest, capital_gains
- **Loans**: personal_loan, student_loan, mortgage
- **Other**: gift, refund, other

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yinsights8/personal_expense_tracker_mcp.git
   cd personal_expense_tracker_mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # or if using uv
   uv sync
   ```

3. Run the MCP server:
   ```bash
   python main.py
   ```

## 📖 Usage

### MCP Integration

This server provides the following MCP tools:

#### Expense Management
- `add_expense(date, amount, category, subcategory="", note="")` - Add a new expense entry
- `list_expenses(start_date, end_date)` - List expenses within a date range
- `edit_expense(expense_id, date=None, amount=None, category=None, subcategory=None, note=None)` - Edit an existing expense
- `delete_expense(expense_id)` - Delete an expense entry
- `summarize(start_date, end_date, category=None)` - Summarize expenses by category

#### Credit/Income Management
- `add_credit(date, amount, category, subcategory="", note="")` - Add a new credit entry
- `list_credits(start_date, end_date)` - List credits within a date range
- `edit_credit(credit_id, date=None, amount=None, category=None, subcategory=None, note=None)` - Edit an existing credit
- `delete_credit(credit_id)` - Delete a credit entry
- `summarize_credits(start_date, end_date, category=None)` - Summarize credits by category

#### Category Information
- `categories()` - Access the JSON resource containing all available categories

### Example Usage

```python
# Add an expense
add_expense("2024-01-15", 45.99, "food", "dining_out", "Lunch with colleagues")

# Add income
add_credit("2024-01-01", 5000.00, "employment", "salary", "Monthly salary")

# List expenses for January
list_expenses("2024-01-01", "2024-01-31")

# Edit an expense (change amount)
edit_expense(5, amount=55.99)

# Summarize expenses by category
summarize("2024-01-01", "2024-01-31")
```

## 🗄️ Database Schema

The application uses SQLite with two main tables:

### Expenses Table
```sql
CREATE TABLE expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT '',
    note TEXT DEFAULT ''
);
```

### Credits Table
```sql
CREATE TABLE credits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT '',
    note TEXT DEFAULT ''
);
```

## 🛠️ Development

### Project Structure
```
personal_expense_tracker_mcp/
├── main.py                 # Main MCP server implementation
├── src/
│   ├── categories.json     # Category definitions
│   ├── initialize_db.py    # Database initialization
│   └── personal_expence_tracker.db  # SQLite database (not tracked)
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── pyproject.toml         # Project configuration
└── uv.lock               # Dependency lock file
```

### Adding New Categories

Edit `src/categories.json` to add new categories or subcategories. The JSON structure supports nested categorization.

### Database Management

The database is automatically initialized when the server starts. Database files are excluded from version control for privacy.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔒 Privacy & Security

- Database files are excluded from version control
- All financial data is stored locally on your device
- No data is transmitted to external servers
- MCP server runs locally for maximum privacy

## 📞 Support

If you encounter any issues or have questions:
1. Check the existing issues on GitHub
2. Create a new issue with detailed information
3. Include error messages, steps to reproduce, and your environment details

---

**Built with ❤️ for personal finance management**