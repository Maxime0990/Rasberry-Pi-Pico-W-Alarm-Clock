import os

def read_ics(file_path):
    """
    Reads an ICS file and extracts marked events.
    Assumes events are marked with a specific keyword in the DESCRIPTION field (e.g., "ALARM").
    """
    if not os.path.exists(file_path):
        print("File not found:", file_path)
        return []

    events = []
    with open(file_path, 'r') as f:
        event_data = {}
        for line in f:
            line = line.strip()
            if line.startswith("BEGIN:VEVENT"):
                event_data = {}  # Start a new event
            elif line.startswith("END:VEVENT"):
                # Add event if it is marked for an alarm
                if "ALARM" in event_data.get("DESCRIPTION", ""):
                    events.append(event_data)
                event_data = {}  # Clear event data
            elif ":" in line:
                # Parse key-value pairs from the ICS file
                key, value = line.split(":", 1)
                event_data[key] = value
    return events

def format_event_times(events):
    """
    Formats extracted events for display or processing.
    """
    formatted_events = []
    for event in events:
        title = event.get("SUMMARY", "No Title")
        start_time = event.get("DTSTART", "Unknown Time")
        formatted_events.append({"title": title, "start_time": start_time})
    return formatted_events

# File path to the ICS file on the Pico
ics_file_path = "/path/to/your_calendar.ics"

# Read and process the ICS file
marked_events = read_ics(ics_file_path)
if marked_events:
    print("Extracted Marked Events:")
    for event in format_event_times(marked_events):
        print(f"Title: {event['title']}, Time: {event['start_time']}")
else:
    print("No marked events found or file is missing.")
