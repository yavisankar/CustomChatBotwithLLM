import openai
import ast
import re
import pandas as pd
import json
from IPython.display import display, HTML

def initialize_conversation():
    '''
    Returns a list [{"role": "system", "content": system_message}]
    '''

    delimiter = "####"

    example_user_dict = {'Destination Type': "beach",
                         'Budget': "50000",
                         'Travel Duration': "7 days",
                         'Travel Companions': "solo",
                         'Preferred Activities': "adventure"}

    example_user_req = {'Destination Type': "_",
                        'Budget': "_",
                        'Travel Duration': "_",
                        'Travel Companions': "_",
                        'Preferred Activities': "_"}

    system_message = f"""
    You are an intelligent Travel Planner AI and your goal is to create a personalized travel plan for the user.
    You need to ask relevant questions to understand the user's travel preferences and requirements.
    Your final objective is to fill the values for the different keys ('Destination Type', 'Budget', 'Travel Duration', 'Travel Companions', 'Preferred Activities') in the python dictionary and be confident of the values.
    These key-value pairs define the user's travel profile.
    The python dictionary looks like this:
    {{'Destination Type': 'values', 'Budget': 'values', 'Travel Duration': 'values', 'Travel Companions': 'values', 'Preferred Activities': 'values'}}
    The value for 'Budget' should be a numerical value extracted from the user's response.
    All other keys should have values that align with the user's preferences, such as 'beach', 'mountains', 'luxury', or 'adventure', as inferred from the user's input.
    The example dictionary provided contains representative values only.

    {delimiter}
    Here are some instructions around the values for the keys:
    - The value for 'Budget' should be a numerical value extracted from the user's response.
    - 'Destination Type' should reflect a specific preference such as 'beach', 'mountains', 'city', etc.
    - 'Travel Duration' should clearly indicate the length of the trip in days or weeks.
    - 'Travel Companions' should clarify if the user is traveling 'solo', with 'family', 'friends', or 'partner'.
    - 'Preferred Activities' should include specific preferences like 'adventure', 'relaxation', 'sightseeing', etc.
    - Do not randomly assign values to any of the keys.
    - The values must be inferred from the user's response.

    {delimiter}
    To build the user's travel profile, follow these chain-of-thoughts:
    1. Begin by understanding the user's preferences and requirements. Ask open-ended questions to gather information about their ideal travel experience.
    2. Gradually narrow down the details to fill in the dictionary keys. For instance:
       - Ask about the type of destination they prefer (e.g., 'beach', 'mountains', 'city').
       - Clarify their budget for the trip.
       - Confirm their preferred travel duration.
       - Identify their companions for the trip (if any).
       - Understand the activities they enjoy during vacations (e.g., 'adventure', 'relaxation').
    3. Validate the filled values. If unsure about any key, ask clarifying questions.

    {delimiter}
    Here is an example conversation:
    User: "I want to go on a vacation."
    Assistant: "That sounds exciting! Let's plan your perfect getaway. To start, do you have a specific type of destination in mind, like a beach, mountains, or a city? Or are you open to exploring options?"
    User: "I love beaches."
    Assistant: "Beaches are a fantastic choice for relaxation and fun. Could you share your budget for the trip so I can tailor recommendations accordingly?"
    User: "I can spend up to 50,000 INR."
    Assistant: "Got it! A beach destination within a 50,000 INR budget is possible. How many days do you plan to spend on this trip?"
    User: "I want to go for a week."
    Assistant: "Great! Are you traveling solo or with someone?"
    User: "I'll be traveling solo."
    Assistant: "Noted. Do you prefer a relaxing beach vacation, or are you looking for activities like water sports and adventure?"
    User: "I enjoy adventure activities."
    Assistant: "{example_user_dict}"
    {delimiter}

    Start with a friendly greeting and encourage the user to share their travel preferences and requirements.
    """
    conversation = [{"role": "system", "content": system_message}]
    return conversation


