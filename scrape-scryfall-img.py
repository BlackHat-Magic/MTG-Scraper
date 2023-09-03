from models import Artist, Work, engine
from sqlalchemy.orm import sessionmaker, joinedload
from concurrent.futures import ThreadPoolExecutor
import requests, json, time

# initialize database
Session = sessionmaker(bind=engine)
session = Session()

# load bulk data from scryfall
with open("./json/unique-artwork.json") as f:
    data = json.load(f)

# loop through data
for i, card in enumerate(data):
    # query artist in existing aomtg database
    card_artist_name = card.get("artist", "unknown")
    card_artist = session.query(Artist).filter(
        Artist.name.contains(card_artist_name)
    ).first()
    #if artist not in database, create new entry
    if(not card_artist):
        print(f"artist {card_artist_name} not in database; adding...")
        card_artist = Artist(
            name=card_artist_name
        )
        session.add(card_artist)
    
    # query card in existing aomtg database
    card_name = card.get("name", f"unknown-{i}")
    card_in_database = session.query(Work).join(Artist).filter(Artist.name==card_artist.name, Work.name.contains(card_name)).options(joinedload(Work.artist)).first()
    # if card is in database, add scryfall art image urls to database
    if(card_in_database):
        card_in_database.scryfall_urls = card.get("image_uris", {})
        continue
    # else, create new entry in database
    print(f"card {card_name} not in database; adding...")
    card_in_database = Work(
        name=card_name,
        set_=card.get("set_name", None),
        scryfall_urls=card.get("image_uris", []),
        artist = card_artist,
        on_aomtg=False
    )
    session.add(card_in_database)

session.commit()

# loop through all cards not on aomtg
def downloadImage(work):
    # make names filesystem friendly
    artist_name = work.artist.name.replace(' ', '-').replace('/', '_')
    card_name = work.name.replace(' ', '-').replace('/', '_')
    card_set = work.set_.replace(' ', '-').replace('/', '_')
    print(f"Image {card_name} by {artist_name} from set {card_set} submitted...")

    # retrieve image from scryfall
    image_url = work.scryfall_urls.get("art_crop", "")
    if(not(image_url)):
        print(f"Image {card_name} by {artist_name} from set {card_set} does not have art_crop image url; skipping...")
        return
    try:
        response = requests.get(image_url)
    except:
        print(f"Image {card_name} by {artist_name} from set {card_set} failed GET request; skipping...")
        return
    if(response.status_code != 200):
        print(f"Image {card_name} by {artist_name} from set {card_set} returned response code {response.status_code}; skipping...")
        return
    image_data = response.content

    # write image data to file
    with open(f"images/{artist_name}--{card_name}--{card_set}.png", "wb") as png:
        png.write(image_data)

works = session.query(Work).filter(Work.on_aomtg==False).all()
with ThreadPoolExecutor(max_workers=16) as executor:
    for i, work in enumerate(works):
        executor.submit(downloadImage, work)
        time.sleep(0.110)