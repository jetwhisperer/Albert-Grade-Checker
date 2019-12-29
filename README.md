# Albert Grade Checker

Starts up a headless browser that logs in and checks your grades. Refreshes every 10 minutes because there is a 20 minute timeout. 

**Requirements**

    selenium
    Most recent version of Firefox
    yaml (optional, for storing your credentials)
    pushed (optional, for mobile notifications)

**How to Run**
- Clone the project with `git clone https://github.com/jetwhisperer/Albert-Grade-Checker.git` 
- (Optional) Create a file called creds.yaml. Follow the example and input your netID and password. This doesn't steal your password but if you don't want to put your netID or password in the file in plaintext, feel free to leave it blank and it will ask for your password when you run the script. (It's possible to encrypt it but any way to decrypt it can be easily reproduced by an attacker unless each user created their own master key or salt for the encryption and had it stored somewhere it can't be found.) 
- If you want, you can create an account on Pushed and put the APP_KEY and APP_SECRET in creds.yaml and the script will push a notification to your phone when a new grade is added.
- Run `python3 gpa_main.py`

**License**

GNU Public License v3. Feel free to use this however you want, but it must be open-sourced if you fork it.
