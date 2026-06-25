import sys, uuid
sys.path.append('intent_engine')
from intent_engine.core.chatbot import process_message

sess = str(uuid.uuid4())
# Start booking
res1 = process_message('I want to book an appointment', sess)
print('Step1:', res1.get('reply'))
# Send date 'Tomorrow'
res2 = process_message('Tomorrow', sess)
print('Step2:', res2.get('reply'))
# Send time '10:00'
res3 = process_message('10:00', sess)
print('Step3:', res3.get('reply'))
