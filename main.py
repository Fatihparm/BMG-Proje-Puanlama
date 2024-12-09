import requests
from bs4 import BeautifulSoup , Comment
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


score = 0
pages = []  # Pages in the website
headers = 0  # Headers in pages
isIndex = False  # If the URL is index.html or not

urls = ["https://fatihparm.github.io/ruh-ikizin/"]

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


def get_pages(urls):
    global isIndex  # 'isIndex' değişkenini global olarak kullan]

    for url in urls:
        print("URL: ", url)

        # Index kontrolü
        if url.endswith("index.html") or url.endswith("index.html/"):
            isIndex = True
        elif url.endswith(".com/") or url.endswith(".io/"):
            isIndex = True
            url = url + "index.html"
        elif url.endswith(".com") or url.endswith(".io"):
            isIndex = True
            url = url + "/index.html"
        else:
            isIndex = False

        # İlk URL'yi listeye ekle
        if url not in pages:
            pages.append(url)

        # İlk URL için istek yap
        response = polite_get(url)
        if response is None:
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a")

        # Bağlantıları ekle
        for link in links:
            href = link.get("href")
            if href and href.endswith(".html") and "://" not in href:
                page_link = f"{url.rsplit('/', 1)[0]}/{href}"
                if page_link not in pages:  # Aynı bağlantıyı tekrar eklemeyin
                    pages.append(page_link)

def has_header(content):
    if (content.find(["h1","h2","h3","h4","h5","h6"]) is not None):
        return True
    else:
        return False

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
    """
    Kontrol eder: Sayfa içeriğinde doğrudan <!-- --> şeklinde yorum var mı?
    """
    # Yorum düğümlerini bul
    comments = content.find_all(string=lambda text: isinstance(text, Comment))
    # Yorum varsa True döndür
    return bool(comments)


def has_image(content):
    """
    Kontrol eder: Sayfa içeriğinde en az bir resim var mı?
    """
    if content.find("img"):
        return True
    return False


def evaluate_pages():
    total_score = 0
    total_index_score = 0
    total_image_score = 0
    total_header_score = 0
    total_paragraph_score = 0
    pages_with_comments = 0
    comment_count = 0
    total_comment_score = 0
    table_score_added = False  # Tablo puanı eklenip eklenmediğini takip eder
    image_pages_count = 0  # Resim bulunan sayfa sayısı

    for page in pages:
        response = polite_get(page)
        if response is None:
            continue
        soup = BeautifulSoup(response.content, "html.parser")

        # Resim Kontrolü
        if has_image(soup):
            image_pages_count += 1

        # Header Kontrolü
        header_score = 4 if has_header(soup) else 0

        # Tablo Kontrolü
        if has_table(soup) and not table_score_added:  # Legal tablo kontrolü
            table_score_added = True

        # Paragraf Kontrolü
        paragraph_score = 4 if has_long_paragraph(soup) else 0

        # Yorum Kontrolü
        comment_count += 1 if has_comment(soup) else 0

        # Sayfa Bazlı Bilgileri Yazdır
        print("Sayfa: ", page)
        print(f"Header Puanı: {header_score}")
        print(f"Paragraf Puanı: {paragraph_score}")
        print(f"Yorum Satırı?: {has_comment(soup)}")
        print(f"Tablo Var mı?: {has_table(soup)}")
        print(f"Resim Var mı?: {has_image(soup)}")
        print("--------------------------------------------------")

        # Sayfa Bazlı Toplam
        total_header_score += header_score
        total_paragraph_score += paragraph_score
    print("Tüm Sayfaların Değerlendirilmesi Tamamlandı.")

    # Indeks Sayfa Kontrolü
    total_index_score = 4 * len(pages)
    if total_index_score >= 20:
        total_index_score = 20
    # Resim Puanını Toplam Skora Ekle
    total_image_score = min(image_pages_count * 4, 20)  # Maksimum 20 puan
    print(f"Resim Bulunan Sayfa Sayısı: {image_pages_count}")
    print(f"Resim Puanı: {total_image_score}")

    print(f"Yorum satırı olan sayfa sayısı: {comment_count}")

    # Tablo Puanını Toplam Skora Ekle
    table_score = 10 if table_score_added else 0
    print(f"Tablo Puanı: {table_score}")

    # Yorum Puanını Toplam Skora Ekle
    if comment_count == len(pages):
        total_comment_score = 10

    if total_header_score >= 20:
        total_header_score = 20
    
    if total_paragraph_score >= 20:
        total_paragraph_score = 20

    # Tüm Skorları Topla
    total_score = (
        total_image_score
        + total_index_score
        + total_header_score
        + total_paragraph_score
        + total_comment_score
        + table_score
    )

    # Toplam Puan Yazdır
    print("******************************************")
    print("İndeks Puanı: ", total_index_score)
    print("Header Puanı: ", total_header_score)
    print("Resim Puanı: ", total_image_score)
    print("Paragraf Puanı: ", total_paragraph_score)
    print("Yorum Puanı: ", total_comment_score)
    print("Tablo Puanı: ", table_score)
    print("Toplam Puan (100 üzerinden): ", min(total_score, 100))  # Maksimum 100

# Sayfaları Al ve Değerlendir
get_pages(urls)
evaluate_pages()

