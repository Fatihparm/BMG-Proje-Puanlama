import requests
from bs4 import BeautifulSoup, Comment
import time
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_config(file_path="config.json"):
    with open(file_path, "r") as file:
        return json.load(file)

def load_urls(file_path="urls.txt"):
    with open(file_path, "r") as file:
        return file.readlines()

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
    pages = set()  # Set kullanımı, tekrar eden bağlantıları önler.

    # Base URL sonlandırmaları kontrol edilip normalize ediliyor.
    if base_url.endswith("/"):
        base_url = base_url.rstrip("/")
    if base_url.endswith("index.html"):
        base_url = base_url.rsplit("/", 1)[0]
    if not base_url.endswith(".html"):
        base_url += "/index.html"

    # Base URL'e erişim.
    response = polite_get(base_url)
    if response is None:
        return list(pages)

    soup = BeautifulSoup(response.content, "html.parser")
    links = soup.find_all("a")

    # Base sayfayı ekliyoruz.
    pages.add(base_url)

    # Tüm <a> etiketlerindeki href'leri kontrol ediyoruz.
    for link in links:
        href = link.get("href")
        if not href:
            continue  # Href boşsa atla.

        # Href bir tam URL değilse, base URL ile birleştiriyoruz.
        if "://" not in href:
            if href.startswith("/"):
                full_link = f"{base_url.rsplit('/', 3)[0]}{href}"  # Kök URL'yi baz alarak birleştir.
            else:
                full_link = f"{base_url.rsplit('/', 1)[0]}/{href}"
        else:
            full_link = href

        # Sadece belirtilen github.io kök URL'leri kabul ediliyor.
        if "github.io" not in full_link or not full_link.startswith(base_url.rsplit("/", 1)[0]):
            continue

        # Kabul edilen sayfa formatlarını kontrol et.
        if (
            full_link.endswith(".html") or
            full_link.endswith("/") or
            full_link == base_url.rsplit("/", 1)[0]  # Ana dizini ekler.
        ):
            pages.add(full_link)

    return list(pages)


def has_js(content):
    return bool(content.find("script"))

def has_header(content):
    return content.find(["h1", "h2", "h3", "h4", "h5", "h6"]) is not None

def has_table(content):
    tables = content.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) >= 2:
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    return True
    return False

def has_long_paragraph(content):
    paragraphs = content.find_all("p")
    for paragraph in paragraphs:
        if len(paragraph.get_text(strip=True)) >= 300:
            return True
    return False

def has_comment(content):
    comments = content.find_all(string=lambda text: isinstance(text, Comment))
    return bool(comments)

def has_image(content):
    return bool(content.find("img"))

def evaluate_pages_with_config(base_url, config):
    pages = get_pages(base_url)
    if not pages:
        print(f"{base_url} için sayfa bulunamadı.")
        return

    weights = config["weights"]
    thresholds = config["thresholds"]

    toplam_skor = 0
    toplam_sayfa_sayisi = len(pages)
    baslik_uyumlu_sayfa = 0
    paragraf_uyumlu_sayfa = 0
    resim_uyumlu_sayfa = 0
    yorumlu_sayfa_sayisi = 0
    tablo_puani_eklendi = False

    for page in pages:
        response = polite_get(page)
        if response is None:
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        # Başlık Kontrolü
        if has_header(soup):
            baslik_uyumlu_sayfa += 1

        # Tablo Kontrolü
        if has_table(soup) and not tablo_puani_eklendi:
            tablo_puani_eklendi = True

        # Paragraf Kontrolü
        if has_long_paragraph(soup):
            paragraf_uyumlu_sayfa += 1

        # Resim Kontrolü
        if has_image(soup):
            resim_uyumlu_sayfa += 1

        # Yorum Kontrolü
        if has_comment(soup):
            yorumlu_sayfa_sayisi += 1

    # Skor Hesaplamaları
    toplam_indeks_puani = min(weights["index"] * toplam_sayfa_sayisi, weights["max_index_score"])
    toplam_baslik_puani = weights["header"] * (baslik_uyumlu_sayfa / toplam_sayfa_sayisi) if toplam_sayfa_sayisi > 0 else 0
    toplam_paragraf_puani = weights["paragraph"] * (paragraf_uyumlu_sayfa / toplam_sayfa_sayisi) if toplam_sayfa_sayisi > 0 else 0
    toplam_resim_puani = weights["image"] * (resim_uyumlu_sayfa / toplam_sayfa_sayisi) if toplam_sayfa_sayisi > 0 else 0
    toplam_yorum_puani = weights["comments"] if yorumlu_sayfa_sayisi == toplam_sayfa_sayisi else 0
    tablo_puani = weights["table"] if tablo_puani_eklendi else 0

    toplam_skor = (
        toplam_indeks_puani
        + toplam_baslik_puani
        + toplam_paragraf_puani
        + toplam_resim_puani
        + toplam_yorum_puani
        + tablo_puani
    )

    # Sonuçları Yazdır
    print("******************************************")
    print(f"İndeks Puanı: {toplam_indeks_puani} (Her sayfa {weights['index']} puan kazandırır, maksimum {weights['max_index_score']} puan)")
    print(f"Başlık Puanı: {toplam_baslik_puani:.2f} ({baslik_uyumlu_sayfa} / {toplam_sayfa_sayisi} sayfa, Puan hesaplama: {weights['header']} * ({baslik_uyumlu_sayfa} / {toplam_sayfa_sayisi}))")
    print(f"Paragraf Puanı: {toplam_paragraf_puani:.2f} ({paragraf_uyumlu_sayfa} / {toplam_sayfa_sayisi} sayfa, Puan hesaplama {weights['paragraph']} *{paragraf_uyumlu_sayfa} / {toplam_sayfa_sayisi}))")
    print(f"Resim Puanı: {toplam_resim_puani:.2f} ({resim_uyumlu_sayfa} / {toplam_sayfa_sayisi} sayfa, Puan hesaplama {weights['image']} * {resim_uyumlu_sayfa} / {toplam_sayfa_sayisi})")
    print(f"Yorum Puanı: {toplam_yorum_puani} ({'Tüm sayfalarda yorum bulundu' if yorumlu_sayfa_sayisi == toplam_sayfa_sayisi else 'Her sayfada yorum satırı bulunamadı'}, varsa {weights['comments']} puan)")
    print(f"Tablo Puanı: {tablo_puani} (Tablo bulundu mu: {'Evet' if tablo_puani_eklendi else 'Hayır'}, tablo puanı: {weights['table']})")
    print(f"Toplam Skor (100 üzerinden): {min(toplam_skor, 100):.2f}")


# Main Evaluation
config = load_config("config.json")
urls = load_urls("urls.txt")
for url in urls:
    evaluate_pages_with_config(url, config)
