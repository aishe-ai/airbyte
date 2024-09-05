#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#


from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple
import requests

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator

from datetime import datetime, timezone


def format_datetime(dt_string):
    dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class FirefliesAiStream(HttpStream, ABC):
    url_base = "https://api.fireflies.ai/graphql"

    def __init__(self, config: Mapping[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.config = config

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        data = response.json()
        if len(data.get("data", {}).get("transcripts", [])) == 50:
            return {"skip": response.request.body["variables"]["skip"] + 50}
        return None

    def request_params(
        self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        return {}

    def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
        data = response.json()
        for transcript in data.get("data", {}).get("transcripts", []):
            yield transcript


class Transcripts(FirefliesAiStream):
    primary_key = "id"

    def path(self, **kwargs) -> str:
        return ""

    def request_headers(self, **kwargs) -> Mapping[str, Any]:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self.config['credentials']['api_key']}"}

    def request_body_json(
        self,
        stream_state: Mapping[str, Any],
        stream_slice: Mapping[str, Any] = None,
        next_page_token: Mapping[str, Any] = None,
    ) -> Optional[Mapping]:
        query = """
        query Transcripts($fromDate: DateTime, $toDate: DateTime, $hostEmail: [String], $participantEmail: [String], $limit: Int, $skip: Int) {
          transcripts(
            fromDate: $fromDate
            toDate: $toDate
            host_email: $hostEmail
            participant_email: $participantEmail
            limit: $limit
            skip: $skip
          ) {
            id
            sentences {
              index
              speaker_name
              speaker_id
              text
              raw_text
              start_time
              end_time
              ai_filters {
                task
                pricing
                metric
                question
                date_and_time
                text_cleanup
                sentiment
              }
            }
            title
            speakers {
              id
              name
            }
            host_email
            organizer_email
            meeting_info {
              fred_joined
              silent_meeting
              summary_status
            }
            calendar_id
            user {
              user_id
              email
              name
              num_transcripts
              recent_meeting
              minutes_consumed
              is_admin
              integrations
            }
            fireflies_users
            participants
            date
            transcript_url
            audio_url
            video_url
            duration
            meeting_attendees {
              displayName
              email
              phoneNumber
              name
              location
            }
            summary {
              gist
              bullet_gist
              short_overview
              action_items
              keywords
              outline
              overview
              shorthand_bullet
            }
          }
        }
        """

        variables = {}
        # In the request_body_json method:
        if self.config.get("startDate"):
            variables["fromDate"] = format_datetime(self.config["startDate"])
        if self.config.get("endDate"):
            variables["toDate"] = format_datetime(self.config["endDate"])
        if self.config.get("host_emails"):
            variables["hostEmail"] = self.config["host_emails"]
        if self.config.get("participant_emails"):
            variables["participantEmail"] = self.config["participant_emails"]
        variables["limit"] = 50
        variables["skip"] = next_page_token.get("skip", 0) if next_page_token else 0

        request_body = {"query": query, "variables": variables}
        print(request_body)
        return request_body

    def request_method(self) -> str:
        return "POST"


class SourceFirefliesAi(AbstractSource):
    def check_connection(self, logger, config) -> Tuple[bool, any]:
        try:
            url = "https://api.fireflies.ai/graphql"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config['credentials']['api_key']}"}
            query = "query { transcripts(limit: 1) { id } }"
            response = requests.post(url, headers=headers, json={"query": query})
            response.raise_for_status()
            return True, None
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        auth = TokenAuthenticator(token=config["credentials"]["api_key"])
        return [Transcripts(authenticator=auth, config=config)]
