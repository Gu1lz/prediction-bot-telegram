from scraper import fetch_search
from parser import parse_question
from weather import fetch_weather
from decision import best_market
from datetime import datetime

def run():
    events = fetch_search()
    for m in events:
        question = m["title"]
        unit = m["markets"][0]["groupItemTitle"]
        print(question + "-" + m["endDate"] + " - " + m["slug"] + " - " + m["createdAt"])
        parsed = parse_question(question, unit)
        if not parsed:
            continue
        print("URL: polymarket.com/event/" + m["slug"])
        print(parsed)
        if parsed["type"] == "temperature":
            weather = fetch_weather(parsed["lat"], parsed["lon"], m["endDate"], parsed["unit"])
            print(weather)
            one, second = best_market(m["markets"], weather["temperature_max"])
            print(one[1]["slug"])
            print(one[1]["outcomePrices"])
            print(second[1]["slug"])

if __name__ == "__main__":
    run()
