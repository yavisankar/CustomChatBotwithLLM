import openai
import ast
import re
import pandas as pd
import json
from IPython.display import display, HTML
from flask import Flask, redirect, url_for, render_template, request
from functions import *

openai.api_key = open('OPENAI_API_Key.txt', 'r').read().strip()

app = Flask(__name__)

conversation_bot = []

conversation = initialize_conversation()
introduction = get_chat_completions(conversation)
conversation_bot.append({'bot': introduction})
top_3_vacations = None


@app.route("/")
def default_func():
    global conversation_bot, conversation, top_3_vacations
    return render_template("index.html", name_xyz = conversation_bot)

@app.route("/end_conv", methods = ['POST', 'GET'])
def end_conv():
    global conversation_bot, conversation, top_3_vacations
    conversation_bot = []
    conversation = initialize_conversation()
    introduction = get_chat_completions(conversation)
    conversation_bot.append({'bot': introduction})
    top_3_vacations = None
    return redirect(url_for('default_func'))

@app.route("/invite", methods = ['POST'])
def invite():
    global conversation_bot, conversation, top_3_vacations, conversation_reco
    user_input = request.form["user_input_message"]
    prompt = 'You are an intelligent Travel Planner AI and your goal is to create a personalized travel plan for the user.     You need to ask relevant questions to understand the user''s travel preferences and requirements.     Your final objective is to fill the values for the different keys (''Destination Type'', ''Budget'', ''Travel Duration'', ''Travel Companions'', ''Preferred Activities'') in the python dictionary and be confident of the values.     These key-value pairs define the user''s travel profile.     The python dictionary looks like this:     {{''Destination Type'': ''values'', ''Budget'': ''values'', ''Travel Duration'': ''values'', ''Travel Companions'': ''values'', ''Preferred Activities'': ''values''}}     The value for ''Budget'' should be a numerical value extracted from the user''s response.     All other keys should have values that align with the user''s preferences, such as ''beach'', ''mountains'', ''luxury'', or ''adventure'', as inferred from the user''s input.     The example dictionary provided contains representative values only.'
    moderation = moderation_check(user_input)
    if moderation == 'Flagged':
        display("Sorry, this message has been flagged. Please restart your conversation.")
        return redirect(url_for('end_conv'))
    
    if top_3_vacations is None:

        conversation.append({"role": "user", "content": user_input + prompt})
        conversation_bot.append({'user': user_input})

        response_assistant = get_chat_completions(conversation)
        moderation = moderation_check(response_assistant)
        if moderation == 'Flagged':
            display("Sorry, this message has been flagged. Please restart your conversation.")
            return redirect(url_for('end_conv'))    


        confirmation = intent_confirmation_layer(response_assistant)

        print("Intent Confirmation Yes/No:",confirmation.get('result'))

        if "No" in confirmation.get('result'):
            conversation.append({"role": "assistant", "content": str(response_assistant)})
            conversation_bot.append({'bot': response_assistant})

        else:
            response = dictionary_present(response_assistant)
            print("WAIT")
            conversation_bot.append({'bot': "Thank you for providing all the information. Kindly wait, while I fetch the products: \n"})

            top_3_vacations = compare_travel_with_user(response)

            print("top 3 laptops are", top_3_vacations)

            validated_reco = recommendation_validation(top_3_vacations)
            if len(validated_reco) == 0:
                conversation_bot.append({'bot': "Sorry, we do not have laptops that match your requirements."})

            conversation_reco = initialize_conv_reco(validated_reco)
            conversation_reco.append({"role": "user", "content": "This is my user profile" + str(validated_reco)})
            recommendation = get_chat_completions(conversation_reco)

            moderation = moderation_check(recommendation)
            if moderation == 'Flagged':
                display("Sorry, this message has been flagged. Please restart your conversation.")
                return redirect(url_for('end_conv'))

            conversation_reco.append({"role": "assistant", "content": str(recommendation)})
            conversation_bot.append({'bot': recommendation})

    else:
        conversation_reco.append({"role": "user", "content": user_input})
        conversation_bot.append({'user': user_input})

        response_asst_reco = get_chat_completions(conversation_reco)

        moderation = moderation_check(response_asst_reco)
        if moderation == 'Flagged':
            print("Sorry, this message has been flagged. Please restart your conversation.")
            return redirect(url_for('end_conv'))

        conversation.append({"role": "assistant", "content": response_asst_reco})
        conversation_bot.append({'bot': response_asst_reco})

    return redirect(url_for('default_func'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

    