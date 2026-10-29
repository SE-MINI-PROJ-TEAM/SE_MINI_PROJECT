"""Static vocabulary for the synthetic seed data."""

FIRST_NAMES = [
    "Aarav", "Aditi", "Aditya", "Akash", "Ananya", "Anika", "Arjun", "Bhavya", "Chaitra", "Deepak",
    "Divya", "Farhan", "Gauri", "Harsh", "Ishaan", "Jahnavi", "Karthik", "Kavya", "Lakshmi", "Manish",
    "Meera", "Nikhil", "Nisha", "Om", "Pooja", "Pranav", "Priya", "Rahul", "Riya", "Rohan",
    "Sanjana", "Shreya", "Siddharth", "Sneha", "Suresh", "Tanvi", "Uday", "Varun", "Vidya", "Yash",
]
LAST_NAMES = [
    "Agarwal", "Bhat", "Chandra", "Desai", "Gowda", "Hegde", "Iyer", "Joshi", "Kamath", "Kulkarni",
    "Mehta", "Menon", "Nair", "Patel", "Prabhu", "Rao", "Reddy", "Sharma", "Shetty", "Singh",
    "Srinivasan", "Subramanian", "Trivedi", "Varma", "Verma",
]

# 50 course offerings: (code, title, credits)
COURSES = [
    ("CS101", "Programming in Python", 4), ("CS102", "Data Structures", 4), ("CS103", "Discrete Mathematics", 3),
    ("CS104", "Computer Organisation", 3), ("CS201", "Algorithms", 4), ("CS202", "Database Systems", 4),
    ("CS203", "Operating Systems", 4), ("CS204", "Computer Networks", 3), ("CS205", "Software Engineering", 3),
    ("CS206", "Theory of Computation", 3), ("CS301", "Machine Learning", 4), ("CS302", "Compiler Design", 3),
    ("CS303", "Web Technologies", 3), ("CS304", "Cloud Computing", 3), ("CS305", "Information Security", 3),
    ("CS306", "Computer Graphics", 3), ("CS307", "Distributed Systems", 3), ("CS308", "Human-Computer Interaction", 3),
    ("CS401", "Deep Learning", 4), ("CS402", "Natural Language Processing", 3), ("CS403", "Big Data Analytics", 3),
    ("CS404", "Mobile Application Development", 3), ("CS405", "Blockchain Fundamentals", 3), ("CS406", "Embedded Systems", 3),
    ("MA101", "Engineering Mathematics I", 4), ("MA102", "Engineering Mathematics II", 4), ("MA201", "Linear Algebra", 3),
    ("MA202", "Probability and Statistics", 3), ("MA203", "Numerical Methods", 3), ("MA301", "Optimisation Techniques", 3),
    ("PH101", "Engineering Physics", 3), ("PH102", "Physics Laboratory", 2), ("CH101", "Engineering Chemistry", 3),
    ("EC101", "Basic Electronics", 3), ("EC201", "Digital Signal Processing", 4), ("EC202", "Microprocessors", 3),
    ("EC301", "Communication Systems", 3), ("EE101", "Electrical Circuits", 3), ("ME101", "Engineering Mechanics", 3),
    ("ME102", "Engineering Graphics", 2), ("HS101", "Technical Communication", 2), ("HS102", "Professional Ethics", 2),
    ("HS201", "Principles of Economics", 3), ("HS202", "Organisational Behaviour", 3), ("MG101", "Entrepreneurship", 3),
    ("MG201", "Project Management", 3), ("DS101", "Introduction to Data Science", 3), ("DS201", "Data Visualisation", 3),
    ("AI101", "Artificial Intelligence", 4), ("AI201", "Reinforcement Learning", 3),
]

# Raw (un-normalised) rubric templates; the seeder normalises them to 100% like the real API does.
RUBRIC_TEMPLATES = [
    [("Assignments", "Assignments", 20), ("Mid-term Exam", "Exams", 30), ("Project", "Projects", 20), ("End-term Exam", "Exams", 30)],
    [("Lab Assignments", "Assignments", 25), ("Mid-term Exam", "Exams", 25), ("Final Exam", "Exams", 35)],
    [("Assignments", "Assignments", 10), ("Capstone Project", "Projects", 40), ("Final Exam", "Exams", 50)],
    [("Quizzes", "Assignments", 15), ("Assignments", "Assignments", 15), ("Mid-term Exam", "Exams", 30), ("End-term Exam", "Exams", 40)],
]

DISPUTE_REASONS = [
    "I believe my end-term answer to question 4 was marked incorrectly; the method is correct.",
    "The project rubric awarded fewer marks than the posted criteria; please re-evaluate.",
    "There appears to be a totalling error in my mid-term paper. Requesting a recheck.",
    "My assignment 2 submission was graded as incomplete but I submitted all parts on time.",
]
