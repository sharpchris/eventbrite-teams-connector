import logging, os, httpx, asyncio
from typing import List

import azure.functions as func

async def post_emails(emails: List[str]) -> None:
    # Post the emails to Power Automate for adding to the Team
    p_url = os.environ['powerAutomateURL']
    p_params = {
        "api-version":"2016-06-01",
        "sv":"1.0",
        "sp":"/triggers/manual/run",
        "sig": os.environ['powerAutomateSig']
    }
    for email in emails:
        data = {"email": email}
        async with httpx.AsyncClient() as client:
            try:
                # Would make this async if I though people were adding more than one attendee per order
                p = await client.post(p_url, json=data, params=p_params)
                p.raise_for_status()
                logging.info(f"Added {email} to the Team.")
            except:
                # Could catch errors in adding people to the Team
                # a 5xx would be caught here if the attendee's email address wasn't in the company's Active Directory
                client.aclose()
        

def main(req: func.HttpRequest) -> func.HttpResponse:

    # Catch the webhook sent by Eventbrite for a new Order being placed
    logging.info('Python HTTP trigger function processed a request.')

    # Check to see if this is just an Eventbrite test
    try:
        if req.get_json()['config']['action'] == "test":
            return func.HttpResponse(
                f"Endpoint test successful",
                status_code=200
            )
    except:
        pass

    # Get the Eventbrite API URL where more info can be found about the order
    try:
        req_body: List = req.get_json()
        url: str = req_body['api_url']
    except:
        print("Could not find 'api_url' in the request body")
        return func.HttpResponse(
            "Could not find 'api_url' in the request body",
            status_code=400
        )

    # Get the Attendees listed on the received Eventbrite Order
    headers = {"Authorization": f"Bearer {os.environ['eventbriteToken']}"}
    # Append "attendees" to the Eventbrite API URL simplify getting the attendees from the Order
    url += "attendees"
    try:
        r = httpx.get(url, headers=headers)
    except:
        print(f"Could not reach Eventbrite api url {url}")
        return func.HttpResponse(
            f"Could not reach Eventbrite api url {url}",
            status_code=400
        )

    # Get the emails of the attendees in the Eventbrite Order
    emails: List[str] = []
    try:
        for attendee in r.json()['attendees']:
            emails.append(attendee['profile']['email'])
    except KeyError:
        print(f"Could not find ['attendees'] in the response from the Eventbrite api for the url {url}")
        return func.HttpResponse(
            f"Could not find ['attendees'] in the response from the Eventbrite api for the url {url}",
            status_code=400
        )

    # Async post the emails
    asyncio.run(post_emails(emails))
            
    # Respond to Eventbrite to let them know the webhook address is still working
    return func.HttpResponse(
        f"Found the api_url {url}\nThe email(s) posted were {emails}",
        status_code=201,
    )

