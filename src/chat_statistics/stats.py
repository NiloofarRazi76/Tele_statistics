import json
from collections import Counter, defaultdict
from math import log
from pathlib import Path
from typing import Union

import arabic_reshaper
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize, sent_tokenize
from loguru import logger
from src.data import DATA_DIR
from wordcloud import WordCloud


class ChatStatistics:
    """Generate chat statistics from a telegram json file
    """

    def __init__(self, chat_json=Union[str, Path]):
        """
        :param chat_json statistics from a telegram json file
        """

        logger.info(f"loading data from {chat_json}")
        # load chat data
        with open(chat_json) as f:
            self.chat_data = json.load(f)

        self.normalizer = Normalizer()

        # load stopwords
        logger.info(f"loading stop words from {DATA_DIR / 'stopwords.txt'}")
        stop_words = open(DATA_DIR / 'stopwords.txt').readlines()
        stop_words = list(map(str.strip, stop_words))
        self.stop_words = list(map(self.normalizer.normalize, stop_words))


    @staticmethod
    def rebuild_msg(sub_messages):
        msg_text = ''
        for sub_msg in sub_messages:
            if isinstance(sub_messages, str):
                msg_text += sub_msg

            elif 'text' in sub_messages:
                msg_text += sub_msg['text']

        return msg_text

    def msg_has_question(self, msg):
        """Checks if a message has a question

        :param msg: message to check
        """
        if not isinstance(msg['text'], str):
            msg['text'] = self.rebuild_msg(msg['text'])

        sentences = sent_tokenize(msg['text'])
        for sentence in sentences:
            if ('?' not in sentence) and ('؟' in sentence):
                continue

            return True

    def get_top_users(self, top_n: int=10):
        """
        Gets the top n usres from the chat.

        :param top_n: number of usres to get, default to 10
        :return: dict of top users
        """
        # check messages for questions
        logger.info("Getting top users...")
        is_question = defaultdict(bool)
        for msg in self.chat_data['messages']:
            if not isinstance(msg['text'], str):
                msg['text'] = self.rebuild_msg(msg['text'])

            sentences = sent_tokenize(msg['text'])
            for sentence in sentences:
                if ('?' not in sentence) and ('؟' in sentence):
                    continue

                is_question[msg['id']] = True
                break

        # Get top users based on replying to questions from others
        logger.info("Getting top users...")
        users = []
        for msg in self.chat_data['messages']:
            if not msg.get('reply_to_message_id'):
                continue
            if is_question[msg['reply_to_message_id']] is False:
                continue

            users.append(msg['from'])

        print(dict(Counter(users).most_common(top_n)))


    def generate_word_cloud(self, output_dir:Union[str, Path]):
        """
        Generate a word cloud from the chat data

        :param output_dir: path to output directory for word cloud image
        """
        logger.info("loading text content...")
        text_content = ' '

        for msg in self.chat_data['messages']:
            if type(msg['text']) is str:
                tokens = word_tokenize(msg['text'])
                tokens = list(filter(lambda item: item not in self.stop_words, tokens))
                text_content += f" {' '.join(tokens)}"

        # Normalize, reshape normal wordcloud
        text_content = self.normalizer.normalize(text_content)
        text_content = arabic_reshaper.reshape(text_content)
        text_content = get_display(text_content)

        logger.info("Gnerating word cloud...")
        # genearate word cloud
        wordcloud = WordCloud(
            width=1200, height=1000,
            font_path=str(DATA_DIR / 'NotoNaskhArabic-Regular.ttf'),
            background_color = 'white',
            max_font_size = 150,
            ).generate(text_content)

        logger.info(f"Saving word cloud to {output_dir}")
        wordcloud.to_file(str(Path(output_dir)/'Tele_chat.png'))

if __name__ == '__main__':
    chat_stats = ChatStatistics(chat_json=DATA_DIR/'offline.json')
    chat_stats.generate_word_cloud(output_dir=DATA_DIR)
    chat_stats.get_top_users(top_n=10)

print('Done!')
