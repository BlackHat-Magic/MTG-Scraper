from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Artist, Work, engine
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
import os, requests

artists = []
urls = []

Session = sessionmaker(bind=engine)
session = Session()

def get_artists():
    # download and parse the page of links to MTG Artists
    response = requests.get(url="https://www.artofmtg.com/mtg-artists/")
    list_page = BeautifulSoup(response.content, "html.parser")

    # Loop through and add an array containing [artist_name, artist_url] to artists set
    for li in list_page.find(class_="wp-tag-cloud").find_all("li"):
        a_tag = li.find("a")
        artists.append({"name": a_tag.text, "url": a_tag.get("href", None)})

# get artist names & urls
get_artists()

def loop_artists(artists):
    with ThreadPoolExecutor(max_workers=16) as executor:
        tfutures = []
        futures = []
        for artist in artists:
            # initialize an artist object in database w/ name & url
            new_artist = Artist(
                name=artist["name"],
                aomtg_url=artist["url"]
            )
            session.add(new_artist)

            # submit that to loop through their images
            tfutures.append((executor.submit(loop_images, new_artist), new_artist))
        
        for future, artist in tfutures:
            art_urls = future.result()

            for url in art_urls:
                futures.append(executor.submit(download_image, url, artist))
        
        for future in as_completed(futures):
            future.result()

def loop_images(artist):
    # get input artist's portfolio page
    response = requests.get(url=artist.aomtg_url)
    artist_page = BeautifulSoup(response.content, "html.parser")
    print(f"accessing {artist.name}'s art; status code: {response.status_code}")

    # empty set of urls of their works
    urls = set()

    # loop through their works and add the url to the set
    for thumbnail_container in artist_page.find(id="portfolio").find_all(class_="elastic-portfolio-item"):
        link_tag = thumbnail_container.find("div", class_="work-item").find("div", class_="work-info").find("a")
        link = link_tag.get("href", None)
        urls.add(link)
    
    # submit each work url for download
    return(urls)

def download_image(url, artist):
    print(f"downloading {url}")
    # download and parse artwork page
    page = BeautifulSoup(requests.get(url=url).content, "html.parser")

    # find the image
    image_element = page.find("img", class_="attachment-full")

    # get the image url and download
    image_url = image_element.get("data-src")
    image = requests.get(url=image_url).content

    # card info is in img tag metadata; extract it
    title = page.find("title")
    card_name = title.text.split(" MtG Art from ")[0]
    card_set = title.text.split(" MtG Art from ")[1].split(f" by {artist.name}")[0]

    # write image to disk
    with open(f"images/{artist.name.replace(' ', '-').replace('/', '_')}--{card_name.replace(' ', '-').replace('/', '_')}--{card_set.replace(' ', '-').replace('/', '_')}.png", "wb") as f:
        f.write(image)
    
    # add image to database
    new_work = Work(
        name=card_name,
        set_=card_set,
        aomtg_url=image_url,
        artist=artist,
        on_aomtg=True
    )
    session.add(new_work)

loop_artists(artists)
session.commit()