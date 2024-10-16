from dotenv import load_dotenv
import os
import telebot
from telebot import types
import json


load_dotenv()
tg_token = os.environ['TG_TOKEN']
bot = telebot.TeleBot(tg_token)

with open("question_answer.json", "r", encoding='utf-8') as f:
    help_info = json.load(f)

questions = []
for pair in help_info:
    for question in pair.keys():
        questions.append(question)

try:
    with open('needHelp.json', 'r', encoding='utf8') as file:
        needHelp = json.load(file)
except FileNotFoundError:
    needHelp = []
    with open("needHelp.json", "w", encoding='utf8') as file:
        json.dump(needHelp, file, ensure_ascii=False)

try:
    with open("users_info.json", "r", encoding='utf-8') as file:
        joinedUsers = json.load(file)
except FileNotFoundError:
    joinedUsers = []
    with open("users_info.json", "w", encoding='utf8') as file:
        json.dump(joinedUsers, file, ensure_ascii=False)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttonA = types.KeyboardButton('Техподдержка')
    buttonB = types.KeyboardButton('Часто задаваемые вопросы')
    buttonC = types.KeyboardButton('Рассылка')
    buttonD = types.KeyboardButton('Контактная информация')

    markup.row(buttonA)
    markup.row(buttonB)
    markup.row(buttonC)
    markup.row(buttonD)

    bot.send_message(message.chat.id, 'Здравствуйте, это бот ТСЖ "Максима",\nЗдесь вы можете:\n ・Задать вопрос или найти ответ среди часто задаваемых вопросов.\n ・Подписаться на общедомовую рассылку.\n ・Узнать контактную информацию ТСЖ "Максима."', reply_markup=markup)


@bot.message_handler(commands=['answer'])
def ts_reply(message):
    if needHelp:
        text = message.text
        found = False
        for user in needHelp:
            if user['username'] in text and str(user['message_id']) in text:
                bot.send_message(user['chat_id'], text[text.lower().find('ответ'):])
                needHelp.remove(user)   
                with open("needHelp.json", "w", encoding='utf8') as file:
                    json.dump(needHelp, file, ensure_ascii=False)
                found = True
        if not found:
            bot.send_message(os.environ.get('GROUP_ID'),'Не удалось найти сообщений от данного пользователя.')
    else:
        bot.send_message(os.environ.get('GROUP_ID'),'Все сообщения отвечены')


@bot.message_handler(commands=['mailling'])
def mailling(message):
    for user in joinedUsers:
        bot.send_message(user, message.text)


@bot.message_handler(content_types='text')
def message_reply(message):
    text = message.text
    if text == 'Часто задаваемые вопросы' or text == 'Назад к вопросам':
        send_questions(message)
    send_answers(message)
    if text == 'На Главную':
        start(message)
    if text == 'Техподдержка':
        bot.send_message(message.chat.id, 'Напишите ваш вопрос в формате "Вопрос: ..." и мы ответим вам как можно скорее')
    if text == 'Рассылка':
        malling_info(message)
    if text == 'Подписаться':
        save_chatid(message)
    if 'Вопрос:' in text:
        if not needHelp:
            message_to_ts(message)
        else:
            for user in needHelp:
                if message.from_user.username == user['username']:
                    bot.send_message(message.chat.id, 'Вы уже отправили вопрос, пожалуйста дождитесь ответа')
                    break
                else:
                    message_to_ts(message)


def send_questions(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for button in questions:
        markup.row(types.KeyboardButton(button))
    markup.row(types.KeyboardButton('Назад к вопросам'), types.KeyboardButton('На Главную'))
    text_message = ''
    for question in questions:
        question_num = questions.index(question) + 1
        text_message += f'{question_num}. {question} \n'
    bot.send_message(message.chat.id, f'Часто задаваемые вопросы:\n{text_message}', reply_markup=markup)


def send_answers(message):
    for question in questions:
        if message.text in question:
            answer = help_info[questions.index(question)][message.text]
            bot.send_message(message.chat.id, answer)


def message_to_ts(message):
    needHelp.append(
        {
            'username': message.from_user.username,
            'chat_id': message.chat.id,
            'message_id': message.message_id
        }
    )
    with open("needHelp.json", "w", encoding='utf8') as file:
        json.dump(needHelp, file, ensure_ascii=False)
    bot.send_message(os.environ.get('GROUP_ID'), f'Пользователь @{message.from_user.username} написал: "{message.text}", message_id: {message.message_id}')


def malling_info(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton('Подписаться'))
    markup.row(types.KeyboardButton('На Главную'))
    bot.send_message(message.chat.id, 'Рассылка будет содержать информацию важную для собственников, например: \nинформация о предстоящих собраниях, изменениях в стоимости коммунальных услуг, ремонте в доме и так далее.', reply_markup=markup)


def save_chatid(message):
    joinedUsers.append(message.chat.id) if message.chat.id not in joinedUsers else joinedUsers
    with open("users_info.json", "w", encoding='utf8') as file:
        json.dump(joinedUsers, file, ensure_ascii=False)


bot.infinity_polling()
