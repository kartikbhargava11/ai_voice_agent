from datetime import datetime

def human_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%-d')
        return date_obj.strftime('%A, %-d %B')
    except Exception:
        return date_str
    

def human_time(time_str):
    try:
        time_obj = datetime.strptime(time_str, '%H:%M')
        return time_obj.strftime('%-I:%M %p').replace(':00', '')
    except Exception:
        return time_str