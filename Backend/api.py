import datetime
import os
import random
import string
from functools import wraps

import jwt
import werkzeug
from bson import ObjectId
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
from flask_cors import CORS
from waitress import serve
from marshmallow import Schema, fields
from werkzeug.security import generate_password_hash
import logging

from API.src.database_helper import database_helper
from ChatBot.src.chatbot_semantic import ChatBot
from ChatBot.src.chatbot_spacy import ChatBotSpacy

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Th1s1ss3cr3t'
app.config['Mongo_LOCATION'] = str(os.environ.get('DATABASE', "localhost"))
app.config['Mongo_USER'] = 'cb_ritz'
app.config['Mongo_PASSWORD'] = '3290rCum#'
app.config['Mongo_DATABASE'] = 'ChatBot'
app.config['Mongo_COLLECTION'] = 'questions'
app.config['Mongo_USER_COLLECTION'] = 'users'
app.config['Mongo_USER_SESSION_COLLECTION'] = "sessions"
app.config['Mongo_CLIENTS_COLLECTION'] = 'clients'


class GetQuerySchema(Schema):
    id = fields.Str()


def get_Questions():
    global databaseHelper
    cursor_init = databaseHelper.get(collection=app.config.get('Mongo_COLLECTION'),
                                     exclude={"_id": 0, "responses": 0, "links": 0})

    init_chat_bot_sample_questions_bachelor = []
    init_chat_bot_sample_questions_master = []
    for documents in cursor_init:
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


