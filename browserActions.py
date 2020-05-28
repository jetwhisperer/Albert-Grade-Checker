import re
import os
import time
import getpass

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


if 'Testing' in cfg:
    testing = cfg['Testing']
else:
    testing = False

# Globals
grades_list = {}
unreleased_classes = []
maxClassNameLen = 0

print('Started', time.strftime('%d%b at %H:%M'))


if 'netID' not in cfg or not cfg['netID']:
    print('''Add netID to creds.yaml to remove the need to type this in every time.
    it will just ask for the password.
    Example:
    netID: abc123

    but for now,''')
    netID = input('netID?\n')
else:
    print('If this fails to login, ensure the netID/password in creds.yaml are correct.')
    netID = cfg['netID']

password = getpass.getpass()

if testing or 'APP_KEY' not in cfg or 'APP_SECRET' not in cfg or not cfg['APP_KEY'] or not cfg['APP_SECRET']:
    # If it's testing or if they're not there or blank, we'll print to the console
    print('Add Pushed APP_KEY and APP_SECRET to creds.yaml if you want to use Pushed for notifications')
    class TerminalPush:

        def push_app(self, st):
            print(st)


    p = TerminalPush()
else:
    import pushed

    p = pushed.Pushed(cfg['APP_KEY'], cfg['APP_SECRET'])


def waitPageChange(browser):
    current_url = browser.current_url
    WebDriverWait(browser, 600).until(EC.url_changes(current_url))


def browserInit(visible=False):
    options = Options()
    if not visible:
        options.add_argument('-headless')

    browser = webdriver.Firefox(executable_path=os.getcwd() + '/geckodriver', options=options)
    return browser

def clickTheButtons(action, locs):
    currPos = [0, 0]
    for x, y in locs:
        action.move_by_offset(x - currPos[0], y - currPos[1]).click()
        action.pause(0.1)
        currPos = [x, y]
    action.move_by_offset(0 - currPos[0], 0 - currPos[1]).perform()


def browserLogin(browser):
    browser.get('http://albert.nyu.edu')
    print('Browser started and at Albert...')
    browser.find_element_by_link_text('Sign in to Albert').click()  # Clicks the login thing
    buttonLocs = [[78, 434], [245, 278]]

    if browser.find_elements_by_id('netid'):
        browser.find_element_by_id('netid').send_keys(netID)
        browser.find_element_by_id('password').send_keys(password)

        browser.find_element_by_name('_eventId_proceed').click()
        print('Browser logged in at', time.strftime('%H:%M, %d%b'), 'EST...')
    time.sleep(3)

    if 'shibboleth' in browser.current_url:
        browser.execute_script("""
        var element = arguments[0];
        element.parentNode.removeChild(element);
        """, browser.find_element_by_xpath('/html/body/div[1]'))
        size = browser.get_window_size()
        browser.set_window_size(500, 510)
        time.sleep(0.5)

        action = ActionChains(browser)  # Security features don't allow selenium to click things with precision
        clickTheButtons(action, buttonLocs)


        print('Requesting MFA...')
        waitPageChange(browser)
        browser.set_window_size(size['width'], size['height'])
        print('MFA successful...')
        print('\nNext MFA request will be approximately',
              time.strftime('%d%b at %H:%M', time.gmtime(time.time() + (28 * 3600))), 'EST\n')


def updateGPA(browser, GPAref, pushBool):
    a = browser.find_elements_by_xpath('//h2')

    if not a:
        browser.get(
            'https://sis.portal.nyu.edu/psp/ihprod/EMPLOYEE/EMPL/h/?tab=IS_SSS_TAB&jsconfig=IS_ED_SSS_GRADESLnk')
        a = browser.find_elements_by_xpath('//h2')

    for i in a:
        b = re.search(r'\d\.\d{3}', i.text)
        if b:
            b = b[0]
            if b != GPAref:  # This is ugly but there's no name for it and the xpath index varied between 0 and 13...
                if pushBool:
                    p.push_app('New GPA: ' + str(b))
                GPAref = b
                print('Your GPA is', GPAref)
            break
    return GPAref


def updateGrades(browser, pushBool):
    global unreleased_classes
    global maxClassNameLen
    global netID
    global password
    browser.get(
        'https://sis.portal.nyu.edu/psp/ihprod/EMPLOYEE/EMPL/h/?tab=IS_SSS_TAB&jsconfig=IS_ED_SSS_GRADESLnk')
    time.sleep(1)

    if 'shibboleth' in browser.current_url:
        browserLogin(browser)
        browser.get(
            'https://sis.portal.nyu.edu/psp/ihprod/EMPLOYEE/EMPL/h/?tab=IS_SSS_TAB&jsconfig=IS_ED_SSS_GRADESLnk')

    WebDriverWait(browser, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#IS_ED_SSS_GRADESLnk > span")))
    time.sleep(3)

    latest_next_sem = browser.find_elements_by_xpath('//div[4]/div/h4')
    currMo = time.strftime('%b')
    if len(latest_next_sem) == 1:  # Either a Fall Grad or it's the Spring Semester, not Senior Year.
        if currMo == 'Dec' or currMo == 'Jan':
            gradeTable = browser.find_elements_by_xpath('//div[4]/div[1]/table/tbody/tr/td')  # Fall Grad
        else:
            gradeTable = browser.find_elements_by_xpath('//div[5]/div[1]/table/tbody/tr/td')  # Spring Semester
    else:
        if currMo == 'May' or currMo == 'Jun':
            gradeTable = browser.find_elements_by_xpath('//div[4]/div[1]/table/tbody/tr/td')  # Senior Spring Grades
        else:
            gradeTable = browser.find_elements_by_xpath('//div[4]/div[2]/table/tbody/tr/td')  # Fall Grades

    # print('\n\n\n')
    grades = []

    if not pushBool:
        maxClassNameLen = max([len(gradeTable[i].text) for i in range(1, len(gradeTable), 6)])
        unreleased_classes = [i for i in range(1, len(gradeTable), 6)]

    ind = 0
    while ind < len(unreleased_classes):
        i = unreleased_classes[ind]

        if not re.search(r'EXAMINATION HOUR', gradeTable[i].text):
            grades.append(gradeTable[i].text + ' ' * (maxClassNameLen + 1 - len(gradeTable[i].text)) + gradeTable[i + 4].text)

            if gradeTable[i].text not in grades_list and gradeTable[i + 4].text != ' ':
                grades_list[gradeTable[i].text] = gradeTable[i + 4].text
                unreleased_classes.pop(ind)

                if pushBool:
                    p.push_app(gradeTable[i].text + ': ' + gradeTable[i + 4].text)
            else:
                ind += 1
        else:
            unreleased_classes.pop(ind)

    grades = '\n'.join(grades)
    print('\rLast refreshed:', time.strftime('%d%b at %H:%M'), '               ', end='')
    return grades
