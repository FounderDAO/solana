import requests
import csv

# URL API
API_URL = "https://topvalidators.app/api/validators"

# Получаем данные из API
response = requests.get(API_URL)
if response.status_code != 200:
    print("Ошибка запроса:", response.status_code)
    exit()
else:
    print("Данные получены")
    
# Преобразуем в JSON
validators = response.json()

# Фильтруем по наличию website
filtered_validators = [v for v in validators if v.get("website")]
print("All Validators Count", len(filtered_validators))
# Записываем в CSV
csv_filename = "validators_with_website.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # Заголовки
    writer.writerow(["Name", "Description", "Website"])
    # Данные
    for v in filtered_validators:
        writer.writerow([v.get("name", ""), v.get("description", ""), v.get("website", "")])

print(f"Файл {csv_filename} сохранён.")

