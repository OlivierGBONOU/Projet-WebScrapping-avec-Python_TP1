from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
from selenium import webdriver
import psycopg2
import logging
import json
import time
import re

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s: %(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def clean_data_dict(data, artist):
    def convert_count(value):
        value = str(value).strip()
        match = re.match(r'([\d,.]+)\s*([KMB])?', value)
        if not match:
            return value
        number = float(match.group(1).replace(',', '.'))
        multiplier = match.group(2) if match.group(2) else ''
        if multiplier == 'K':
            return int(number * 1000)
        elif multiplier == 'M':
            return int(number * 1000000)
        elif multiplier == 'B':
            return int(number * 1000000000)
        return int(number)
    
    def clean_title(title):
        escaped_artist = artist
        patterns_to_remove = [
            r'\(Official Music Video\)', r'"', r'\-', r'\(Official Visualiser\)',
            r'\(Official Music Audio\)', r'audio', r'\(Official Audio\)', r'\(Live\)',
            r'\(Visualizer\)', r'\(Official Video\)', r'\(Acoustic Session\)',
            r'\(Directors Cut\)', r'\(Dance Video\)', r'\(Dance Audio\)',
            r'Official', r'\( \)', r'\(\)', r'\[ \]', r'\[\]',
            r'\(Official Lyric Video\)', fr'\({escaped_artist}\)'
        ]
        cleaned_title = title
        for pattern in patterns_to_remove:
            cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)
        return ' '.join(cleaned_title.split())
    
    def convert_time_ago_to_date(published_since):
        current_date = datetime.now()
        current_year = current_date.year
        if not isinstance(published_since, str):
            return current_year
        matches = re.search(r'(\d+)\s*(year|month|day)s?\s*ago', published_since, flags=re.IGNORECASE)
        if matches:
            number = int(matches.group(1))
            unit = matches.group(2).lower()
            if unit == 'year':
                return current_year - number
            elif unit == 'month':
                publication_date = current_date - timedelta(days=30 * number)
                return publication_date.year
            elif unit == 'day':
                publication_date = current_date - timedelta(days=number)
                return publication_date.year
        year_match = re.search(r'(\d+)\s*ans?', published_since, flags=re.IGNORECASE)
        if year_match:
            return current_year - int(year_match.group(1))
        month_match = re.search(r'(\d+)\s*mois?', published_since, flags=re.IGNORECASE)
        if month_match:
            return (current_date - timedelta(days=30 * int(month_match.group(1)))).year
        day_match = re.search(r'(\d+)\s*jours?', published_since, flags=re.IGNORECASE)
        if day_match:
            return (current_date - timedelta(days=int(day_match.group(1)))).year
        hour_match = re.search(r"(\d+)\s*heures?", published_since, flags=re.IGNORECASE)
        if hour_match:
            return (current_date - timedelta(hours=int(hour_match.group(1)))).year
        return current_year
    
    cleaned_data = {
        'Nom': data['Nom'].strip(),
        'Photo': data['Photo'].strip(),
        'Photo Banniere': data['Photo Banniere'].strip(),
        'Nombre abonné': convert_count(data['Nombre abonné'].replace(' subscribers', '').replace(' abonnés', '')),
        'Nombre de vidéo': int(data['Nombre de vidéo'].replace(' videos', '').replace(' vidéos', '')),
        'Titre': [clean_title(title) for title in data['Titre']],
        'Lien': data['Lien'],
        'Video Image': data['Video Image'],
        'Vues': [convert_count(view.replace(' views', '').replace(' vues', '')) for view in data['Vues']],
        'Publié depuis': [convert_time_ago_to_date(date) for date in data['Publié depuis']]
    }
    
    return cleaned_data

