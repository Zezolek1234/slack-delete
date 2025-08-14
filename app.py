import os
import re
import logging  # DODANO: Importujemy moduł do logowania
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# DODANO: Konfiguracja logowania, aby było widoczne na Render
logging.basicConfig(level=logging.INFO)

# Inicjalizacja aplikacji Flask
app = Flask(__name__)

# --- Konfiguracja ---
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    logging.error("Błąd krytyczny: Zmienna środowiskowa SLACK_BOT_TOKEN nie jest ustawiona.")
    exit()

# Inicjalizacja klienta Slack API
slack_client = WebClient(token=SLACK_BOT_TOKEN)

def parse_message_link(link):
    """
    Parsuje link do wiadomości Slacka, aby uzyskać ID kanału i timestamp.
    """
    # Usunięcie znaków '<' i '>' które Slack czasem dodaje
    clean_link = link.strip('<>')
    match = re.search(r'archives/([A-Z0-9]+)/p(\d{10})(\d{6})', clean_link)
    if match:
        channel_id = match.group(1)
        timestamp = f"{match.group(2)}.{match.group(3)}"
        return channel_id, timestamp
    return None, None

@app.route("/slack/delete-message", methods=["POST"])
def delete_message_command():
    data = request.form
    message_link = data.get("text")

    # DODANO: Logujemy otrzymany link
    logging.info(f"Otrzymano żądanie usunięcia z linkiem: '{message_link}'")

    if not message_link:
        return jsonify({"response_type": "ephemeral", "text": "Musisz podać link do wiadomości, którą chcesz usunąć."})

    channel_id, timestamp = parse_message_link(message_link)

    # DODANO: Logujemy wynik parsowania linku
    logging.info(f"Wynik parsowania -> Channel ID: {channel_id}, Timestamp: {timestamp}")

    if not channel_id or not timestamp:
        return jsonify({"response_type": "ephemeral", "text": "Nieprawidłowy format linku do wiadomości. Upewnij się, że wkleiłeś poprawny link."})

    try:
        # DODANO: Logujemy tuż przed wywołaniem API
        logging.info(f"Próba wywołania chat.delete z kanałem '{channel_id}' i timestampem '{timestamp}'")
        
        result = slack_client.chat_delete(channel=channel_id, ts=timestamp)
        
        # DODANO: Logujemy pełną odpowiedź od Slacka w przypadku sukcesu
        logging.info(f"Odpowiedź API Slacka (sukces): {result}")

        if result["ok"]:
            return jsonify({"response_type": "ephemeral", "text": "Wiadomość została pomyślnie usunięta."})
        else:
            error_message = result.get("error", "Nieznany błąd.")
            return jsonify({"response_type": "ephemeral", "text": f"Nie udało się usunąć wiadomości. Błąd: `{error_message}`"})

    except SlackApiError as e:
        # DODANO: Logujemy PEŁNĄ odpowiedź błędu od API Slacka
        logging.error(f"Wystąpił błąd SlackApiError. Pełna odpowiedź: {e.response}")
        return jsonify({"response_type": "ephemeral", "text": f"Wystąpił błąd API: {e.response['error']}"})

if __name__ == "__main__":
    app.run(debug=True, port=3000)
