# import packages #
from nordvpn_switcher import initialize_VPN,rotate_VPN,terminate_VPN
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import random
import time
import json
import re

#start VPN rotation#
initialize_VPN(save=1)

###########################
######write functions######
###########################

def scrape_profiles(users,definition_user,start_from = None,end_on = None):
    profiles = ["https://letterboxd.com" + user for user in users]
    VPN_reset = 0

    if start_from is None:
        start_from = 0
    if end_on is None:
        end_on = len(profiles) + 1

    profiles = profiles[start_from:end_on]

    for p,profile in enumerate(profiles):
        keys = ['profile','film','film id','rating','love']
        user_watched = {key: [] for key in keys}
        user_watched['profile'] = profile
        print("Scraping profile #"+ str(p+1)+"\n"
              "-------------------------------\n")
        for page in range(1,400):
            try:
                openpage = requests.get(profile+"films/page/"+str(page))
            except:
                break
            else:
                loadpage = bs(openpage.text, "html.parser")
                films_page = loadpage.find_all('li', {"class":"poster-container"})
                if len(films_page) > 0:
                    print("page " + str(page) + " loaded.")
                    for film in films_page:
                            div_obj = film.find('div')
                            user_watched['film'].append(div_obj.get("data-film-slug"))
                            user_watched['film id'].append(div_obj.get("data-film-id"))
                            try:
                                 rating = film.select('span[class*="rating"]')[0].get_text()
                            except:
                                 rating = "NA"

                            finally:
                                user_watched['rating'].append(rating)

                            try:
                                love = film.select('span[class*="icon-liked"]')[0]
                            except:
                                love = "No"
                            else:
                                love = "Yes"
                            finally:
                                user_watched['love'].append(love)
                    time.sleep(random.uniform(1,2))
                else:
                    print("Done!\n\n")
                    break

        name_file = "users/user" + "_" + str(definition_user) + "_" + str(p+start_from+1) + ".csv"
        user_write = json.dumps(user_watched)
        f = open(name_file, "w")
        f.write(user_write)
        f.close()

        VPN_reset = VPN_reset + 1
        if VPN_reset == 50:
            VPN_reset = 0
            rotate_VPN()

#########################################
#[[1]] obtain profile links of top users#
#########################################

links = ["https://letterboxd.com/people/popular/this/all-time/page/" + str(i) for i in range(1,129)]

link_users_total = []
print("\nScraping links of top users' profiles...\n"
      "############################\n")
for i,link in enumerate(links):
    sleep_random = random.uniform(3,7)
    openpage = requests.get(link)
    print("\nPage "+ str(i+1) +" loaded!")
    loadpage = bs(openpage.text,"html.parser")
    users = loadpage.find_all("h3")

    for element in users:
        link_users = element.find("a").get('href')
        link_users_total.append(link_users)
    print("Users successfully added!\n"
          "----------------------------\n")

    time.sleep(sleep_random)

#save profile links to hard drive#
with open('users/link_letterboxd_profiles.txt', 'w') as f:
    for item in link_users_total:
        f.write("%s\n" % item)

##################
#scrape top users#
##################
with open('users/link_letterboxd_profiles.txt') as f:
    link_topusers_total = f.read().splitlines()

print("\nScraping profiles of top users...\n"
      "############################\n")
scrape_profiles(link_topusers_total,"top_users")

############################################
#[[2]] obtain profile links to random users#
############################################

#scrape links to popular movies#
popular_movies = ["https://letterboxd.com/dave/list/imdb-top-250/page/" + str(i) for i in range(1,4)]

link_popularmovies_total = []
print("\nScraping links to popular movies....\n"
      "############################\n")
for i,link in enumerate(popular_movies):
    sleep_random = random.uiniform(1,2)
    openpage = requests.get(link)
    print("\nPage "+ str(i+1) +" loaded!")
    loadpage = bs(openpage.text,"html.parser")
    ultags = loadpage.find_all("ul")

    for index,ul_tag in enumerate(ultags):
        if "data-film-slug" in str(ul_tag):
            tag_index = index

    for element in ultags[tag_index]:
        link_movies = [x.find('div')['data-film-slug'] for x in ultags[tag_index].find_all("li")]
        for movie in link_movies:
            link_popularmovies_total.append(movie)
    print("Popular movie links successfully added!\n"
          "----------------------------\n")
    time.sleep(sleep_random)
link_popularmovies_total = list(pd.Series(link_popularmovies_total).drop_duplicates())

#obtain links to random profiles that rated popular movies#
rating_pop_movies = ["https://letterboxd.com"+filmlink+"members/page/" for filmlink in link_popularmovies_total]
profiles_regular = []

print("\nScraping random profiles that rated popular movies....\n"
      "############################\n")
for index,pop_movie in enumerate(rating_pop_movies):
    moviename = re.search('film/(.+?)/members', pop_movie)[1].replace("-", " ")
    print("\n\033[1mSearch number "+str(index+1) + "\nMovie: " + moviename + "\033[0m")

    previous_length_profiles = len(profiles_regular)
    scraped_pages = []
    successful_pages = elapsed_time_min = 0
    start_time = time.time()

    while successful_pages < 30 and elapsed_time_min < 5:
        available_pages = set(range(200)) - set(scraped_pages)
        random_page = random.sample(available_pages,1)[0]
        time.sleep(random.uniform(1,2))
        openpage = requests.get(pop_movie+str(random_page))
        if openpage.status_code == 200:
            successful_pages += 1
            scraped_pages.append(random_page)
            loadpage = bs(openpage.text, "html.parser")

            rating_dummy = loadpage.find_all("tr")
            rating_dummy = ["rating rated" in str(x.find_all('td')[1]) for x in rating_dummy[1:]]
            rating_dummy = [i for i in range(len(rating_dummy)) if rating_dummy[i] is True]

            for pick in rating_dummy:
                profile = loadpage.find_all(class_="table-person")[pick].find('a').get('href')
                profiles_regular.append(profile)
        else:
            pass

        elapsed_time_min = (time.time() - start_time)/60
        if elapsed_time_min > 5:
            print("\nWasn't able to scrape 30 pages in 5 minutes, scraping the next movie...")
            break

    if successful_pages == 30:
        print("\nScraped " + str(len(profiles_regular) - previous_length_profiles) + " profiles " + "in " + str(round(elapsed_time_min,1)) + " minutes.")
        print("Scraped pages:"+str(scraped_pages))

print("\n# of profiles before deleting duplicates: "+str(len(profiles_regular))) #70562
profiles_regular = pd.Series(profiles_regular).drop_duplicates().reset_index()
print("\n# of profiles after deleting duplicates: "+str(len(profiles_regular))) #39093

#save profile links to hard drive#
print("\nWriting profiles to hard drive...")
with open('users/link_letterboxd_profiles_normal_users.txt', 'w') as f:
    for item in profiles_regular:
        f.write("%s\n" % item)

#####################
#scrape normal users#
#####################
with open('users\link_letterboxd_profiles_normal_users.txt') as f:
    link_normalusers_total = f.read().splitlines()

print("\nScraping profiles of random users...\n"
      "############################\n")
scrape_profiles(link_normalusers_total,"normal_users",start_from=3188,end_on=15000)