from concurrent.futures import ThreadPoolExecutor, as_completed
from models import Artist, Work, engine
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import time, os, requests

Session = sessionmaker(bind=engine)
session = Session()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}

def scrape(work, subreddit):
    # search subreddit
    # print(f"[ STATUS ] .. Searching for {work.name} by {work.artist.name} on r/{subreddit}...")
    query = f"{work.name.replace(' ', '+')}+by+{work.artist.name.replace(' ', '+')}"
    try:
        time.sleep(0.100)
        response = requests.get(
            f"https://old.reddit.com/r/{subreddit}/search",
            headers = headers,
            params = {
                "q": query,
                "restrict_sr": "on",
                "include_over_18": "on",
                "sort": "relevance",
                "t": "all"
            }
        )
    except Exception as e:
        print(f"searching r/{subreddit} for \"{work.name} by {work.artist.name}\" resulted in error {e}; skipping...")
        return
    if(response.status_code != 200):
        print(f"[ ERROR {response.status_code} ] searching r/{subreddit} for \"{work.name} by {work.artist.name}\" returned code {response.status_code}; skipping...")
        return
    search_page = BeautifulSoup(response.content, "lxml")
    
    # get results
    result_container = search_page.find(class_="search-result-listing")
    result = result_container.find(class_="search-title")
    if(not result):
        # print(f"[ NOT FOUND ] searching r/{subreddit} for \"{work.name} by {work.artist.name}\" yielded no results; skipping...")
        return
    if(not work.name in result.text):
        # print(f"[ NOT FOUND ] searching r/{subreddit} for \"{work.name} by {work.artist.name}\" yielded no matching results; skipping...")
        return
    
    # navigate to image page
    try:
        time.sleep(0.100)
        response = requests.get(
            result["href"],
            headers = headers
        )
    except Exception as e:
        print(f"[ ERROR ] ... accessing {result['href']} for {work.name} by {work.artist.name} resulted in error {e}; skipping...")
        return
    if(response.status_code != 200):
        print(f"[ ERROR {response.status_code} ] accessing {result['href']} for {work.name} by {work.artist.name} returned code {response.status_code}; skipping...")
        return
    image_page = BeautifulSoup(response.content, "lxml")
    
    # get image
    image_link = image_page.select("a.may-blank.post-link")[0]
    image_url = image_link["href"]
    if(work.reddit_urls and image_url in work.reddit_urls):
        print(f"[ DISCARDED ] {work.name} by {work.artist.name} already downloaded from {image_url}; skipping...")
        return
    try:
        time.sleep(0.100)
        response = requests.get(
            image_url,
            headers = headers
        )
    except Exception as e:
        print(f"[ ERROR ] ... accessing image {image_url} for {work.name} by {work.artist.name} resulted in error {e}; skipping...")
        return
    image_data = Image.open(BytesIO(response.content))

    # update card urls
    if(work.reddit_urls == None or type(work.reddit_urls) != list):
        work.reddit_urls = []
    work.reddit_urls.append(image_url)

    # prepare filename stuff
    artist_name = work.artist.name.replace(" ", "-").replace("/", "_")
    work_name = work.name.replace(" ", "-").replace("/", "_")
    set_name = work.set_.replace(" ", "-").replace("/", "_")
    filename = f"{artist_name}--{work_name}--{set_name}.png"

    # check if image exists; if image does not exist or existing image is smaller, save; discard smaller image
    if(not os.path.exists(f"./images/{filename}")):
        print(f"[ STATUS ] .. New image for {work.name} by {work.artist.name}; saving...")
        image_file.save(f"./images/{filename}")
    else:
        local_image = Image.open(f"./images/{filename}")
        image_data_size = image_data.size[0] * image_data.size[1]
        local_image_size = local_image.size[0] * local_image.size[1]
        if(image_data_size > local_image_size):
            print(f"[ STATUS ] .. Larger image for {work.name} by {work.artist.name} from {image_url}; saving...")
            image_data.save(f"./images/{filename}")
        else:
            print(f"[ DISCARDED ] Smaller/equal image for {work.name} by {work.artist.name} from {image_url}; skipping...")
    
    session.commit()

subreddits = [
    "mtgporn",
    "ImaginaryArchers",
    "ImaginaryAssassins",
    "ImaginaryAstronauts",
    "ImaginaryKnights",
    "ImaginaryLovers",
    "ImaginaryMythology",
    "ImaginaryNobles",
    "ImaginaryScholars",
    "ImaginarySoldiers",
    "ImaginaryWarriors",
    "ImaginaryWitches",
    "ImaginaryWizards",
    "ImaginaryAngels",
    "ImaginaryDwarves",
    "ImaginaryElves",
    "ImaginaryFairies",
    "ImaginaryHumans",
    "ImaginaryImmortals",
    "ImaginaryMerfolk",
    "ImaginaryOrcs",
    "ImaginaryBattlefields",
    "ImaginaryCityscapes",
    "ImaginaryHellscapes",
    "ImaginaryMindscapes",
    "ImaginaryPathways",
    "ImaginarySeascapes",
    "ImaginarySkyscapes",
    "ImaginaryStarscapes",
    "ImaginaryWastelands",
    "ImaginaryWeather",
    "ImaginaryWildlands",
    "ImaginaryWorlds",
    "ImaginaryArchitecture",
    "ImaginaryCastles",
    "ImaginaryDwellings",
    "ImaginaryInteriors",
    "ImaginaryBeasts",
    "ImaginaryBehemoths",
    "ImaginaryCarnage",
    "ImaginaryDemons",
    "ImaginaryDragons",
    "ImaginaryElementals",
    "ImaginaryHorrors",
    "ImaginaryHybrids",
    "ImaginaryLeviathans",
    "ImaginaryMonsterGirls",
    "ImaginaryUndead",
    "ImaginaryWorldEaters",
    "ImaginaryArmor",
    "ImaginaryCybernetics",
    "ImaginaryCyberpunk",
    "ImaginaryFutureWar",
    "ImaginaryFuturism",
    "ImaginaryMechs",
    "ImaginaryPortals",
    "ImaginaryRobotics",
    "ImaginaryStarships",
    "ImaginarySteampunk",
    "ImaginaryVehicles",
    "ImaginaryWeaponry",
    "ImaginaryAww",
    "ImaginaryBestOf",
    "ImaginaryColorscapes",
    "ImaginaryFeels",
    "ImaginaryPets",
    "ImaginarySliceofLife",
    "ImaginaryTurtleWorlds",
    "AdorableDragons",
    "BadAssDragons",
    "BirdsForScale",
    "CharacterArt",
    "EpicMounts",
    "ReasonableFantasy",
    "SuperStructures",
    "SympatheticMonsters",
    "WholesomeFantasyArt"
]

work = works = session.query(Work).filter(Work.on_aomtg==False).all()

with ThreadPoolExecutor(max_workers=64) as executor:
    futures = []
    for work in works:
        for subreddit in subreddits:
            future = executor.submit(scrape, work, subreddit)
            futures.append(future)
            time.sleep(0.100)
    for future in as_completed(futures):
        result = future.result()
        print(result)