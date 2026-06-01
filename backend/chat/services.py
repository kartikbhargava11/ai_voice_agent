

def handle_chat_message(user_message):

    # AI receptionist logic will live here
    # later, this function will call openAI
    # for now, keeping it rule based

    # temporary
    return {
        'reply': 'Sure, I can help you book an appointment. May I know you full name?',
        'next_step': 'collect_name'
    }