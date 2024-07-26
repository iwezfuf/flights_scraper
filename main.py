from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
import requests
from bs4 import BeautifulSoup

DEBUG_MODE = False

# Remove the # before the next line to enter debug mode
#DEBUG_MODE = True

# Change this to get more/less results from azair
MAX_AZAIR_RESULTS = 15

# Change this to get more/less results from kiwi
# Warning - the more results you want, the longer it takes to load
MAX_KIWI_RESULTS = 10

# Do not forget to change the year once in a while
month_map = {
    '1': 'január 2025', '2': 'február 2025', '3': 'marec 2025',
    '4': 'apríl 2025', '5': 'máj 2025', '6': 'jún 2025',
    '7': 'júl 2024', '8': 'august 2024', '9': 'september 2024',
    '10': 'október 2024', '11': 'november 2024', '12': 'december 2024'
}

class Flight:
    def __init__(self, start_day: int = 0, start_month: int = 0, end_day: int = 0, end_month: int = 0, price: int = 0):
        self.start_day = start_day
        self.start_month = start_month
        self.end_day = end_day
        self.end_month = end_month
        self.price = price
        self.from_code = ""
        self.to_code = ""
        self.from_name = ""
        self.to_name = ""
        self.carrier_from = ""
        self.carrier_to = ""

    def from_azair(self, date_from: str, date_to: str, price: str, from_code: str = "", from_name: str = "", to_code: str = "", to_name: str = "", carrier_from: str = "", carrier_to: str = ""):
        break_char: str = "."
        if date_from.find("/") != -1:
            break_char = "/"

        self.start_day = int(date_from.split(break_char)[0])
        self.start_month = int(date_from.split(break_char)[1])
        self.end_day = int(date_to.split(break_char)[0])
        self.end_month = int(date_to.split(break_char)[1])
        self.from_code = from_code
        self.from_name = from_name
        self.to_code = to_code
        self.to_name = to_name
        self.carrier_from = carrier_from
        self.carrier_to = carrier_to

        self.price = round(float(price))

    def from_kiwi(self, date_from: str, date_to: str, price: str, from_code: str = "", to_code: str = "", carrier: str = ""):
        self.price = int(price[:-2])
        date1 = date_from[3:].replace(".", "").split()
        date2 = date_to[3:].replace(".", "").split()
        self.start_day = int(date1[0])
        self.start_month = int(date1[1])
        self.end_day = int(date2[0])
        self.end_month = int(date2[1])
        self.from_code = from_code
        self.to_code = to_code
        if carrier.find("Wizz") != -1:
            self.carrier_from = "Wizzair"
        elif carrier == "Ryanair":
            self.carrier_from = "Ryanair"
        else:
            self.carrier_from = "other"

    def offset_price(self, offset: int):
        self.price -= offset

    def create_link(self) -> str:
        if self.carrier_from == "Ryanair":
            return create_ryanair_link(self, self.from_code, self.to_code)
        else:
            return create_wizz_link(self, self.from_code, self.to_code)

    def to_string(self) -> str:
        if self.start_month == self.end_month:
            return f"{self.start_day}. - {self.end_day}. {month_map[str(self.start_month)]} za {self.price}€"
        else:
            return f"{self.start_day}. {month_map[str(self.start_month)]} - {self.end_day}. {month_map[str(self.end_month)]} za {self.price}€"

    def same_trip(self, other: 'Flight') -> bool:
        return self.start_day == other.start_day \
           and self.start_month == other.start_month \
           and self.end_day == other.end_day \
           and self.end_month == other.end_month

    def __eq__(self, __value: object) -> bool:
        return self.same_trip(__value) and self.price == __value.price
    
    def __hash__(self) -> int:
        return hash((self.start_day, self.start_month, self.end_day, self.end_month, self.price))


def sort_flights(flights: list[Flight]) -> list[Flight]:
    return sorted(flights, key=lambda x: (x.start_month, x.start_day, x.end_month, x.end_day))

def date_to_string(month: int, day: int) -> str:
    return f"{month_map[str(month)][-4:]}-{str(month).zfill(2)}-{str(day).zfill(2)}"

def create_wizz_link(flight: Flight, from_code: str, to_code: str) -> str:
    from_date: str = date_to_string(flight.start_month, flight.start_day)
    to_date: str = date_to_string(flight.end_month, flight.end_day)
    return f"https://wizzair.com/sk-sk/booking/select-flight/{from_code}/{to_code}/{from_date}/{to_date}/1/0/0/null"

def create_ryanair_link(flight: Flight, from_code: str, to_code: str) -> str:
    from_date: str = date_to_string(flight.start_month, flight.start_day)
    to_date: str = date_to_string(flight.end_month, flight.end_day)
    return f"https://www.ryanair.com/sk/en/trip/flights/select?adults=1&dateOut={from_date}&dateIn={to_date}&originIata={from_code}&destinationIata={to_code}"

def add_flight_to_list(flights: list[Flight], flight: Flight):
    for f in flights:
        if f.same_trip(flight):
            if f.price > flight.price:
                flights.remove(f)
                flights.append(flight)
            return
    flights.append(flight)


def print_flights_with_links(flights: list[Flight]):
    print("<p>")
    for flight in flights:
        if flight.carrier_from != "Ryanair" and flight.carrier_from.find("Wizz") == -1:
            print_flights_without_links([flight])
            continue
        print('<a href="', end="")
        print(flight.create_link(), end="")
        print(f'">- {flight.to_string()}</a><br />')
    print("</p>")

def print_flights_without_links(flights: list[Flight]):
    for flight in flights:   
        print("- " + flight.to_string())

def print_flights(flights: list[Flight]):
    print_flights_with_links(flights)
    print()
    print_flights_without_links(flights)


