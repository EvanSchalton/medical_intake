import re
from openai import OpenAI
from time import time, sleep
from halo import Halo
import textwrap
import yaml
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
## add file handler to logger
handler = logging.FileHandler('debugging_logs/log_%s.log' % time())
handler.setLevel(logging.DEBUG)
## add formatter to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
## add handler to logger
logger.addHandler(handler)


###     file operations
def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()
    
client = OpenAI(api_key=open_file('key_openai.txt').strip())
###     API functions


def chatbot(conversation, model="gpt-4-0613", temperature=0, max_tokens=2000):

    max_retry = 7
    retry = 0
    while True:
        try:
            spinner = Halo(text='Thinking...', spinner='dots')
            spinner.start()

            logger.debug(f"conversation: {conversation}")
            
            response = client.chat.completions.create(
                model=model,
                messages=conversation,
                temperature=temperature,
                max_tokens=max_tokens
            )

            logger.debug(f"response: {response}")

            text = response.choices[0].message.content
            logger.debug(f"text: {text}")

            spinner.stop()

            logger.debug(f"response.usage.total_tokens: {response.usage.total_tokens}")
            
            return text, response.usage.total_tokens
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            exit(5)


def chat_print(text):
    formatted_lines = [textwrap.fill(line, width=120, initial_indent='    ', subsequent_indent='    ') for line in text.split('\n')]
    formatted_text = '\n'.join(formatted_lines)
    print('\n\n\nCHATBOT:\n\n%s' % formatted_text)


if __name__ == '__main__':
    
    
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_00_demographics.md')})

    user_messages = list()
    all_messages = list()
    
    ## INTAKE PORTION
    print('Describe your demographic information to the intake bot. Type SUBMIT when done.')
    standard_fields = {
        "age (years)": "",
        "weight (lbs)": "",
        "height (inches)": "",
    }

    print("\n\n")
    for field in standard_fields:
        # get user input
        standard_fields[field] = input(f'PATIENT: {field}: ').strip()
    
    demo_string = ", ".join(f"{k}: {v}" for k,v in standard_fields.items())
    text = f"About Me: {demo_string}"

    user_messages.append(text)
    all_messages.append('PATIENT: %s' % text)
    conversation.append({'role': 'user', 'content': text})
    response, tokens = chatbot(conversation)
    
    conversation.append({'role': 'assistant', 'content': response})
    all_messages.append('DEMOGRAPHICS: %s' % response)
    print('\n\nDEMOGRAPHICS: %s' % response)
    
    conversation.append({'role': 'system', 'content': open_file('system_00_demographics.md')})

    print('Describe your demographics to the intake bot. Type FINISHED when you feel like you\'ve given enough information.')

    while True:
        # get user input
        text = input('PATIENT: ').strip()
        if text == 'FINISHED':
            break
        user_messages.append(text)
        all_messages.append('PATIENT: %s' % text)
        conversation.append({'role': 'user', 'content': text})
        response, tokens = chatbot(conversation)
        
        conversation.append({'role': 'assistant', 'content': response})
        all_messages.append('DEMOGRAPHICS: %s' % response)
        print('\n\nDEMOGRAPHICS: %s' % response)

    conversation.append({'role': 'system', 'content': open_file('system_01_intake.md')})

    print('Describe your symptoms to the intake bot. Type DONE when done.')

    while True:
        # get user input
        text = input('\n\nPATIENT: ').strip()
        if text == 'DONE':
            break
        user_messages.append(text)
        all_messages.append('PATIENT: %s' % text)
        conversation.append({'role': 'user', 'content': text})
        response, tokens = chatbot(conversation)
        
        conversation.append({'role': 'assistant', 'content': response})
        all_messages.append('INTAKE: %s' % response)
        print('\n\nINTAKE: %s' % response)
    
    ## CHARTING NOTES
    
    print('\n\nGenerating Intake Notes')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_02_prepare_notes.md')})
    text_block = '\n\n'.join(all_messages)
    chat_log = '<<BEGIN PATIENT INTAKE CHAT>>\n\n%s\n\n<<END PATIENT INTAKE CHAT>>' % text_block
    save_file('logs/log_%s_chat.txt' % time(), chat_log)
    conversation.append({'role': 'user', 'content': chat_log})
    notes, tokens = chatbot(conversation)
    print('\n\nNotes version of conversation:\n\n%s' % notes)
    save_file('logs/log_%s_notes.txt' % time(), notes)
    
    ## GENERATING REPORT

    print('\n\nGenerating Hypothesis Report')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_03_diagnosis.md')})
    conversation.append({'role': 'user', 'content': notes})
    report, tokens = chatbot(conversation)
    save_file('logs/log_%s_diagnosis.txt' % time(), report)
    print('\n\nHypothesis Report:\n\n%s' % report)

    ## CLINICAL EVALUATION

    print('\n\nPreparing for Clinical Evaluation')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_04_clinical.md')})
    conversation.append({'role': 'user', 'content': notes})
    clinical, tokens = chatbot(conversation)
    save_file('logs/log_%s_clinical.txt' % time(), clinical)
    print('\n\nClinical Evaluation:\n\n%s' % clinical)

    ## REFERRALS & TESTS

    print('\n\nGenerating Referrals and Tests')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_05_referrals.md')})
    conversation.append({'role': 'user', 'content': notes})
    referrals, tokens = chatbot(conversation)
    save_file('logs/log_%s_referrals.txt' % time(), referrals)
    print('\n\nReferrals and Tests:\n\n%s' % referrals)
