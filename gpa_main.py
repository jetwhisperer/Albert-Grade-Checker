import os
import re
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

if os.path.exists('creds.yaml'):
    import yaml

    with open("creds.yaml", "r") as ymlfile:
        cfg = yaml.safe_load(stream=ymlfile)
else:
    cfg = {}

grades_list = {}

if 'Testing' in cfg:
    testing = cfg['Testing']
else:
    testing = False

# month = int(time.strftime('%b'))
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
    password: password
    
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


    class TerminalPush:

        def push_app(self, st):
            print('Simulated:', st)


    p = TerminalPush()
else:
    import pushed

    p = pushed.Pushed(cfg['APP_KEY'], cfg['APP_SECRET'])


def wait_page_change(browser):
    current_url = browser.current_url
    WebDriverWait(browser, 600).until(EC.url_changes(current_url))


def browser_init():
    options = Options()
    if not testing:
        options.add_argument('-headless')

    browser = webdriver.Firefox(executable_path=os.getcwd() + '/geckodriver', options=options)
    return browser


def browser_login(browser):
    browser.get('http://albert.nyu.edu')
    print('Browser started and at Albert...')
    browser.find_element_by_link_text('Sign in to Albert').click()  # Clicks the login thing

    browser.find_element_by_id('netid').send_keys(netID)
    browser.find_element_by_id('password').send_keys(password)

    browser.find_element_by_name('_eventId_proceed').click()
    print('Browser logged in...')
    time.sleep(3)

    if 'shibboleth' in browser.current_url:
        size = browser.get_window_size()
        browser.set_window_size(500, 510)
        time.sleep(0.5)

        action = ActionChains(browser)  # Security features don't allow selenium to click things with precision
        action.move_by_offset(200, 430).click()  # Remember me for 1 day
        action.pause(0.1)
        action.move_by_offset(0, -130).click().perform()  # Send Me a Push
        print('Requesting MFA...')

        wait_page_change(browser)
        browser.set_window_size(size['width'], size['height'])
        print('MFA successful...')


def UpdateGPA(browser, GPAref):
    a = browser.find_elements_by_xpath('//h2')  # This is ugly but there's no name for it and the xpath index varied...
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


def UpdateGrades(browser):
    try:
        browser.get(
            'https://sis.portal.nyu.edu/psp/ihprod/EMPLOYEE/EMPL/h/?tab=IS_SSS_TAB&jsconfig=IS_ED_SSS_GRADESLnk')
        time.sleep(1)

        if 'shibboleth' in browser.current_url:
            browser_login(browser)
            browser.get(
                'https://sis.portal.nyu.edu/psp/ihprod/EMPLOYEE/EMPL/h/?tab=IS_SSS_TAB&jsconfig=IS_ED_SSS_GRADESLnk')

        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#IS_ED_SSS_GRADESLnk > span")))
        time.sleep(3)
        c = browser.find_elements_by_xpath('//div[4]/div[2]/table/tbody/tr/td')
        print('\n\n\n')
        grades = []
        for i in range(1, len(c), 6):
            if not re.search(r'EXAMINATION HOUR', c[i].text):
                grades.append(c[i].text + ' ' * (31 - len(c[i].text)) + ' ' + c[i + 4].text)
                if c[i].text not in grades_list and c[i + 4].text != ' ':
                    grades_list[c[i].text] = c[i + 4].text
                    p.push_app(c[i].text + ': ' + c[i + 4].text)
        grades = '\n'.join(grades)
        print(grades)
        print('Last refreshed:', time.strftime('%d%b at %H:%M'))

    except Exception as e:
        print('------------------------------------------------------------------------\n'
              'There was an error. Here\'s the exception\n', str(e))
        with open('ErrorLog.txt', 'a') as file:
            print(time.strftime('%d%b at %H:%M:%S'), '\n', str(e), '\n--------\n', file=file)


def run():
    browser = browser_init()
    browser_login(browser)
    if not testing:
        sleeptime = 600  # seconds
    else:
        sleeptime = 30

    UpdateGrades(browser)
    GPAref = UpdateGPA(browser, '0')

    time.sleep(sleeptime)

    while True:
        UpdateGrades(browser)
        GPAref = UpdateGPA(browser, GPAref)

        time.sleep(sleeptime)


run()
