import os
import re
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

# --- Konfiguracja ---
# Pobierz token bota ze zmiennej środowiskowej dla bezpieczeństwa
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    print("Błąd: Zmienna środowiskowa SLACK_BOT_TOKEN nie jest ustawiona.")
    exit()

# Inicjalizacja klienta Slack API
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Funkcja do parsowania linku wiadomości
def parse_message_link(link):
    """
    Parsuje link do wiadomości Slacka, aby uzyskać ID kanału i timestamp.
    Przykładowy link: https://twojworkspace.slack.com/archives/C12345678/p1629885698000100
    """
    match = re.search(r'archives/([A-Z0-9]+)/p(\d{10})(\d{6})', link)
    if match:
        channel_id = match.group(1)
        # Timestamp w Slack API wymaga kropki przed ostatnimi 6 cyframi
        timestamp = f"{match.group(2)}.{match.group(3)}"
        return channel_id, timestamp
    return None, None

# Endpoint, który będzie obsługiwał komendę
@app.route("/slack/delete-message", methods=["POST"])
def delete_message_command():
    # Pobranie danych z żądania od Slacka
    data = request.form
    message_link = data.get("text")

    if not message_link:
        return jsonify({"response_type": "ephemeral", "text": "Musisz podać link do wiadomości, którą chcesz usunąć."})

    # Parsowanie linku
    channel_id, timestamp = parse_message_link(message_link)

    if not channel_id or not timestamp:
        return jsonify({"response_type": "ephemeral", "text": "Nieprawidłowy format linku do wiadomości. Upewnij się, że wkleiłeś poprawny link."})

    try:
        # Wywołanie API Slacka w celu usunięcia wiadomości
        result = slack_client.chat_delete(channel=channel_id, ts=timestamp)

        if result["ok"]:
            return jsonify({"response_type": "ephemeral", "text": "Wiadomość została pomyślnie usunięta."})
        else:
            # Zwrócenie błędu, jeśli usunięcie się nie powiodło
            error_message = result.get("error", "Nieznany błąd.")
            return jsonify({"response_type": "ephemeral", "text": f"Nie udało się usunąć wiadomości. Błąd: `{error_message}`"})

    except SlackApiError as e:
        # Obsługa błędów API
        return jsonify({"response_type": "ephemeral", "text": f"Wystąpił błąd API: {e.response['error']}"})

# Uruchomienie serwera
if __name__ == "__main__":
    # Pamiętaj, aby w środowisku produkcyjnym użyć serwera WSGI, np. Gunicorn
    app.run(debug=True, port=3000)
