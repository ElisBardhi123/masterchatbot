import db_queries as queries
import ChatBot.src.chatbot_semantic as semantic_bot
import ChatBot.src.chatbot_spacy as spacy_bot
import matplotlib.pyplot as plt
import time
import json

def getChatbot():
    content_bachelor, content_master = queries.getResult()
    return semantic_bot.ChatBot(content_bachelor, content_master)

def getResponseByQuestion(sample_question):
    response = queries.getResponseByQuestion(sample_question)
    print(response["response"])
    print(f'Links: {response["links"]}')
    return response

def insertNewQuestion(new_question, question):
    question_id = False
    if new_question:
        question_id = queries.insertNewQuestion(question=question)
    print("Es tut mir leid, dass ich dir nicht helfen könnte.")
    print(
        "Wir werden Ihre Frage an der Sekretariat weiterleiten und Ihnen eine Antwort dazu so schnell wie möglich per Mail zuschicken lassen.")
    print("Das Gespräch wird neugestartet\n")
    return question_id

def updateQuestion(question, response):
    queries.updateQuestion(question, response)
    print("Der Frage wurde die neue Antwort zugewiesen.")
    index = input("Möchten Sie Links hinzufügen?\n")
    if index == "Ja":
        while True:
            link = input("Bitte geben Sie einen Link ein (0 für Abbrechen)\n")
            if link == "0":
                break
            else:
                queries.insertLinkToResponse(link, response)
                print("Der Link wurde erfolgreich hinzugefügt\n")
    print("Bitte trainieren Sie das Modell, um die neuen Fragen zur Verfügung zu stellen")
    print("Das Gespräch wird neugestartet\n")

def insertNewTagToResponse(tag, question):
    response = input("Wie lautet die neue Antwort?")
    response_id = queries.insertNewResponse(response, tag, scope)
    updateQuestion(question, response_id)

def deleteQuestion(id):
    queries.deleteQuestion(id)
    print("Die Frage wurde gelöscht.")
    print("Das Gespräch wird neugestartet\n")

def printTopQuestionsToText(top_questions):
    print("\n\nTop 5 Fragen: \n")
    for index, question in enumerate(top_questions):
        print(f'{index}. {question[0]} ({question[1]} Mal aufgerufen)')

def showPieChart(scopes):
    question_counts = [scope[1] for scope in scopes]
    plt.pie(question_counts, labels=[scope[0] + " (" + str(scope[1]) + ")" for scope in scopes])
    plt.axis('equal')
    plt.title('Anzahl')
    plt.show()

def prepareStatistics():
    top_questions = queries.getTopFiveAskedQuestions()
    printTopQuestionsToText(top_questions)
    scopes = queries.getScopesFromLog()
    showPieChart(scopes)
    tags = queries.getTagsFromLog()
    showPieChart(tags)

def getResponses():
    responses = queries.getResponses()
    for response in responses:
        questions = queries.getQuestionsByResponseId(response_id=response["id"])
        response["questions"] = questions
        links = queries.getLinksByResponseId(response_id=response["id"])
        response["links"] = links
    return responses

def downloadQuestionsAndResponses():
    print("Fragen werden heruntergeladen.....")
    data = getResponses()
    name = time.time()
    with open(f'chatbot_questions/chatbot_questions_{name}.json', "w") as outfile:
        json.dump(data, outfile,indent=4, ensure_ascii=False)
    print(f'Fragen wurden in der Datei "chatbot_questions_{name}" gespeichert')


