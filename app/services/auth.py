from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["Authentication"])

@router.get("/login")
async def steam_login():
    return RedirectResponse(
        f"https://steamcommunity.com/openid/login?"
        "openid.ns=http://specs.openid.net/auth/2.0&"
        "openid.mode=checkid_setup&"
        f"openid.return_to=http://localhost:8000/auth/callback&"
        "openid.realm=http://localhost:8000&"
        "openid.identity=http://specs.openid.net/auth/2.0/identifier_select&"
        "openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select"
    )

@router.get("/auth/callback")
async def steam_callback(request: Request):
    try:
        params = dict(request.query_params)
        steam_id = params.get("openid.claimed_id", "").split("/")[-1]
        return {"steam_id": steam_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {e}")