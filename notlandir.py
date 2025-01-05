import requests
from bs4 import BeautifulSoup, Comment
import time
import urllib3
import json
from urllib.parse import urljoin
import argparse
import csv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

global tresholds, weights , config, urls
class Not:
    def __init__(self, url, index_score, header_score, paragraph_score, image_score, comment_score, table_score, total_score):
        self.url = url
        self.index_score = index_score
        self.header_score = header_score
        self.paragraph_score = paragraph_score
        self.image_score = image_score
        self.comment_score = comment_score
        self.table_score = table_score
        self.total_score = total_score

def load_config(file_path="config.json"):
    with open(file_path, "r") as file:
        return json.load(file)

def load_urls(file_path="urls.txt"):
    with open(file_path, "r") as file:
        return file.readlines()
config = load_config("config.json")
tresholds = config["tresholds"]
weights = config["weights"]
    
def polite_get(url, delay=2):
    """
    Makes an HTTP GET request with a polite delay between requests.
    """
    time.sleep(delay)  # Polite delay
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"},
            verify=False,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {url}: {e}")
        return None

def get_pages(base_url):
    """
    Verilen bir base URL'deki tüm .html sayfalarını ve belirtilen kurallara uygun sayfaları döndürür.
    """
    pages = set()  # Tekrarlayan bağlantıları önlemek için set kullanılır.

    # Base URL'nin temizlenmesi (gereksiz boşluk veya satır sonu karakterleri kaldırılır).
    base_url = base_url.strip()
    if base_url.endswith("/"):
        base_url = base_url.rstrip("/")
    if not base_url.endswith(".html"):  # Base URL dizinse, `index.html` varsayılır.
        base_url += "/index.html"

    # Base URL'e erişim.
    response = polite_get(base_url)
    if response is None:
        return list(pages)

    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a")

    # Base sayfa ekleniyor.
    pages.add(base_url)

    # Tüm <a> etiketlerindeki href'leri kontrol ediyoruz.
    for link in links:
        href = link.get("href")
        if not href:
            continue  # Boş bağlantılar atlanır.

        # Href bir tam URL değilse, base URL ile birleştirilir.
        full_link = urljoin(base_url, href.strip())

        # Sadece verilen kök URL'ye bağlı sayfalar kabul ediliyor.
        if not full_link.startswith(base_url.rsplit("/", 1)[0]):
            continue

        # Kabul edilen sayfa formatları.
        if (
            full_link.endswith(".html") or  # .html sayfalar
            full_link.endswith("/")         # Dizin bağlantıları
        ):
            pages.add(full_link)

    return sorted(pages)  # Sıralı liste olarak döndürülür.



def has_js(content):
    """
    Sayfa içinde harici (external) JavaScript kullanılıp kullanılmadığını kontrol eder.
    """
    scripts = content.find_all("script")
    for script in scripts:
        src = script.get("src")
        if src:  # src varsa bu harici bir JS'dir
            return True
    return False


def has_header(content):
    """
    Sayfa içinde en az bir başlık etiketi (h1, h2, h3, h4, h5, h6) kullanılıp kullanılmadığını kontrol eder.
    """
    return content.find(["h1", "h2", "h3", "h4", "h5", "h6"]) is not None

def has_table(content):
    """
    Sayfa içinde tablo etiketi (table) kullanılıp kullanılmadığını kontrol eder.
    (En az 2 satır ve 2 sütun içeren bir tablo.)
    """
    tables = content.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) >= 2:
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    return True
    return False

def has_long_paragraph(content, tresholds):
    """
    Sayfa içinde 300 karakterden uzun bir paragraf içeren bir paragraf olup olmadığını kontrol eder.
    """
    paragraphs = content.find_all("p")
    for paragraph in paragraphs:
        if len(paragraph.get_text(strip=True)) >= tresholds["paragraph_length"]:
            return True
    return False

def has_comment(content):
    """
    Sayfa içinde yorum satırı (comment) içeren bir etiket olup olmadığını kontrol eder.
    """
    comments = content.find_all(string=lambda text: isinstance(text, Comment))
    return bool(comments)

def has_image(content):
    """
    Sayfa içinde en az bir resim etiketi (img) kullanılıp kullanılmadığını kontrol eder.
    """
    return bool(content.find("img"))

def log_to_file(log_file, message):
    """
    Log dosyasına mesaj yazma işlevi.
    """
    with open(log_file, "a", encoding="utf-8") as file:
        file.write(message + "\n")

