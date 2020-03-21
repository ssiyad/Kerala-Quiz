#!/usr/bin/env python

# -------------------------------------------------------------
# Kerala Quiz - A Telegram Bot for playing quiz in communities.
# @author: Sumithran a.k.a zume
# @github: https://github.com/zume2020
# license: MIT
# -------------------------------------------------------------

import logging
import json
import requests
import random

from time import sleep
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, run_async

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

logging.INFO("Starting Engine")

score = {}

# global pool
# global delay_flag

q_round = 0
correct_answer = 0
delay_flag = 0


@run_async
def start(update, context):
    update.message.reply_text(
        'Hi {}! Use /quiz to start quiz'.format(update.message.chat.first_name))


@run_async
def send_quiz(context):
    """Send the alarm message."""
    global answer
    global category
    global correct_answer
    global q_round

    url = 'https://opentdb.com/api.php?amount=5&category=22&type=multiple'

    r = requests.get(url)
    j = r.json()

    pool = j['results']
    # print(pool)
    random.shuffle(pool)

    try:
        x = pool.pop()

        question = x['question']
        answer = x['correct_answer'].lower()
        category = x['category']

        print(answer)

        job = context.job

        qLoop = 0

        for x in range(4):
            if correct_answer == 0:
                if x > 0:
                    hint = "Hint: {}".format(answer[-x:])
                    print(hint)
                else:
                    hint = ""

                q_message = "❓*QUESTION* _[{}]_ \n{} \n{}".format(
                    category, question, hint)
                context.bot.send_message(job.context,
                                         text=q_message,
                                         parse_mode=ParseMode.MARKDOWN)
                if x == 3:
                    noGuessMessage = "⛔️ Nobody guessed, Correct answer was *{}*".format(
                        answer)
                    context.bot.send_message(job.context,
                                             text=noGuessMessage,
                                             parse_mode=ParseMode.MARKDOWN)

                sleep(12)
            else:
                print("Correct answer triggered")
        print(x)
        correct_answer = 0  # check this
        q_round += 1
        print("q round ", q_round)
        print(score)

        if q_round > 4:
            q_round = 0
            # stoping the quiz

            score_message = ""
            sorted_score = sorted(score.items(), key=lambda x: x[1])
            print(sorted_score)
            for k, v in sorted_score:
                print(k, v)
                score_message += "{} {}\n".format(k, v)

            context.bot.send_message(job.context, text=score_message)
            job.schedule_removal()

    except IndexError as e:
        job = context.job
        print("q round while error is", q_round)
        print(e)
        context.bot.send_message(job.context, text="stoped")
        job.schedule_removal()


@run_async
def set_quiz(update, context):

    chat_id = update.message.chat_id
    try:
        # Add job to queue and stop current one if there is a timer already
        update.message.reply_text(
            '🏁 *Round Starts*!', parse_mode=ParseMode.MARKDOWN)

        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_repeating(
            send_quiz, 2, context=chat_id)
        context.chat_data['job'] = new_job
        # update.message.reply_text('question!')

    except (IndexError, ValueError):
        update.message.reply_text('error')


@run_async
def unset(update, context):
    """Remove the job if the user changed their mind."""
    if 'job' not in context.chat_data:
        update.message.reply_text('You have no active quiZZzZes!')
        return

    job = context.chat_data['job']
    job.schedule_removal()
    # del context.chat_data['job']

    update.message.reply_text('✋ *Stopped*!', parse_mode=ParseMode.MARKDOWN)


# def check(update, context):
#     if update.message.text.lower() == answer:
#         global correct_answer, score
#         correct_answer = 1
#         answer_result = "Correct answer: {}\n{}".format(answer,update.message.chat.first_name)
#         context.bot.send_message(chat_id=update.effective_chat.id, text=answer_result)
#         score.append([update.message.chat.first_name,0])

@run_async
def check(update, context):
    if update.message.text.lower() == answer:
        print("Correct answer")
        global correct_answer, score

        correct_answer = 1

        f_name = update.message.from_user.first_name

        answer_result = "🍀 Yes, *{}*!\n\n🏆 {} +1".format(answer, f_name)

        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=answer_result,
                                 parse_mode=ParseMode.MARKDOWN)

        if f_name in score:
            score[f_name] += 1
        else:
            score[f_name] = 1


@run_async
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def getToken():
    with open('token.json') as f:
        data = json.load(f)
        token = data['token']
    return token


def main():
    """Run bot."""

    updater = Updater(getToken(), use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("quiz", set_quiz,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("stop", unset, pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.text, check))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
