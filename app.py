import traceback
import sys
import logging
from bottle import default_app, request, post
from mail_tools import get_sender_email_data, send_email, get_recipient_email_text, get_email_obj_text, \
    get_email_address_list
import json
import re

response_texts = []
response_ttss = []


@post('/')
def work():
    try:
        response = {
            "version": request.json["version"],
            "session": request.json["session"],
            "response": {
                "end_session": False
            }
        }
        req = request.json

        if req["session"]["new"] or req["request"]["original_utterance"].lower().strip() in ["привет", "хай", "дарова",
                                                                                             "ку",
                                                                                             "даров", "здарова",
                                                                                             "hello", "hi"]:
            response["response"]["text"] = "Привет, навык позволяет отправлять почту с помощью умного ассистента." \
                                           " Чтобы начать ответьте 'старт'. Для выхода из навыка " \
                                           " ответьте 'пока' или 'стоп'."
            response["response"]["tts"] = " Прив+ет, н+авык позвол+яет отправл+ять п+очту с п+омощью умного ассист+ента." \
                                          " Чт+обы нач+ать отв+етьте старт. Для в+ыхода из н+авыка" \
                                          " отв+етьте пок+а или стоп."
            response_texts.append(response["response"]["text"])
            response_ttss.append(response["response"]["tts"])
        else:
            try:
                if req["request"]["original_utterance"].lower().strip() in ["стоп", "закончили",
                                                                            "не надо", "все", "хватит",
                                                                            "пока", "до свидания", "конец",
                                                                            "нет", "отбой", "хватит"]:

                    response["response"]["text"] = "Всего хорошего, до свидания!"
                    response["response"]["tts"] = "Всег+о хор+ошего, до свид+ания!"
                    response_texts.append(response["response"]["text"])
                    response_ttss.append(response["response"]["tts"])
                    response["response"]["end_session"] = True
                elif req["session"]["user"]["access_token"]:
                    response["response"]["text"] = response_texts[len(response_texts) - 1]
                    response["response"]["tts"] = response_ttss[len(response_ttss) - 1]
                    if req["request"]["original_utterance"].lower().strip() == "помощь":
                        response["response"]["text"] = "Привет, навык позволяет отправлять почту с помощью умного ассистента." \
                                                       " Чтобы начать ответьте 'старт'. Для выхода из навыка " \
                                                       " ответьте 'пока' или 'стоп'"
                        response["response"]["tts"] = " Прив+ет, н+авык позвол+яет отправл+ять п+очту " \
                                                      " с п+омощью умного ассист+ента. Чт+обы нач+ать отв+етьте старт." \
                                                      " Для в+ыхода из н+авыка отв+етьте пок+а или стоп."
                        response_texts.append(response["response"]["text"])
                        response_ttss.append(response["response"]["tts"])
                    else:

                        if req["request"]["original_utterance"].lower().strip().strip() == "старт":
                            global access_token
                            access_token = req["session"]["user"]["access_token"]
                            if get_sender_email_data(access_token):
                                global sender_email_name
                                sender_email_name = get_sender_email_data(access_token)[0]
                                global sender_email
                                sender_email = get_sender_email_data(access_token)[1]
                                response["response"]["text"] = f"Получаю ваш текущий email, ваш" \
                                                               f" email - {sender_email}. Чтобы продолжить," \
                                                               f" ответьте, 'список контактов'. "
                                response["response"]["tts"] = f" Получ+аю ваш тек+ущий " \
                                                              f" email, ваш email - {sender_email}. " \
                                                              f" Чт+обы прод+олжить отв+етьте сп+исок конт+актов."
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])
                            else:
                                response["response"]["text"] = "Не удалось определить ваш email. Что то пошло не так," \
                                                               " начните сначала. Ответьте 'старт' или 'помощь'."

                                response["response"]["tts"] = "Не удал+ось определ+ить ваш email." \
                                                              " Что то пошл+о не так, начн+ите снач+ала. " \
                                                              " Отв+етьте старт или п+омощь. "
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])

                        elif req["request"]["original_utterance"].lower().strip() == "список контактов":
                            global email_address_list
                            email_address_list = get_email_address_list(access_token, sender_email)
                            if email_address_list:
                                response["response"]["text"] = "Список контактов сформирован." \
                                                               " Я могу начать писать письмо. Кому будем отправлять? " \
                                                               " Назовите получателя, сказав 'получатель'," \
                                                               " а дальше назовите его имя и фамилию," \
                                                               " если это физ. лицо," \
                                                               " или же название компании, если это юр. лицо"

                                response["response"]["tts"] = "Сп+исок конт+актов сформир+ован. Я мог+у нач+ать пис+ать письм+о." \
                                                              " Ком+у б+удем отправл+ять? Назов+ите получ+ателя," \
                                                              " сказ+ав получ+атель, а д+альше назов+ите ег+о имя" \
                                                              " и фам+илию, если это физ лиц+о или же назв+ание" \
                                                              " комп+ании, если это юр лиц+о. "
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])

                            else:
                                response["response"]["text"] = "Список контактов не удалось сформировать или же он пуст."

                                response["response"]["tts"] = " Сп+исок конт+актов не удал+ось сформиров+ать или же он пуст."
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])

                        elif re.match(r"^получатель [\S\sa-zA-Zа-яА-Я0-9_.+-]+$",
                                      req["request"]["original_utterance"].lower().strip()):
                            if get_recipient_email_text(req["request"]["original_utterance"]):
                                global recipient_email_name
                                recipient_email_name = get_recipient_email_text(req["request"]["original_utterance"])[0]
                                global recipient_email
                                recipient_email = get_recipient_email_text(req["request"]["original_utterance"])[1]
                                response["response"]["text"] = f"Email получателя {recipient_email}. Чтобы продолжить," \
                                                               f" ответьте, 'тема письма'." \
                                                               f" Если хотите изменить email получателя," \
                                                               f" введите прошлую команду еще раз."
                                response["response"]["tts"] = f"Email получ+ателя {recipient_email}." \
                                                              f" Чт+обы прод+олжить, отв+етьте, т+ема письм+а." \
                                                              f" Если хот+ите измен+ить email получ+ателя," \
                                                              f" введ+ите пр+ошлую ком+анду ещ+е раз."
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])
                            else:
                                response["response"]["text"] = "Не удалось определить email получателя." \
                                                               " Возможно его нет в сформированном списке контактов." \
                                                               " Попробуйте снова, введите прошлую команду еще раз."
                                response["response"]["tts"] = "Не удал+ось определ+ить email получ+а" \
                                                              " теля. Возм+ожно его нет в сформир+ованном" \
                                                              " сп+иске конт+актов. Попр+обуйте сн+ова," \
                                                              " введ+ите пр+ошлую ком+анду еще раз."
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])

                        elif req["request"]["original_utterance"].lower().strip() == "тема письма":
                            response["response"]["text"] = "Придумайте тему письма, сказав, 'тема'...," \
                                                           " а дальше только полёт вашей мысли"
                            response["response"]["tts"] = "Прид+умайте т+ему письм+а, сказав, т+ема...," \
                                                          " а д+альше т+олько пол+ёт в+ашей м+ысли"
                            response_texts.append(response["response"]["text"])
                            response_ttss.append(response["response"]["tts"])

                        elif re.match(r"^тема (?!.*\bписьма\b)[\S\sa-zA-Zа-яА-Я0-9_.+-]+$",
                                      req["request"]["original_utterance"].lower().strip()):
                            global subject
                            subject = get_email_obj_text(req["request"]["original_utterance"].strip(), "тема")
                            subject = subject if re.match(r'[+.!?]', subject[len(subject) - 1]) else subject + '.'
                            response["response"]["text"] = f"Тема письма - {subject} Чтобы продолжить," \
                                                           f" ответьте, 'текст письма'." \
                                                           f" Если хотите изменить тему письма," \
                                                           f" скажите 'тема письма' еще раз."
                            response["response"]["tts"] = f"Т+ема письм+а - {subject} Чт+обы прод+олжить," \
                                                          f" отв+етьте, текст письм+а." \
                                                          f" Если хот+ите измен+ить т+ему письм+а, " \
                                                          f" скаж+ите т+ема письм+а ещ+е раз."
                            response_texts.append(response["response"]["text"])
                            response_ttss.append(response["response"]["tts"])

                        elif req["request"]["original_utterance"].lower().strip() == "текст письма":
                            response["response"]["text"] = "Придумайте текст письма, сказав, 'текст'...," \
                                                           " а дальше только полёт вашей мысли"
                            response["response"]["tts"] = "Прид+умайте текст письм+а, сказ+ав, текст..." \
                                                          " а д+альше т+олько пол+ёт в+ашей м+ысли"
                            response_texts.append(response["response"]["text"])
                            response_ttss.append(response["response"]["tts"])

                        elif re.match(r"^текст (?!.*\bписьма\b)[\S\sa-zA-Zа-яА-Я0-9_.+-]+$",
                                      req["request"]["original_utterance"].lower().strip()):
                            global message
                            message = get_email_obj_text(req["request"]["original_utterance"].strip(), "текст")
                            message = message if re.match(r'[+.!?]', message[len(message) - 1]) else message + '.'
                            response["response"]["text"] = f"Текст письма - {message} Чтобы продолжить," \
                                                           f" ответьте, 'отправка письма'." \
                                                           f" Если хотите изменить текст письма," \
                                                           f" скажите 'текст письма' еще раз."
                            response["response"]["tts"] = f"Текст письм+а - {message} Чт+обы прод+олжить," \
                                                          f" отв+етьте, отпр+авка письм+а." \
                                                          f" Если хот+ите измен+ить текст письм+а, " \
                                                          f" скаж+ите текст письм+а ещ+е раз."
                            response_texts.append(response["response"]["text"])
                            response_ttss.append(response["response"]["tts"])

                        elif req["request"]["original_utterance"].lower().strip() == "отправка письма":
                            response["response"]["text"] = "Отправляю письмо, подтвердите," \
                                                           " ответив, 'подтверждаю', либо вы можете" \
                                                           " вернуться назад и изменить текст," \
                                                           " тему или получателя письма."
                            response["response"]["tts"] = "Отправл+яю письм+о, подтверд+ите," \
                                                          " отв+етив, подтвержд+аю, л+ибо вы м+ожете" \
                                                          " верн+уться наз+ад и измен+ить текст,т+ему или" \
                                                          " получ+ателя письм+а."
                            response_texts.append(response["response"]["text"])
                            response_ttss.append(response["response"]["tts"])

                        elif req["request"]["original_utterance"].lower().strip() == "подтверждаю":
                            if send_email(access_token=access_token, sender_email_name=sender_email_name,
                                          sender_email=sender_email, recipient_email_name=recipient_email_name,
                                          recipient_email=recipient_email, subject=subject, message=message):
                                response["response"]["text"] = "Письмо отправлено."
                                response["response"]["tts"] = "Письм+о отпр+авлено."
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])
                            else:
                                response["response"]["text"] = "Письмо уже отправлено, либо на" \
                                                               " сервере какие то проблемы"
                                response["response"]["tts"] = "Письм+о уж+е отпр+авлено, л+ибо на " \
                                                              "с+ервере как+ие то пробл+емы"
                                response_texts.append(response["response"]["text"])
                                response_ttss.append(response["response"]["tts"])
                            sender_email_name = sender_email = recipient_email_name = \
                                recipient_email = subject = message = ""
                        elif req["request"]["command"].lower().strip() in ["спасибо", "большое спасибо"]:
                            response["response"]["text"] = "Пожалуйста, всегда к вашим услугам!"
                            response["response"]["tts"] = "Пож+алуйста, всегд+а к в+ашим усл+угам!"

            except KeyError:
                response["start_account_linking"] = {}
                response["response"][
                    "text"] = "Привет, отправим почту кому-нибудь? Только для начала надо авторизоваться." \
                              " Чтобы начать ответьте 'старт'." \
                              " Для выхода из навыка ответьте 'пока' или 'стоп'."

                response["response"][
                    "tts"] = "Прив+ет, отпр+авим п+очту ком+у ниб+удь? Только для начала надо авторизоваться." \
                             " Чт+обы нач+ать отв+етьте старт. Для в+ыхода из н+авыка отв+етьте пок+а" \
                             " или стоп."
    except Exception :
        response["response"]["text"] = "Потерена связь с космосом, повторите предыдущую команду или начните сначала."
        response["response"]["tts"] = "Пот+ерена связь с космосом, повтор+ите предыд+ущую ком+анду или начн+ите снач+ала."
    return json.dumps(response)


application = default_app()
