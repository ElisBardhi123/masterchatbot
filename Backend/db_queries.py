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
    cursor.execute(f'SELECT question FROM questions WHERE response_id = "{response_id}"')
    result = cursor.fetchall()
    return [question for question, in result]

def getQuestionsAndIDByResponseId(response_id):
    cursor.execute(f'SELECT id, question FROM questions WHERE response_id = "{response_id}"')
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

def insertNewQuestion(question, response_id='0'):
    sql = "INSERT INTO questions (question, response_id) VALUES (%s, %s)"
    values = (question, response_id)
    cursor.execute(sql, values)
    cnx.commit()

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
    sql = "UPDATE questions SET response_id = %s WHERE id = %s"
    values = (response_id, question_id)
    cursor.execute(sql, values)
    cnx.commit()

def insertNewResponse(response, tag, scope):
    sql = "INSERT INTO responses (id, responses, tag, scope) VALUES (%s, %s, %s, %s)"
    id = generate_random_string()
    values = (id, response, tag, scope)
    cursor.execute(sql, values)
    cnx.commit()
    return id

def deleteQuestion(id):
    sql = f'DELETE FROM questions WHERE id = "{id}"'
    cursor.execute(sql)
    cnx.commit()

def insertNewLog(question_id, response_id):
    sql = f'INSERT INTO logs (question_id, response_id, timestamp) VALUES ({question_id},{response_id}, CURRENT_TIMESTAMP)'
    cursor.execute(sql)
    cnx.commit()
    return cursor.lastrowid

def getQuestionId(question):
    cursor.execute(f'SELECT id FROM questions WHERE question = "{question}"')
    return cursor.fetchall().pop()[0]

#if __name__ == '__main__':
#    print(insertNewLog(1, "0"))

