import os
import openai

#import click
def get_completion(prompt, model='gpt-4'):
    openai.api_key = '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'
    messages = [{'role': 'user', 'content': prompt}]
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0,)
    return response.choices[0].message['content']

def get_completion_fast(prompt, model='gpt-3.5-turbo'):
    openai.api_key = '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'
    messages = [{'role': 'user', 'content': prompt}]
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0,)
    return response.choices[0].message['content']


# if __name__ == '__main__':
#     prompt=prompt1
#     response = get_completion(prompt)
    
#to run this bitch in terminal, run "python3 terminalGPT.py"
