import os
import pushed
import re
import time
import yaml

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


with open("creds.yaml", "r") as ymlfile:
    cfg = yaml.safe_load(stream=ymlfile)


# month = int(time.strftime('%b'))
testing = cfg['Testing']


class Test:

    def push_app(self, st):
        print('Simulated:', st)

    def __repr__(self):
        return 'Teeessttt'

# if month == 12 or month < 4:
#    semester = 2  # Fall
# else:
#    semester = 1  # Spring
#  TODO: This is because it shows the Fall and Spring semesters in a Table though
#        Spring hasn't happened. Or is this even necessary? Does it always have
#        one more? Unless you're graduating? Please let me know

print('Started', time.strftime('%d%b at %H:%M'))


print('If this fails to login, change the password in creds.yaml.')


if 'netID' not in cfg or not cfg['netID']:
    print('''Add netID and password to creds.yaml to remove the need to type this in every time.
    Or just put your netID and it will just ask for the password.
    Example:
    netID: abc123
    password: yopasswordhere
    
    but for now,''')
    netID = input('netID?\n')
else:
    netID = cfg['netID']

if 'password' not in cfg or not cfg['password']:
    password = input('Password?\n')
else:
    password = cfg['password']

if testing or 'APP_KEY' not in cfg or 'APP_SECRET' not in cfg or not cfg['APP_KEY'] or not cfg['APP_SECRET']:
# If it's testing or if they're not there or blank.
    print('Add APP_KEY and APP_SECRET to creds.yaml if you want to use Pushed for notifications')
    p = Test()
else:
    p = pushed.Pushed(cfg['APP_KEY'], cfg['APP_SECRET'])


def browser_init():
    options = Options()
    if not testing:
        options.add_argument('-headless')

    browser = webdriver.Firefox(executable_path=os.getcwd()+'/geckodriver', options=options)
    return browser


def browser_login(browser, netID):
    browser.get('http://albert.nyu.edu')
    print('Browser started and at Albert...')
    browser.find_element_by_link_text('Sign in to Albert').click()  # Clicks the login thing

    browser.find_element_by_id('netid').send_keys(netID)
    browser.find_element_by_id('password').send_keys(password)

    browser.find_element_by_name('_eventId_proceed').click()
    print('Browser logged in...')

    size = browser.get_window_size()
    browser.set_window_size(500, 500)
    time.sleep(2)
    action = ActionChains(browser)
    action.move_by_offset(200, 300)
    action.click()
    action.perform()
    time.sleep(1)

    # p.push_app('It\'s me...')
    print('Requesting MFA...')
    browser.set_window_size(size['width'], size['height'])
    current_url = browser.current_url
    WebDriverWait(browser, 600).until(EC.url_changes(current_url))

    print('MFA successful...')
    WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#IS_ED_SSS_GRADESLnk > span")))


def UpdateGPA(browser, p, GPAref):
    a = browser.find_elements_by_xpath('//h2')
    if not a:
        browser.back()
        browser.refresh()
    for i in a:
        b = re.search(r'\d\.\d{3}', i.text)
        if b:
            b = b[0]
            if b != GPAref:
                p.push_app('New GPA: ' + str(b))
                GPAref = b
            break
    return GPAref


def UpdateGrades(browser, p, grades_list):
    try:
        browser.get('https://sis.portal.nyu.edu/psp/ihprod/EMPLOYEE/EMPL/h/?tab=IS_SSS_TAB&jsconfig=IS_ED_SSS_GRADESLnk')
        WebDriverWait(browser, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#IS_ED_SSS_GRADESLnk > span")))
        time.sleep(3)
        c = browser.find_elements_by_xpath('//div[4]/div[2]/table/tbody/tr/td')
        print('\n\n\n')
        grades = []
        for i in range(1, len(c), 6):
            if c[i].text != 'EXAMINATION HOUR':
                grades.append(c[i].text + ' ' * (31 - len(c[i].text)) + ' ' + c[i + 4].text)
                if c[i].text not in grades_list and c[i + 4].text != ' ':
                    grades_list[c[i].text] = c[i + 4].text
                    p.push_app(c[i].text + ': ' + c[i + 4].text)
        grades = '\n'.join(grades)
        print(grades)
        print('Last refreshed:', time.strftime('%d%b at %H:%M'))
        return False  # Did it die?
    except Exception as e:
        print('------------------------------------------------------------------------\n'
              'There was an error. If this doesn\'t keep breaking, the except worked\n')
        print("Just in case it doesn't fix it, here's the exception\n", str(e))
        with open('ErrorLog.txt', 'a') as file:
            print(time.strftime('%d%b at %H:%M:%S'), '\n', str(e), '\n--------\n', file=file)
        p.push_app('App died')
        return True  # Did it die?


def run(netID, p, password):
    browser = browser_init()
    browser_login(browser, netID)
    del netID, password
    grades_list = {}
    if not testing:
        sleeptime = 600  # seconds
    else:
        sleeptime = 10

    UpdateGrades(browser, p, grades_list)
    GPAref = UpdateGPA(browser, p, '0')

    time.sleep(sleeptime)

    Died = False
    while not Died:
        Died = UpdateGrades(browser, p, grades_list)
        GPAref = UpdateGPA(browser, p, GPAref)

        time.sleep(sleeptime)

    return browser, p


browser, p = run(netID, p, password)  # For when I run in console then do commands after
