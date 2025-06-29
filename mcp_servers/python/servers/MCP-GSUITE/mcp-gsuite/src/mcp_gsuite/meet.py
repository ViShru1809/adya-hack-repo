from googleapiclient.discovery import build
from . import gauth
import logging
import traceback
from datetime import datetime
import pytz

class MeetService():
    def __init__(self, credentials):
        """
        Initialize the Meet service with provided credentials.
        
        Args:
            credentials: Google OAuth2 credentials object
        """
        authorized_credentials = gauth.authorize_credentials(credentials)
        self.service = build('calendar', 'v3', credentials=authorized_credentials)

    def create_meeting(self, summary: str, start_time: str, end_time: str,
                      description: str | None = None,
                      attendees: list | None = None,
                      timezone: str | None = None) -> dict | None:
        """
        Create a new Google Meet meeting.
        
        Args:
            summary (str): Title of the meeting
            start_time (str): Start time in RFC3339 format
            end_time (str): End time in RFC3339 format
            description (str, optional): Description of the meeting
            attendees (list, optional): List of attendee email addresses
            timezone (str, optional): Timezone for the meeting
            
        Returns:
            dict: Created meeting data or None if creation fails
        """
        try:
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_time,
                    'timeZone': timezone or 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': timezone or 'UTC',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }
            
            if description:
                event['description'] = description
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
                
            created_event = self.service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1,
                sendNotifications=True
            ).execute()
            
            return created_event
            
        except Exception as e:
            logging.error(f"Error creating Meet meeting: {str(e)}")
            logging.error(traceback.format_exc())
            return None 

    def cancel_meeting(self, event_id: str) -> bool:
        """
        Cancel a Google Meet meeting.
        
        Args:
            event_id (str): The ID of the meeting/event to cancel
            
        Returns:
            bool: True if successfully canceled, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendNotifications=True
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error canceling Meet meeting: {str(e)}")
            logging.error(traceback.format_exc())
            return False

    def reschedule_meeting(self, event_id: str, new_start_time: str, new_end_time: str,
                          timezone: str | None = None) -> dict | None:
        """
        Reschedule an existing Google Meet meeting.
        
        Args:
            event_id (str): The ID of the meeting/event to reschedule
            new_start_time (str): New start time in RFC3339 format
            new_end_time (str): New end time in RFC3339 format
            timezone (str, optional): Timezone for the meeting
            
        Returns:
            dict: Updated meeting data or None if update fails
        """
        try:
            # First get the existing event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update the time fields
            event['start'] = {
                'dateTime': new_start_time,
                'timeZone': timezone or event['start'].get('timeZone', 'UTC'),
            }
            event['end'] = {
                'dateTime': new_end_time,
                'timeZone': timezone or event['end'].get('timeZone', 'UTC'),
            }
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendNotifications=True
            ).execute()
            
            return updated_event
            
        except Exception as e:
            logging.error(f"Error rescheduling Meet meeting: {str(e)}")
            logging.error(traceback.format_exc())
            return None 

    def get_all_meetings(self, time_min: str | None = None, time_max: str | None = None, 
                        max_results: int = 100, include_past: bool = False) -> list:
        """
        Get all Google Meet meetings from the calendar.
        
        Args:
            time_min (str, optional): Start time in RFC3339 format. Defaults to current time.
            time_max (str, optional): End time in RFC3339 format
            max_results (int): Maximum number of meetings to return (default: 100)
            include_past (bool): Whether to include past meetings (default: False)
            
        Returns:
            list: List of meetings with Google Meet links
        """
        try:
            # If no time_min specified and not including past meetings, use current time
            if not time_min and not include_past:
                time_min = datetime.now(pytz.UTC).isoformat()

            # Prepare parameters
            params = {
                'calendarId': 'primary',
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime',
                'timeMin': time_min if time_min else None,
                'timeMax': time_max if time_max else None
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Execute the events().list() method
            events_result = self.service.events().list(**params).execute()
            
            # Extract only events with Google Meet links
            meetings = []
            for event in events_result.get('items', []):
                # Check if event has conferenceData (Meet link)
                if event.get('conferenceData') and event['conferenceData'].get('conferenceId'):
                    meeting = {
                        'id': event.get('id'),
                        'summary': event.get('summary'),
                        'description': event.get('description'),
                        'start': event.get('start'),
                        'end': event.get('end'),
                        'status': event.get('status'),
                        'creator': event.get('creator'),
                        'organizer': event.get('organizer'),
                        'attendees': event.get('attendees'),
                        'hangoutLink': event.get('hangoutLink'),
                        'conferenceData': event.get('conferenceData'),
                        'recurringEventId': event.get('recurringEventId'),
                        'created': event.get('created'),
                        'updated': event.get('updated')
                    }
                    meetings.append(meeting)
            
            return meetings
            
        except Exception as e:
            logging.error(f"Error retrieving Meet meetings: {str(e)}")
            logging.error(traceback.format_exc())
            return []