def evaluate_pages(base_url, config, log_file="log.txt"):
    """
    Sayfa analizlerini loglar ve nihai sonuçları bir dosyaya kaydeder.
    """
    pages = get_pages(base_url)
    log_to_file(log_file, f"{base_url} için {len(pages)} sayfa bulundu.\n")
    if not pages:
        log_to_file(log_file, f"{base_url} için sayfa bulunamadı.\n")
        return
    
    sonuclar = []
    toplam_sayfa_sayisi = len(pages)
    toplam_skor = 0
    baslik_uyumlu_sayfa = 0
    paragraf_uyumlu_sayfa = 0
    resim_uyumlu_sayfa = 0
    yorumlu_sayfa_sayisi = 0
    tablo_puani_eklendi = False

    for page in pages:
        response = polite_get(page)
        if response is None:
            log_to_file(log_file, f"{page}: Sayfaya erişilemedi.\n")
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        if has_js(soup):
            toplam_skor = -1
            log_to_file(log_file, f"{page}: Harici JS içeriyor, değerlendirme yapılamadı.\n")
            return

        # Başlık Kontrolü
        header_check = has_header(soup)
        if header_check:
            baslik_uyumlu_sayfa += 1

        # Tablo Kontrolü
        table_check = has_table(soup)
        if table_check and not tablo_puani_eklendi:
            tablo_puani_eklendi = True

        # Paragraf Kontrolü
        paragraph_check = has_long_paragraph(soup, tresholds)
        if paragraph_check:
            paragraf_uyumlu_sayfa += 1

        # Resim Kontrolü
        image_check = has_image(soup)
        if image_check:
            resim_uyumlu_sayfa += 1

        # Yorum Kontrolü
        comment_check = has_comment(soup)
        if comment_check:
            yorumlu_sayfa_sayisi += 1

        # Sayfa bazında analiz loglama
        log_to_file(
            log_file,
            f"Sayfa: {page}\n"
            f"Başlık Bulundu: {'Evet' if header_check else 'Hayır'}\n"
            f"Tablo Bulundu: {'Evet' if table_check else 'Hayır'}\n"
            f"Uzun Paragraf Bulundu: {'Evet' if paragraph_check else 'Hayır'}\n"
            f"Resim Bulundu: {'Evet' if image_check else 'Hayır'}\n"
            f"Yorum Satırı Bulundu: {'Evet' if comment_check else 'Hayır'}\n"
        )

    # Skor Hesaplamaları
    toplam_indeks_puani = round(min(weights["index"] * toplam_sayfa_sayisi, weights["max_index_score"]))
    toplam_baslik_puani = round(weights["header"] * (baslik_uyumlu_sayfa / toplam_sayfa_sayisi) if toplam_sayfa_sayisi > 0 else 0)
    toplam_paragraf_puani = round(weights["paragraph"] * (paragraf_uyumlu_sayfa / toplam_sayfa_sayisi) if toplam_sayfa_sayisi > 0 else 0)
    toplam_resim_puani = round(weights["image"] * (resim_uyumlu_sayfa / toplam_sayfa_sayisi) if toplam_sayfa_sayisi > 0 else 0)
    toplam_yorum_puani = round(weights["comments"] if yorumlu_sayfa_sayisi == toplam_sayfa_sayisi else 0)
    tablo_puani = round(weights["table"] if tablo_puani_eklendi else 0)

    toplam_skor = round(
        toplam_indeks_puani
        + toplam_baslik_puani
        + toplam_paragraf_puani
        + toplam_resim_puani
        + toplam_yorum_puani
        + tablo_puani
    )

    # Nihai sonuçları log dosyasına yazma
    log_to_file(
        log_file,
        "\n******************************************\n"
        f"URL: {base_url}\n"
        f"İndeks Puanı: {toplam_indeks_puani} (Her sayfa {weights['index']} puan kazandırır, maksimum {weights['max_index_score']} puan)\n"
        f"Başlık Puanı: {toplam_baslik_puani:.2f} ({baslik_uyumlu_sayfa} / {toplam_sayfa_sayisi} sayfa, Puan hesaplama: {weights['header']} * ({baslik_uyumlu_sayfa} / {toplam_sayfa_sayisi}))\n"
        f"Paragraf Puanı: {toplam_paragraf_puani:.2f} ({paragraf_uyumlu_sayfa} / {toplam_sayfa_sayisi} sayfa, Puan hesaplama {weights['paragraph']} * ({paragraf_uyumlu_sayfa} / {toplam_sayfa_sayisi}))\n"
        f"Resim Puanı: {toplam_resim_puani:.2f} ({resim_uyumlu_sayfa} / {toplam_sayfa_sayisi} sayfa, Puan hesaplama {weights['image']} * ({resim_uyumlu_sayfa} / {toplam_sayfa_sayisi}))\n"
        f"Yorum Puanı: {toplam_yorum_puani} ({'Tüm sayfalarda yorum bulundu' if yorumlu_sayfa_sayisi == toplam_sayfa_sayisi else 'Her sayfada yorum satırı bulunamadı'}, varsa {weights['comments']} puan)\n"
        f"Tablo Puanı: {tablo_puani} (Tablo bulundu mu: {'Evet' if tablo_puani_eklendi else 'Hayır'}, tablo puanı: {weights['table']})\n"
        f"Toplam Skor (100 üzerinden): {min(toplam_skor, 100):.2f}\n"
        "******************************************\n"
    )
    print(f"{base_url} için değerlendirme tamamlandı. Detaylı analizler log dosyasına kaydedildi.")
    sonuclar.append(Not(base_url, toplam_indeks_puani, toplam_baslik_puani, toplam_paragraf_puani, toplam_resim_puani, toplam_yorum_puani, tablo_puani, min(toplam_skor, 100)))
    return sonuclar

def write_to_csv(sonuclar):
    with open("sonuclar.csv", "w", newline="", encoding="utf-8") as file:
        # Sadece URL ve Total Skor için alan adları
        fieldnames = ["url", "total_score"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        # Başlıkları yaz
        writer.writeheader()
        
        # Her bir 'Not' nesnesini yaz
        for sonuc in sonuclar:
            writer.writerow({
                "url": sonuc.url, 
                "total_score": sonuc.total_score
            })

def main(input_file):
    print("Değerlendirme başladı...")
    config = load_config("config.json")
    urls = load_urls(input_file)
    output_file = "sonuclar.csv"

    sonuclar = []
    for url in urls:
        url = url.strip()  # Boşlukları temizle
        sonuc = evaluate_pages(url, config)
        if sonuc:  # Eğer boş değilse listeye ekle
            sonuclar.extend(sonuc)  # Sonuçlar bir liste olduğu için genişletiyoruz

    write_to_csv(sonuclar)  # Sonuçları CSV'ye yaz
    print(f"Değerlendirme tamamlandı. Sonuçlar {output_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    try:
        input_file = "urls.txt"
        main(input_file)
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