def get_chat_completions(input, json_format = False):
    MODEL = 'gpt-3.5-turbo'

    system_message_json_output = """<<. Return output in JSON format to the key output.>>"""

    # If the output is required to be in JSON format
    if json_format == True:
        # Append the input prompt to include JSON response as specified by OpenAI
        input[0]['content'] += system_message_json_output

        # JSON return type specified
        chat_completion_json = openai.chat.completions.create(
            model = MODEL,
            messages = input,
            response_format = { "type": "json_object"},
            seed = 1234)

        output = json.loads(chat_completion_json.choices[0].message.content)

    # No JSON return type specified
    else:
        chat_completion = openai.chat.completions.create(
            model = MODEL,
            messages = input,
            seed = 2345)

        output = chat_completion.choices[0].message.content

    return output

def iterate_llm_response(funct, debug_response, num = 10):
    """
    Calls a specified function repeatedly and prints the results.
    This function is designed to test the consistency of a response from a given function.
    It calls the function multiple times (default is 10) and prints out the iteration count,
    the function's response(s).
    Args:
        funct (function): The function to be tested. This function should accept a single argument
                          and return the response value(s).
        debug_response (dict): The input argument to be passed to 'funct' on each call.
        num (int, optional): The number of times 'funct' will be called. Defaults to 10.
    Returns:
        This function only returns the results to the console.
    """
    i = 0  # Initialize counter

    while i < num:  # Loop to call the function 'num' times

        response = funct(debug_response)  # Call the function with the debug response

        # Print the iteration number, result, and reason from the response
        print("Iteration: {0}".format(i))
        print(response)
        print('-' * 50)  # Print a separator line for readability
        i += 1  # Increment the counter

# Example usage: test the consistency of responses from 'intent_confirmation_layer'
# iterate_llm_response(get_chat_completions, messages)

def moderation_check(user_input):
    # Call the OpenAI API to perform moderation on the user's input.
    response = openai.moderations.create(input=user_input)

    # Extract the moderation result from the API response.
    moderation_output = response.results[0].flagged
    # Check if the input was flagged by the moderation system.
    if response.results[0].flagged == True:
        # If flagged, return "Flagged"
        return "Flagged"
    else:
        # If not flagged, return "Not Flagged"
        return "Not Flagged"
    
def intent_confirmation_layer(response_assistant):
    
    delimiter = "####"

    allowed_destination_types = {'beach', 'mountains', 'city', 'desert', 'forest'}
    allowed_companions = {'solo', 'family', 'friends', 'partner'}
    allowed_activities = {'adventure', 'relaxation', 'sightseeing', 'luxury', 'cultural'}

    prompt = f"""
    You are a senior evaluator who has an eye for detail. The input text will contain a user's travel preferences captured through the following keys:
    {{
    'Destination Type': 'values',
    'Budget': 'number',
    'Travel Duration': 'values',
    'Travel Companions': 'values',
    'Preferred Activities': 'values'
    }}
    - The value for 'Destination Type' should only be from the allowed values: {allowed_destination_types}.
    - The value for 'Budget' should only be a numerical value.
    - The value for 'Travel Duration' should be a valid duration string like '7 days' or '2 weeks'.
    - The value for 'Travel Companions' should only be from the allowed values: {allowed_companions}.
    - The value for 'Preferred Activities' should only be from the allowed values: {allowed_activities}.
    
    Next, you need to evaluate if the keys have values filled correctly.
    Only output a one-word string in JSON format at the key 'result' - Yes/No.
    Thought 1 - Output a string 'Yes' if the values are correctly filled for all keys, otherwise output 'No'.
    Thought 2 - If the answer is No, mention the reason in the key 'reason'.
    Thought 3 - Think carefully before answering.
    """

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"""Here is the input: {response_assistant}"""}
    ]

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        response_format={"type": "json_object"},
        seed=1234
    )

    json_output = json.loads(response.choices[0].message.content)

    return json_output

