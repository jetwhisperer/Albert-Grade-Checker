from browserActions import *

def run():
    browser = browserInit(testing)
    browserLogin(browser)
    if not testing:
        sleeptime = 600  # seconds
    else:
        sleeptime = 600

    print("\n" + updateGrades(browser, False))  # Show the user their initial grades in case it changed
    GPAref = updateGPA(browser, '0', False)

    time.sleep(sleeptime)

    try:
        while True:
            try:
                updateGrades(browser, True)
                GPAref = updateGPA(browser, GPAref, True)

                time.sleep(sleeptime)

            except KeyboardInterrupt:
                print("Have a good day!\n")
                break

            except Exception as e:
                print('--------', 'There was an error. Here\'s the exception', str(e), sep='\n')
                with open('ErrorLog.txt', 'a') as file:
                    print(time.strftime('%d%b at %H:%M:%S'), '\n', str(e), file=file, sep='')
                    print('Current URL:', browser.current_url, file=file)
                    print('--------', file=file)

    finally:
        browser.close()


run()
