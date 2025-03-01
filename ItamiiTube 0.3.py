import yt_dlp
from tqdm import tqdm
import threading
import time
import sys
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime
import subprocess
import pkg_resources
import requests

# Globalne zmienne
failed_downloads = []
active_downloads = []
playlist_progress = None
lock = threading.Lock()

# Funkcja animacji trzech kropek - pokazuje ładowanie
# Funkcja do aktualizacji wspólnego paska postępu i listy aktywnych pobrań
def update_progress_bar(total_files):
    global playlist_progress

    while len(active_downloads) > 0 or playlist_progress.n < total_files:
        with lock:
            current_status = ", ".join(active_downloads)
        playlist_progress.set_description(f"Pobieranie: {current_status[:30]}{'...' if len(current_status) > 30 else ''}")
        playlist_progress.refresh()
        time.sleep(1)

# Funkcja do zapisania wersji bibliotek do pliku
def save_installed_versions_to_file():
    libraries = ["yt-dlp", "tqdm", "requests"]  # Lista bibliotek do monitorowania
    versions_info = {}

    for library in libraries:
        try:
            installed_version = pkg_resources.get_distribution(library).version
            versions_info[library] = installed_version
        except pkg_resources.DistributionNotFound:
            versions_info[library] = "Nie znaleziono"
   
###############DEV###############
 ## Funkcja do aktualizacji określonych bibliotek
#def update_libraries():
#    libraries = ["yt-dlp", "tqdm", "requests"]  # Lista bibliotek do zaktualizowania
#    
#    for library in libraries:
#        try:
#            print(f"Aktualizowanie {library}...")
#            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", library])
#            print(f"{library} zostało zaktualizowane.")
#        except subprocess.CalledProcessError as e:
#            print(f"Nie udało się zaktualizować {library}: {e}")
#
 ## Wywołanie funkcji aktualizującej
#update_libraries()
#################################












# Zmienna z wersją aktualną
current_version = "0.3.0"  # Zmieniaj tę wartość przy każdej aktualizacji

# Funkcja do zapisania wersji do pliku
def save_version_to_file(version):
    version_file_path = os.path.join(os.path.expanduser("~"), "Music", "ItamiiTube", "version.txt")
    with open(version_file_path, "w") as version_file:
        version_file.write(version)

# Funkcja do odczytania wersji z pliku
def read_version_from_file():
    version_file_path = os.path.join(os.path.expanduser("~"), "Music", "ItamiiTube", "version.txt")
    if os.path.exists(version_file_path):
        with open(version_file_path, "r") as version_file:
            return version_file.read().strip()
    else:
        return None

# Funkcja do sprawdzenia i aktualizacji aplikacji
def check_for_updates():
    stored_version = read_version_from_file()

    # Jeśli plik z wersją nie istnieje, zapisujemy wersję z kodu
    if stored_version is None:
        print("Brak pliku version.txt. Tworzę nowy plik z aktualną wersją...")
        save_version_to_file(current_version)
        stored_version = current_version

    # Sprawdzamy, czy wersja na GitHubie jest nowsza
    github_version = get_github_version()

    # Jeśli wersja GitHub jest nowsza, przeprowadzamy aktualizację
    if github_version > stored_version:
        print("Nowa wersja dostępna! Aktualizuję aplikację...")
        update_application()
    else:
        print("Aplikacja jest aktualna.")

# Funkcja do pobrania wersji z GitHub (można zmienić na API)
def get_github_version():
    # Przykładowa funkcja, która pobiera wersję z GitHub (zastąp odpowiednim API)
    # W tym przypadku wersja jest w pliku JSON na GitHubie
    try:
        response = requests.get("https://api.github.com/repos/twoje_repozitorio/twoja_aplikacja/releases/latest")
        response_data = response.json()
        return response_data["tag_name"]  # Zwraca tag wersji, np. "v1.0.1"
    except requests.RequestException as e:
        print(f"Błąd podczas pobierania wersji z GitHub: {e}")
        return current_version  # Jeśli coś pójdzie źle, pozostajemy przy aktualnej wersji