def dictionary_present(response):
    delimiter = "####"

    user_req = {'Destination Type': 'beach',
                'Budget': '50000',
                'Travel Duration': '7 days',
                'Travel Companions': 'family',
                'Preferred Activities': 'relaxation'}

    prompt = f"""You are a Python expert. You are provided with an input string.
            Your task is to check if there is a Python dictionary present in the string.
            It will have the following format {user_req}.
            You must extract the relevant values from the input and return only the Python dictionary in JSON format.
            The output should match the format as {user_req}.

            {delimiter}
            Make sure that the value of 'Budget' is present in the user input.
            The output should contain the exact keys and values as present in the input.
            Ensure the keys and values are in the given format:
            {{
            'Destination Type': 'beach/mountains/city/adventure/etc.',
            'Budget': 'numerical value',
            'Travel Duration': 'number of days',
            'Travel Companions': 'solo/family/friends/etc.',
            'Preferred Activities': 'relaxation/adventure/sightseeing/etc.'
            }}
            Here are some sample input-output pairs for better understanding:
            {delimiter}
            input 1: - Destination Type: beach - Budget: 50000 INR - Travel Duration: 7 days - Travel Companions: family - Preferred Activities: relaxation
            output 1: {{'Destination Type': 'beach', 'Budget': '50000', 'Travel Duration': '7 days', 'Travel Companions': 'family', 'Preferred Activities': 'relaxation'}}

            input 2: {{'Destination Type': 'mountains', 'Budget': '80000', 'Travel Duration': '10 days', 'Travel Companions': 'solo', 'Preferred Activities': 'adventure'}}
            output 2: {{'Destination Type': 'mountains', 'Budget': '80000', 'Travel Duration': '10 days', 'Travel Companions': 'solo', 'Preferred Activities': 'adventure'}}

            input 3: Here is your travel profile 'Destination Type': 'city','Budget': '120000','Travel Duration': '14 days','Travel Companions': 'friends','Preferred Activities': 'sightseeing'
            output 3: {{'Destination Type': 'city', 'Budget': '120000', 'Travel Duration': '14 days', 'Travel Companions': 'friends', 'Preferred Activities': 'sightseeing'}}
            {delimiter}
            """
    messages = [{"role": "system", "content": prompt},
                {"role": "user", "content": f"""Here is the user input: {response}""" }]

    confirmation = get_chat_completions(messages, json_format=True)

    return confirmation

def product_map_layer(travel_description):
    delimiter = "#####"

    travel_spec = {
        "Destination Type": "(Type of destination, e.g., beach, mountain, city)",
        "Budget": "(Total budget for the trip)",
        "Travel Companions": "(Family, Friends, Solo, Couple)",
        "Travel Duration": "(Number of days)",
        "Preferred Activities": "(Relaxation, Adventure, Sightseeing, Shopping, etc.)",
    }

    values = {'low', 'medium', 'high'}

    prompt = f"""
    You are a Travel Preferences Classifier whose job is to extract the key features of a user's travel description and classify them based on the provided criteria.
    To analyze each travel description, perform the following steps:
    Step 1: Extract the user's primary travel preferences from the description {travel_description}.
    Step 2: Store the extracted preferences in {travel_spec}.
    Step 3: Classify each item in {travel_spec} into {values} where applicable, based on the following rules:
    {delimiter}
    Destination Type:
    - beach: <<< Destinations like tropical islands, coastlines, or resorts >>>.
    - mountain: <<< Destinations with high altitudes, hiking trails, or snow activities >>>.
    - city: <<< Urban centers with museums, shopping, and vibrant nightlife >>>.

    Travel Budget:
    - low: <<< Budget less than 20,000 INR >>>.
    - medium: <<< Budget between 20,000 INR and 70,000 INR >>>.
    - high: <<< Budget greater than 70,000 INR >>>.

    Travel Companions:
    - family: <<< Group includes parents, children, or extended family >>>.
    - friends: <<< Traveling with a group of close friends >>>.
    - solo: <<< Traveling alone >>>.
    - couple: <<< Traveling as a pair >>>.

    Travel Duration:
    - short: <<< Duration less than 3 days >>>.
    - medium: <<< Duration between 3 and 7 days >>>.
    - long: <<< Duration greater than 7 days >>>.

    Preferred Activities:
    - relaxation: <<< Activities such as spa, lounging by the beach, or light exploration >>>.
    - adventure: <<< Activities like hiking, water sports, or extreme sports >>>.
    - sightseeing: <<< Visiting historical landmarks, museums, or cultural sites >>>.
    - shopping: <<< Exploring malls, local markets, or retail destinations >>>.
    {delimiter}

    {delimiter}
    Here is an example input-output pair for few-shot learning:
    input 1: "I am planning a family trip to a beach destination for 5 days. I love relaxing and sightseeing, and my budget is around 60,000 INR."
    output 1: {{
        "Destination Type": "beach",
        "Travel Budget": "medium",
        "Travel Companions": "family",
        "Travel Duration": "medium",
        "Preferred Activities": "relaxation, sightseeing"
    }}
    {delimiter}
    ### Ensure that the output is in a JSON format matching the above schema strictly. ###
    """

    input_data = f"""Follow the above instructions step-by-step and output the dictionary in JSON format {travel_spec} for the following travel description: {travel_description}."""
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": input_data}]

    response = get_chat_completions(messages, json_format=True)

    return response


