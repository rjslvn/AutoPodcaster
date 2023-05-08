import os
import requests
import json
import openai
from pydub import AudioSegment
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Set the OpenAI API key
openai.api_key = 'your_api_key_here'

# Function to convert text to speech using ElevenLabs API
def elevenlabs_speak(text):
    CHUNK_SIZE = 5000
    voice_id = "NkCxB2DN5XwgvsnhTRql"  # Replace with the appropriate voice ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": "your_api_key_here",
    }

    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.25,
            "similarity_boost": .6,
        },
    }
    # Send a POST request to the ElevenLabs API
    response = requests.post(url, headers=headers, json=data)

    # Retrieve the audio content from the response
    audio_content = b""
    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunk:
            audio_content += chunk

    return audio_content

# Function to fetch daily events from CNN website
def get_daily_events_for_date(date):
    url = "https://www.cnn.com"
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Unable to fetch news articles.")
        return []

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    daily_events = []

    # Extract headlines from the HTML content
    for headline in soup.find_all("h2"):
        daily_events.append(headline.get_text(strip=True))
    return daily_events

# Function to recursively expand a summary
def expand_summary(summary, depth=0, max_depth=1):
    if depth >= max_depth:
        return summary

    # Call the OpenAI API to expand the summary
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Expand on the following summary: {summary}",
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.7,
    )
    expanded = response.choices[0].text.strip()

    return expand_summary(expanded, depth=depth+1, max_depth=max_depth)

# Function to generate a summary from a news headline
def generate_summary(article):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Summarize the following news headline: {article}",
        max_tokens=2000,
        n=1,
        stop=None,
        temperature=0.7,
    )
    result = response.choices[0].text.strip()
    if not result:
        result = f"Unable to generate a summary for the headline: {article}"
    else:
        result = expand_summary(result)
    return result

# Function to stitch multiple MP3 files together
def stitch_mp3_files(mp3_files):
    output = AudioSegment.empty()
    for file in mp3_files:
        audio = AudioSegment.from_mp3(file)
        output += audio
    return output
# Main script
if __name__ == "__main__":
    # Get news articles for the previous day
    date = datetime.now() - timedelta(days=1)
    daily_events = get_daily_events_for_date(date)

    # Generate summaries for each daily event
    summaries = []
    for event in daily_events:
        expanded_summary = expand_summary(event)
        summary = generate_summary(expanded_summary)
        summaries.append(summary)

    # Print the generated summaries
    print("Generated summaries:", summaries)

    # Convert summaries to speech and save them as separate MP3 files
    mp3_files = []
    for i, summary in enumerate(summaries, start=1):
        audio_content = elevenlabs_speak(summary)
        file_name = f"Summary_{i}.mp3"
        with open(file_name, "wb") as audio_file:
            audio_file.write(audio_content)
        mp3_files.append(file_name)

    # Stitch the separate MP3 files together into a single file
    master_summary = stitch_mp3_files(mp3_files)
    # Export the stitched audio as an MP3 file
    master_summary.export("DailySummary.mp3", format="mp3")
