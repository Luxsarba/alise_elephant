from flask import Flask, request, jsonify
import logging
import random

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info(f'Response:  {response!r}')

    return jsonify(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        sessionStorage[user_id] = {
            'suggests': ["Не хочу.", "Не буду.", "Отстань!"],
            'first_name': None,
            'attempts': 0
        }
        res['response']['text'] = 'Привет! Купи слона!'
        res['response']['buttons'] = get_suggests(user_id)
        return

    session = sessionStorage[user_id]

    # Проверяем, представился ли пользователь
    if session['first_name'] is None:
        first_name = get_first_name(req)
        if first_name:
            session['first_name'] = first_name
            res['response']['text'] = f'Приятно познакомиться, {first_name}! Купи слона!'
            res['response']['buttons'] = get_suggests(user_id)
            return

    session['attempts'] += 1

    # Расширенный список фраз для согласия
    agreement_phrases = ['ладно', 'куплю', 'покупаю', 'хорошо', 'ок', 'согласен']
    for phrase in agreement_phrases:
        if phrase in req['request']['original_utterance'].lower():
            res['response']['text'] = 'Слона можно найти на Яндекс.Маркете!'
            res['response']['end_session'] = True
            sessionStorage[user_id] = None
            return

    # Случайные ответы на отказ
    refusal_responses = [
        f'Все говорят "{req['request']['original_utterance']}", а ты купи слона!',
        f'Каждый может сказать "{req['request']['original_utterance']}", а ты купи слона!',
        f'Ну и что?! А ты возьми и купи слона!'
    ]
    res['response']['text'] = random.choice(refusal_responses)
    res['response']['buttons'] = get_suggests(user_id)

    # Ограничение попыток
    if session['attempts'] >= 5:
        res['response']['text'] = 'Ладно, не хочешь слона — до свидания!'
        res['response']['end_session'] = True
        sessionStorage[user_id] = None


def get_suggests(user_id):
    session = sessionStorage[user_id]
    suggests = [{'title': suggest, 'hide': True} for suggest in session['suggests'][:2]]
    session['suggests'] = session['suggests'][1:]
    sessionStorage[user_id] = session

    if len(suggests) < 2:
        suggests.append({
            "title": "Ладно",
            "url": "https://market.yandex.ru/search?text=слон",
            "hide": True
        })
    return suggests


def get_first_name(req):
    for entity in req['request']['nlu']['entities']:
        if entity['type'] == 'YANDEX.FIO':
            return entity['value'].get('first_name', None)
    return None


if __name__ == '__main__':
    app.run()