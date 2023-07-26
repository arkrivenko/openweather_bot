import telebot
import pyowm
import os

from dotenv import load_dotenv
from telebot import types
from pyowm.commons.exceptions import NotFoundError


load_dotenv()

token = os.getenv('TOKEN')
api_key = os.getenv('OWM_KEY')

bot = telebot.TeleBot(token)

owm = pyowm.OWM(api_key)
weather_manager = owm.weather_manager()


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, 'Hello! I am a weather forecast bot. Type /help to see a list of commands.')


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message,
                 '/current_by_geo - get current weather forecast by geolocation\n'
                 '/current_by_city - get current weather forecast by city name\n')


@bot.message_handler(commands=['current_by_geo'])
def get_geo_button(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_geo = types.KeyboardButton(text='Send GEO', request_location=True)
    keyboard.add(button_geo)
    bot.send_message(message.chat.id, 'Hello! Press the button and send me your location.',
                     reply_markup=keyboard)


@bot.message_handler(content_types=['location'])
def get_weather_at_location(message):
    chat_id = message.chat.id
    lat, lon = message.location.latitude, message.location.longitude

    try:
        observation = weather_manager.weather_at_coords(lat, lon)
        w = observation.weather

        temp = w.temperature('celsius')['temp']
        time = w.reference_time('iso').split('+')[0]
        status = w.detailed_status
        bot.send_message(chat_id, f'Now({time}) {status} temp {temp}°C.')

        forecast = weather_manager.forecast_at_coords(lat, lon, interval='daily', limit=5)

        for weather in forecast.forecast.weathers:
            status = weather.detailed_status
            temp = weather.temperature('celsius')['temp']
            time = weather.reference_time('iso').split('+')[0]

            bot.send_message(chat_id, f'{time}: {status}, temp {temp}°C.')

    except NotFoundError:
        bot.send_message(chat_id, 'Unable to find the weather data')


@bot.message_handler(commands=['current_by_city'])
def hourly_forecast(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Enter the name of the locality.')
    bot.register_next_step_handler(msg, get_weather_at_city, chat_id)


def get_weather_at_city(message, chat_id):
    city_name = message.text
    if not city_name:
        msg = bot.send_message(chat_id, 'An empty request has been entered, please try again.')
        bot.register_next_step_handler(msg, get_weather_at_city, chat_id)
    else:
        try:
            observation = weather_manager.weather_at_place(city_name)
            w = observation.weather

            temp = w.temperature('celsius')['temp']
            status = w.detailed_status

            bot.send_message(chat_id,
                             f'Now {status} temp {temp}°C.')

            forecast = weather_manager.forecast_at_place(city_name, interval='daily', limit=5)

            for weather in forecast.forecast.weathers:
                status = weather.detailed_status
                temp = weather.temperature('celsius')['temp']
                time = weather.reference_time('iso').split('+')[0]

                bot.send_message(chat_id, f'{time}: {status}, temp {temp}°C.')

        except NotFoundError:
            bot.send_message(chat_id, 'Unable to find the weather data')


if __name__ == '__main__':
    bot.infinity_polling(skip_pending=True)
