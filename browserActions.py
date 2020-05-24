import re
import os
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def waitPageChange(browser):
    current_url = browser.current_url
    WebDriverWait(browser, 600).until(EC.url_changes(current_url))


def browserInit(visible=False):
    options = Options()
    if not visible:
        options.add_argument('-headless')

    browser = webdriver.Firefox(executable_path=os.getcwd() + '/geckodriver', options=options)
    return browser


def browserLogin(browser, netID, password):
    browser.get('http://albert.nyu.edu')
    print('Browser started and at Albert...')
    browser.find_element_by_link_text('Sign in to Albert').click()  # Clicks the login thing

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
        # browser.set_window_size(500, 710)  # Standardized window size to click the buttons in
        time.sleep(0.5)

        action = ActionChains(browser)  # Security features don't allow selenium to click things with precision
        action.move_by_offset(200, 430).click()  # Remember me for 1 day
        # action.move_by_offset(100, 630).click()  # Remember me for 1 day
        action.pause(.1)
        action.move_by_offset(0, -180).click()  # Send Me a Push
        action.pause(.1)
        action.move_by_offset(-200, -250).perform()  # Reset mouse position
        # action.move_by_offset(-100, -500).perform()  # Reset mouse position

        print('Requesting MFA...')
        waitPageChange(browser)
        browser.set_window_size(size['width'], size['height'])
        print('MFA successful...')
        print('\nNext MFA request will be approximately',
              time.strftime('%d%b at %H:%M', time.gmtime(time.time() + (28 * 3600))), 'EST\n')


def updateGPA(browser, GPAref, pushBool, p):
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


def updateGrades(browser, pushBool, grades_list, p):
    global unreleased_classes
    global maxClassNameLen
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
            fdsaf = gradeTable[i].text
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