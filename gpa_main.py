import getpass

from browserActions import *

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


def run():
    browser = browserInit(testing)
    browserLogin(browser, netID, password)
    if not testing:
        sleeptime = 600  # seconds
    else:
        sleeptime = 600

    print("\n" + updateGrades(browser, False, grades_list, p))  # Show the user their initial grades in case it changed
    GPAref = updateGPA(browser, '0', False, p)

    time.sleep(sleeptime)

    try:
        while True:
            try:
                updateGrades(browser, True, grades_list, p)
                GPAref = updateGPA(browser, GPAref, True, p)

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