# Azair
##############################################################################################################


def get_azair_flights(url: str, num: int) -> list[Flight]:
    response = requests.get(url)
    text = response.text
    soup = BeautifulSoup(text, "html.parser")
    entries = soup.find_all("div", class_="result")
    results = []
    for entry in entries:
        if len(results) == num:
            break
        # with open("azair.html", "w", encoding="utf-8") as file:
        #     file.write(str(entry))

        # Get span with class date and get the text
        date_there = entry.find("span", class_="date").text.split()[1]
        # Get the second span with class date and get the text
        date_back = entry.find_all("span", class_="date")[1].text.split()[1]
        # Get div with class totalPrice and get the text until first whitespace
        price = entry.find("div", class_="totalPrice").text.split()[0][1:]
        # Get span with class from and get the text
        from_span = entry.find("span", class_="from")
        # get text from first space
        from_code = from_span.find("span", class_="code").text[:3]
        from_span.find("span").clear()
        from_name = from_span.text[6:].strip()
        # Get span with class to and get the text
        to_span = entry.find("span", class_="to")
        to_code = to_span.find("span", class_="code").text[:3]
        to_span.find("span").clear()
        to_name = to_span.text[6:].strip()

        # Get the carriers
        from_div = entry.find_all("div", class_="detail")[0].find("p")
        to_div = entry.find_all("div", class_="detail")[1].find("p")
        carrier_from = ""
        carrier_to = ""
        for child in from_div.children:
            if hasattr(child, 'has_attr') and child.has_attr("class") is not None and "airline" in child["class"]:
                carrier_from = child.text
        for child in to_div.children:
            if hasattr(child, 'has_attr') and child.has_attr("class") is not None and "airline" in child["class"]:
                carrier_to = child.text

        flight = Flight()
        flight.from_azair(date_there, date_back, price, from_code, from_name, to_code, to_name, carrier_from, carrier_to)

        add_flight_to_list(results, flight)
    return results




##############################################################################################################



# Kiwi
##############################################################################################################
print("Starting browser...")

options = FirefoxOptions()
if not DEBUG_MODE:
    options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
driver.set_window_position(0, 0)
driver.maximize_window()


def get_kiwi_flights(driver, url: str, num: int) -> list[Flight]:
    driver.get(url)
    wait = WebDriverWait(driver, 15)

    # Click on position (x=0, y=100) to close the cookies popup and google login popup
    driver.execute_script("document.elementFromPoint(0, 100).click();")

    load_more_button_xpath = "//*[contains(text(), 'Načítať viac')]"

    time.sleep(2)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test="ResultCardWrapper"]')))

    from_code = driver.find_elements(By.CSS_SELECTOR, '[data-test="stationName"]')[0].text
    to_code = driver.find_elements(By.CSS_SELECTOR, '[data-test="stationName"]')[1].text

    results = []
    for i in range(0, 50):
        driver.execute_script("window.scrollTo(0, 50000)")
        if DEBUG_MODE:
            print("Number of results so far:", len(results), "at i =", i)
        if len(results) >= num:
            break
        try:
            result_card_wrapper = driver.find_elements(By.CSS_SELECTOR, '[data-test="ResultCardWrapper"]')[i]
            result_card_price = result_card_wrapper.find_elements(By.CSS_SELECTOR, '[data-test="ResultCardPrice"]')[0]
            price = result_card_price.find_element(By.CSS_SELECTOR, "div > span").text
            
            date1_p = result_card_wrapper.find_elements(By.CSS_SELECTOR, '[data-test="ResultCardSectorDepartureDate"]')[0]
            date1 = date1_p.find_element(By.CSS_SELECTOR, "p > time").text

            date2_p = result_card_wrapper.find_elements(By.CSS_SELECTOR, '[data-test="ResultCardSectorDepartureDate"]')[1]
            date2 = date2_p.find_element(By.CSS_SELECTOR, "p > time").text

            carrier = result_card_wrapper.find_element(By.CSS_SELECTOR, "img").get_attribute("title")

            flight = Flight()
            flight.from_kiwi(date1, date2, price, from_code, to_code, carrier)
            add_flight_to_list(results, flight)
        except Exception as e:
            if DEBUG_MODE:
                print("error", i, e)
            if DEBUG_MODE:
                print("Trying to load more...")
            
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, load_more_button_xpath)))
                driver.execute_script("window.scrollTo(0, 50000)")
                wait.until(EC.element_to_be_clickable((By.XPATH, load_more_button_xpath)))
                load_more_button = driver.find_element(By.XPATH, load_more_button_xpath)
                load_more_button.click()
                time.sleep(2)
            except Exception as e:
                print("Failed to load more")
                print()
                break

    return results


##############################################################################################################
user_input = ""
results: list[Flight] = ""
while True:
    user_input = input('Give me Kiwi or Azair link or write a number to reduce prices: \n')

    if user_input == "q":
        break

    if user_input[0] == "-" or user_input.isdecimal():
        reduce_by = int(user_input)
        for result in results:
            result.offset_price(reduce_by)
        print_flights(results)
        continue

    link = user_input

    if link.find("kiwi") == -1 and link.find("azair") == -1:
        print("Wrong link")
        continue

    link += "&currency=EUR"
    
    if link.find("kiwi") != -1:
        try:
            results = get_kiwi_flights(driver, link, num=MAX_KIWI_RESULTS)
        except Exception as e:
            print("Error:", str(e))
    elif link.find("azair") != -1:
        try:
            results = get_azair_flights(link, num=MAX_AZAIR_RESULTS)
        except Exception as e:
            print("Error:", str(e))
    
    results = sort_flights(results)
    print_flights(results)

    print("\nDone\n")


driver.close()