# Funkcja do aktualizacji aplikacji
def update_application():
    # Pobierz najnowszą wersję aplikacji z GitHub
    download_url = "https://github.com/twoje_repozitorio/twoja_aplikacja/releases/latest/download/your_application.exe"
    response = requests.get(download_url)

    if response.status_code == 200:
        download_path = os.path.join(os.getenv("ProgramFiles"), "ItamiiTube", "your_application.exe")
        with open(download_path, "wb") as file:
            file.write(response.content)
        print(f"Aplikacja zaktualizowana do wersji {current_version}.")
        # Zaktualizuj wersję w pliku version.txt
        save_version_to_file(current_version)
    else:
        print("Błąd podczas pobierania nowej wersji aplikacji.")

# Funkcja do usunięcia starego EXE
def remove_old_exe():
    old_exe_path = os.path.join(os.getenv("ProgramFiles"), "ItamiiTube", "old_version_application.exe")
    if os.path.exists(old_exe_path):
        os.remove(old_exe_path)
        print("Usunięto starą wersję aplikacji.")
    else:
        print("Nie znaleziono starej wersji do usunięcia.")

# Główna funkcja
def main():
    check_for_updates()

















# Funkcja, która obsługuje pasek postępu pobierania
def progress_hook(d):
    global progress_bar, loading

    if d['status'] == 'downloading':
        loading = False

        if progress_bar is None:
            total_size = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Pobieranie", ncols=100)

        current = d.get('downloaded_bytes', 0)
        progress_bar.n = current
        progress_bar.refresh()

    elif d['status'] == 'finished':
        if progress_bar:
            progress_bar.close()
        print(f"\nZakończono pobieranie: {d['filename']}")
        progress_bar = None

    elif d['status'] == 'extracting':
        loading = True

# Funkcja, która pobiera tytuł filmu z URL
def get_video_title(url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noprogress': True}) as ydl:
            # Wykrywanie serwisu
            if 'nicovideo.jp' in url:
                info_dict = ydl.extract_info(url, download=False)
                return info_dict.get('title', 'Nieznany tytuł z NicoVideo')
            elif 'youtube.com' in url or 'youtu.be' in url:
                info_dict = ydl.extract_info(url, download=False)
                return info_dict.get('title', 'Nieznany tytuł z YouTube')
            else:
                return "Nieznany serwis"
    except Exception as e:
        log_error(f"Błąd podczas uzyskiwania tytułu: {url}, {e}")
        return "Nieznany tytuł"

# Funkcja do logowania błędów do pliku
def log_error(error_message):
    log_folder = os.path.join(os.path.expanduser("~"), "Music", "ItamiiTube", "buglogs")
    os.makedirs(log_folder, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_folder, f"error_log_{timestamp}.txt")

    with open(log_file_path, "a") as log_file:
        log_file.write(f"{timestamp} - {error_message}\n")

# Funkcja do pobierania filmów z URL

# Funkcja do pobierania pojedynczego pliku
def download_video(url, output_path, file_format):
    global active_downloads
    video_title = get_video_title(url)

    # Konfiguracja opcji dla NicoVideo
    ydl_opts = {
        'format': f'{file_format}/best',
        'quiet': True,
        'noprogress': True,
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'age_limit': 0,  # Ignoruj ograniczenia wiekowe
    }

    # Jeśli format to mp3, dodajemy postprocessing
    if file_format == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }], 
        })

    with lock:
        active_downloads.append(video_title)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError as e:
        failed_downloads.append((url, "Błąd podczas pobierania"))  # Zmieniamy na URL w przypadku błędu
        log_error(f"Błąd podczas pobierania {url}: {e}")
    except Exception as e:
        failed_downloads.append((url, "Nieznany błąd"))  # Zmieniamy na URL w przypadku błędu
        log_error(f"Błąd podczas pobierania {url}: {e}")
    finally:
        with lock:
            active_downloads.remove(video_title)
            playlist_progress.update(1)

# Funkcja pobierająca filmy lub playlisty, obsługująca równoległe pobieranie
def download_videos(urls, output_path, file_format, num_threads):
    global playlist_progress, active_downloads

    total_files = len(urls)
    playlist_progress = tqdm(total=total_files, desc="Pobieranie playlisty", ncols=100, unit="pliki")

    # Wątek do aktualizacji paska
    updater_thread = threading.Thread(target=update_progress_bar, args=(total_files,))
    updater_thread.start()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(download_video, url, output_path, file_format) for url in urls]
        for future in futures:
            future.result()  # Obsługuje błędy podczas pobierania

    updater_thread.join()
    playlist_progress.close()

    # Wyświetl listę nieudanych pobrań
    if failed_downloads:
        print("\nLista nieudanych pobrań:")
        for video_title, reason in failed_downloads:
            print(f"Film: {video_title} - Powód: {reason}")
    else:
        print("\nWszystkie pliki pobrano pomyślnie.")
        
