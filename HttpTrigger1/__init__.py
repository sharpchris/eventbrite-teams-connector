import logging, os, httpx
from sys import api_version
from typing import List

import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:

    # Catch the webhook sent by Eventbrite for a new Order being placed
    logging.info('Python HTTP trigger function processed a request.')
    try:
        req_body: List = req.get_json()
        url: str = req_body['api_url']
    except:
        print("Could not find 'api_url' in the request body")

        return func.HttpResponse(
            f"Did not find the api_url",
            status_code=400
        )

    # Get the Attendees listed on the received Eventbrite Order
    headers = {"Authorization": f"Bearer {os.environ['eventbriteToken']}"}
    # Append "attendees" to the Eventbrite API URL simplify getting the attendees from the Order
    url += "attendees"
    r = httpx.get(url, headers=headers)

    # Get the emails of the attendees in the Eventbrite Order
    emails = []
    for attendee in r.json()['attendees']:
        emails.append(attendee['profile']['email'])

    # Post the emails one by one to Power Automate for adding to the Team
    p_url = os.environ['powerAutomateURL']
    p_params = {
        "api-version":"2016-06-01",
        "sv":"1.0",
        "sp":"%2Ftriggers%2Fmanual%2Frun",
        "sig": os.environ['powerAutomateSig']
    }
    for email in emails:
        data = {"email": email}
        p = httpx.post(p_url, json=data, params=p_params)

    # Respond to Eventbrite to let them know the webhook address is still working
    return func.HttpResponse(
        f"Found the api_url {url}\n The email(s) posted were {emails}\nand were sent to {p.url}\nwith content {p.content}",
        status_code=200,
    )

