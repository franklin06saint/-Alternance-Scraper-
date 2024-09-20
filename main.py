import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
import time

def parse_date(date_string):
    if "hier" in date_string.lower():
        return datetime.now().date() - timedelta(days=1)
    else:
        try:
            return datetime.strptime(date_string, "%d sept. %Y").date()
        except ValueError:
            return datetime.now().date()  # Si le format n'est pas reconnu, on considère que c'est aujourd'hui

def scrape_job_details(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        missions = soup.find('section', string=lambda text: 'Les missions du poste' in text if text else False)
        missions_text = missions.find_next('p').text.strip()[:500] + '...' if missions else 'Non spécifié'
        
        profile = soup.find('section', string=lambda text: 'Le profil recherché' in text if text else False)
        profile_text = profile.find_next('p').text.strip()[:500] + '...' if profile else 'Non spécifié'
        
        return {
            'missions': missions_text,
            'profile': profile_text
        }
    except Exception as e:
        print(f"Erreur lors de l'extraction des détails de l'offre : {str(e)}")
        return {
            'missions': 'Non spécifié',
            'profile': 'Non spécifié'
        }

def scrape_hellowork(date_filter='all'):
    base_url = "https://www.hellowork.com/fr-fr/emploi/recherche.html"
    params = {
        "k": "alternance",
        "p": 1
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_jobs = []
    max_pages = 5  # Limite le scraping aux 5 premières pages
    
    while params['p'] <= max_pages:
        print(f"Scraping page {params['p']}...")
        response = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        job_listings = soup.find_all('div', class_='tw-group tw-h-full tw-overflow-hidden tw-bg-secondary tw-rounded-sm tw-border tw-border-greyLighter hover:tw-border-grey focus-within:tw-outline focus-within:tw-transition-none tw-transition-border-color tw-duration-100')
        
        for job in job_listings:
            try:
                title = job.find('p', class_='tw-typo-l sm:small-group:tw-typo-l sm:tw-typo-xl').text.strip()
                company = job.find('p', class_='tw-typo-s tw-inline').text.strip()
                location = job.find('div', class_='tw-readonly tw-tag-secondary-s tw-w-fit tw-border-0').text.strip()
                contract_tags = job.find_all('div', class_='tw-readonly tw-tag-secondary-s tw-w-fit tw-border-0')
                contract = contract_tags[1].text.strip() if len(contract_tags) > 1 else 'Non spécifié'
                salary = job.find('div', class_='tw-readonly tw-tag-attractive-s tw-w-fit tw-border-0')
                salary = salary.text.strip() if salary else 'Non spécifié'
                duration = job.find('div', class_='tw-readonly tw-tag-primary-s tw-w-fit')
                duration = duration.text.strip() if duration else 'Non spécifié'
                
                publication_date = job.find('div', class_='tw-typo-s tw-text-grey').text.strip()
                parsed_date = parse_date(publication_date)
                
                if date_filter == 'all' or (date_filter == '24h' and (datetime.now().date() - parsed_date).days <= 1) or \
                   (date_filter == '3days' and (datetime.now().date() - parsed_date).days <= 3) or \
                   (date_filter == '1week' and (datetime.now().date() - parsed_date).days <= 7) or \
                   (date_filter == '1month' and (datetime.now().date() - parsed_date).days <= 30):
                
                    job_link = job.find('a', href=True)
                    full_job_url = f"https://www.hellowork.com{job_link['href']}" if job_link else 'Non spécifié'
                    
                    job_details = scrape_job_details(full_job_url) if full_job_url != 'Non spécifié' else {'missions': 'Non spécifié', 'profile': 'Non spécifié'}
                    
                    all_jobs.append({
                        'Titre': title,
                        'Entreprise': company,
                        'Localisation': location,
                        'Type de contrat': contract,
                        'Salaire': salary,
                        'Durée': duration,
                        'Date de publication': publication_date,
                        'Missions': job_details['missions'],
                        'Profil recherché': job_details['profile'],
                        'URL de l\'offre': full_job_url
                    })
            except Exception as e:
                print(f"Erreur lors de l'extraction d'une offre : {str(e)}")
        
        if params['p'] < max_pages:
            params['p'] += 1
            time.sleep(5)  # Pause de 5 secondes entre chaque page
        else:
            break
    
    return all_jobs

def save_to_csv(jobs):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"C:\\Users\\Ch0sen\\Desktop\\script\\Alt\\alternance_jobs_{timestamp}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Titre', 'Entreprise', 'Localisation', 'Type de contrat', 'Salaire', 'Durée', 'Date de publication', 'Missions', 'Profil recherché', 'URL de l\'offre'])
        writer.writeheader()
        for job in jobs:
            writer.writerow(job)
    
    print(f"Données sauvegardées dans {filename}")

if __name__ == "__main__":
    date_filter = input("Choisissez un filtre de date (all/24h/3days/1week/1month): ")
    jobs = scrape_hellowork(date_filter)
    save_to_csv(jobs)
    print(f"Nombre total d'offres récupérées : {len(jobs)}")