import os
from pathlib import Path
from time import sleep
from dotenv import load_dotenv
from groq import Groq
 
load_dotenv()
 
apikey=os.getenv("GROQ_API_KEY")
if not apikey:
    raise ValueError("api key bana le bhaii!!")
 
client=Groq(api_key=apikey)
model="openai/gpt-oss-120b"
def ask_llm(prompt):
    message=[
        {
            "role":"user",
            "content":prompt
        }
    ]
    response= client.chat.completions.create(messages=message,model=model)
    return response.choices[0].message.content

print(ask_llm("hii"))

# def ask_llm(prompt):
   
#     message.append(       
#         {
#             "role":"user",
#             "content":prompt
#         })

#     response= client.chat.completions.create(messages=message,model=model,tools=TOOLS)
#     ans=response.choices[0].message.content       
#     message.append({
#                 "role":"assistant",
#                 "content":ans
#             })
#     return ans

# print(ask_llm("hii"))
# chat thing
# while True:
#     user=input("you:")
#     if user.strip().lower()in ('exit','quite'):
#         break
#     ans=ask_llm(user)
#     print("bot: ",ans)
