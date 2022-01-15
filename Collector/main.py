import configparser
import os
import json

from glob import glob
from html.parser import HTMLParser


path_to_config = "../config.txt"


def class_filter(necessary_classes: list, classes: str):
    for necessary_class in necessary_classes:
        if necessary_class not in classes:
            # print(necessary_class)
            # print(classes)
            return False
    return True


def is_question(classes: str):
    necessary_classes = ["deferredfeedback"]
    return class_filter(necessary_classes, classes)


def is_qtext(classes: str):
    necessary_classes = ["qtext"]
    return class_filter(necessary_classes, classes)


def is_answer(classes: str):
    if not class_filter(['r0'], classes) and not class_filter(['r1'], classes):
        return False
    return True


def is_correct_answer(classes: str):
    return class_filter([' correct'], classes) # TODO: normal checking, without odd space. Don't delete it


class QuestionHTMLParser(HTMLParser):
    questions = {}
    question_flag = False
    div_counter = 0
    qtext_flag_div = False
    qtext_flag_p = False
    atext_flag_div = False
    atext_flag_p = False
    current_text = None
    current_answer = None

    def handle_starttag(self, tag, attrs):
        if tag == "div":
            for attr in attrs:
                if attr[0] == 'class':
                    classes = attr[1:][0]
                    if is_question(classes):
                        is_correct = None
                        if 'correct' in classes:
                            is_correct = True
                        if 'incorrect' in classes:
                            is_correct = False
                        if is_correct is None:
                            raise Exception("Unparsed question: with tag <", tag, "> and attributes: ", attrs)
                        self.question_flag = True
                        self.current_text = None
                        if is_correct:
                            print("Found a question with correct answer")
                            self.current_answer = None
                        else:
                            print("Found a question with incorrect answer")
                            self.current_answer = False
            if self.question_flag:
                self.div_counter += 1
                if attr[0] == 'class':
                    classes = attr[1:][0]
                    if is_qtext(classes):
                        self.qtext_flag_div = True
                        # print("Found a text of the question")
                    elif is_answer(classes) and is_correct_answer(classes):
                        self.atext_flag_div = True
                        # print("Found a correct answer for the question")
        elif tag == 'p':
            if self.qtext_flag_div:
                self.qtext_flag_p = True
                # print("Inside p tag of the text")
            if self.atext_flag_div:
                self.atext_flag_p = True

    def handle_endtag(self, tag):
        # print("Encountered an end tag :", tag)
        if tag == "div":
            if self.question_flag:
                self.div_counter -= 1
                if self.div_counter == 0:
                    self.question_flag = False
                    self.questions.update({self.current_text: self.current_answer})
                    self.current_answer = None
                    self.current_text = None
                    print("End of the question")
            if self.qtext_flag_div:
                self.qtext_flag_div = False
            if self.atext_flag_div:
                self.atext_flag_div = False
        elif tag == 'p':
            self.qtext_flag_p = False
            self.atext_flag_p = False

    def handle_data(self, data):
        if self.qtext_flag_p:
            self.current_text = data
            print("Found the text: ", data)
        if self.atext_flag_p:
            self.current_answer = data
            print("Found the answer: ", data)


def parse_html(html_file: str):
    with open(html_file, 'r') as html_input:
        contents = html_input.read()
        parser = QuestionHTMLParser()
        parser.feed(contents)
        return parser.questions


def main():
    global config
    previous_answers_dir = os.path.join("../", config['DEFAULT']['PREVIOUS_ANSWERS_DIR'])
    answers_json_path = os.path.join("../", config['DEFAULT']['ANSWERS_JSON_PATH'])
    if not os.path.isdir(previous_answers_dir):
        raise Exception("Not dir at " + previous_answers_dir)
    for html_file in glob(os.path.join(previous_answers_dir, '*.html')):
        print("Parsing " + html_file)
        parsed_answers = parse_html(html_file)
        print(parsed_answers)

        answers = {}
        if os.path.isfile(answers_json_path):
            with open(answers_json_path, "r") as json_input:
                answers = json.loads(json_input.read())
        answers.update(parsed_answers)

        with open(answers_json_path, 'w') as json_output:
            json_output.write(json.dumps(answers))


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(path_to_config)
    main()
