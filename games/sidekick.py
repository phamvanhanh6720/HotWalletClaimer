import os
import shutil
import sys
import time
import re
import json
import getpass
import random
import subprocess
from PIL import Image
from pyzbar.pyzbar import decode
import qrcode_terminal
import fcntl
from fcntl import flock, LOCK_EX, LOCK_UN, LOCK_NB
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, \
    ElementClickInterceptedException
from datetime import datetime, timedelta
from selenium.webdriver.chrome.service import Service as ChromeService

from claimer import Claimer


class SideKickClaimer(Claimer):

    def initialize_settings(self):
        super().initialize_settings()
        self.script = "games/sidekick.py"
        self.prefix = "SideKick:"
        self.url = "https://web.telegram.org/k/#@sidekick_fans_bot"
        self.pot_full = "Filled"
        self.pot_filling = "to fill"
        self.seed_phrase = None
        self.forceLocalProxy = False
        self.forceRequestUserAgent = False
        self.allow_early_claim = False
        self.start_app_xpath = "//button[span[contains(text(), 'Play')]]"

    def __init__(self):
        self.settings_file = "variables.txt"
        self.status_file_path = "status.txt"
        self.wallet_id = ""
        self.load_settings()
        self.random_offset = random.randint(self.settings['lowestClaimOffset'], self.settings['highestClaimOffset'])
        super().__init__()

    def next_steps(self):
        if self.step:
            pass
        else:
            self.step = "01"

        try:
            self.launch_iframe()
            self.increase_step()

            self.set_cookies()

        except TimeoutException:
            self.output(f"Step {self.step} - Failed to find or switch to the iframe within the timeout period.", 1)

        except Exception as e:
            self.output(f"Step {self.step} - An error occurred: {e}", 1)

    def full_claim(self):
        self.step = "100"

        self.launch_iframe()

        xpath = "//button[contains(text(), 'START')]"
        present = self.move_and_click(xpath, 20, True, "click the 'START' button", self.step, "clickable")
        self.increase_step()

        if present:
            xpath = "//button[contains(text(), 'Awesome!')]"
            next_button = self.move_and_click(xpath, 20, True, "click the 'Awesome!' button", self.step, "clickable")
            self.increase_step()

            xpath = "//button[contains(text(), 'CLAIM')]"
            next_button = self.move_and_click(xpath, 20, True, 'click the "CLAIM" button', self.step, "clickable")
            self.increase_step()

        self.get_balance(False)

        xpath = "//div[contains(text(), 'Pass')]/.."
        self.move_and_click(xpath, 20, True, "click on the 'Pass' page", self.step, "visible")
        self.increase_step()

        xpath = "(//div[contains(text(), 'GO')])[1]"
        self.move_and_click(xpath, 20, True, "click the 'GO' button on daily checkin task", self.step, "visible")
        self.increase_step()

        xpath = "//button[contains(text(), 'Claim')]"
        self.move_and_click(xpath, 20, True, "click the 'Claim' button", self.step, "clickable")
        self.increase_step()

        xpath = "//button[contains(text(), 'See you tomorrow')]"
        success = self.move_and_click(xpath, 20, False, "check for claim success", self.step, "visible")
        self.increase_step()

        # self.get_balance(False)

        wait_time_minutes = self.get_wait_time(self.step, "pre-claim") + self.random_offset

        if not success:
            return 60
        else:
            return wait_time_minutes

    def get_balance(self, claimed=False, retries=5):
        prefix = "After" if claimed else "Before"
        default_priority = 2 if claimed else 1

        priority = min(self.settings['verboseLevel'], default_priority)

        balance_text = f'{prefix} BALANCE:' if claimed else f'{prefix} BALANCE:'
        balance_xpath = f"//div[contains(text(), 'DIAMONDS')]/../span"

        for try_th in range(retries):
            try:
                balance_element = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, balance_xpath))
                )

                if balance_element:
                    balance_value = balance_element.text
                    if balance_value != '0':
                        self.output(f"Step {self.step} - {balance_text} {balance_value}", priority)
                        break
                    else:
                        self.output(f"Step {self.step} - Try to get {balance_text} {try_th+1}th", priority)
                        time.sleep(5)

            except NoSuchElementException:
                self.output(f"Step {self.step} - Element containing '{prefix} Balance:' was not found.", priority)
            except Exception as e:
                self.output(f"Step {self.step} - An error occurred: {str(e)}", priority)

        self.increase_step()

    def get_wait_time(self, step_number="108", beforeAfter="pre-claim", max_attempts=1):
        current_time_utc = datetime.now(timezone.utc)
        next_day_start = (current_time_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_to_next_day = int((next_day_start - current_time_utc).total_seconds() / 60)

        return time_to_next_day


def main():
    claimer = SideKickClaimer()
    claimer.run()


if __name__ == "__main__":
    main()