def insert_data(data):
    conn = psycopg2.connect(dbname='db_youtube_scrapper', user='postgres', password='root', host='db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO videos (artist_name, artist_photo, banner_photo, subscribers_count, videos_count, title, link, video_image, views, posted_since)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (data['Nom'], data['Photo'], data['Photo Banniere'], data['Nombre abonné'], data['Nombre de vidéo'], data['Titre'], data['Lien'], data['Video Image'], data['Vues'], data['Publié depuis']))
    
    conn.commit()
    cursor.close()
    conn.close()

# Code
def scrape_youtube(artist):
    # Configurer les options du navigateur
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Assurer une taille d'écran consistante
    # Ajouter un user-agent moderne pour éviter les blocages
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Ajouter des préférences pour contourner les boîtes de dialogue
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"
    
    # Initialiser le driver avec un système de retry
    max_driver_attempts = 3
    driver = None
    for driver_attempt in range(max_driver_attempts):
        try:
            service = ChromeService(executable_path="/usr/local/bin/chromedriver")  # Chemin aligné avec le Dockerfile
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("WebDriver démarré avec succès.")
            break  # Si ça réussit, sortir de la boucle
        except Exception as e:
            logger.warning(f"Échec du lancement du WebDriver (tentative {driver_attempt + 1}/{max_driver_attempts}): {e}")
            if driver_attempt == max_driver_attempts - 1:
                logger.error("Impossible de lancer le WebDriver après plusieurs tentatives")
                raise  # Relancer l'exception pour que Celery gère l'échec
            time.sleep(5)  # Attendre avant de réessayer
            
    # Vérifier que driver a été initialisé avant de continuer
    if driver is None:
        raise RuntimeError("Le WebDriver n'a pas pu être initialisé.")
    
    wait = WebDriverWait(driver, 10)
    
    # Ouvrir YouTube et rechercher l'artiste
    driver.get("https://www.youtube.com/")
    print(f"Recherche de l'artiste : {artist}")

    search = wait.until(EC.element_to_be_clickable((By.NAME, 'search_query')))
    search_query = artist + ' Officiel'
    search.send_keys(search_query.upper())
    search.send_keys(Keys.RETURN)

    time.sleep(3)
    
    # Fonction pour attendre qu'un élément soit visible et accessible
    def wait_for_element(selector, by=By.CSS_SELECTOR, timeout=20, retries=3):
        for attempt in range(retries):
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.visibility_of_element_located((by, selector))
                )
                # Vérifier que l'élément est aussi interactif
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((by, selector))
                )
                return element
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Élément non trouvé après {retries} tentatives: {selector}")
                    raise
                logger.warning(f"Tentative {attempt+1}/{retries} échouée pour l'élément {selector}: {e}")
                time.sleep(2)  # Attendre avant de réessayer
    
    # Fonction pour faire défiler lentement afin d'assurer le chargement des éléments
    def scroll_slowly(pixels=300, pause=0.5, max_scrolls=10):
        """Fait défiler la page lentement pour charger le contenu progressivement"""
        for _ in range(max_scrolls):
            driver.execute_script(f"window.scrollBy(0, {pixels});")
            time.sleep(pause)  # Pause courte pour laisser charger le contenu
    
    # Recherche de la chaîne de l'artiste - méthode robuste avec plusieurs sélecteurs possibles
    channel_selectors = [
        "yt-img-shadow.style-scope.ytd-channel-renderer img#img",
        "#channel-thumbnail img",
        ".ytd-channel-renderer #img"
    ]
    
    # Défiler lentement pour s'assurer que tous les résultats sont chargés
    scroll_slowly(pixels=300, pause=1, max_scrolls=5)
    
    # Essayer les différents sélecteurs pour trouver la chaîne
    channel_found = False
    for selector in channel_selectors:
        try:
            # Vérifier si l'élément existe sans attendre
            channels = driver.find_elements(By.CSS_SELECTOR, selector)
            if channels:
                # Défiler jusqu'au premier élément trouvé
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", channels[0])
                time.sleep(2)  # Attendre que tout soit bien chargé
                
                # Attendre que l'élément soit cliquable avant de cliquer
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                channels[0].click()
                channel_found = True
                logger.info(f"Canal trouvé et cliqué avec le sélecteur: {selector}")
                break
        except Exception as e:
            logger.warning(f"Échec avec le sélecteur {selector}: {e}")
    
    # Si aucun des sélecteurs n'a fonctionné, essayer une méthode alternative
    if not channel_found:
        try:
            logger.info("Tentative de méthode alternative pour trouver le canal")
            # Chercher par texte contenant le nom de l'artiste
            xpath_query = f"//a[contains(text(), '{artist}')]"
            possible_links = driver.find_elements(By.XPATH, xpath_query)
            
            if possible_links:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", possible_links[0])
                time.sleep(2)
                possible_links[0].click()
                channel_found = True
                logger.info("Canal trouvé par recherche de texte")
            else:
                # Cliquer sur le premier résultat de recherche
                first_result = wait_for_element("ytd-video-renderer,ytd-channel-renderer", timeout=10)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_result)
                time.sleep(2)
                first_result.click()
                channel_found = True
                logger.info("Premier résultat de recherche cliqué")
        except Exception as e:
            logger.error(f"Méthode alternative échouée: {e}")
    
    # S'assurer que la page a bien chargé
    time.sleep(5)
    
    # Accéder à la page des vidéos - avec vérification et attente
    try:
        # Essayer de trouver le tab "Vidéos"
        videos_tab_selectors = [
            'yt-tab-shape:nth-of-type(2) > div',
            '#tabsContent [role="tab"]:nth-child(2)',
            'yt-tab-shape-behavior[role="tab"]:contains("Vidéos")',
            '//div[contains(text(), "Vidéos") and @role="tab"]'
        ]
        
        tab_found = False
        for selector in videos_tab_selectors[:3]:  # Pour les CSS selectors
            try:
                videos_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                videos_tab.click()
                tab_found = True
                logger.info(f"Onglet Vidéos trouvé avec sélecteur: {selector}")
                break
            except Exception:
                continue
        
        # Si les sélecteurs CSS ont échoué, essayer XPATH
        if not tab_found:
            try:
                videos_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, videos_tab_selectors[3]))
                )
                videos_tab.click()
                tab_found = True
            except Exception as e:
                logger.warning(f"Échec de localisation de l'onglet Vidéos: {e}")
        
        # Si toujours pas trouvé, chercher par JavaScript
        if not tab_found:
            logger.info("Tentative de clic sur l'onglet Vidéos via JavaScript")
            driver.execute_script("""
                var tabs = document.querySelectorAll('[role="tab"]');
                for(var i=0; i<tabs.length; i++) {
                    if(tabs[i].textContent.includes('Vidéos')) {
                        tabs[i].click();
                        return true;
                    }
                }
                return false;
            """)
            time.sleep(5)  # Attendre après l'exécution du JavaScript
        
    except Exception as e:
        logger.error(f"Erreur lors de l'accès à l'onglet Vidéos: {e}")
    
    # Attendre que la page se charge complètement
    time.sleep(5)
    
    # Extraire les informations de la chaîne avec gestion d'erreurs et réessais
    channel_info = {}
    
    # Structure pour les sélecteurs et leurs noms de champ correspondants
    channel_selectors = {
        "banniere_image": {
            "selectors": [
                '#page-header-banner-sizer > yt-image-banner-view-model > img',
                '#page-header img[src*="banner"]',
                '#bg.ytd-c4-tabbed-header-renderer img'
            ],
            "attribute": "src"
        },
        "artist_name": {
            "selectors": [
                '#page-header > yt-page-header-renderer > yt-page-header-view-model > div > div.page-header-view-model-wiz__page-header-headline > div > yt-dynamic-text-view-model > h1',
                '#channel-name .ytd-channel-name',
                'h1.ytd-channel-name'
            ],
            "attribute": "text"
        },
        "artist_photo": {
            "selectors": [
                '#page-header > yt-page-header-renderer > yt-page-header-view-model > div > div.page-header-view-model-wiz__page-header-headline > yt-decorated-avatar-view-model > yt-avatar-shape > div > div > div > img',
                '#avatar img',
                '#channel-header-container #img'
            ],
            "attribute": "src"
        },
        "subscribers_count": {
            "selectors": [
                '#page-header > yt-page-header-renderer > yt-page-header-view-model > div > div.page-header-view-model-wiz__page-header-headline > div > yt-content-metadata-view-model > div:nth-child(3) > span:nth-child(1)',
                '#subscriber-count',
                '.ytd-c4-tabbed-header-renderer #subscriber-count'
            ],
            "attribute": "text"
        },
        "videos_count": {
            "selectors": [
                '#page-header > yt-page-header-renderer > yt-page-header-view-model > div > div.page-header-view-model-wiz__page-header-headline > div > yt-content-metadata-view-model > div:nth-child(3) > span:nth-child(3) > span',
                '#videos-count',
                '.ytd-c4-tabbed-header-renderer #videos-count'
            ],
            "attribute": "text"
        }
    }
    
    # Extraire chaque information avec réessai
    for info_name, info_data in channel_selectors.items():
        for attempt in range(3):  # 3 tentatives par champ
            try:
                for selector in info_data["selectors"]:
                    try:
                        element = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        
                        if info_data["attribute"] == "text":
                            value = element.text
                        else:
                            value = element.get_attribute(info_data["attribute"])
                        
                        if value:
                            channel_info[info_name] = value.strip()
                            logger.info(f"Information {info_name} extraite avec succès")
                            break  # Sortir de la boucle des sélecteurs si on a trouvé
                    except Exception:
                        continue  # Essayer le prochain sélecteur
                
                # Si on a trouvé la valeur, sortir de la boucle des tentatives
                if info_name in channel_info:
                    break
                else:
                    logger.warning(f"Tous les sélecteurs ont échoué pour {info_name}, tentative {attempt+1}/3")
                    time.sleep(2)  # Pause avant réessai
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction de {info_name}: {e}")
                if attempt == 2:  # Dernière tentative
                    channel_info[info_name] = "Information non disponible"
    
    # Fonction améliorée pour faire défiler et charger toutes les vidéos
    def scroll_and_load_videos(max_videos=100, scroll_pause=2):
        """
        Fait défiler la page pour charger les vidéos, avec surveillance du chargement
        et détection intelligente de la fin de la liste
        """
        videos_before = 0
        consecutive_same_count = 0
        total_scrolls = 0
        max_scrolls = 50  # Limite de sécurité
        
        while True:
            # Compter les vidéos actuellement chargées
            current_videos = len(driver.find_elements(By.CSS_SELECTOR, 'ytd-rich-grid-media'))
            
            # Si on a atteint le nombre maximum souhaité ou si plus rien ne se charge
            if current_videos >= max_videos or consecutive_same_count >= 3 or total_scrolls >= max_scrolls:
                logger.info(f"Fin du défilement: {current_videos} vidéos chargées après {total_scrolls} défilements")
                break
            
            # Défilement progressif
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(scroll_pause)  # Attendre le chargement
            
            # Vérifier si de nouvelles vidéos ont été chargées
            if current_videos == videos_before:
                consecutive_same_count += 1
            else:
                consecutive_same_count = 0
            
            videos_before = current_videos
            total_scrolls += 1
            
            # Log pour suivre la progression
            if total_scrolls % 5 == 0:
                logger.info(f"Défilement en cours: {current_videos} vidéos chargées")
    
    # Faire défiler et charger les vidéos
    scroll_and_load_videos(max_videos=150)  # Ajuster le nombre selon les besoins
    
    # Parcourir les vidéos et extraire les informations avec une meilleure gestion des erreurs
    videos = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ytd-rich-grid-media'))
    )
    
    logger.info(f"Nombre de vidéos trouvées: {len(videos)}")
    
    # Créer des listes pour stocker les informations des vidéos
    titles = []
    links = []
    views_list = []
    video_image_list = []
    time_posted_list = []
    
    # Sélecteurs alternatifs pour les différentes informations
    video_selectors = {
        "title": ['#video-title', 'h3 a', '.title-wrapper h3'],
        "link": ['a#thumbnail.yt-simple-endpoint.style-scope.ytd-thumbnail[href]', 'a.yt-simple-endpoint[href*="watch"]'],
        "image": ['yt-image img', 'img.yt-core-image'],
        "views": ['#metadata-line > span:nth-child(3)', '.ytd-video-meta-block span:nth-child(1)'],
        "time_posted": ['#metadata-line > span:nth-child(4)', '.ytd-video-meta-block span:nth-child(2)']
    }
    
    # Fonction pour extraire un élément avec plusieurs sélecteurs
    def extract_element(video_element, selector_list, attribute="text"):
        for selector in selector_list:
            try:
                element = video_element.find_element(By.CSS_SELECTOR, selector)
                if attribute == "text":
                    return element.text.strip()
                else:
                    return element.get_attribute(attribute).strip()
            except Exception:
                continue
        return None  # Retourne None si aucun sélecteur n'a fonctionné
    
    for index, video in enumerate(videos):
        try:
            # Faire défiler pour s'assurer que l'élément est visible
            if index % 5 == 0:  # Défiler tous les 5 éléments pour ne pas trop ralentir
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", video)
                time.sleep(0.5)  # Courte pause pour le chargement
            
            # Extraire le titre
            title = extract_element(video, video_selectors["title"])
            
            # Extraire le lien
            video_link = None
            for selector in video_selectors["link"]:
                try:
                    video_link_element = video.find_element(By.CSS_SELECTOR, selector)
                    video_link = video_link_element.get_attribute('href')
                    if video_link:
                        break
                except Exception:
                    continue
            
            # Extraire l'image
            video_image = None
            if video_link_element:  # Si on a trouvé le lien, chercher l'image à l'intérieur
                for selector in video_selectors["image"]:
                    try:
                        video_image_element = video_link_element.find_element(By.CSS_SELECTOR, selector)
                        video_image = video_image_element.get_attribute("src")
                        if video_image:
                            break
                    except Exception:
                        continue
            
            # Extraire les vues
            views = extract_element(video, video_selectors["views"])
            
            # Extraire la date de publication
            time_posted = extract_element(video, video_selectors["time_posted"])
            
            # Si toutes les informations essentielles sont présentes, les ajouter aux listes
            if title and video_link:
                titles.append(title)
                links.append(video_link)
                views_list.append(views if views else "Vues non disponibles")
                video_image_list.append(video_image if video_image else "Image non disponible")
                time_posted_list.append(time_posted if time_posted else "Date non disponible")
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'extraction des informations de la vidéo {index}: {e}")
    
    # Vérifier si on a extrait des données
    if not titles:
        logger.warning("Aucune vidéo extraite. Tentative de méthode alternative.")
        # Méthode alternative - rechercher directement par XPATH
        try:
            alternative_videos = driver.find_elements(By.XPATH, "//ytd-rich-item-renderer")
            for video in alternative_videos[:30]:  # Limiter aux 30 premiers pour des raisons de performance
                try:
                    title_element = video.find_element(By.XPATH, ".//a[@id='video-title']")
                    title = title_element.text.strip()
                    video_link = title_element.get_attribute("href")
                    
                    # Chercher l'image
                    image_element = video.find_element(By.XPATH, ".//img[@class='yt-core-image']")
                    video_image = image_element.get_attribute("src")
                    
                    # Chercher les métadonnées
                    metadata_elements = video.find_elements(By.XPATH, ".//span[@class='style-scope ytd-video-meta-block']")
                    views = metadata_elements[0].text if len(metadata_elements) > 0 else "Vues non disponibles"
                    time_posted = metadata_elements[1].text if len(metadata_elements) > 1 else "Date non disponible"
                    
                    titles.append(title)
                    links.append(video_link)
                    video_image_list.append(video_image)
                    views_list.append(views)
                    time_posted_list.append(time_posted)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'extraction alternative: {e}")
        except Exception as e:
            logger.error(f"Méthode alternative échouée: {e}")
    
    # Créer un DataFrame à partir des listes
    data = {
        'Nom': channel_info.get('artist_name', artist),
        'Photo': channel_info.get('artist_photo', "Photo non disponible"),
        'Photo Banniere': channel_info.get('banniere_image', "Bannière non disponible"),
        'Nombre abonné': channel_info.get('subscribers_count', "Abonnés non disponibles"),
        'Nombre de vidéo': channel_info.get('videos_count', "Nombre de vidéos non disponible"),
        'Titre': titles,
        'Lien': links,
        'Video Image': video_image_list,
        'Vues': views_list,
        'Publié depuis': time_posted_list
    }
    
    logger.info(f"Extraction terminée. {len(titles)} vidéos extraites pour {artist}.")
    
    # Nettoyer les données avant de les retourner
    data = clean_data_dict(data=data, artist=artist)
    
    # Enregistrer les données dans un fichier JSON
    filename = f"resuslt_data.json"
    with open(filename, 'w', encoding='utf-8-sig') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    
    # Fermer le navigateur proprement
    try:
        driver.quit()
        logger.info("WebDriver fermé avec succès")
    except Exception as e:
        logger.warning(f"Erreur lors de la fermeture du WebDriver: {e}")
    
    return data