api = Api(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
schema = GetQuerySchema()

global databaseHelper
databaseHelper = database_helper(app.config.get('Mongo_USER'), app.config.get('Mongo_PASSWORD'),
                                 app.config.get('Mongo_LOCATION'), app.config.get('Mongo_DATABASE'))

init_chat_bot_sample_questions_bachelor, init_chat_bot_sample_questions_master = get_Questions()

setting_cursor = databaseHelper.get(collection="settings")
chatbot_name = ""
for documents in setting_cursor:
    chatbot_name = documents["ChatBot"]

global chatbot_german_semantic
global chatbot_spacy

chatbot_german_semantic = ChatBot(content_bachelor=init_chat_bot_sample_questions_bachelor,
                                  content_master=init_chat_bot_sample_questions_master)

chatbot_spacy = ChatBotSpacy(content_bachelor=init_chat_bot_sample_questions_bachelor,
                             content_master=init_chat_bot_sample_questions_master)

logging.basicConfig(filename='API.log', level=logging.DEBUG,
                    format='[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    datefmt='%m-%d %H:%M:%S')


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"]
            token = str.replace(str(token), 'Bearer ', '')

        if not token:
            return make_response(jsonify({'message': 'Kein Token!'}), 401)

        try:
            data = jwt.decode(token, app.config.get("SECRET_KEY"), algorithms=["HS256"])
            usr_cursor = databaseHelper.get(collection=app.config.get('Mongo_USER_COLLECTION'),
                                            search_content={'_id': ObjectId(data['public_id'])})
            user = usr_cursor[0]
            token_cursor = databaseHelper.get(collection=app.config.get('Mongo_USER_SESSION_COLLECTION'),
                                              search_content={'token': token})
            token_query = token_cursor[0]
            if token_query is None:
                return make_response(jsonify({'message': 'Token existiert nicht!'}), 401)
            else:
                if datetime.datetime.fromtimestamp(data['exp']) >= datetime.datetime.utcnow():
                    current_user = user
                else:
                    return make_response(jsonify({'message': 'Der Token ist abgelaufen!'}), 401)
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)
        return f(current_user, *args, **kwargs)

    return decorator


class AskQuestion(Resource):
    def post(self):
        global chatbot_german_semantic
        global chatbot_spacy
        try:
            data = request.get_json()
            client_key = request.headers.get("client")
            source = request.headers.get("Origin")
            clients = databaseHelper.get(collection=app.config.get('Mongo_CLIENTS_COLLECTION'),
                                         search_content={'client_url': source})
            client = clients[0]
            if client['client_secret'] == client_key:
                question = data['message']
                scope = data["scope"]

                setting_cursor_t = databaseHelper.get(collection="settings")
                chatbot_name_t = ""
                for documents_t in setting_cursor_t:
                    chatbot_name_t = documents_t["ChatBot"]

                if chatbot_name_t == "German Semantic":
                    sample_question, max_score = chatbot_german_semantic.chat(question=question, scope=scope)
                else:
                    sample_question, max_score = chatbot_spacy.chat(question=question, scope=scope)

                answer_cursor = databaseHelper.get(collection=app.config.get('Mongo_COLLECTION'),
                                                   search_content={"questions": sample_question, "scope": scope})
                answer = []
                links = []
                for doc in answer_cursor:
                    answer = (doc["responses"])
                    links.append(doc["links"])

                log_setting_cursor = databaseHelper.get(collection="settings")
                activate_chat_logging = False
                for entry in log_setting_cursor:
                    activate_chat_logging = entry["logging"]

                if activate_chat_logging:
                    model = chatbot_name_t
                    question_content = {"question": question, "answer": answer, "score": max_score, "model": model}
                    databaseHelper.insert(collection="logging", content=question_content)

                if max_score >= 0.7:
                    response = make_response(jsonify({'message': answer, 'links': links}), 200)
                elif max_score >= 0.35:
                    response = make_response(jsonify({
                        'message': "Wir nehmen an, dass es um folgende Frage geht: " + sample_question + "\n Daraus ergibt "
                                                                                                         "sich folgende "
                                                                                                         "Antwort: " + answer,
                        'links': links}), 200)
                else:
                    response = make_response(jsonify({
                        'message': "Leider konnte keine passende Antwort auf Ihre Frage gefunden werden. Bitte schauen Sie in folgendes FAQ.",
                        'links': [[
                            "https://www.thm.de/mnd/component/edocman/faq-b-sc-wirtschaftsinformatik?Itemid=0" if scope == "bachelor" else "https://www.thm.de/mnd/component/edocman/faq-m-sc-wirtschaftsinformatik?Itemid=0"]]
                    }), 200)



            else:
                response = make_response(jsonify({'message': "Falscher API Key"}), 401)
        except Exception as e:
            logging.error(e)
            response = make_response(jsonify({'message': "Nicht autorisiert!"}), 401)
        return response


class Question(Resource):
    @token_required
    def get(self, user):
        errors = schema.validate(request.args)
        if errors:
            response = make_response(jsonify("Falscher Parameter"), 406)
            return response
        if len(request.args) == 0:
            cursor = databaseHelper.get(collection=app.config.get('Mongo_COLLECTION'))
            questions = []
            for document in cursor:
                document["_id"] = str(ObjectId(document["_id"]))
                questions.append(document)
            response = make_response(jsonify(questions), 200)
            return response
        else:
            try:
                cursor = databaseHelper.get(collection=app.config.get('Mongo_COLLECTION'),
                                            search_content={'_id': ObjectId(request.args["id"])})
                questions = []
                for document in cursor:
                    document["_id"] = str(ObjectId(document["_id"]))
                    questions.append(document)
                response = make_response(jsonify(questions), 200)
                return response
            except Exception as e:
                logging.error(e)
                response = make_response(jsonify("Diese ID ist nicht vorhanden!"), 404)
                return response

    @token_required
    def post(self, user):
        try:
            data = request.get_json()
            question = {"questions": data["questions"], "responses": data["responses"], "scope": data["scope"],
                        "links": data["links"]}
            db_response = databaseHelper.insert(collection=app.config.get('Mongo_COLLECTION'), content=question)
            response = make_response(jsonify({'message': db_response.acknowledged}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def put(self, user):
        try:
            data = request.get_json()
            new_values = {
                "$set": {"questions": data["questions"], "responses": data["responses"], "scope": data["scope"],
                         "links": data["links"]}}
            databaseHelper.updateOne(collection=app.config.get('Mongo_COLLECTION'),
                                     search_content={'_id': ObjectId(data["_id"])},
                                     new_values=new_values)
            response = make_response(jsonify({'message': 1}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def delete(self, user):
        try:
            id = request.args["id"]
            databaseHelper.deleteOne(collection=app.config.get('Mongo_COLLECTION'),
                                     search_content={'_id': ObjectId(id)})
            response = make_response(jsonify({'message': 1}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class ChatBotSettings(Resource):
    @token_required
    def get(self, user):
        content = open("API.log", "r")
        response = []
        for line in content:
            response.append(line)
        return make_response(jsonify({'message': response}))

    @token_required
    def post(self, user):
        data = request.get_json()
        name = data["chatbot"]
        global chatbot_german_semantic
        global chatbot_spacy
        try:
            init_chat_bot_questions_bachelor, init_chat_bot_questions_master = get_Questions()
            global chatbot_german_semantic
            global chatbot_spacy

            chatbot_german_semantic = ChatBot(content_bachelor=init_chat_bot_questions_bachelor,
                                              content_master=init_chat_bot_questions_master)
            chatbot_spacy = ChatBotSpacy(content_bachelor=init_chat_bot_questions_bachelor,
                                         content_master=init_chat_bot_questions_master)

            setting_cur = databaseHelper.get(collection="settings")
            id_s = None
            for doc in setting_cur:
                id_s = ObjectId(doc["_id"])

            new_value = {"$set": {"ChatBot": name}}
            result = databaseHelper.updateOne(collection="settings", search_content={"_id": id_s}, new_values=new_value)

            return make_response(jsonify({'message': result.acknowledged}), 200)
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class TrainChatBot(Resource):
    @token_required
    def get(self, user):
        try:
            global chatbot_spacy, chatbot_german_semantic, databaseHelper

            setting_cursor_t = databaseHelper.get(collection="settings")
            chatbot_name_t = ""
            for documents_t in setting_cursor_t:
                chatbot_name_t = documents_t["ChatBot"]

            cursor = databaseHelper.get(collection=app.config.get('Mongo_COLLECTION'), exclude={"_id": 0})

            sample_questions = []
            for doc in cursor:
                sample_questions.append(doc["questions"])
            init_chat_bot_questions_bachelor, init_chat_bot_questions_master = get_Questions()

            if chatbot_name_t == "German Semantic":
                content = chatbot_german_semantic.rebuildTensors(init_chat_bot_questions_bachelor,
                                                                 init_chat_bot_questions_master)
            else:
                content = chatbot_spacy.rebuildTensors(init_chat_bot_questions_bachelor, init_chat_bot_questions_master)

            response = make_response(jsonify(content), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class User(Resource):
    @token_required
    def get(self, user):
        try:
            user_cursor = databaseHelper.get(collection=app.config.get('Mongo_USER_COLLECTION'),
                                             exclude={"password": 0})
            users = []
            for user in user_cursor:
                user["_id"] = str(ObjectId(user["_id"]))
                users.append(user)
            response = make_response(jsonify(users), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def post(self, user):
        try:
            data = request.get_json()
            content = {"username": data["username"], "firstname": data["firstname"], "lastname": data["lastname"],
                       "mail": data["mail"], "password": generate_password_hash(data["password"])}
            databaseHelper.insert(collection=app.config.get('Mongo_USER_COLLECTION'), content=content)
            response = make_response(jsonify(str(data["username"]) + " added!"), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def delete(self, user):
        try:
            id = request.args["id"]
            databaseHelper.deleteOne(collection=app.config.get('Mongo_USER_COLLECTION'),
                                     search_content={'_id': ObjectId(id)})
            response = make_response(jsonify({'message': "Gelöscht"}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def put(self, user):
        try:
            data = request.get_json()
            change_id = data["_id"]
            username = data["username"]
            firstname = data["firstname"]
            lastname = data["lastname"]
            mail = data["mail"]
            password = generate_password_hash(data["password"])
            new_values = {"$set": {"username": username, "firstname": firstname, "lastname": lastname, "mail": mail,
                                   "password": password}}
            databaseHelper.updateOne(collection=app.config.get('Mongo_USER_COLLECTION'),
                                     search_content={'_id': ObjectId(change_id)}, new_values=new_values)
            response = make_response(jsonify({'message': str(username) + " changed!"}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class Client(Resource):
    @token_required
    def get(self, user):
        try:
            result = databaseHelper.get(collection=app.config.get('Mongo_CLIENTS_COLLECTION'))
            result_list = []
            for client in result:
                client["_id"] = str(ObjectId(client["_id"]))
                result_list.append(client)
            response = make_response(jsonify(result_list), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def post(self, user):
        try:
            data = request.get_json()
            client_secret = random_key()
            content = {"client_url": data["client_url"], "client_secret": client_secret}
            result = databaseHelper.insert(collection=app.config.get('Mongo_CLIENTS_COLLECTION'), content=content)
            if result.acknowledged:
                response = make_response(
                    jsonify(str(data["client_url"]) + " added! The Client Secret is " + client_secret), 200)
            else:
                response = make_response(jsonify(str("Client nicht angelegt!")), 400)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def put(self, user):
        try:
            data = request.get_json()
            change_id = data["_id"]
            client_url = data["client_url"]
            client_secret = random_key()
            new_values = {"$set": {"client_url": client_url, "client_secret": client_secret}}
            databaseHelper.updateOne(collection=app.config.get('Mongo_CLIENTS_COLLECTION'),
                                     search_content={'_id': ObjectId(change_id)}, new_values=new_values)
            response = make_response(
                jsonify({'message': str(client_url) + " changed! The new Client Secret is: " + client_secret}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)

    @token_required
    def delete(self, user):
        try:
            id = request.args["id"]
            databaseHelper.deleteOne(collection=app.config.get('Mongo_CLIENTS_COLLECTION'),
                                     search_content={'_id': ObjectId(id)})
            response = make_response(jsonify({'message': "Gelöscht"}), 200)
            return response
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class Login(Resource):
    def get(self):
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return make_response(jsonify({'message': 'could not verify'}), 401)

        try:
            usr_cursor = databaseHelper.get(collection=app.config.get('Mongo_USER_COLLECTION'),
                                            search_content={'username': auth.username})
            user = usr_cursor[0]
            password = user["password"]
            user_public_id = str(ObjectId(user["_id"]))
            user_firstname = user["firstname"]
            user_lastname = user["lastname"]
            user_email = user["mail"]

            if werkzeug.security.check_password_hash(password, auth.password):
                token = jwt.encode(
                    {'public_id': user_public_id, 'prename': user_firstname, 'lastname': user_lastname,
                     'email': user_email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                    app.config['SECRET_KEY'], algorithm="HS256")
                databaseHelper.insert(collection=app.config.get('Mongo_USER_SESSION_COLLECTION'),
                                      content={'token': token})
                return make_response(jsonify({'token': token}), 200)
            return make_response(jsonify({'message': 'could not verify'}), 400)
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class Logging(Resource):
    @token_required
    def get(self, user):
        cursor = databaseHelper.get(collection="logging")
        logs = []
        for document in cursor:
            document["_id"] = str(ObjectId(document["_id"]))
            logs.append(document)
        response = make_response(jsonify(logs), 200)
        return response

    @token_required
    def post(self, user):
        try:
            data = request.get_json()
            activate_chat_logging = data["logging"]

            log_setting_cursor = databaseHelper.get(collection="settings")
            id_s = None
            for doc in log_setting_cursor:
                id_s = ObjectId(doc["_id"])

            new_value = {"$set": {"logging": activate_chat_logging}}
            databaseHelper.updateOne(collection="settings", search_content={"_id": id_s}, new_values=new_value)

            if not activate_chat_logging:
                databaseHelper.dropCollection(name="logging")
            return make_response(jsonify({'message': activate_chat_logging}), 200)
        except Exception as e:
            logging.error(e)
            return make_response(jsonify({'message': 'Fehler! Weiter Informationen sind dem Log zu entnehmen.'}), 500)


class getChatbotModelType(Resource):
    @token_required
    def get(self, user):
        cursor = databaseHelper.get(collection="settings")
        model = ""
        for document in cursor:
            model = (document["ChatBot"])
        response = make_response(jsonify({"model": model}), 200)
        return response


def random_key():
    characters = list(string.ascii_letters + string.digits + "!@#$%^&*()")
    length = 16
    random.shuffle(characters)
    secret = []
    for i in range(length):
        secret.append(random.choice(characters))
    random.shuffle(secret)
    client_secret = "".join(secret)
    return client_secret


api.add_resource(Question, "/api/")
api.add_resource(Login, "/api/login")
api.add_resource(User, "/api/user")
api.add_resource(Client, "/api/client")
api.add_resource(AskQuestion, "/api/askQuestion")
api.add_resource(ChatBotSettings, "/api/chatBot")
api.add_resource(TrainChatBot, "/api/chatBot/train")
api.add_resource(getChatbotModelType, "/api/chatBot/model")
api.add_resource(Logging, "/api/logging")

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
