
from selenium import webdriver
import time
import json
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

BASE_URL = 'craigslist.org'
# show-curtain opaque

def get_storage_json(url) -> json:
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(chrome_options=chrome_options)
    print('Browser opened')
    
    driver.get(url)
    delay = 30 

    print(f"Waiting for selector:  #search-results-page-1")
    WebDriverWait(driver,delay).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"#search-results-page-1")))
    
    iframe_el = driver.find_element(By.ID,'cl-local-storage')
    print(f"Ifram el has been found")
    iframe_ur = iframe_el.get_attribute('src')
    
    iframe_el = None
    iframe_ur = None
    try:
        iframe_el = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, 'cl-local-storage'))) 
        iframe_ur = iframe_el.get_attribute('src')
        print(f"Iframe url was found: {iframe_ur}")
    except TimeoutException:
        print('No iframe found')

    if iframe_el:

        time.sleep(4)
        
        # Open a new window
        driver.execute_script("window.open('');")
        print(f"New window has been opened")
        # Switch to the new window and open URL B
        driver.switch_to.window(driver.window_handles[1])
        driver.get(iframe_ur)
        time.sleep(2)
        local_storage = driver.execute_script("return localStorage.getItem('resultSets')")
        try:
            json_string = json.loads(local_storage)
            print(f"Local storage found")
        except Exception as e:
            print(f'No data  found for {url} ')
            return False
        
        driver.quit()
        print(f"Browser closed")
        return json_string
    else:
        print('No data available in localstorage')
        return False

def generate_links(json_string: json) -> list:
    if json_string:
        data = json_string
        keys = data.keys()
        key = [i for i in keys][0]

        hosts_list = data[key]['hostsList']
        subareas_list = data[key]['subareasList']
        categories_list = data[key]['categoriesList']
        print(hosts_list)
        print(subareas_list)
        print(categories_list)
        results_sets = data[key]['resultList']
        ids = []
        for item in results_sets:
            generated_url = f"https://{hosts_list[item[0]]}.{BASE_URL}/{subareas_list[item[1]]}/{categories_list[item[2]]}/{item[-1]}.html"
            ids.append(generated_url)
        
        print(f"Found {len(ids)} links")
        return ids
    else:
        return False    
def get_links(url:str) -> list:
    json_data = get_storage_json(url)
    links = generate_links(json_data)
    if links:
        return links
    else:
        return False
 


app = FastAPI()

@app.get("/crgl/")
def update_item(request: Request):
    requested_url = request.query_params.get('url')
    print(f"Url received: {requested_url}")
    if requested_url:
        data = get_links(requested_url)
        if data:
            json_compatible_item_data = jsonable_encoder(data)
            return JSONResponse(content=json_compatible_item_data)
        else:
            rs = jsonable_encoder({f"status":"No Local storage, for {requested_url}"})
            return JSONResponse(content=rs)
    else:
        res = {"status":404}
        json_compatible_item_data_error = jsonable_encoder(res)
        return JSONResponse(content=json_compatible_item_data_error)