# Główna funkcja do uruchomienia w CMD
if __name__ == "__main__":
    main()
     # Zapisz aktualne wersje przy uruchomieniu
    while True:
        # Pętla do ponownego uruchamiania
        while True:
            url = input("Podaj link do YouTube, X (Twitter), Instagram itp.: ").strip()
            if ("youtube.com/watch?v=" in url or 
                "youtu.be/" in url or 
                "youtube.com/playlist?list=" in url or
                #"nicovideo.jp/watch/" in url or 
                #"vimeo.com/" in url or 
                #"dailymotion.com/video/" in url or
                "twitch.tv/" in url or 
                "facebook.com/" in url or 
                "instagram.com/" in url or
                "soundcloud.com/" in url or 
                #"bandcamp.com/" in url or 
                "tiktok.com/" in url or
                "mixcloud.com/" in url or 
                #"bilibili.com/" in url or 
                #"liveleak.com/" in url or
                "reddit.com/" in url or 
                #"periscope.tv/" in url or 
                #"metacafe.com/" in url or
                "x.com/" in url):
                break
            print("Nieprawidłowy link. Proszę podać poprawny link do YouTube lub NicoVideo.")


        output_path = os.path.join(os.path.expanduser("~"), "Music", "ItamiiTube")
        os.makedirs(output_path, exist_ok=True)

        is_playlist = "playlist" in url

        if is_playlist:
            folder_name = datetime.now().strftime("%Y-%m-%d")
            playlist_folder = os.path.join(output_path, folder_name)
            os.makedirs(playlist_folder, exist_ok=True)

            change_folder_name = input(f"Stworzono folder '{folder_name}'. Czy chcesz zmienić nazwę folderu? (tak/nie): ").strip().lower()
            if change_folder_name == "tak":
                new_folder_name = input("Podaj nową nazwę folderu: ").strip()
                if new_folder_name:
                    os.rename(playlist_folder, os.path.join(output_path, new_folder_name))
                    playlist_folder = os.path.join(output_path, new_folder_name)
                    print(f"Nazwa folderu zmieniona na: {new_folder_name}")

        else:
            playlist_folder = output_path

        # Wybór formatu zapisu pliku
        while True:
            print("\nDostępne formaty plików:")
            print("1. Najlepszy video + audio (domyślny)")
            print("2. Audio")
            print("3. Tylko video")
            print("4. MP3")
            print("5. Inny format (podaj ręcznie)")

            format_choice = input("Wybierz format (1/2/3/4/5): ").strip()

            if format_choice in ["1", "2", "3", "4", "5"]:
                if format_choice == "1":
                    file_format = 'bestvideo+bestaudio'
                elif format_choice == "2":
                    file_format = 'bestaudio'
                elif format_choice == "3":
                    file_format = 'bestvideo'
                elif format_choice == "4":
                    file_format = 'mp3'  # Nowa opcja MP3
                elif format_choice == "5 -wadliwe-":
                    file_format = input("Podaj format (np. mp4, webm, etc.): ").strip()
                break
            else:
                print("Nieprawidłowy wybór. Proszę spróbować ponownie.")

        # Wybór liczby wątków
        max_threads = os.cpu_count() or 4
        print(f"\nMaksymalna liczba wątków: {max_threads}")

        while True:
            try:
                num_threads = int(input(f"Ile wątków chcesz użyć (1-{max_threads}): ").strip())
                if 1 <= num_threads <= max_threads:
                    break
                else:
                    print(f"Proszę podać liczbę między 1 a {max_threads}.")
            except ValueError:
                print("Nieprawidłowa liczba. Proszę podać liczbę całkowitą.")

        # Pobieranie listy URL z playlisty
        if is_playlist:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                result = ydl.extract_info(url, download=False)
                urls = [entry['url'] for entry in result['entries']]
        else:
            urls = [url]

        # Rozpoczynamy pobieranie filmów
        download_videos(urls, playlist_folder, file_format, num_threads)

        # Zapytanie o ponowne pobranie
        retry = input("\nCzy chcesz pobrać coś jeszcze? (tak/nie): ").strip().lower()
        if retry not in ("tak", "t"):
            print("Dziękujemy za korzystanie z aplikacji!")
            break