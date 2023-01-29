import mysql.connector
import json

# Connect to the database
cnx = mysql.connector.connect(user='root',
                              password='',
                              host='localhost',
                              port=3306,
                              database='chatbot')

# Do something with the connection
question_array = ["Wie viele Wahlpflichtmodule gibt es?",
                  "Ich habe den Plan im Jahre 2021, ab September, an der London South Bank University ein Auslandssemester zu machen. Dies sind die Module, die an der Hochschule, für meine im Ausland zu erbringende Zeit in Frage kommen würden. Business Information Technology, Business Intelligence, Business or Computing, International Foundation Course. Ich wollte wissen, ob diese Module mir dann auch hier an der THM anerkannt werden? Falls sie die falsche Ansprechperson sind, wissen sie mit wem ich darüber sprechen sollte?“.",
                  "Ich habe den Plan ein Auslandsemester zu machen und wollte wissen, ob die Module Business Information Technology, Business Intelligence, Business or Computing, International Foundation Course auch an der THM anerkannt werden?",
                  "Kann ich mir Module aus einem Auslandsemester anerkennen lassen?",
                  "Wo ist der Campus für Wirtschaftsinformatik",
                  "Wann kann ich mich für die Bachelorarbeit anmelden?",
                  "Dauer des Studiums?",
                  "Gibt es ein Vorpraktikum, das man vor der Immatrikulation ablegen muss?",
                  "Im welchen Semester fängt der Studiengang für Wirtschaftsinformatik an?",
                  "Wann startet das Studium für Wirtschaftsinformatik?",
                  "Wie viele Wahlpflichtmodule gibt es?",
                  "Ich habe den Plan im Jahre 2021, ab September, an der London South Bank University ein Auslandssemester zu machen. Dies sind die Module, die an der Hochschule, für meine im Ausland zu erbringende Zeit in Frage kommen würden. Business Information Technology, Business Intelligence, Business or Computing, International Foundation Course. Ich wollte wissen, ob diese Module mir dann auch hier an der THM anerkannt werden? Falls sie die falsche Ansprechperson sind, wissen sie mit wem ich darüber sprechen sollte?",
                  "Ich habe den Plan ein Auslandsemester zu machen und wollte wissen, ob die Module Business Information Technology, Business Intelligence, Business or Computing, International Foundation Course auch an der THM anerkannt werden?",
                  "Kann ich mir Module aus einem Auslandsemester anerkennen lassen?",
                  "Wo finde ich Dozierende und Semesterarbeiten für die Wahlpflichtmodule des MSc Wirtschaftsinformatik?"]

cursor = cnx.cursor()
try:
    cursor.execute("CREATE TABLE responses ( id VARCHAR(24) PRIMARY KEY,"
               "scope VARCHAR(20),"
               "responses TEXT,"
               "tag TEXT);")
except Exception as e:
    if e.sqlstate == '42S01':
        print('Table "responses" exists. Creation will be skipped')

try:
    cursor.execute("CREATE TABLE questions (id INT AUTO_INCREMENT PRIMARY KEY, "
               "question LONGTEXT NOT NULL, "
               "response_id VARCHAR(24), "
               "FOREIGN KEY (response_id) REFERENCES responses(id) );")
except Exception as e:
    if e.sqlstate == '42S01':
        print('Table "questions" exists. Creation will be skipped')

try:
    cursor.execute("CREATE TABLE links "
               "(id INT AUTO_INCREMENT PRIMARY KEY,"
               "link LONGTEXT NOT NULL,"
               "response_id VARCHAR(24),"
               "FOREIGN KEY (response_id) REFERENCES responses(id))")
except Exception as e:
    if e.sqlstate == '42S01':
        print('Table "links" exists. Creation will be skipped')

try:
    cursor.execute("CREATE TABLE logs (id INT AUTO_INCREMENT PRIMARY KEY,"
                   "question_id INT(11),"
                   "FOREIGN KEY (question_id) REFERENCES questions(id),"
                   "response_id VARCHAR(24),"
                   "FOREIGN KEY (response_id) REFERENCES res ponses(id),"
                   "timestamp DATETIME)")
except Exception as e:
    if e.sqlstate == '42S01':
        print('Table "links" exists. Creation will be skipped')

# open the file
with open('chatbot_questions.json') as json_file:
    # load the contents of the file into a variable
    data = json.load(json_file)

# the data variable now contains the contents of the JSON file as a Python object

try:
    for response in data:
        sql = "INSERT INTO responses (id, responses, scope, tag) VALUES (%s, %s, %s, %s)"
        values = (response["_id"],
                  response["responses"],
                  response["scope"],
                  response["tag"])
        cursor.execute(sql, values)
        cnx.commit()

        for question in response["questions"]:
            sql = "INSERT INTO questions (question, response_id) VALUES (%s, %s)"
            values = (question, response["_id"])
            cursor.execute(sql, values)
            cnx.commit()

        for link in response["links"]:
            sql = "INSERT INTO links (link, response_id) VALUES (%s, %s)"
            values = (link,response["_id"])
            cursor.execute(sql, values)
            cnx.commit()
except Exception as e:
    print("There is an Error")

# Close the connection
cnx.close()