if __name__ == '__main__':
    #scope = input("Willkomen zu dem THM Chatbot. Haben Sie eine Frage über Bachelor oder Master?\n")
    scope = "bachelor"
    #user = input("Welcher User sind Sie ?\n")
    user = "student"
    chatbot = getChatbot()
    while True:
        if user == "student":
            new_question = False
            index = input("\n\nWie kann ich Ihnen helfen (Student)?\n"
                             "1. Fragen stellen\n"
                             "2. User ändern\n"
                             "0. Beenden")
            if index == "0":
                break
            elif index == "2":
                user = "admin"
            else:
                question = input("\nWie lautet Ihre Frage?")
                top_questions = chatbot.chat(question, scope)
                sample_question, max_score = top_questions.pop(0)
                response = queries.getResponseByQuestion(sample_question)
                answer = response["response"]
                links = response["links"]
                if max_score < 0.99:
                    new_question = True
                if max_score >= 0.7:
                    print(answer)
                    print(f'Links: {links}')
                    print(f'Ähnlichkeit: {max_score}')
                elif max_score >= 0.35:
                    print("Wir nehmen an, dass es um folgende Frage geht: " + sample_question + "\nDaraus ergibt sich folgende Antwort: " + answer)
                else:
                    print("Leider konnte keine passende Antwort auf Ihre Frage gefunden werden. Bitte schauen Sie in folgendes FAQ.")

                boolean = input("\nSind Sie mit der Antwort zufrieden?\n")
                if boolean == "Ja":
                    print("Vielen Dank für Ihre Rückmeldung! Das Gespräch wird neugestartet\n\n")
                    if new_question:
                        question_id = queries.insertNewQuestion(question=question, response_id=response["id"])
                    else:
                        question_id = queries.getQuestionId(sample_question)
                    queries.insertNewLog(question_id, response["id"], scope)
                else:
                    print("Welche der folgenden Fragen ist Ihrer Frage ähnlich?\n")
                    for index, top_question in enumerate(top_questions):
                        print(f'{index+1}: {top_question[0]} ({top_question[1]})')
                    print(f'0: Keine')
                    index = input()
                    if index != '0':
                        response = getResponseByQuestion(top_questions[int(index)-1][0])
                        if new_question:
                            question_id = queries.insertNewQuestion(question=question, response_id=response["id"])
                        else:
                            question_id = queries.getQuestionId(sample_question)
                        queries.insertNewLog(question_id, response["id"], scope)
                        print("Vielen Dank für Ihre Rückmeldung! Das Gespräch wird neugestartet\n\n")
                    else:
                        top_questions = list(set([question[0] for question in top_questions]))
                        tags = queries.getTagsFromQuestions(top_questions)
                        tags = list(set(tags))
                        print("Zu welcher Kategorie gehört Ihre Frage?")
                        for index, tag in enumerate(tags):
                            print(f'{index+1}: {tag}')
                        index = input(f'0: Keine\n')
                        if index != '0':
                            similar_questions = queries.getQuestionsByTag(tags[int(index) - 1])
                            for index, similar_question in enumerate(similar_questions):
                                print(f'{index + 1}: {similar_question}')
                            index = input(f'0: Keine\n')
                            if index != '0':
                                response = getResponseByQuestion(sample_question[int(index)+1])
                                if new_question:
                                    question_id = queries.insertNewQuestion(question=question,
                                                                            response_id=response["id"])
                                else:
                                    question_id = queries.getQuestionId(sample_question)
                                queries.insertNewLog(question_id, response["id"], scope)
                                print("Vielen Dank für Ihre Rückmeldung! Das Gespräch wird neugestartet\n\n")
                            else:
                                question_id = insertNewQuestion(new_question, question)
                                queries.insertNewLog(question_id, 0, scope)
                        else:
                            question_id = insertNewQuestion(new_question, question)
                            queries.insertNewLog(question_id, 0, scope)

#       ADMIN Part
        elif user == "admin":
            index = input("\n\nWie kann ich Ihnen helfen (Admin)?\n"
                             "1. Modell trainieren\n"
                             "2. Fragen bearbeiten\n"
                             "3. User ändern\n"
                             "4. Statistiken aufrufen\n"
                             "5. Fragen herunterladen\n"
                             "0. Beenden")
            if index == "0":
                break
            elif index == "1":
                print("Das Chatbot wird neu trainiert. Bitte warten Sie!")
                chatbot = getChatbot()
                print("Training erfolgreich")
            elif index == "3":
                user = "student"
                pass
            elif index == "4":
                prepareStatistics()
            elif index == "5":
                downloadQuestionsAndResponses()
                pass
            elif index == "2":
                questions = queries.getUnrevisedQuestions()
                if len(questions) == 0:
                    print("Es sind keine neue Fragen vorhanden")
                    print("Das Gespräch wird neugestartet")
                else:
                    print("\n\nBitte wählen Sie eine Frage zum Bearbeiten aus:")
                    for index, question in enumerate(questions):
                        print(f'{index+1}: {question[1]}')
                    print("------------------------------------")
                    index = input("0: Zurück zum Anfang")
                    if index == "0":
                        pass
                    else:
                        question = questions[int(index)-1]
                        tags = queries.getTagsByScope(scope)
                        print("\n\nZu welcher Kategorie gehört diese Frage?")
                        for index, tag in enumerate(tags):
                            print(f'{index+1}: {tag}')
                        print("------------------------------------")
                        print(f'#: Neue Kategorie')
                        print(f'##: Frage löschen')
                        index = input("0: Zurück zum Anfang")
                        if index == "0":
                            questions = []
                            pass
                        elif index == "##":
                            deleteQuestion(question[0])
                        elif index == "#":
                            tag = input("\n\nWie lautet die neue Kategorie?")
                            insertNewTagToResponse(tag, question[0])
                        else:
                            tag = tags[int(index)-1]
                            responses = queries.getResponsesByTag(tag, scope)
                            for index, response in enumerate(responses):
                                print(f'{index + 1}: {response[1]}')
                            print(f'#: Neue Antwort')
                            index = input("0: Zurück zum Anfang")
                            if index == "0":
                                pass
                            elif index == "#":
                                insertNewTagToResponse(tag, question[0])
                            else:
                                updateQuestion(question[0], responses[int(index) - 1][0])


