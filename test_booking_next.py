import sys, uuid
sys.path.append('intent_engine')
from intent_engine.core.chatbot import process_message

sess = str(uuid.uuid4())
process_message('I want to book an appointment', sess)  # start booking
res = process_message('Next Monday', sess)
print('Reply:', res.get('reply'))
