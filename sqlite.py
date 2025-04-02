import sqlite3

# Connect to SQLite
connection = sqlite3.connect("student.db")

# Create a cursor object
cursor = connection.cursor()

# Create the STUDENT table
table_info = """
CREATE TABLE IF NOT EXISTS STUDENT (
    NAME VARCHAR(25),
    CLASS VARCHAR(25),
    SECTION VARCHAR(25),
    MARKS INT
);
"""
cursor.execute(table_info)

# Insert 50 records manually
records = [
    ("Krish", "Data Science", "A", 90),
    ("Sudhanshu", "Data Science", "B", 100),
    ("Darius", "Data Science", "A", 86),
    ("Vikash", "DEVOPS", "A", 50),
    ("Dipesh", "DEVOPS", "A", 35),
    ("Amit", "Data Science", "C", 75),
    ("Rohan", "Cyber Security", "B", 80),
    ("Mihir", "AI", "A", 92),
    ("Sara", "Cloud Computing", "C", 88),
    ("Priya", "Data Science", "A", 95),
    ("Suresh", "DEVOPS", "B", 40),
    ("Mahesh", "AI", "A", 77),
    ("John", "Cyber Security", "C", 89),
    ("Alice", "Cloud Computing", "B", 94),
    ("Bob", "Data Science", "C", 67),
    ("Charlie", "DEVOPS", "A", 72),
    ("David", "AI", "B", 91),
    ("Eve", "Cyber Security", "A", 85),
    ("Frank", "Cloud Computing", "C", 78),
    ("Grace", "Data Science", "B", 99),
    ("Helen", "DEVOPS", "C", 65),
    ("Ian", "AI", "A", 84),
    ("Jack", "Cyber Security", "B", 79),
    ("Kate", "Cloud Computing", "C", 93),
    ("Leo", "Data Science", "A", 97),
    ("Mona", "DEVOPS", "B", 55),
    ("Nancy", "AI", "C", 90),
    ("Oscar", "Cyber Security", "A", 73),
    ("Paul", "Cloud Computing", "B", 82),
    ("Quincy", "Data Science", "C", 88),
    ("Rachel", "DEVOPS", "A", 47),
    ("Steve", "AI", "B", 96),
    ("Tom", "Cyber Security", "C", 76),
    ("Uma", "Cloud Computing", "A", 89),
    ("Victor", "Data Science", "B", 92),
    ("Wendy", "DEVOPS", "C", 53),
    ("Xavier", "AI", "A", 98),
    ("Yasmine", "Cyber Security", "B", 74),
    ("Zack", "Cloud Computing", "C", 95),
    ("Aarav", "Data Science", "A", 66),
    ("Bhavya", "DEVOPS", "B", 81),
    ("Chetan", "AI", "C", 87),
    ("Divya", "Cyber Security", "A", 99),
    ("Eshan", "Cloud Computing", "B", 71),
    ("Fiona", "Data Science", "C", 83),
    ("Gautam", "DEVOPS", "A", 45),
    ("Harsha", "AI", "B", 94),
    ("Isha", "Cyber Security", "C", 72),
    ("Jatin", "Cloud Computing", "A", 91),
    ("Kiran", "Data Science", "B", 85),
]

# Insert records into the database
cursor.executemany("INSERT INTO STUDENT VALUES (?, ?, ?, ?)", records)

# Display all the records
print("The inserted records are:")
data = cursor.execute("SELECT * FROM STUDENT")
for row in data:
    print(row)

# Commit changes and close connection
connection.commit()
connection.close()