import pandas as pd  
import json

def compare_travel_with_user(user_req_dict):
    travel_df = pd.read_csv('updated_travel.csv')
    user_requirements = user_req_dict  
    travel_budget_mapping = {'low': 0, 'medium': 1, 'high': 2}
    travel_duration_mapping = {'short': 0, 'medium': 1, 'long': 2}
    activities_mapping = {'relaxation': 1, 'sightseeing': 1, 'adventure': 2, 'exploration': 2}
    budget = travel_budget_mapping.get(str(user_requirements.get('Budget', 'medium')).lower(), 1)
    duration = travel_duration_mapping.get(str(user_requirements.get('Travel Duration', 'medium')).lower(), 1)
    filtered_travel = travel_df.copy()
    filtered_travel['BudgetScore'] = filtered_travel['Budget'].apply(lambda x: travel_budget_mapping.get(str(x).lower(), 1))
    filtered_travel['DurationScore'] = filtered_travel['Duration'].apply(lambda x: travel_duration_mapping.get(str(x).lower(), 1))
    filtered_travel['Score'] = 0
    for index, row in filtered_travel.iterrows():
        score = 0
        if row['BudgetScore'] >= budget:
            score += 1
        if row['DurationScore'] >= duration:
            score += 1
        
        
        filtered_travel.loc[index, 'Score'] = score  

    top_travel_destinations = filtered_travel.sort_values('Score', ascending=False).head(3)

    top_travel_json = top_travel_destinations.to_json(orient='records')  

    return top_travel_json

def recommendation_validation(laptop_recommendation):
    data = json.loads(laptop_recommendation)
    data1 = []
    for i in range(len(data)):
        if data[i]['Score'] >= 1:
            data1.append(data[i])

    return data1

def initialize_conv_reco(travel_options):
    system_message = f"""
    You are an intelligent travel planner and you are tasked with the objective to \
    solve the user queries about any destination or trip from the travel options list in the user message. \
    You should consider the user's travel preferences, budget, and other relevant factors while answering the questions.

    Start with a brief summary of each destination or trip in the following format, in decreasing order of price:
    1. <Destination Name> : <Major attractions/activities>, <Price in Rs>
    2. <Destination Name> : <Major attractions/activities>, <Price in Rs>
    
    """
    user_message = f""" These are the user's preferred travel options: {travel_options}"""
    conversation = [{"role": "system", "content": system_message },
                    {"role":"user","content":user_message}]
    return conversation

