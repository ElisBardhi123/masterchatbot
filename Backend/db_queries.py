import mysql.connector
import json
import random
import string

cnx = mysql.connector.connect(user='root',
                              password='',
                              host='localhost',
                              port=3306,
                              database='chatbot')

cursor = cnx.cursor()

def generate_random_string():
    return ''.join(random.choices(string.hexdigits, k=24))

def getResult():
    cursor = prepareDataFromDatabase()
    init_chat_bot_sample_questions_bachelor = []
    init_chat_bot_sample_questions_master = []
    for documents in cursor:
        if documents["scope"] == "bachelor":
            if isinstance(documents["questions"], list):
                for item in documents["questions"]:
                    init_chat_bot_sample_questions_bachelor.append(item)
            else:
                init_chat_bot_sample_questions_bachelor.append(documents["questions"])
        else:
            if isinstance(documents["questions"], list):
                for item in documents["questions"]:
                    init_chat_bot_sample_questions_master.append(item)
            else:
                init_chat_bot_sample_questions_master.append(documents["questions"])

    return init_chat_bot_sample_questions_bachelor, init_chat_bot_sample_questions_master


def getResponses():
    result = []
    cursor.execute("SELECT * FROM responses WHERE id != 0")
    responses = cursor.fetchall()
    column_names = [id[0] for id in cursor.description]
    for entry in responses:
        r_object = {}
        for i, value in enumerate(entry):
            r_object[column_names[i]] = value
        result.append(r_object)
    return result

def getResponseIdByQuestion(question):
    cursor.execute(f'SELECT response_id FROM questions WHERE question = "{question}" AND response_id != 0')
    return cursor.fetchall().pop()[0]

def getResponseByResponseId(response_id):
    cursor.execute(f'SELECT responses FROM responses WHERE id = "{response_id}"')
    return cursor.fetchall().pop()[0]

def getQuestionsByResponseId(response_id):
    cursor.execute(f'SELECT question FROM questions WHERE response_id = "{response_id}" AND revised = 1')
    result = cursor.fetchall()
    return [question for question, in result]

def getUnrevisedQuestions():
    cursor.execute(f'SELECT id, question FROM questions WHERE revised = 0')
    result = cursor.fetchall()
    return [[question[0], question[1]] for question in result]

def getLinksByResponseId(response_id):
    cursor.execute(f'SELECT link FROM links WHERE response_id = "{response_id}"')
    result = cursor.fetchall()
    return [link for link, in result]

def prepareDataFromDatabase():
    responses = getResponses()
    for response in responses:
        response["questions"] = getQuestionsByResponseId(response["id"])
        response["links"] = getLinksByResponseId(response["id"])
    return responses

def getResponseByQuestion(question):
    response_id = getResponseIdByQuestion(question)
    return {"id": response_id,"response": getResponseByResponseId(response_id), "links": getLinksByResponseId(response_id)}

def getTagsFromQuestions(questions):
    categories = []
    for question in questions:
        categories.append(getTagFromQuestion(question))
    return categories

def getTagFromQuestion(question):
    cursor.execute(f'SELECT tag FROM responses as r JOIN questions as q ON r.id = q.response_id WHERE q.question = "{question}"')
    return cursor.fetchall().pop()[0]

def getQuestionsByTag(tag):
    cursor.execute(
        f'SELECT question FROM questions as q JOIN responses as r ON r.id = q.response_id WHERE r.tag = "{tag}"')
    result = cursor.fetchall()
    return [question for question, in result]

def getTagsByScope(scope):
    cursor.execute(f'SELECT DISTINCT tag from responses WHERE tag IS NOT NULL AND scope = "{scope}"')
    result = cursor.fetchall()
    return [tag for tag, in result]

def getResponsesByTag(tag, scope):
    sql = f'SELECT id, responses from responses WHERE tag = "{tag}" AND scope = "{scope}"'
    cursor.execute(sql)
    result = cursor.fetchall()
    return [[tag[0], tag[1]] for tag in result]

def updateQuestion(question_id, response_id):
    sql = "UPDATE questions SET response_id = %s, revised = 1 WHERE id = %s"
    values = (response_id, question_id)
    cursor.execute(sql, values)
    cnx.commit()

def deleteQuestion(id):
    sql = f'DELETE FROM questions WHERE id = "{id}"'
    cursor.execute(sql)
    cnx.commit()

def getQuestionId(question):
    cursor.execute(f'SELECT id FROM questions WHERE question = "{question}"')
    return cursor.fetchall().pop()[0]

def insertNewResponse(response, tag, scope):
    sql = "INSERT INTO responses (id, responses, tag, scope) VALUES (%s, %s, %s, %s)"
    id = generate_random_string()
    values = (id, response, tag, scope)
    cursor.execute(sql, values)
    cnx.commit()
    return id

def insertNewLog(question_id, response_id, scope):
    sql = f'INSERT INTO logs (question_id, response_id, scope, timestamp) VALUES ({question_id},"{response_id}", "{scope}" , CURRENT_TIMESTAMP)'
    cursor.execute(sql)
    cnx.commit()
    return cursor.lastrowid
def insertNewQuestion(question, response_id='0'):
    sql = "INSERT INTO questions (question, response_id) VALUES (%s, %s)"
    values = (question, response_id)
    cursor.execute(sql, values)
    cnx.commit()
    return cursor.lastrowid

def getTopFiveAskedQuestions():
    sql = "SELECT q.question, COUNT(l.question_id) as amount FROM `logs` as l join questions as q on l.question_id = q.id GROUP BY q.question LIMIT 5"
    cursor.execute(sql)
    result = cursor.fetchall()
    return [[question[0], question[1]] for question in result]

def getScopesFromLog():
    sql = "SELECT scope, count(scope) FROM logs GROUP By scope"
    cursor.execute(sql)
    result = cursor.fetchall()
    return [[scope[0], scope[1]] for scope in result]

def getTagsFromLog():
    sql = "SELECT r.tag, COUNT(r.tag) FROM logs as l join responses as r on l.response_id = r.id GROUP BY r.tag"
    cursor.execute(sql)
    result = cursor.fetchall()
    return [[tag[0], tag[1]] for tag in result]


def insertLinkToResponse(link, response_id):
    sql = f'INSERT INTO links (link, response_id) VALUES ("{link}","{response_id}")'
    cursor.execute(sql)
    cnx.commit()
    return cursor.lastrowid


def getEmailFromQuestionId(question_id):
    cursor.execute(f'SELECT email FROM logs WHERE question_id = "{question_id}"')
    return cursor.fetchall().pop()[0]


def getNumberOfQuestionsFromLogs():
    sql = 'SELECT "Nicht beantwortete Fragen" AS Name, COUNT(question_id) FROM logs WHERE response_id = 0 ' \
          'UNION ' \
          'SELECT "Beantwortete Fragen" AS Name, COUNT(question_id) FROM logs WHERE response_id <> 0 '
    cursor.execute(sql)
    result = cursor.fetchall()
    return [[question[0], question[1]] for question in result]

if __name__ == '__main__':
    import chatbot_controller as cb
    cb.prepareStatistics()
