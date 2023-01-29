import spacy


class ChatBotSpacy:
    def __init__(self, content_bachelor, content_master):
        self.model = spacy.load("de_core_news_lg")
        self.sample_question_bachelor = content_bachelor
        self.sample_question_master = content_master

    def chat(self, question, scope):
        try:
            if scope == "bachelor":
                sample_question = self.sample_question_bachelor
            else:
                sample_question = self.sample_question_master
                
            similarities = []
            for item in sample_question:
                question_embedding = self.model(item)
                similarities.append(question_embedding.similarity(self.model(question)))

            max_item = max(similarities)
            max_index = similarities.index(max_item)
            
            return str(sample_question[max_index]), float(max_item)
        except Exception as e:
            return str(e)

    def rebuildTensors(self, question_bachelor, question_master):
        try:
            self.sample_question_bachelor = question_bachelor
            self.sample_question_master = question_master
            return str("Training abgeschlossen!")
        except:
            return str("Training fehlgeschlagen!")