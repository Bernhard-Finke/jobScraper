import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import csv

from time import sleep


class JobListing:
    def __init__(self, job_title, company, location, link, description):
        self.job_title = job_title
        self.company = company
        self.location = location
        self.link = link
        self.description = description

    def __eq__(self, other):
        return self.job_title == other.job_title and self.company == other.company

    def __hash__(self):
        return hash((self.job_title, self.company))

    def __str__(self):
        return "Job: " + self.job_title + " at " + self.company + "\nLocation: " + self.location

    def to_array(self):
        return [self.job_title, self.company, self.location, self.link, self.description]
        #pd.DataFrame({"Job Title": self.job_title, "Company": self.company, "Location": self.location,
                             #"Salary": self.salary, "Link": self.link, "Job Description": self.description}, index=[0])


def process_job(driver, postings, current_link, site_key):
    driver.get(current_link)

    if site_key == 'Glassdoor':
        title = driver.find_element(By.XPATH, "//div[@class='css-17x2pwl e11nt52q6']").text
        location = driver.find_elements(By.XPATH, "//div[@class='css-1v5elnn e11nt52q2']")[0].text
        employer = driver.find_element(By.XPATH, "//div[@class='css-16nw49e e11nt52q1']").text.partition('\n')[0]
        job_desc = driver.find_element(By.XPATH, "//*[starts-with(@id,'JobDesc1')]").text
    elif site_key == 'Indeed':
        site_title = driver.title.split('-')
        title = site_title[0].strip()
        location = site_title[1].strip()
        employer = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute("content")
        job_desc = driver.find_element(By.XPATH, "//div[@id='jobDescriptionText']").text
    elif site_key == 'Guardian':
        description = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
        description_split = re.split('in|with|\.', description)
        title = description_split[0].strip()
        location = description_split[1].strip()
        employer = description_split[2].strip().title()
        job_desc = driver.find_element(By.XPATH, "//div[@class='mds-edited-text mds-font-body-copy-bulk']").text
    else:
        raise KeyError

    current_job = JobListing(title, employer, location, current_link, job_desc)
    print(current_job)
    if current_job not in postings:
        postings.append(current_job)
    else:
        print("Already in dataframe")
    return postings

def main():
    area = "London, England (UK)"
    job = "Air Traffic Controller Jobs"

    if "UK" in area:
        code = "uk"
    elif "Germany" in area:
        code = "de"
    elif "Netherlands" in area:
        code = "nl"
    else:
        raise Exception


    try:
        with open('Job Postings.csv') as csv_file:
            csv_reader = csv.reader(csv_file)
            job_postings = []
            for row in csv_reader:
                job_postings.append(JobListing(row[0], row[1], row[2], row[3], row[4]))
    except FileNotFoundError:
        job_postings = []

    job_sites_dict = {'Glassdoor': ['https://www.glassdoor.com/Job', 'sc.location', 'sc.keyword'],
                      'Indeed': ['https://{}.indeed.com'.format(code), 'text-input-where', 'text-input-what'],
                      'Guardian': ['https://jobs.theguardian.com/', 'location', 'keywords']}

    browser = webdriver.Edge()
    browser.maximize_window()

    for current_key in job_sites_dict.keys():

        if current_key == 'Guardian':
            if code != "uk":
                continue
            else:
                area = area.split(',')[0]
                if area == "London":
                    area = "London (Greater)"
        browser.get(job_sites_dict.get(current_key)[0])

        location_bar = browser.find_element(By.ID, job_sites_dict.get(current_key)[1])
        location_bar.clear()
        location_bar.send_keys(area)
        search_bar = browser.find_element(By.ID, job_sites_dict.get(current_key)[2])
        search_bar.clear()
        search_bar.send_keys(job)
        sleep(2)
        search_bar.send_keys(Keys.DOWN)
        search_bar.send_keys(Keys.ENTER)
        sleep(2)


        if current_key == 'Glassdoor':
            elem = browser.find_element(By.ID, "JobSearch")
            html = elem.get_attribute('innerHTML')
            job_links = re.findall(r'https:\/\/www\.glassdoor.*/job-l.*?(?=")', html)
        elif current_key == 'Indeed':
            link_ends = re.findall(r'/rc/clk.*?(?=&)', browser.page_source)
            job_links = []
            [job_links.append(job_sites_dict.get(current_key)[0] + end + "&from=serp&vjs=3") for end in link_ends]
        elif current_key == 'Guardian':
            link_ends = set(re.findall(r'/job/\d*/[\w-]*/', browser.page_source))
            job_links = []
            [job_links.append('https://jobs.theguardian.com' + end) for end in link_ends]
        else:
            raise KeyError
        for link in job_links[0:1]:
            job_postings = process_job(driver=browser, postings=job_postings, current_link=link, site_key=current_key)

    browser.close()
    print(job_postings)
    with open('Job Postings.csv', 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        [csv_writer.writerow(row.to_array()) for row in job_postings]

if __name__ == '__main__':
    main()