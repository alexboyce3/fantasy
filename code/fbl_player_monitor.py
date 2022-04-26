from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from unidecode import unidecode

# import player list
players = pd.read_excel('player_names.xlsx', sheet_name = 'AllPlayers')
tmp = players[(players.owner == 'Boyce') | (players.watch == 1)]
player_df = pd.DataFrame(pd.concat([tmp['mlb_name'],
                                   tmp['cbs_name'],
                                   tmp['fg_name'],
                                   tmp['yahoo_name']]).drop_duplicates().dropna())
player_df['player_name'] = player_df[0].str.lower()
player_df['player_name'] = player_df['player_name'].str.replace(' ', '-')
player_df['of_interest'] = 1
player_df.set_index(0, inplace=True)
player_df.index.name = None
player_df.head()


# cbs scrape
cbs = pd.DataFrame()
counter = 1
while counter <= 5:
    link_stem = 'https://www.cbssports.com/fantasy/baseball/players/news/all/both'
    if counter > 1:
        link = link_stem + "/" + str(counter)
    else:
        link = link_stem

    html = requests.get(link)
    soup = BeautifulSoup(html.content, 'html.parser') #convert to BS

    links = soup.findAll('a', attrs={'href': re.compile("^/fantasy/baseball/[a-z]")})
    for x in range(len(links)):
        link_text = links[x].get('href')
        if re.compile('^/fantasy/baseball/players/[0-9]').search(link_text):
            tmp = pd.DataFrame(['https://www.cbssports.com' + link_text,links[x+1].text]).T
            cbs = cbs.append(tmp)

    counter += 1
    
cbs.rename(columns={0: 'link', 1: 'text'}, inplace=True)
cbs['player_name'] = cbs.link.str.split('/')
cbs['player_name'] = cbs.player_name.str[-2]
cbs.drop_duplicates(inplace=True)


# fantasy pros scrape
fp = pd.DataFrame()
counter = 1
while counter <= 5:
    link_stem = 'https://www.fantasypros.com/mlb/player-news.php'
    if counter > 1:
        link = link_stem + "?page=" + str(counter)
    else:
        link = link_stem

    html = requests.get(link)
    soup = BeautifulSoup(html.content, 'html.parser') #convert to BS

    links = soup.findAll('a', attrs={'href': re.compile("^/mlb/news/[0-9]")})
    for x in range(len(links)):
        link_text = links[x].get('href')
        tmp = pd.DataFrame(['https://www.fantasypros.com' + link_text, links[x].text]).T
        fp = fp.append(tmp)

    counter += 1
    
fp.rename(columns={0: 'link', 1: 'text'}, inplace=True)
fp.drop_duplicates(subset='link', inplace=True)
tmp = fp.text.str.split(' ')
fp['player_name'] = (tmp.str[0] + "-" + tmp.str[1]).str.lower()


# rotoballer scrape
rb = pd.DataFrame()
counter = 1
while counter <= 5:
    link_stem = 'https://www.rotoballer.com/player-news?sport=mlb'
    if counter > 1:
        link = "https://www.rotoballer.com/player-news/page/{}?sport=mlb".format(str(counter))
    else:
        link = link_stem

    html = requests.get(link)
    soup = BeautifulSoup(html.content, 'html.parser') #convert to BS

    links = soup.findAll('a', attrs={'href': re.compile("^https://www.rotoballer.com/player-news/[a-z]"),
                                     'rel': 'bookmark'})
    for x in range(len(links)):
        link_text = links[x].get('href')
        tmp = pd.DataFrame([link_text, links[x].text]).T
        rb = rb.append(tmp)

    counter += 1
    
rb.rename(columns={0: 'link', 1: 'text'}, inplace=True)
rb.drop_duplicates(subset='link', inplace=True)
tmp = rb.link.str.replace('https://www.rotoballer.com/player-news/','').str.split('-')
rb['player_name'] = (tmp.str[0] + "-" + tmp.str[1]).str.lower()


# combine everything
combined = pd.concat([cbs, fp, rb])
combined = combined.applymap(unidecode).reset_index()
combined = combined.merge(player_df, on='player_name', how='left').drop(columns='index')


# latest news
prev = pd.read_csv('all_player_news.csv', index_col=0)
prev['previous'] = 1
prev = prev[['link', 'previous']]


# new news
new = combined.merge(prev, on='link', how='left')
new = new[new.previous != 1]
len(new)


# new of interest
new[(new.of_interest == 1) & (new.text.str.len() > 20)].sort_values(by='player_name')


# all new
pd.set_option('display.max_rows', 100)
new


# export all new
everything = pd.concat([pd.read_csv('all_player_news.csv', index_col=0), new.drop(columns='previous')])
everything.reset_index(inplace=True, drop=True)
everything.drop_duplicates()
assert len(new) + len(prev) == len(everything)
everything.to_csv('all_player_news.csv')