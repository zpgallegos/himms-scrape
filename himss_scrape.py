import string
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

BASE_URL = (
    "https://www.compusystems.com/servlet/AttendeeRegLoginServlet"
    "?evt_uid=736&site=LIST&_ga=2.66364074.542960560.1647198777-733399034.1647198777"
)

FIELDS = ["first_name", "last_name", "title", "company", "loc", "desc"]

LETTERS = list(string.ascii_lowercase)

WARN_THRESH = 400

driver = webdriver.Chrome()
driver.get(BASE_URL)

box = driver.find_element(By.ID, "last")
btn = driver.find_element(By.XPATH, "//button[@type='submit']")
clr = driver.find_element(By.XPATH, "//button[@type='button']")


def parse_person(person):
    divs = person.find_elements(By.TAG_NAME, "div")
    assert len(divs) == len(FIELDS)
    return {attr: field.text for attr, field in zip(FIELDS, divs)}


def has_people(tbl):
    try:
        tbl.find_element(By.CLASS_NAME, "person")
        return True
    except NoSuchElementException:
        return False


def first_row_visible(tbl):
    first = tbl.find_element(By.CLASS_NAME, "row")
    return "display: none;" not in first.get_attribute("style")


class table_showing_results:
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        tbl = driver.find_element(By.CLASS_NAME, "results")
        if has_people(tbl) or first_row_visible(tbl):
            return tbl
        else:
            return False


def combination_search(letter):
    results = []
    counts = {}

    for ltr in LETTERS:
        qry = letter + ltr

        print(f"querying `{qry}`")

        clr.click()
        box.clear()
        box.send_keys(qry)
        btn.click()

        wait = WebDriverWait(driver, 30)
        tbl = wait.until(table_showing_results((By.CLASS_NAME, "results")))

        if has_people(tbl):
            people = tbl.find_elements(By.CLASS_NAME, "person")
            n = len(people)

            if n > WARN_THRESH:
                print(f"{qry} exceeded thresh with {n} results")
                res, cnt = combination_search(qry)
                results += res
                counts.update(cnt)
            else:
                for person in people:
                    results.append(parse_person(person))
                counts[qry] = len(people)
        else:
            counts[qry] = 0

    return results, counts


def process_letter(letter):
    results = []
    counts = {}

    print(f"querying `{letter}`")

    clr.click()
    box.clear()
    box.send_keys(letter)
    btn.click()

    wait = WebDriverWait(driver, 30)
    tbl = wait.until(table_showing_results((By.CLASS_NAME, "results")))

    if has_people(tbl):
        people = tbl.find_elements(By.CLASS_NAME, "person")
        n = len(people)

        if n > WARN_THRESH:
            print(f"{letter} exceeded thresh with {n} results")
            res, cnt = combination_search(letter)
            results += res
            counts.update(cnt)
        else:
            for person in people:
                results.append(parse_person(person))
            counts[letter] = n
    else:
        counts[letter] = 0

    return results, counts


def scrape():
    results = []
    counts = {}

    for ltr in LETTERS:
        res, cnts = process_letter(ltr)
        results += res
        counts.update(cnts)

    return results, counts


if __name__ == "__main__":

    results, counts = scrape()

    res = pd.DataFrame(results)
    res.to_pickle("results.pkl")

    x, y = zip(*counts.items())
    cnt = pd.DataFrame({"qry": x, "cnt": y})
    cnt.to_pickle("counts.pkl")