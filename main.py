from bs4 import BeautifulSoup
from selenium import webdriver
from time import sleep
import csv
from datetime import datetime
from argparse import ArgumentParser

# example url: https://www.imovelweb.com.br/apartamentos-venda-cristo-rei-curitiba-2-quartos-200000-400000-reales.html

BASE_URL = "https://www.imovelweb.com.br/apartamentos"

def find_apt(neighborhood, minprice, maxprice, bedrooms, sale):

    # build url
    url = BASE_URL 
    url += f"-{sale}" if sale else ""
    url += f"-{neighborhood}" if neighborhood else ""
    url += f"-{bedrooms}-quartos" if bedrooms else ""
    url += f"-{minprice}-{maxprice}-reales" if minprice and maxprice else ""
    url += ".html"
    print(url)

    # get page html 
    driver = webdriver.Chrome()
    driver.get(url)
    sleep(1)
    data = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
    soup = BeautifulSoup(data.encode('utf-8'), 'html.parser')

    # find all results
    result_container = soup.find_all('div', class_='postings-container')
    results = result_container[0].find_all('div')    

    results_filtered = []
    for result in results:
        try:
            apartament = {}

            # get price as int
            price_div = result.find('div', attrs={'data-qa': 'POSTING_CARD_PRICE'})
            apartament["price"] = int(price_div.text.replace('R$ ', '').replace('.', ''))
            cond_div = result.find('div', attrs={'data-qa': 'expensas'})
            apartament["condominium"] = int(cond_div.text.replace('R$ ', '').replace('.', '').replace(' Condominio', '')) if cond_div else 0
            
            # get address
            location_div = result.find('div', attrs={'data-qa': 'POSTING_CARD_LOCATION'})
            location_children = location_div.parent.findChildren('div', recursive=False)
            apartament["street"] = location_children[0].text
            apartament["neighborhood"] = location_children[1].text

            # get features
            features_div = result.find('div', attrs={'data-qa': 'POSTING_CARD_FEATURES'})
            features_spans = features_div.findChildren('span', recursive=False)
            for span in features_spans:
                feature = span.findChildren('span', recursive=False)[0].text
                if "m²" in feature and apartament.get("area") is None:
                    apartament["area"] = int(feature.replace(' m²', ''))
                elif "m²" in feature:
                    apartament["use_area"] = int(feature.replace(' m²', ''))
                elif "quartos" in feature:
                    apartament["bedrooms"] = int(feature.replace(' quartos', ''))
                elif "banheiros" in feature or "ban" in feature:
                    apartament["bathrooms"] = int(feature.replace(' banheiro', '').replace(' ban', ''))
                elif "vaga" in feature:
                    apartament["parking"] = int(feature.replace(' vagas', '').replace(' vaga', ''))
            if apartament.get("parking") is None:
                apartament["parking"] = 0

            # get link
            link_div = result.find_all('a')[0]
            apartament["link"] = "https://www.imovelweb.com.br" + link_div['href']

            results_filtered.append(apartament)

        except AttributeError:
            continue

    # sort by price and remove duplicates
    results_filtered = [dict(t) for t in {tuple(d.items()) for d in results_filtered}]
    results_filtered.sort(key=lambda x: x["price"])
    [print(result) for result in results_filtered]

    # save to csv
    keys = results_filtered[0].keys()
    with open(f"{datetime.now().strftime('%d-%m-%Y-%H-%M-%S')}-results.csv", 'w', newline='')  as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(results_filtered)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-n", "--neighborhood", help="neighborhood to search")
    parser.add_argument("-p", "--price", nargs=2, metavar=('minprice', 'maxprice'), help="price range to search")
    parser.add_argument("-b", "--bedrooms", help="min number of bedrooms")
    parser.add_argument("-s", "--sale", help="search for sale or rent", choices=['venda', 'aluguel'])
    args = parser.parse_args()

    find_apt(args.neighborhood, args.price[0], args.price[1], args.bedrooms, args.sale)