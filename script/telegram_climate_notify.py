''' Requirements '''
import pandas as pd
import requests
from datetime import date
import os


''' Parameters '''

LATITUDE = '40.561538'
LONGITUDE = '-3.623315'
ID_CITY = '28134' # San Sebastian de los reyes

today = date.today()
TODAY_ISO = today.isoformat()
TODAY_FORMATTED = today.strftime('%d/%m/%Y')

''' Credentials'''

def read_credentials():
    file_path = os.path.join(os.path.dirname(os.getcwd()),'credentials','credentials.csv')
    df  = pd.read_csv(file_path, sep=',')
    API_KEY_OW      = df['api-key'][df['platform']=='openweather'].iloc[0]
    API_KEY_AEMET   = df['api-key'][df['platform']=='aemet'].iloc[0]
    del df
    return API_KEY_OW, API_KEY_AEMET

def get_gofrinator_credentials():
    file_path = os.path.join(os.path.dirname(os.getcwd()),'credentials','telegram_gofrinator.csv')
    df  = pd.read_csv(file_path, sep=',')
    TOKEN      = df['value'][df['item']=='token'].iloc[0]
    CHAT_ID    = df['value'][df['item']=='chat-id'].iloc[0]
    del df
    return TOKEN, CHAT_ID


def current_weather(LATITUDE, LONGITUDE, API_KEY_OW):
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={LATITUDE}&lon={LONGITUDE}&units=metric&appid={API_KEY_OW}'
    r = requests.get(url)
    data = r.json()
    TEMP = str(data['main']['temp'])+'°C'
    FEEL = str(data['main']['feels_like'])+'°C'
    HUMD = str(data['main']['humidity'])+'%'
    WIND = str(data['wind']['speed'])+' km/h'
    SKY = str(data['weather'][0]['description'])
    return TEMP, FEEL, WIND, HUMD, SKY


def get_prob_precipitacion(probPrecipitacion):
    probs = []
    for i in range(len(probPrecipitacion)):
        if 'value' in probPrecipitacion[i] and probPrecipitacion[i]['value'] > 0:
            probs.append(
                str(probPrecipitacion[i]['periodo']) +
                ': ' + str(probPrecipitacion[i]['value']) + '%'
            )
    return probs

def forecast_weather(ID_CITY, API_KEY_AEMET):
    url = f'https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/{ID_CITY}/?api_key={API_KEY_AEMET}'
    r = requests.get(url)
    response = r.json()
    url = response['datos']
    data = requests.get(url).json()
    days = data[0]['prediccion']['dia']
    for day in days:
        if day['fecha'].startswith(TODAY_ISO):
            
            prob_precipitacion = day.get('probPrecipitacion', [])
            PROBS = get_prob_precipitacion(prob_precipitacion)

            temps_all = day['temperatura']['dato']
            TEMPS = [(str(t['hora']) + ':00: ' + str(t['value']) + '°C') for t in temps_all]
            
            senstermica_all = day['sensTermica']['dato']
            FEELTERM = [(str(t['hora']) + ':00: ' + str(t['value']) + '°C') for t in senstermica_all]
            break
    del prob_precipitacion
    del temps_all
    del senstermica_all
    return FEELTERM, TEMPS, PROBS

def emoji_status(SKY):
    status = SKY.lower()
    if "clear" in status:
        return "☀️"
    elif "few clouds" in status:
        return "🌤️"
    elif "scattered clouds" in status:
        return "⛅"
    elif "broken clouds" in status:
        return "🌥️"
    elif "overcast clouds" in status:
        return "☁️"
    elif "shower rain" in status or "light rain" in status:
        return "🌦️"
    elif "rain" in status:
        return "🌧️"
    elif "thunderstorm" in status:
        return "⛈️"
    elif "snow" in status:
        return "❄️"
    elif "mist" in status or "fog" in status:
        return "🌫️"
    else:
        return "🌈"

def formatear_mensaje_tiempo(TODAY_ISO, TEMP, FEEL, WIND, HUMD, SKY, TEMPS, FEELTERM, PROBS):
    EMOJI_SKY = emoji_status(SKY)

    message =f"""
    {EMOJI_SKY} Buenos días! {EMOJI_SKY}

⏰ El tiempo ahora ⏰

{EMOJI_SKY} Estado del cielo: <b>{SKY}</b>
🌡️ Temperatura: <b>{TEMP}</b>
🤒 Sensación térmica: <b>{FEEL}</b>
💨 Viento: <b>{WIND}</b>
💧 Humedad: <b>{HUMD}</b>

📅 Pronóstico para hoy 📅

🌡️ Temperatura 🌡️\n
"""
    for t in TEMPS:
        message += f"<b>{t}</b>\n"

    message += "\n🤒 Sensación térmica 🤒\n\n"
    for s in FEELTERM:
        message += f"<b>{s}</b>\n"

    message += "\n🌧️ Probabilidad de lluvia 🌧️\n"
    for p in PROBS:
        message += f"<b>{p}</b>\n"

    return message


def telegram_notify(MESSAGE,TOKEN, CHAT_ID):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": MESSAGE,
        "parse_mode": "HTML"
    }
    requests.get(url, params=params)

if __name__ == "__main__":
    API_KEY_OW, API_KEY_AEMET = read_credentials()
    TOKEN, CHAT_ID = get_gofrinator_credentials()
    N_TEMP, N_FEEL, N_WIND, N_HUMD, N_SKY = current_weather(LATITUDE, LONGITUDE, API_KEY_OW)
    F_FEELTERM, F_TEMPS, F_PROBS = forecast_weather(ID_CITY, API_KEY_AEMET)
    MESSAGE = formatear_mensaje_tiempo(TODAY_FORMATTED, N_TEMP, N_FEEL, N_WIND, N_HUMD, N_SKY, F_TEMPS, F_FEELTERM, F_PROBS)
    telegram_notify(MESSAGE,TOKEN, CHAT_ID)