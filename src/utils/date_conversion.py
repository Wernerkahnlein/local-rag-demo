from datetime import datetime

def convert_date(date: str):
    spanish_to_english = {
        "Ene": "Jan", "Feb": "Feb", "Mar": "Mar", "Abr": "Apr",
        "May": "May", "Jun": "Jun", "Jul": "Jul", "Ago": "Aug",
        "Sep": "Sep", "Oct": "Oct", "Nov": "Nov", "Dic": "Dec"
    }
    converted_date = date.replace(date[3:6], spanish_to_english[date[3:6]])
    parsed_date = datetime.strptime(converted_date, "%d-%b-%y")
    return parsed_date.isoformat()