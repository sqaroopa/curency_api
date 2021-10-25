from flask import Flask, jsonify, Response
from flask_restful import Api, Resource, reqparse, inputs
from lxml import etree
from datetime import date, datetime, timedelta
import requests

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///name.db'
currencies_list = 'https://www.cbr.ru/scripts/XML_valFull.asp'
quotes_by_day = 'http://www.cbr.ru/scripts/XML_daily.asp'
xml_path = 'currency_list.xml'


@app.route('/')
def hello_world():
    return 'Hello World!'


@api.resource('/currency_list')
class CurrencyList(Resource):
    @staticmethod
    def get():
        root = etree.parse(xml_path).getroot()
        children = list(root)
        codes = []
        for child in root:
            if child[5].text != None:
                print(child[5].text)
                codes.append(child[5].text)
        return codes


@api.resource('/quotes_by_day')
class ValByDate(Resource):
    @staticmethod

    def get():
        parser = reqparse.RequestParser()
        parser.add_argument(
            'start_time',
            type=lambda x: datetime.strptime(x, '%Y-%m-%d'),
            help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
            required=True
        )
        parser.add_argument(
            'end_time',
            type=lambda x: datetime.strptime(x, '%Y-%m-%d'),
            help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
            required=True
        )
        parser.add_argument(
            'currency',
            type=str,
            help="Enter currency code from the list",
            default='USD',
            required=True
        )

        args = parser.parse_args()
        if args['start_time'] is None:
            return Response(requests.get(quotes_by_day), mimetype='text/xml', content_type='utf-8')
        else:
            start_time = args['start_time'].date()
            end_time = args['end_time'].date()
            currency_code = args['currency']
            start_time_formt = '/'.join(str(start_time).split('-')[::-1])
            end_time_formt = '/'.join(str(end_time).split('-')[::-1])
            days = [start_time_formt, end_time_formt]
            quotes1 = []
            quotes2 = []
            for day in days:
                req = requests.get(f'{quotes_by_day}?date_req={day}', stream=True)
                cont = etree.parse(req.raw)
                root = cont.getroot()
                children = list(root)
                for child in root:
                    pair = (child[1].text, child[4].text)
                    if day == start_time_formt:
                        quotes1.append(pair)
                    else:
                        quotes2.append(pair)
            # print(quotes1)
            # print(quotes2)
            selected_currency = []

            for currency in [quotes1, quotes2]:
                for t in currency:
                    # print(f'api: {currency_code} list: {currency[0][0]}')
                    if currency_code == t[0]:
                        # print(f'api: {currency_code} list: {t[0]}')
                        # print(currency_code)
                        # selected_currency.append(float(currency[0][1].replace(',', '.')))
                        selected_currency.append(float(t[1].replace(',', '.')))



            # print(f'Value of {currency_code} by {start_time}: {selected_currency[0]} RUB')
            # print(f'Value of {currency_code} by {end_time}: {selected_currency[1]} RUB')
            # print(f'Difference in value for {currency_code} between {start_time} and {end_time}: {round(abs(selected_currency[0] - selected_currency[1]), 4)} RUB')

            out = jsonify({
                f'Value of {currency_code} by {start_time}':  f'{selected_currency[0]} RUB',
                f'Value of {currency_code} by {end_time}': f'{selected_currency[1]} RUB',
                f'Difference between {start_time} and {end_time}': f'{round(abs(selected_currency[0] - selected_currency[1]), 4)} RUB'}
                 )
        return out


if __name__ == '__main__':
    app.run()
