#
# Copyright (c) 2024 Airbyte, Inc., all rights reserved.
#

import requests
import concurrent.futures

from requests import Request, Session
from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential

from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.requests_native_auth import TokenAuthenticator

from abc import ABC


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
    cursor_field = "fromDate"
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
query Transcripts(
  $fromDate: DateTime
  $toDate: DateTime
  $hostEmail: String
  $participantEmail: String
  $limit: Int
  $skip: Int
) {
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
        if self.config.get("startDate"):
            variables["fromDate"] = format_datetime(self.config["startDate"])
        if self.config.get("endDate"):
            variables["toDate"] = format_datetime(self.config["endDate"])
        if stream_slice:
            variables["hostEmail"] = stream_slice["hostEmail"]
            variables["participantEmail"] = stream_slice["participantEmail"]
        variables["limit"] = 50
        variables["skip"] = next_page_token.get("skip", 0) if next_page_token else 0

        request_body = {"query": query, "variables": variables}
        return request_body

    def stream_slices(self, **kwargs) -> Iterable[Optional[Mapping[str, Any]]]:
        for host_email in self.config.get("host_emails", []):
            for participant_email in self.config.get("participant_emails", []):
                yield {"hostEmail": host_email, "participantEmail": participant_email}

    # overwrite needed because of fireflies api needs arent meet by base http class
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _fetch_next_page(
        self,
        stream_slice: Optional[Mapping[str, Any]] = None,
        stream_state: Optional[Mapping[str, Any]] = None,
        next_page_token: Optional[Mapping[str, Any]] = None,
    ) -> Tuple[requests.PreparedRequest, requests.Response]:
        url = self.url_base
        headers = self.request_headers()
        json_body = self.request_body_json(stream_state, stream_slice, next_page_token)

        session = Session()
        request = Request(self.request_method(), url, headers=headers, json=json_body)
        prepared_request = session.prepare_request(request)

        response = session.send(prepared_request)
        response.raise_for_status()

        return prepared_request, response

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

    def read_records(self, **kwargs) -> Iterable[Mapping[str, Any]]:
        streams = self.streams(self.config)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(stream.read_records, **kwargs) for stream in streams]
            for future in concurrent.futures.as_completed(futures):
                for record in future.result():
                    yield record
