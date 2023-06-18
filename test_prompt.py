# subject = 'left leaning red black trees'
# prompt1 = 'while I am teaching {subject} right now. \
#                                 Can you give me advice to make my students feel like they should \
#                                 pay attention more and engage them more in the next 2 minutes? \
#                                 What other teaching methods can I use to immediately improve classroom \
#                                 engagement in this topic? Please list 4 multiple choice options with examples and breakdowns of the examples in 5 bullet points'
from terminal_gpt import get_completion, get_completion_fast

OPENAI_API_KEY = "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"

responses = ''
percentage = '70'
subject = 'left leaning red black trees'
emotion = 'bored'
prompt1 = f'In this moment, I am a teacher and {percentage}% of my students are \
{emotion} while I am teaching {subject} right now. \
Can you give me advice to make my students feel like they should \
pay attention more and engage them more within the next 2 minutes? \
What other teaching methods can I use to immediately improve classroom \
engagement in this topic? Please list 4 multiple choice options using 1, 2, 3, and 4 with \
examples and breakdowns of each of the examples in 5 bullet points'
print("prompt1", prompt1)
prompt1_response = get_completion_fast(prompt1, OPENAI_API_KEY=OPENAI_API_KEY)
print("prompt1_response", prompt1_response)
responses += prompt1_response
option = '2'
prompt2 = f'given the options {responses}, let us say that I want to use option {option}. \
give me an example of this idea and thoroughly explain the steps for me to execute \
this idea using one bullet point per step to take to show my students this example within 5 minutes.'
#print("prompt2", prompt2)
prompt2_response = get_completion_fast(prompt2, OPENAI_API_KEY=OPENAI_API_KEY)
print("prompt2_response", prompt2_response)
responses += prompt2_response
# #responses = ' '.join(responses)
# print(responses)
# prompt3 = f'given {responses}, what is the answer given from the most recent solution in {responses} plus 12?'
# print("prompt3", prompt3)
# prompt3_response = [get_completion(prompt3)]
# print("prompt3_response", prompt3_response)
# responses = ' '.join(prompt3_response)
# print(responses)


# prompt1 = 'given {given}, what is the previous answer + 12?'

