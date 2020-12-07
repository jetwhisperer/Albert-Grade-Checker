# Albert Grade Checker

Starts up a headless browser that logs in and checks your grades. Refreshes every 10 minutes because there is a 20 minute timeout. 

**Requirements**

    Most recent version of Firefox
    Python 3:    
        selenium
        yaml (optional, for storing your netID)
        pushed (optional, for mobile notifications)

**How to Run**
- Clone the project with `git clone https://github.com/jetwhisperer/Albert-Grade-Checker.git` 
- Navigate to the directory and run `pip install -r requirements.txt`
- (Optional) Create a file called creds.yaml. Follow the example and input your netID so you don't have to type it every time.
- If you want, you can create an account on Pushed and put the APP_KEY and APP_SECRET in creds.yaml and the script will push a notification to your phone when a new grade is added.
- Run `python3 gpa_main.py`

**License**

GNU Public License v3. Feel free to use this however you want, but it must be open-sourced if you fork it.
