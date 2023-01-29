from sentence_transformers import SentenceTransformer, util


class ChatBot:
    def __init__(self, content_bachelor, content_master):
        self.model = SentenceTransformer("ChatBot/src/model/German-semantic")
        self.sample_question_bachelor = content_bachelor
        self.sample_question_embeddings_bachelor = self.model.encode(self.sample_question_bachelor, convert_to_tensor=True)
        self.sample_question_master = content_master
        self.sample_question_embeddings_master = self.model.encode(self.sample_question_master, convert_to_tensor=True)

    def chat(self, question, scope):
        try:
            if scope == "bachelor":
                sample_question_embeddings = self.sample_question_embeddings_bachelor
                sample_question = self.sample_question_bachelor
            else:
                sample_question_embeddings = self.sample_question_embeddings_master
                sample_question = self.sample_question_master

            question_embedding = self.model.encode(question, convert_to_tensor=True)

            cosine_scores = util.pytorch_cos_sim(sample_question_embeddings, question_embedding)

            top_questions = []
            for i in range(6):
                index = max(range(len(cosine_scores)), key=cosine_scores.__getitem__)
                max_score = cosine_scores[index]
                top_questions.append([str(sample_question[index]), float(max_score)])
                cosine_scores[index] = 0
            return top_questions
        except Exception as e:
            return str(e)

    def rebuildTensors(self, question_bachelor, question_master):
        try:
            self.sample_question_embeddings_bachelor = self.model.encode(question_bachelor, convert_to_tensor=True)
            self.sample_question_embeddings_master = self.model.encode(question_master,
                                                                       convert_to_tensor=True)
            return str("Training abgeschlossen!")
        except:
            return str("Training fehlgeschlagen!")