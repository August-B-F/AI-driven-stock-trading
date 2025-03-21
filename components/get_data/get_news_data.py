import datetime
from urllib.parse import quote
from gnews import GNews
import random
import json
import time
from stem import Signal
from stem.control import Controller

# for selenium scraping 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from collections import OrderedDict

# for article sentiment analysis 
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re

from components.logging.logging import write_to_log
from components.misc.progress_bar import print_progress_bar  

def renew_tor_ip(controller):
    controller.authenticate("oadjaoi123")
    controller.signal(Signal.NEWNYM)

def random_delay(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def fetch_article_titles(company_name, period, controller, user_agents, tor_proxy, service):
    dates = []

    try: 
        with open(f"data/raw_data/raw_news/{company_name}.json", "r") as file:
            news_data = json.load(file)
            file.close()
            
    except:
        news_data = {}

    for n in range(period):
        date = datetime.datetime.now() - datetime.timedelta(days=n)
        date = date.strftime('%Y-%m-%d')
        
        if date not in news_data: 
            dates.append(date)
            
    if dates != []: 
        renew_tor_ip(controller)
        random_user_agent = random.choice(user_agents)

        options = ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--page-load-strategy=eager")
        options.add_argument(f"--user-agent={random_user_agent}")
        options.add_argument(f'--proxy-server={tor_proxy}')

        driver = webdriver.Chrome(service=service, options=options)
    else: 
        return news_data

    for date in dates:
        date_str = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%m/%d/%Y')
        news_data[date] = {}
        
        random_delay(1, 2)
        
        driver.get(f"https://www.google.com/search?q={company_name}&tbm=nws&hl=en&gl=us&tbs=cdr:1,cd_min:{date_str},cd_max:{date_str}")
        
        if "https://consent.google.com/" in driver.current_url:
            for i in range(3): 
                try:
                    reject_button = driver.find_element(By.XPATH, "//form[@action='https://consent.google.com/save']")
                    reject_button.click()
                    
                    break

                except Exception as e:
                    random_delay(1, 2)
                    
        elif "https://www.google.com/sorry/index" in driver.current_url:
            driver.quit()
            int("google blocking")

        for i in range(4): 
            if driver.find_elements(By.CLASS_NAME, "XIzzdf") != []: 
                break
            
            else:  
                random_delay(1, 2)

        articles = driver.find_elements(By.CLASS_NAME, "SoAPf") 

        for i, article in enumerate(articles):
            title = article.find_element(By.CLASS_NAME, "n0jPhd").text
            
            try:
                snippet = article.find_element(By.CLASS_NAME, "GI74Re").text
                
            except: 
                snippet = ""
                
            link = driver.find_elements(By.CLASS_NAME, "WlydOe")[i].get_attribute("href")
            
            news_data[date][i] = {
                "title": title,
                "link": link,
                "snippet": snippet,
                "score": None,
                "sentiment": None,
                "probability": None,
                "content": None,
                "description": None
            }  
            
        news_data = OrderedDict(sorted(news_data.items(), key=lambda x: datetime.datetime.strptime(x[0], "%Y-%m-%d"), reverse=True))

        with open(f"data/raw_data/raw_news/{company_name}.json", "w") as file:
            json.dump(news_data, file, indent=4)
            file.close()

    driver.quit()

    return news_data
          
# def fetch_article_titles(company_name, period): 
#     dates = []
#     encoded_query = quote(company_name)
#     language = "en"
    
#     # dates to scrape   
#     try:
#         with open(f"data/raw_data/raw_news/{company_name}.json", "r") as file:
#             news_data = json.load(file)
#             file.close()
            
#     except:
#         news_data = {}
    
#     for n in range(period):
#         date = datetime.now() - timedelta(days=n)
#         date = date.strftime('%Y-%m-%d')
        
#         if date not in news_data: 
#             dates.append(date)

#     # fetching the titles using rss 
#     for date in dates: 
#         rss_url = f'https://news.google.com/rss/search?q={encoded_query}&hl={language}&gl=US&ceid=US:{language}'
#         feed = feedparser.parse(rss_url)
        
#         news_data[date] = {}

#         start_date = datetime.strptime(date, '%Y-%m-%d')
#         end_date = start_date + timedelta(days=1)
        
#         if feed.entries:
#             index = 0 
#             for entry in feed.entries:
#                 try:
#                     pubdate = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z')
                    
#                 except:
#                     continue

#                 if start_date <= pubdate <= end_date:
#                     title = entry.title
#                     link = entry.link

#                     index += 1                     
#                     news_data[date][str(index)] = {
#                         "title": title,
#                         "link": link,
#                         "snippet": title,
#                         "score": None,
#                         "sentiment": None,
#                         "probability": None,
#                         "content": None,
#                         "description": None
#                     }
                    
#                     if index >= 10: 
#                         break 
                    
#         else:
#             write_to_log(f"Could not find news for company on {date} at: {datetime.now()}")
            
#     # write to json  
#     with open(f"data/raw_data/raw_news/{company_name}.json", "w") as file:
#         json.dump(news_data, file, indent=4)
#         file.close()
        
#     return news_data

def get_article_content(company, links):
    google_news = GNews(language="en", max_results=10)
    # MAX_RETRIES = 3

    
    for date_str, articles in links.items():
        for i, article in articles.items():
            if article["content"] is not None:
                continue
            
            try:
                article_text = google_news.get_full_article(article["link"]).text
            except Exception as e:
                article_text = ""

            article["content"] = article_text
            
            # for attempt in range(MAX_RETRIES):
            #     try:
            #         link = article["link"]
            #         snippet = article["snippet"]
            #         driver.get(link)
                    
            #         WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
            #         # use newspaper3k to extract article content
            #         article_obj = Article(link)
            #         article_obj.download()
            #         article_obj.parse()
            #         article_text = article_obj.text
                    
            #         if (SequenceMatcher(None, snippet, article_text).ratio() < 0.5 and ("cookie" in article_text.lower() or "cookies" in article_text.lower())):
            #             try:
            #                 accept_button = WebDriverWait(driver, 5).until(
            #                     EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'OK') or contains(text(), 'Godkänn alla') or contains(text(), 'consent') or contains(text(), 'Consent') or contains(text(), 'Godkänn') or contains(text(), 'Acceptera') or contains(text(), 'Tillåt') or contains(text(), 'Godkänn alla cookies') or contains(text(), 'Accept all cookies') or contains(text(), 'Acceptera alla') or contains(text(), 'Acceptera alla cookies') or contains(text(), 'Accept all') or contains(text(), 'Accept all cookies')]"))
            #                 )
            #                 accept_button.click()
            #                 driver.get(link)
                            
            #                 WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                            
            #                 # Re-extract article content after handling cookie consent
            #                 article_obj = Article(link)
            #                 article_obj.download()
            #                 article_obj.parse()
            #                 article_text = article_obj.text
                            
            #             except Exception as e:
            #                 pass
                        
            #         if article_text == "":
            #             try:
            #                 article_text = google_news.get_full_article(driver.current_url).text
            #             except Exception as e:
            #                 article_text = "Error"

            #         article["content"] = article_text
            #         print(article_text)
            #         break

            #     except Exception as e:
            #         if attempt < MAX_RETRIES - 1:
            #             random_delay()
            #         else:
            #             article["content"] = "Error"

            random_delay()

    with open(f"data/raw_data/raw_news/{company}.json", "w") as file:
        json.dump(links, file, indent=4)

def estimate_sentiment(news):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert").to(device)
    labels = ["positive", "negative", "neutral"]

    if news:
        tokens = tokenizer(news, return_tensors="pt", padding=True).to(device)
        result = model(tokens["input_ids"], attention_mask=tokens["attention_mask"])["logits"]
        result = torch.nn.functional.softmax(torch.sum(result, 0), dim=-1)
        probability = result[torch.argmax(result)].item()
        sentiment = labels[torch.argmax(result)]
        
        return probability, sentiment
    
    else:
        return 0, labels[-1]

def perform_sentiment_analysis(company):
    with open(f"data/raw_data/raw_news/{company}.json", "r") as file:
        json_data = json.load(file)
        file.close()

    for date in json_data:
        for article in json_data[date]:
            try:
                if json_data[date][article].get("score") is not None:
                    continue

                content = json_data[date][article]["title"]
                content = content.replace(".", ". ").replace(" ", " ").replace("\n", " ")

                # if content in ("error", "", "null") or content is None or len(content) < 30:
                #     content = json_data[date][article]["title"]
                #     content = content.replace(".", ". ").replace(" ", " ").replace("\n", " ")
                #     if content in ("error", "", "null") or content is None:
                #         continue

                content = re.sub(r"[^\x00-\x7F]+", " ", content)
                try:
                    probability, sentiment = estimate_sentiment(content)
                    
                except:
                    try: 
                        content = content[:2000].rsplit(" ", 1)[0]
                        probability, sentiment = estimate_sentiment(content)
                        
                    except: 
                        content = content[:1500].rsplit(" ", 1)[0]
                        probability, sentiment = estimate_sentiment(content)     
                
                json_data[date][article]["score"] = probability
                json_data[date][article]["finbert_sentiment"] = sentiment

            except:
                continue

    with open(f"data/raw_data/raw_news/{company}.json", "w") as file:
        json.dump(json_data, file, indent=4)  
        file.close()

    return json_data

def get_news_data(companies, period):
    write_to_log(f"News scraping start at: {datetime.datetime.now()}")
    
    news = {}
    fails = 0
    index = 0 
    successes = 0  
    
    service = Service(ChromeDriverManager().install())
    controller = Controller.from_port(port=9051)
    tor_proxy = "socks5://127.0.0.1:9150"
    user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.1108.62 Safari/537.36 Edg/98.0.1108.62"
    ]
    
    for company in companies:
        print_progress_bar(index, len(companies), description="Scraping news: ")
        index += 1 
         
        news[company] = {}
        
        try: 
            for i in range(10): 
                try:      
                    # get news article titles 
                    titles = fetch_article_titles(company, period, controller, user_agents, tor_proxy, service)
                    news[company] = titles
                    
                    break
                    
                except: 
                    if i == 9: 
                        write_to_log(f"Failed to get news titles for {company} at: {datetime.datetime.now()}")
                
            # get news article content 
            content = get_article_content(company, titles)
            news[company] = content
            
            # get sentiment from content 
            sentiment = perform_sentiment_analysis(company)     
            news[company] = sentiment
                        
            successes += 1   

        except Exception as e: 
            fails += 1
            write_to_log(f"Failed to process {company} news at: {datetime.datetime.now()}")
            
        finally: 
            time.sleep(1)

    write_to_log(f"""News scraping done with {successes} successes and {fails} fails at: {datetime.datetime.now()}""")
    
    if successes + fails != len(companies): 
        write_to_log(f"""Something is wrong in news scraping, the times scraped do not match the number of companies. 
Scrapes done: {successes + fails}
Total companies: {len(companies)}""")            

    return news

