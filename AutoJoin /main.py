#!/user/bin/evn python
import re
from time import sleep, strptime, time
import time
import datetime
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from config import conf
from schedule import schedule_lessons
from lessons_urls import lessons_url
import logging
import os, os.path

if (not os.path.exists("reports/logs/")) or (not os.path.exists("reports/comments/")):
    os.makedirs("reports/logs/")
    os.makedirs("reports/comments/")
log_file_name = f"{datetime.datetime.today().strftime('%m-%d-%Y')}"
logging.basicConfig(filename=f'reports/logs/{log_file_name}.log', encoding='utf-8', level=logging.INFO,
                    format='%(asctime)s---%(levelname)s: %(message)s', datefmt='%I:%M:%S(%p)')

class LMS:
    """
       A class to attend and participate in your virtual classes at 'Adobe connect'
    Which will be present in all your virtual classes according to your class schedule
    And works in the classroom according to the settings you set for it (config.py).

    """
    def __init__(self, username, password, login_url, based_simulation_student=None,
                 preference_simulation_active_student='most_students'):
        """
        Constructs all the necessary attributes for the LMS object.

        Parameters
        ----------
            username : str
                for login your lms
            password : str
                for login your lms
            based_simulation_student : str
                way you choices for activity on class
            preference_simulation_active_student : str
                full name of student in Persian format(at first his lastname then firstname)
            path_webdriver : str
                address of webdriver
            login_url : str
                address of login page
        """
        self.username = username
        self.password = password
        self.preference_simulation_active_student = preference_simulation_active_student # most_students  or  another_student
        self.based_simulation_student = based_simulation_student
        self.path_webdriver = "./chromedriver"
        self.driver = webdriver.Chrome(self.path_webdriver)
        self.login_url = login_url
        self.lessons_url = lessons_url
        self.schedule_lessons = schedule_lessons
        self.comments = []

    @property
    def based_simulation_student(self):
        return self.__budget

    @based_simulation_student.setter
    def based_simulation_student(self, value=None):
        if self.preference_simulation_active_student != 'most_students':
            if value == None:
                raise Exception("This field is required")
        self.__budget = value

    def login(self):
        """
        Using username And password First take the login page and then
        send the two mentioned values and as a result log in
        """
        self.driver.get(self.login_url)
        self.driver.find_element_by_name("username").send_keys(self.username)
        self.driver.find_element_by_name("password").send_keys(self.password)
        self.driver.find_element_by_id("loginbtn").click()
        logging.info("you login")

    def logout(self):
        """
        Leaves open pages and closes
        """
        # self.driver.close()
        self.driver.quit()
        logging.info("You logout")

    @classmethod
    def get_results(cls,phrase):
        cls.driver.get("https://www.google.com")
        search_form = cls.driver.find_element_by_name('q')
        search_form.send_keys(phrase)
        search_form.submit()
        try:
            links = cls.driver.find_elements_by_xpath("//ol[@class='web_regular_results']//h3//a")
        except:
            links = cls.driver.find_elements_by_xpath("//h3//a")
        results = []
        for link in links:
            href = link.get_attribute("href")
            results.append(href)
            # self.driver.close()
            return results

    @classmethod
    def search_google(cls):
        cls.get_results("python")

    @staticmethod
    def what_time_is_it():
        """
        Returns hours, minutes and days of the week.

            Returns:
                    weekday (int): number of weekday ( 0 until 6 )
                    clock (str): clock with this format --:--
        """
        today = datetime.datetime.today()
        weekday = today.weekday()
        clock = "{0}:{1}".format(today.hour, today.minute)
        return weekday, clock

    def How_much_time_is_left(self, lesson_clock, clock):
        """
        Calculates how many seconds of class time are left.

            Parameters:
                    lesson_clock (str): clock with this format --:--
                    clock (str): clock with this format --:--

            Returns:
                    time_left.seconds (int): Remaining time of the class in units of seconds.
        """
        (h_now, m_now) = clock.split(':')
        (h_lesson, m_lesson) = lesson_clock.split(':')
        time_elapsed = datetime.timedelta(hours=int(h_now), minutes=int(m_now)) - datetime.timedelta(hours=int(h_lesson),minutes=int(m_lesson))
        print(time_elapsed)
        time_left = datetime.timedelta(hours=1, minutes=30) - datetime.timedelta(seconds=time_elapsed.seconds)
        print(time_left)
        if time_left.days < 0 and time_elapsed.days == 0:
            return f"The class ({lesson_clock}) is over"
        if time_elapsed.days < 0 and time_left.days < 0:
            wait_time = datetime.timedelta(seconds=time_left.seconds) - datetime.timedelta(hours=1, minutes=30)
            return f"The class ({lesson_clock}) has not started yet - The time left until the start of the class(seconds)-->{wait_time.seconds}"
        return time_left

    # def is_class_finished(self, time_left):
    #     """
    #     Checks ( given the remaining time of the class ) if the class is over or not
    #
    #         Parameters:
    #                 time_left (int): Remaining time of the class in units of seconds.
    #
    #         Returns:
    #                 True or False (bool): if the class is over return False else True.
    #     """
    #     if 0 <= time_left < 5400:
    #         return False
    #     else:
    #         return True

    def what_do_i_have_now(self):
        """
        Checks which class you should be attending now, based the date and time today and your class schedule.

            Returns:
                    lesson_url (str): url of the class that should be attending it.
                    time_left (int): Remaining time of the class in units of seconds.
        """
        weekday, clock = self.what_time_is_it()
        try:
            lessons_day = self.schedule_lessons[weekday]
        except KeyError:
            return "You do not have a class today - have fun"
        for lesson_clock in lessons_day.keys():
            time_left = self.How_much_time_is_left(lesson_clock, clock)
            if isinstance(time_left, str):
                logging.info(time_left)
                if 'yet' in time_left:
                    return time_left
                continue
                # return time_left
            # if not self.is_class_finished(time_left.seconds):
            logging.info(f"{time_left} left from class")
            lesson = lessons_day[lesson_clock]
            lesson_url = self.lessons_url[lesson]
            logging.info(f"Now you have {lesson} class")
            return {'lesson_url': lesson_url, 'time_left': time_left}
            # print("---------------")
        return "Today's classes are over"

    def join_class_with_browser(self, url):
        """
        Using url of the class attending it by browser

            Parameters:
                    url (str): url of the class that should be attending it.
        """
        try:
            self.driver.get(url)
            element = self.driver.find_element_by_name("btnname")
            window_before = self.driver.window_handles[0]
            element.click()
            window_after = self.driver.window_handles[1]
            self.driver.switch_to.window(window_after)

            button = self.driver.find_element_by_xpath(
                "//*[@id=\"launchOptionsDialog\"]/div[2]/coral-dialog-content/div[1]/div[1]")
            self.driver.implicitly_wait(15)
            ActionChains(self.driver).move_to_element(button).click(button).perform()
            logging.info("You join the class")
        except Exception as e:
            raise e

    def alike_most_students(self,num_LastMessages):
        """
        It is supposed to be based on the majority of people who were active (only their comments)
            + That this activity is limited to approval and disapproval with '+' and '-'

            Parameters:
                    num_LastMessages (int): number of the new messages.

            Returns:
                    1(True) or 0(False) (bool): if activity done return 1(True) or 0(False).
        """
        count = 0
        res = []
        for com in reversed(self.comments):
            if count > num_LastMessages:
                if len(res)<(num_LastMessages/2):
                    return 0
                self.comment('+') if sum(1 for m in res if m == '+') > (len(res) / 2) else self.comment('-')
                return 1
            if ':' in com:
                comment = com.split(":")
                content_comment = comment[1]
                match = re.search(r'\bYou\b', comment[0])
                if match:
                    return 0
                if ('+' in content_comment) or ('-' in content_comment):
                    res.append('+') if '+' in content_comment else res.append('-')
                count += 1

    def alike_another_student(self, num_LastMessages):
        """
        It is supposed to be based on the activity of a special student (only his comments)
        whose full name is entered by the user
            + If the student was not active according to the majority of people who were active ,we act
            + That this activity is limited to approval and disapproval with '+' and '-'

            Parameters:
                    num_LastMessages (int): number of the new messages.

            Returns:
                    1(True) or 0(False) (bool): if activity done return 1(True) or 0(False).
        """
        count = 0
        flag_1 = False
        flag_2 = True
        for com in reversed(self.comments):
            if count > num_LastMessages:
                if flag_1 and flag_2:
                    logging.info(f" has comment {self.based_simulation_student}")
                    if ('+' in content_comment) or ('-' in content_comment):
                        self.comment('+') if '+' in context_comment else self.comment('-')
                    else:
                        logging.info("his comment text")
                    return 1
                return 0
            if ':' in com:
                comment = com.split(":")
                student_name, content_comment = comment[0], comment[1]
                match_1 = re.search(rf'\b{self.based_simulation_student}\b', student_name)
                if match_1:
                    context_comment = content_comment
                    flag_1 = True
                match_2 = re.search(r'\bYou\b', comment[0])
                if match_2:
                    flag_2 = False
                    return 0
            count += 1

    def active_student(self, time):
        """
        We plan to not only attend class but also play the role of an active student to make it happen
         We have two ways (strategy) :
            (1) - Consider an active student in the class and according to his activity ,we do the same activity
            (2) - Consider the whole class and according to the majority of people ,we do the same activity
            --->( The user fits his class conditions each of ways Who he likes or deems fit, chooses )

            Parameters:
                    time (int): Remaining time of the class in units of seconds.
        """
        first_list = self.driver.find_element_by_id("chatContentArea")
        previous_list = len(first_list.text)
        # wait for new message...
        while (time > 30):
            new_list = self.driver.find_element_by_id("chatContentArea")
            num_new_message = len(new_list.text) - previous_list
            if num_new_message > 0:  # you have new message
                self.comments.clear()
                self.comments = new_list.text.split('\n')
                char_LastMessages = new_list.text[-( num_new_message ):]
                print(char_LastMessages)
                num_LastMessages = sum(1 for m in char_LastMessages if m == ':')
                if num_LastMessages > 2:
                    if self.preference_simulation_active_student == 'another_student':
                        if not self.alike_another_student(num_LastMessages):
                            self.alike_most_students(num_LastMessages)
                    else:
                        self.alike_most_students(num_LastMessages)
                # you can do whatever you want with your last messages
                previous_list = len(new_list.text)  # update length of ul
            time -= 15
            # wait 15 seconds
            sleep(10)


    def fix_page(self):
        """
        maximize window and switch to main frame for continue other functions
        and if there is a modal ,close it
        """
        self.driver.maximize_window()
        self.driver.switch_to.frame(self.driver.find_element_by_xpath("//*[@id=\"html-meeting-frame\"]"));
        try:
            modul_close_button = self.driver.find_element_by_xpath(
                "//*[@id=\"whats-new-dialog\"]/div[3]/button[1]")
            self.driver.implicitly_wait(10)
            ActionChains(self.driver).move_to_element(modul_close_button).click(modul_close_button).perform()
        except:
            pass
    def record_comments(self):
        all_comments = self.driver.find_element_by_id("chatContentArea")
        with open(f"reports/comments/comments-----({datetime.datetime.today().strftime('%m/%d/%Y--%I(%p)')})", 'a+') as file:
            file.write(all_comments.text)
            logging.info("record all comments successful.")

    def comment(self, message):
        """
        Get message and post it to chatTypingArea for submit a comment

            Parameters:
                    message (str): The text of the message that the user intends to record.
        """
        comment_element = self.driver.find_element_by_id("chatTypingArea")
        # comment_element.send_keys(message)
        logging.info(f"You comment ----> '{message}'")
        # comment_element.submit()

    def management(self):
        """
        All activities and functions Manages
        and start activities
        """
        self.login()
        while True:
            # print("pp")
            res = self.what_do_i_have_now()
            if isinstance(res, str):
                if res == "Today's classes are over" or res == "You do not have a class today - have fun":
                    print(res)
                    logging.info(res)
                    self.logout()
                    break
                else:
                    time = int(res.split('-->')[1])
                    sleep(time)
                    if time > 5400:
                        self.login()
                    continue
            try:
                self.join_class_with_browser(res['lesson_url'])
                sleep(20)
                self.fix_page()
                # self.comment("salam")
                self.active_student(res['time_left'].seconds)
            except Exception as e:
                logging.warning(e)
                raise e
            else:
                self.record_comments()
                break

            finally:
                self.logout()


if __name__ == '__main__':
    counter = 0
    while True:
        try:
            time1 = time.time()
            lms = LMS(username = conf['username'],
                      password = conf['password'],
                      login_url=conf['login_url'],
                      preference_simulation_active_student=conf['preference_simulation_active_student'],
                      based_simulation_student=conf['based_simulation_student'])

            lms.management()

        except:
            time2 = time.time()
            print("time2 = ",time2)
            print("time2 = ", time1)
            print("res = ", time2-time1)
            if time2-time1 < 4:
                counter += 1
                print("counter = ", counter)
            if counter > 10 :
                break
            continue
        else:
            break
