from fastapi import FastAPI
from fastmcp import FastMCP
import httpx
import requests

mcp = FastMCP("My MCP Server")

# -------------------------------
# Initialize MCP
# -------------------------------


# -------------------------------
# MCP Tools
# -------------------------------
@mcp.tool
def greet(name: str) -> str:
    return f"Hello, {name}!"


@mcp.tool
def add(a: int, b: int) -> int:
    return a + b


@mcp.tool
def get_objects() -> dict:
    """Fetch public data"""
    try:
        response = requests.get(
            "https://api.restful-api.dev/objects", timeout=10)
        response.raise_for_status()
        return {"result": response.json()}
    except requests.RequestException as e:
        return {"result": f"Error fetching data: {e}"}


def get_access_token() -> str:
    url = "https://dev.falkonsms.com/auth/connect/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "scope": "API",
        "client_id": "Client1",
        "Client_secret": "Client1Secret"
    }

    with httpx.Client(verify=True) as client:
        response = client.post(url, data=data, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to get token: {response.text}")
        return response.json()["access_token"]


@mcp.tool
def send_sms(ToPhoneNumber: str, Body: str) -> str:
    """Send SMS using Falkon SMS API."""
    try:
        token = get_access_token()
        url = "https://dev.falkonsms.com/be-api/api/Messages/Send"
        headers = {
            "Accept": "text/plain",
            "PhoneNumber": "+12407461350",
            "PhoneNumberId": "7b236508-634f-4d03-9676-fdf888f35c29",
            "Authorization": f"Bearer {token}",
            "GroupId": "0",
            "Provider": "Bandwidth",
            "OrgReference": "FBE3",
            "OrganizationId": "5f9ea413-2c36-4826-98db-fc7b46b8186c",
            "UserId": "64476efb-e665-4ff6-ae40-f391023ff725"
        }
        files = {
            "Body": (None, Body),
            "ToPhoneNumber": (None, ToPhoneNumber),
            "Credits": (None, "1"),
            "SequenceId": (None, "")
        }

        with httpx.Client() as client:
            res = client.post(url, headers=headers, files=files)

        if res.status_code == 200:
            return f"✅ Message sent successfully to {ToPhoneNumber}"
        else:
            return f"❌ Failed: {res.status_code} - {res.text}"

    except Exception as e:
        return f"Error: {str(e)}"


mcp_app = mcp.http_app(path='/mcp')

# -------------------------------
# Initialize FastAPI
# -------------------------------
app = FastAPI(title="My Unified API + MCP Server", lifespan=mcp_app.lifespan)
app.mount("/analytics", mcp_app)


# -------------------------------
# Example normal FastAPI routes
# -------------------------------
@app.get("/")
def home():
    return {"message": "Welcome to FastAPI + MCP unified server 🚀"}


@app.get("/api/ping")
def ping():
    return {"status": "ok", "msg": "FastAPI route working fine!"}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
