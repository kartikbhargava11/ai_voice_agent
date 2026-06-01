

def handle_chat_message(user_message):

    # AI receptionist logic will live here
    # later, this function will call openAI
    # for now, keeping it rule based

    if "book" in user_message.lower() or "appointment" in user_message.lower():
        return {
            'reply': 'Sure! I can help you book an appointment. May I know your name',
            'intent': 'book_appointment',
            'next_step': 'collect_name'
        }
    return {
        'reply': 'Sure, I am your AI receptionist. I can help you book appointments and answer questions.',
        'intent': 'general',
        'next_step': 'collect_name'
    }


def is_ready_to_book(state):
    required_fields = [
        'customer_name',
        'customer_phone',
        'service_needed',
        'appointment_date',
        'appointment_time'
    ]

    return all(state.get(field) for field in required_fields)

